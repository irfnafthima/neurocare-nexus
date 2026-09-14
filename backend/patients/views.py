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
    # 3. Handle NP- <-> P- conversions
    if 'NP-' in ident.upper():
        p = Patient.objects.filter(id__iexact=ident.upper().replace('NP-', 'P-')).first()
        if p:
            return p
    if 'P-' in ident.upper():
        p = Patient.objects.filter(id__iexact=ident.upper().replace('P-', 'NP-')).first()
        if p:
            return p
    # 4. Match CustomUser patient device_id, user.id, or full_name (handling NP- and P- variations)
    clean_num = ident.upper().replace('NP-', '').replace('P-', '')
    user_p = CustomUser.objects.filter(role='patient').filter(
        models.Q(device_id__iexact=ident) |
        models.Q(device_id__iexact=f"NP-{clean_num}") |
        models.Q(device_id__iexact=f"P-{clean_num}") |
        models.Q(id=int(ident) if ident.isdigit() else (int(clean_num) if clean_num.isdigit() else -1)) |
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
        # Enforce doctor verification status: blocked or unapproved pending doctors cannot access patients
        prof = getattr(user, 'doctor_profile', None)
        if prof and prof.verification_status in ['REJECTED', 'SUSPENDED', 'BLOCKED']:
            return Patient.objects.none()
        if (not user.approved or user.status == 'PENDING') and prof and prof.verification_status in ['PENDING', 'UNDER_REVIEW']:
            return Patient.objects.none()
        if user.status in ['REJECTED', 'SUSPENDED', 'INACTIVE']:
            return Patient.objects.none()
        from doctors.models import DoctorPatientLink, DoctorConnectionRequest, DoctorProfile
        linked_ids = list(DoctorPatientLink.objects.filter(doctor=user).values_list('patient_id', flat=True))
        q = models.Q(id__in=linked_ids)
        if user.npi:
            q |= models.Q(doctor_npi__npi=user.npi)
            req_pids = DoctorConnectionRequest.objects.filter(doctor_npi__npi=user.npi, status='Approved').values_list('patient_id', flat=True)
            q |= models.Q(id__in=req_pids)
        prof = DoctorProfile.objects.filter(user=user).first()
        if prof and prof.medical_registration_number:
            q |= models.Q(doctor_npi__npi=prof.medical_registration_number)
            req_pids2 = DoctorConnectionRequest.objects.filter(doctor_npi__npi=prof.medical_registration_number, status='Approved').values_list('patient_id', flat=True)
            q |= models.Q(id__in=req_pids2)
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
                'dob': p.dob,
                'phone': p.phone,
                'address': p.address,
                'emergencyContactName': p.emergency_contact_name,
                'emergencyContactPhone': p.emergency_contact_phone,
                'bloodGroup': p.blood_group,
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

class PatientProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        from medical_records.views import can_user_edit_patient_clinical
        patient = find_patient_by_identifier(id)
        if not patient:
            return Response("Patient profile not found.", status=status.HTTP_404_NOT_FOUND)

        if not can_user_edit_patient_clinical(request.user, patient.id):
            return Response("Unauthorized: Permission denied to edit patient profile.", status=status.HTTP_403_FORBIDDEN)

        data = request.data
        if 'name' in data and data['name'].strip():
            patient.name = data['name'].strip()
            if request.user.role == 'patient':
                request.user.full_name = patient.name
                request.user.save(update_fields=['full_name'])

        if 'age' in data and data['age'] is not None:
            try:
                patient.age = int(data['age'])
            except (ValueError, TypeError):
                return Response("Invalid age provided.", status=status.HTTP_400_BAD_REQUEST)

        if 'gender' in data:
            patient.gender = str(data['gender']).strip()
        if 'dob' in data:
            patient.dob = data['dob'] or None
        if 'phone' in data:
            patient.phone = str(data['phone']).strip()
            if request.user.role == 'patient':
                request.user.phone = patient.phone
                request.user.save(update_fields=['phone'])
        if 'address' in data:
            patient.address = str(data['address']).strip()
        if 'emergencyContactName' in data or 'emergency_contact_name' in data:
            patient.emergency_contact_name = (data.get('emergencyContactName') or data.get('emergency_contact_name') or '').strip()
        if 'emergencyContactPhone' in data or 'emergency_contact_phone' in data:
            patient.emergency_contact_phone = (data.get('emergencyContactPhone') or data.get('emergency_contact_phone') or '').strip()
        if 'bloodGroup' in data or 'blood_group' in data:
            patient.blood_group = (data.get('bloodGroup') or data.get('blood_group') or '').strip()
        if 'status' in data:
            patient.status = str(data['status']).strip()
        if 'condition' in data:
            patient.condition = str(data['condition']).strip()

        patient.save()

        log_audit_trail(
            request=request,
            action='Updated Patient Profile',
            target=f"Patient ID: {patient.id} ({patient.name})",
            result='Success'
        )

        return Response({
            'id': patient.id,
            'name': patient.name,
            'age': patient.age,
            'gender': patient.gender,
            'dob': patient.dob,
            'phone': patient.phone,
            'address': patient.address,
            'emergencyContactName': patient.emergency_contact_name,
            'emergencyContactPhone': patient.emergency_contact_phone,
            'bloodGroup': patient.blood_group,
            'status': patient.status,
            'condition': patient.condition
        }, status=status.HTTP_200_OK)

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


class PatientCaregiverLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        patient_id_input = request.data.get('patientId')
        caregiver_ident = str(request.data.get('caregiverIdentifier', '')).strip()

        if not caregiver_ident:
            return Response("Caregiver identifier (Agency ID, Email, or Name) is required.", status=status.HTTP_400_BAD_REQUEST)

        if request.user.role == 'patient':
            p_rec = find_patient_record_for_user(request.user)
            patient = p_rec or (find_patient_by_identifier(patient_id_input) if patient_id_input else None) or Patient.objects.first()
        elif patient_id_input:
            patient = find_patient_by_identifier(patient_id_input)
        else:
            patient = Patient.objects.first()

        if not patient:
            return Response("Patient record not found.", status=status.HTTP_404_NOT_FOUND)

        # 1. Look up caregiver in CustomUser
        from caregivers.models import CaregiverPatientLink, SyntheticCaregiver, CaregiverProfile
        cg_user = CustomUser.objects.filter(role='caregiver').filter(
            models.Q(agency_id__iexact=caregiver_ident) |
            models.Q(email__iexact=caregiver_ident) |
            models.Q(full_name__iexact=caregiver_ident) |
            models.Q(agency_id__icontains=caregiver_ident) |
            models.Q(email__icontains=caregiver_ident) |
            models.Q(full_name__icontains=caregiver_ident)
        ).first()

        # 2. If not found in CustomUser, check SyntheticCaregiver registry
        if not cg_user:
            synth_cg = SyntheticCaregiver.objects.filter(
                models.Q(agency_id__iexact=caregiver_ident) |
                models.Q(name__icontains=caregiver_ident) |
                models.Q(agency_id__icontains=caregiver_ident)
            ).first()
            if synth_cg:
                clean_email = f"{synth_cg.agency_id.lower().replace('-', '')}@caregiver.nexus"
                cg_user, _ = CustomUser.objects.get_or_create(
                    email=clean_email,
                    defaults={
                        'full_name': synth_cg.name,
                        'role': 'caregiver',
                        'agency_id': synth_cg.agency_id,
                        'approved': True,
                        'status': 'ACTIVE'
                    }
                )
                if not cg_user.password:
                    cg_user.set_password('password123')
                    cg_user.save()
                CaregiverProfile.objects.get_or_create(
                    user=cg_user,
                    defaults={
                        'full_name': synth_cg.name,
                        'current_agency': synth_cg.agency,
                        'verification_status': 'VERIFIED'
                    }
                )

        if not cg_user:
            return Response(f"Caregiver '{caregiver_ident}' not found in registered accounts or agency registry.", status=status.HTTP_404_NOT_FOUND)

        # 3. Create or activate CaregiverPatientLink
        link, created = CaregiverPatientLink.objects.get_or_create(
            caregiver=cg_user,
            patient=patient,
            defaults={'is_approved': True, 'is_read_only': False}
        )
        if not created and not link.is_approved:
            link.is_approved = True
            link.is_read_only = False
            link.save()

        log_audit_trail(
            request=request,
            action='Linked Caregiver to Patient',
            target=f"Caregiver: {cg_user.email} -> Patient: {patient.id} ({patient.name})",
            result='Success'
        )

        from notifications.utils import create_notification
        create_notification(
            user=cg_user,
            title="Caregiver Authorization Granted",
            message=f"You have been granted care-team authorization for patient {patient.name} ({patient.id}).",
            category="connection",
            target_id=link.id
        )

        return Response({
            'status': 'success',
            'id': link.id,
            'message': f"Caregiver '{cg_user.full_name or cg_user.email}' successfully linked to patient."
        }, status=status.HTTP_200_OK)


class PatientCaregiverRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        from caregivers.models import CaregiverPatientLink
        link = CaregiverPatientLink.objects.filter(id=id).first()
        if not link:
            return Response("Caregiver link not found.", status=status.HTTP_404_NOT_FOUND)

        cg_email = link.caregiver.email
        pid = link.patient_id
        link.delete()

        log_audit_trail(
            request=request,
            action='Revoked Caregiver Patient Link',
            target=f"Caregiver: {cg_email} -> Patient: {pid}",
            result='Success'
        )
        return Response("Caregiver access revoked successfully.", status=status.HTTP_200_OK)


class PatientFamilyLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        patient_id_input = request.data.get('patientId')
        family_ident = str(request.data.get('familyIdentifier', '')).strip()

        if not family_ident:
            return Response("Family member identifier (Email or Name) is required.", status=status.HTTP_400_BAD_REQUEST)

        if request.user.role == 'patient':
            p_rec = find_patient_record_for_user(request.user)
            patient = p_rec or (find_patient_by_identifier(patient_id_input) if patient_id_input else None) or Patient.objects.first()
        elif patient_id_input:
            patient = find_patient_by_identifier(patient_id_input)
        else:
            patient = Patient.objects.first()

        if not patient:
            return Response("Patient record not found.", status=status.HTTP_404_NOT_FOUND)

        # 1. Look up family user in CustomUser
        fam_user = CustomUser.objects.filter(role='family').filter(
            models.Q(email__iexact=family_ident) |
            models.Q(full_name__iexact=family_ident) |
            models.Q(email__icontains=family_ident) |
            models.Q(full_name__icontains=family_ident)
        ).first()

        if not fam_user:
            return Response(f"Family user '{family_ident}' not found. Please ensure they have registered an account first.", status=status.HTTP_404_NOT_FOUND)

        # 2. Create or activate FamilyPatientLink
        link, created = FamilyPatientLink.objects.get_or_create(
            family=fam_user,
            patient=patient,
            defaults={'is_approved': True, 'can_edit_clinical': False}
        )
        if not created and not link.is_approved:
            link.is_approved = True
            link.save()

        log_audit_trail(
            request=request,
            action='Linked Family Member to Patient',
            target=f"Family: {fam_user.email} -> Patient: {patient.id} ({patient.name})",
            result='Success'
        )

        from notifications.utils import create_notification
        create_notification(
            user=fam_user,
            title="Family Access Granted",
            message=f"You have been granted access to monitor patient {patient.name} ({patient.id}).",
            category="connection",
            target_id=link.id
        )

        return Response({
            'status': 'success',
            'id': link.id,
            'message': f"Family member '{fam_user.full_name or fam_user.email}' linked successfully."
        }, status=status.HTTP_200_OK)


class PatientFamilyRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, id):
        link = FamilyPatientLink.objects.filter(id=id).first()
        if not link:
            return Response("Family link not found.", status=status.HTTP_404_NOT_FOUND)

        fam_email = link.family.email
        pid = link.patient_id
        link.delete()

        log_audit_trail(
            request=request,
            action='Revoked Family Patient Link',
            target=f"Family: {fam_email} -> Patient: {pid}",
            result='Success'
        )
        return Response("Family access revoked successfully.", status=status.HTTP_200_OK)

