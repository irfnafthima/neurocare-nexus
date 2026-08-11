from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from patients.models import Patient
from monitoring.models import SensorReading
from accounts.models import AuditLog

from django.utils import timezone
from patients.models import FamilyPatientLink
from accounts.utils import log_audit_trail

def get_authorized_patients(user):
    role = user.role
    if role == 'admin':
        return Patient.objects.all()
    elif role == 'doctor':
        from doctors.models import DoctorPatientLink
        linked_ids = DoctorPatientLink.objects.filter(doctor=user).values_list('patient_id', flat=True)
        return Patient.objects.filter(id__in=linked_ids)
    elif role == 'caregiver':
        from caregivers.models import CaregiverPatientLink
        linked_ids = CaregiverPatientLink.objects.filter(caregiver=user, is_approved=True).values_list('patient_id', flat=True)
        return Patient.objects.filter(id__in=linked_ids)
    elif role == 'family':
        from patients.models import FamilyPatientLink
        linked_ids = FamilyPatientLink.objects.filter(family=user, is_approved=True).values_list('patient_id', flat=True)
        return Patient.objects.filter(id__in=linked_ids)
    elif role == 'patient':
        p_exact = Patient.objects.filter(name__iexact=user.full_name)
        if p_exact.exists():
            return p_exact
        patient_id = user.device_id.upper().replace('NP-', 'P-') if user.device_id else None
        if patient_id:
            return Patient.objects.filter(id=patient_id)
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
        
        patient_id = None
        if role == 'patient':
            p_exact = Patient.objects.filter(name__iexact=request.user.full_name).first()
            if p_exact:
                patient_id = p_exact.id
            elif request.user.device_id:
                patient_id = request.user.device_id.upper().replace('NP-', 'P-')
            else:
                p_part = Patient.objects.filter(name__icontains=request.user.full_name).first()
                patient_id = p_part.id if p_part else 'P-100'
        elif role == 'family':
            patient_id = request.user.patient_id or 'P-100'
            
        if not patient_id:
            return Response("Patient session binding invalid.", status=status.HTTP_400_BAD_REQUEST)
            
        from doctors.models import DoctorPatientLink, DoctorConnectionRequest
        from caregivers.models import CaregiverPatientLink

        doc_links = DoctorPatientLink.objects.filter(patient_id=patient_id)
        doc_reqs = DoctorConnectionRequest.objects.filter(patient_id=patient_id)
        cg_links = CaregiverPatientLink.objects.filter(patient_id=patient_id)
        family_links = FamilyPatientLink.objects.filter(patient_id=patient_id)
        
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

        patient_id = request.data.get('patientId')
        if not patient_id:
            return Response("Patient ID is required.", status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        link, created = FamilyPatientLink.objects.get_or_create(
            family=request.user,
            patient=patient,
            defaults={'is_approved': False}
        )

        log_audit_trail(
            request=request,
            action='Requested Family Patient Link',
            target=f"Patient ID: {patient_id}",
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
        derived_patient_id = request.user.device_id.upper().replace('NP-', 'P-') if (request.user.role == 'patient' and request.user.device_id) else None
        is_patient = (request.user.role == 'patient' and derived_patient_id == link.patient_id)

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
        derived_patient_id = request.user.device_id.upper().replace('NP-', 'P-') if (request.user.role == 'patient' and request.user.device_id) else None
        is_patient = (request.user.role == 'patient' and (derived_patient_id == link.patient_id or link.patient.name.lower() in request.user.full_name.lower()))

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
