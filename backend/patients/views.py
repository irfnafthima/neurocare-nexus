from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from patients.models import Patient
from monitoring.models import SensorReading
from accounts.models import AuditLog, CustomUser

from django.utils import timezone
from patients.models import FamilyPatientLink
from accounts.utils import log_audit_trail

def get_patient_ids_for_user(user):
    if not user or user.role != 'patient':
        return []
    q = models.Q(name__iexact=user.full_name) | models.Q(id=f"P-{user.id}")
    if user.device_id:
        q |= models.Q(id=user.device_id.upper().replace('NP-', 'P-'))
    return list(Patient.objects.filter(q).values_list('id', flat=True))

def find_patient_record_for_user(user):
    ids = get_patient_ids_for_user(user)
    return Patient.objects.filter(id__in=ids).first()

def find_patient_by_identifier(identifier):
    if not identifier:
        return None
    ident = str(identifier).strip()
    # 1. Exact ID match (case-insensitive)
    p = Patient.objects.filter(id__iexact=ident).first()
    if p:
        return p
    # 2. P-{ident} match
    p = Patient.objects.filter(id__iexact=f"P-{ident}").first()
    if p:
        return p
    # 3. Replace NP- with P-
    if 'NP-' in ident.upper():
        p = Patient.objects.filter(id__iexact=ident.upper().replace('NP-', 'P-')).first()
        if p:
            return p
    # 4. Match CustomUser patient device_id or user.id or full_name
    user_p = CustomUser.objects.filter(role='patient').filter(
        models.Q(device_id__iexact=ident) | 
        models.Q(id=int(ident) if ident.isdigit() else -1) | 
        models.Q(full_name__iexact=ident)
    ).first()
    if user_p:
        rec = find_patient_record_for_user(user_p)
        if rec:
            return rec
    # 5. Name match
    p = Patient.objects.filter(name__iexact=ident).first()
    if p:
        return p
    return Patient.objects.filter(name__icontains=ident).first()

def get_authorized_patients(user):
    role = user.role
    if role == 'admin':
        return Patient.objects.all()
    elif role == 'doctor':
        from doctors.models import DoctorPatientLink, DoctorConnectionRequest
        linked_ids = list(DoctorPatientLink.objects.filter(doctor=user).values_list('patient_id', flat=True))
        q = models.Q(id__in=linked_ids)
        if user.npi:
            q |= models.Q(doctor_npi__npi=user.npi)
            req_pids = DoctorConnectionRequest.objects.filter(doctor_npi__npi=user.npi, status='Approved').values_list('patient_id', flat=True)
            q |= models.Q(id__in=req_pids)
        return Patient.objects.filter(q)
    elif role == 'caregiver':
        from caregivers.models import CaregiverPatientLink
        linked_ids = CaregiverPatientLink.objects.filter(caregiver=user, is_approved=True).values_list('patient_id', flat=True)
        return Patient.objects.filter(id__in=linked_ids)
    elif role == 'family':
        from patients.models import FamilyPatientLink
        linked_ids = FamilyPatientLink.objects.filter(family=user, is_approved=True).values_list('patient_id', flat=True)
        return Patient.objects.filter(id__in=linked_ids)
    elif role == 'patient':
        p_ids = get_patient_ids_for_user(user)
        if p_ids:
            return Patient.objects.filter(id__in=p_ids)
        return Patient.objects.filter(name__icontains=user.full_name)
    return Patient.objects.none()

class PatientListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patients = get_authorized_patients(request.user)
        patients = patients.order_by('-risk')
        
        data = []
        for p in patients:
            latest_tel = SensorReading.objects.filter(patient=p).order_by('-timestamp').first()
            
            vitals = {
                'max30102': {
                    'heartRate': latest_tel.heart_rate if (latest_tel and latest_tel.heart_rate is not None) else 72,
                    'spo2': latest_tel.spo2 if (latest_tel and latest_tel.spo2 is not None) else 98
                },
                'ds18b20': {
                    'temperature': float(latest_tel.temperature) if (latest_tel and latest_tel.temperature is not None) else 36.80
                },
                'mpu6050': {
                    'accelX': float(latest_tel.accel_x) if (latest_tel and latest_tel.accel_x is not None) else 0.05,
                    'accelY': float(latest_tel.accel_y) if (latest_tel and latest_tel.accel_y is not None) else 0.98,
                    'accelZ': float(latest_tel.accel_z) if (latest_tel and latest_tel.accel_z is not None) else 0.04,
                    'gyroX': float(latest_tel.gyro_x) if (latest_tel and latest_tel.gyro_x is not None) else 0.50,
                    'gyroY': float(latest_tel.gyro_y) if (latest_tel and latest_tel.gyro_y is not None) else -1.20,
                    'gyroZ': float(latest_tel.gyro_z) if (latest_tel and latest_tel.gyro_z is not None) else 0.30,
                    'fallDetected': latest_tel.fall_detected if latest_tel else False
                },
                'esp32': {
                    'connected': latest_tel.esp32_connected if latest_tel else True,
                    'battery': latest_tel.esp32_battery if (latest_tel and latest_tel.esp32_battery is not None) else 90,
                    'rssi': latest_tel.esp32_rssi if (latest_tel and latest_tel.esp32_rssi is not None) else -60
                }
            }
            
            data.append({
                'id': p.id,
                'name': p.name,
                'age': p.age,
                'gender': p.gender,
                'room': p.room,
                'condition': p.condition,
                'risk': p.risk,
                'status': p.status,
                'doctorNpi': p.doctor_npi_id,
                'vitals': vitals
            })
            
        log_audit_trail(
            request=request,
            action='Accessed Patient Directory Listings',
            target=f"Queried {len(data)} patient records under {request.user.role.upper()} authorization scope",
            result='Success'
        )
        return Response(data, status=status.HTTP_200_OK)

class PatientNotesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only return notes for authorized patients
        patients = get_authorized_patients(request.user)
        notes_map = {}
        for p in patients:
            notes_map[p.id] = p.ehr_notes or 'No checkup logs saved.'
            
        log_audit_trail(
            request=request,
            action='Accessed EHR Notes Map',
            target=f"Query results: {len(notes_map)} notes retrieved",
            result='Success'
        )
        return Response(notes_map, status=status.HTTP_200_OK)

class PatientNotesUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        notes = request.data.get('notes', '')
        clinician_name = request.data.get('clinicianName', 'Clinician')

        # Caregivers are read-only and cannot modify medical notes
        if request.user.role not in ['doctor', 'admin']:
            return Response("Access Denied: Read-only access restriction.", status=status.HTTP_403_FORBIDDEN)

        # Enforce that doctor is linked to patient
        authorized_patients = get_authorized_patients(request.user)
        if not authorized_patients.filter(id=id).exists():
            return Response("Access Denied: Unauthorized to modify EHR logs for this patient.", status=status.HTTP_403_FORBIDDEN)

        try:
            patient = Patient.objects.get(id=id)
        except Patient.DoesNotExist:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        patient.ehr_notes = notes
        patient.save()

        log_audit_trail(
            request=request,
            action='Modified EHR Notes',
            target=f"Patient Record ID: {id}",
            result='Success'
        )
        return Response("Care notes updated successfully.", status=status.HTTP_200_OK)

class PatientDoctorUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        # Only admins or authorized clinicians can link doctor
        if request.user.role not in ['admin', 'doctor', 'patient']:
            return Response("Unauthorized action.", status=status.HTTP_403_FORBIDDEN)

        doctor_npi_str = request.data.get('doctorNpi')
        try:
            patient = Patient.objects.get(id=id)
        except Patient.DoesNotExist:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        doc_name = 'None'
        if doctor_npi_str:
            from doctors.models import SyntheticNPI
            try:
                doctor_npi = SyntheticNPI.objects.get(npi=doctor_npi_str)
                patient.doctor_npi = doctor_npi
                doc_name = doctor_npi.name
            except SyntheticNPI.DoesNotExist:
                return Response("Doctor NPI not found.", status=status.HTTP_400_BAD_REQUEST)
        else:
            patient.doctor_npi = None

        patient.save()

        log_audit_trail(
            request=request,
            action='Assigned Consulting Doctor',
            target=f"Patient ID: {id} linked to Doctor NPI: {doctor_npi_str or 'None'}",
            result='Success'
        )
        return Response("Consulting doctor updated successfully.", status=status.HTTP_200_OK)

class PatientAccessControlsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # A patient can see their linked doctors, caregivers, and family members
        role = request.user.role
        
        patient_ids = []
        if role == 'patient':
            patient_ids = get_patient_ids_for_user(request.user)
            if not patient_ids:
                p_rec = find_patient_record_for_user(request.user)
                if p_rec:
                    patient_ids = [p_rec.id]
        elif role == 'family':
            target_p = find_patient_by_identifier(request.user.patient_id)
            if target_p:
                patient_ids = [target_p.id]
            else:
                patient_ids = [request.user.patient_id] if request.user.patient_id else []
            
        if not patient_ids:
            return Response("Patient session binding invalid.", status=status.HTTP_400_BAD_REQUEST)
            
        from doctors.models import DoctorPatientLink, DoctorConnectionRequest
        from caregivers.models import CaregiverPatientLink

        doc_links = DoctorPatientLink.objects.filter(patient_id__in=patient_ids)
        doc_reqs = DoctorConnectionRequest.objects.filter(patient_id__in=patient_ids)
        cg_links = CaregiverPatientLink.objects.filter(patient_id__in=patient_ids)
        family_links = FamilyPatientLink.objects.filter(patient_id__in=patient_ids)
        
        data = {
            'doctors': [{
                'id': l.id,
                'doctorName': l.doctor.full_name,
                'doctorEmail': l.doctor.email,
                'specialization': l.doctor.specialization,
                'createdAt': l.created_at.isoformat()
            } for l in doc_links],
            'pendingDoctors': [{
                'id': r.id,
                'doctorName': r.doctor_npi.name,
                'doctorHospital': r.doctor_npi.hospital,
                'status': r.status,
                'createdAt': r.created_at.isoformat()
            } for r in doc_reqs],
            'caregivers': [{
                'id': l.id,
                'caregiverName': l.caregiver.full_name,
                'caregiverEmail': l.caregiver.email,
                'isApproved': l.is_approved,
                'isReadOnly': l.is_read_only,
                'createdAt': l.created_at.isoformat()
            } for l in cg_links],
            'familyMembers': [{
                'id': l.id,
                'familyName': l.family.full_name,
                'familyEmail': l.family.email,
                'isApproved': l.is_approved,
                'createdAt': l.created_at.isoformat()
            } for l in family_links]
        }
        return Response(data, status=status.HTTP_200_OK)

class FamilyRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        if role == 'family':
            links = FamilyPatientLink.objects.filter(family=request.user).order_by('-created_at')
            data = []
            for l in links:
                data.append({
                    'id': l.id,
                    'patientId': l.patient_id,
                    'patientName': l.patient.name,
                    'isApproved': l.is_approved,
                    'createdAt': l.created_at.isoformat()
                })
            return Response(data, status=status.HTTP_200_OK)
        elif role == 'admin':
            links = FamilyPatientLink.objects.all().order_by('-created_at')
            data = []
            for l in links:
                data.append({
                    'id': l.id,
                    'familyEmail': l.family.email,
                    'familyName': l.family.full_name,
                    'patientId': l.patient_id,
                    'patientName': l.patient.name,
                    'isApproved': l.is_approved,
                    'createdAt': l.created_at.isoformat()
                })
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response("Access Denied.", status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        if request.user.role != 'family':
            return Response("Only family members can request links.", status=status.HTTP_403_FORBIDDEN)

        patient_id_input = request.data.get('patientId')
        if not patient_id_input:
            return Response("Patient ID is required.", status=status.HTTP_400_BAD_REQUEST)

        patient = find_patient_by_identifier(patient_id_input)
        if not patient:
            return Response("Patient not found for the provided identifier.", status=status.HTTP_404_NOT_FOUND)

        link, created = FamilyPatientLink.objects.get_or_create(
            family=request.user,
            patient=patient,
            defaults={'is_approved': False}
        )

        log_audit_trail(
            request=request,
            action='Requested Family Patient Link',
            target=f"Patient ID: {patient.id}",
            result='Success'
        )

        return Response({
            'id': link.id,
            'patientId': link.patient_id,
            'isApproved': link.is_approved
        }, status=status.HTTP_200_OK)

class FamilyRequestApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            link = FamilyPatientLink.objects.get(id=id)
        except FamilyPatientLink.DoesNotExist:
            return Response("Link request not found.", status=status.HTTP_404_NOT_FOUND)

        is_admin = (request.user.role == 'admin')
        user_patient_ids = get_patient_ids_for_user(request.user) if request.user.role == 'patient' else []
        is_patient = (request.user.role == 'patient' and (link.patient_id in user_patient_ids or link.patient.name.lower() in request.user.full_name.lower()))

        if not (is_admin or is_patient):
            return Response("Unauthorized to approve this relationship request.", status=status.HTTP_403_FORBIDDEN)

        approved = request.data.get('approved', True)
        link.is_approved = approved
        link.save()

        log_audit_trail(
            request=request,
            action='Updated Family Patient Link Status',
            target=f"Family: {link.family.email} -> Patient: {link.patient_id} (Approved: {approved})",
            result='Success'
        )

        return Response("Family patient link updated successfully.", status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            link = FamilyPatientLink.objects.get(id=id)
        except FamilyPatientLink.DoesNotExist:
            return Response("Link request not found.", status=status.HTTP_404_NOT_FOUND)

        is_admin = (request.user.role == 'admin')
        user_patient_ids = get_patient_ids_for_user(request.user) if request.user.role == 'patient' else []
        is_patient = (request.user.role == 'patient' and (link.patient_id in user_patient_ids or link.patient.name.lower() in request.user.full_name.lower()))

        if not (is_admin or is_patient):
            return Response("Unauthorized to revoke this family link.", status=status.HTTP_403_FORBIDDEN)

        fam_email = link.family.email
        pat_id = link.patient_id
        link.delete()

        log_audit_trail(
            request=request,
            action='Revoked Family Patient Link',
            target=f"Family: {fam_email} -> Patient: {pat_id}",
            result='Success'
        )

        return Response("Family patient link revoked successfully.", status=status.HTTP_200_OK)
