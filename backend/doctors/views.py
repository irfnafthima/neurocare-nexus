from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from doctors.models import (
    SyntheticNPI, DoctorConnectionRequest, DoctorPatientLink, 
    ReferenceDoctorRegistry, HealthFacility, DoctorProfile, 
    DoctorFacilityAffiliation, VerificationRecord
)
from patients.models import Patient
from accounts.models import CustomUser
from accounts.utils import log_audit_trail

class NPILookupView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, npi):
        try:
            prov = SyntheticNPI.objects.get(npi=npi)
            return Response({
                'npi': prov.npi,
                'name': prov.name,
                'hospital': prov.hospital,
                'status': prov.status
            }, status=status.HTTP_200_OK)
        except SyntheticNPI.DoesNotExist:
            return Response("NPI not found in synthetic academic database.", status=status.HTTP_404_NOT_FOUND)

def get_patient_id_for_user(user):
    if user.role == 'family':
        return user.patient_id or 'P-100'
    elif user.role == 'patient':
        patient = Patient.objects.filter(name__iexact=user.full_name).first()
        if patient:
            return patient.id
        if user.device_id:
            return user.device_id.upper().replace('NP-', 'P-')
        patient_partial = Patient.objects.filter(name__icontains=user.full_name).first()
        return patient_partial.id if patient_partial else 'P-100'
    return None

class ConnectionRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        if role == 'doctor':
            doctor_user = request.user
            doctor_npi = doctor_user.npi or (doctor_user.doctor_profile.medical_registration_number if hasattr(doctor_user, 'doctor_profile') and doctor_user.doctor_profile else None)
            
            reqs = DoctorConnectionRequest.objects.filter(doctor_npi_id=doctor_npi).order_by('-created_at')
            data = []
            for r in reqs:
                data.append({
                    'id': r.id,
                    'patientId': r.patient_id,
                    'doctorNpi': r.doctor_npi_id,
                    'status': r.status,
                    'createdAt': r.created_at.isoformat(),
                    'patientName': r.patient.name,
                    'age': r.patient.age,
                    'gender': r.patient.gender,
                    'patientCondition': r.patient.condition,
                    'patientRisk': r.patient.risk,
                    'requestMessage': r.request_message or 'Seeking clinical evaluation and telemetry monitoring.',
                    'generalReason': 'Remote Telemetry Consultation Request'
                })
            return Response(data, status=status.HTTP_200_OK)
        elif role in ['patient', 'family']:
            patient_id = get_patient_id_for_user(request.user)
            if not patient_id:
                return Response("Patient session binding invalid.", status=status.HTTP_400_BAD_REQUEST)
                
            reqs = DoctorConnectionRequest.objects.filter(patient_id=patient_id).order_by('-created_at')
            data = []
            for r in reqs:
                data.append({
                    'id': r.id,
                    'patientId': r.patient_id,
                    'doctorNpi': r.doctor_npi_id,
                    'status': r.status,
                    'createdAt': r.created_at.isoformat(),
                    'doctorName': r.doctor_npi.name,
                    'doctorHospital': r.doctor_npi.hospital
                })
            return Response(data, status=status.HTTP_200_OK)
        else:
            # Caregiver / Admin
            reqs = DoctorConnectionRequest.objects.all().order_by('-created_at')
            data = []
            for r in reqs:
                doc_name = r.doctor_npi.name
                data.append({
                    'id': r.id,
                    'patientId': r.patient_id,
                    'doctorNpi': r.doctor_npi_id,
                    'status': r.status,
                    'createdAt': r.created_at.isoformat(),
                    'patientName': r.patient.name,
                    'doctorName': doc_name
                })
            return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        doctor_npi_str = request.data.get('doctorNpi')
        role = request.user.role
        patient_id = get_patient_id_for_user(request.user)
        request_msg = request.data.get('requestMessage') or request.data.get('message') or request.data.get('reason') or ''

        if not patient_id or not doctor_npi_str:
            return Response("Invalid request details. Patient ID and Doctor NPI required.", status=status.HTTP_400_BAD_REQUEST)

        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient record not found for session.", status=status.HTTP_400_BAD_REQUEST)

        doctor_npi = SyntheticNPI.objects.filter(npi=doctor_npi_str).first()
        if not doctor_npi:
            # Check registered DoctorProfile or CustomUser
            doc_user = CustomUser.objects.filter(role='doctor', npi=doctor_npi_str).first()
            doc_prof = DoctorProfile.objects.filter(medical_registration_number=doctor_npi_str).first()
            doc_name = (doc_user.full_name if doc_user else None) or (doc_prof.user.full_name if doc_prof else None) or 'Dr. Consulting Physician'
            doctor_npi, _ = SyntheticNPI.objects.get_or_create(
                npi=doctor_npi_str,
                defaults={'name': doc_name, 'hospital': 'Clinical Health Practice', 'status': 'Active'}
            )

        # Enforce Duplicate Request Protection
        existing_req = DoctorConnectionRequest.objects.filter(patient=patient, doctor_npi=doctor_npi).first()
        if existing_req:
            if existing_req.status == 'Pending':
                if request_msg:
                    existing_req.request_message = request_msg
                    existing_req.save()
                return Response({
                    'id': existing_req.id,
                    'patientId': existing_req.patient_id,
                    'doctorNpi': existing_req.doctor_npi_id,
                    'status': 'Pending',
                    'createdAt': existing_req.created_at.isoformat(),
                    'message': 'Connection request already pending for this doctor.'
                }, status=status.HTTP_200_OK)
            elif existing_req.status == 'Approved':
                return Response("You are already connected to this doctor.", status=status.HTTP_400_BAD_REQUEST)
            elif existing_req.status == 'Declined':
                # Update status back to Pending for re-requesting
                existing_req.status = 'Pending'
                if request_msg:
                    existing_req.request_message = request_msg
                existing_req.save()
                r = existing_req
        else:
            r = DoctorConnectionRequest.objects.create(
                patient=patient,
                doctor_npi=doctor_npi,
                status='Pending',
                request_message=request_msg
            )

        log_audit_trail(
            request=request,
            action='Dispatched Connection Request',
            target=f"Attending Physician Link: {doctor_npi.name} (MRN: {doctor_npi.npi})",
            result='Success'
        )

        from notifications.utils import create_notification
        doc_user = CustomUser.objects.filter(npi=doctor_npi.npi).first()
        if doc_user:
            create_notification(
                user=doc_user,
                title="New Doctor Connection Request",
                message="A patient has requested to connect with you.",
                category="connection",
                target_id=r.id
            )

        return Response({
            'id': r.id,
            'patientId': r.patient_id,
            'doctorNpi': r.doctor_npi_id,
            'status': r.status,
            'createdAt': r.created_at.isoformat()
        }, status=status.HTTP_201_CREATED if not existing_req else status.HTTP_200_OK)

class ConnectionRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        status_val = request.data.get('status') # 'Approved' or 'Declined'
        if request.user.role != 'doctor':
            return Response("Unauthorized: Attending clinician authentication required.", status=status.HTTP_403_FORBIDDEN)

        try:
            conn_req = DoctorConnectionRequest.objects.get(id=id)
        except DoctorConnectionRequest.DoesNotExist:
            return Response("Connection request not found.", status=status.HTTP_404_NOT_FOUND)

        if status_val in ['Approved', 'ACCEPTED', 'approved', 'accepted']:
            conn_req.status = 'Approved'
            conn_req.save()

            # Update patient record directly (link doctor_npi)
            patient = conn_req.patient
            patient.doctor_npi = conn_req.doctor_npi
            patient.save()

            # Create DoctorPatientLink record for the approving doctor
            DoctorPatientLink.objects.get_or_create(patient=patient, doctor=request.user)

            log_audit_trail(
                request=request,
                action='Approved Connection Request',
                target=f"Patient ID: {conn_req.patient_id}",
                result='Success'
            )
        else:
            conn_req.status = 'Declined'
            conn_req.save()

            log_audit_trail(
                request=request,
                action='Declined Connection Request',
                target=f"Patient ID: {conn_req.patient_id}",
                result='Success'
            )

        from notifications.utils import create_notification
        patient_users = CustomUser.objects.filter(role='patient')
        for pu in patient_users:
            if pu.patient_id == conn_req.patient_id or pu.full_name == conn_req.patient.name:
                create_notification(
                    user=pu,
                    title=f"Doctor Connection {conn_req.status}",
                    message=f"Dr. {request.user.full_name} has {conn_req.status.lower()} your connection request.",
                    category="connection",
                    target_id=conn_req.patient_id
                )

        return Response(f"Connection request {status_val.lower()} successfully.", status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            conn_req = DoctorConnectionRequest.objects.get(id=id)
        except DoctorConnectionRequest.DoesNotExist:
            return Response("Connection request not found.", status=status.HTTP_404_NOT_FOUND)

        doctor_npi_id = conn_req.doctor_npi_id
        conn_req.delete()

        log_audit_trail(
            request=request,
            action='Cancelled Connection Request',
            target=f"Physician ID: {doctor_npi_id}",
            result='Success'
        )

        return Response("Connection request cancelled.", status=status.HTTP_200_OK)

class DoctorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        data = []
        seen_npis = set()

        from doctors.models import DoctorDisciplinaryRecord
        blocked_reg_nos = set(
            DoctorDisciplinaryRecord.objects.filter(
                action_type__in=['SUSPENSION', 'REVOCATION', 'BLACKLIST']
            ).values_list('registration_number', flat=True)
        )

        # 1. Query real registered CustomUser doctors who are active & approved
        doctor_users = CustomUser.objects.filter(
            role='doctor',
            approved=True,
            status='ACTIVE'
        ).select_related('doctor_profile').order_by('full_name')

        for doc_user in doctor_users:
            profile = getattr(doc_user, 'doctor_profile', None)
            
            # Exclude rejected or suspended/blocked doctors
            if profile and profile.verification_status in ['REJECTED', 'SUSPENDED', 'BLOCKED']:
                continue

            npi = doc_user.npi or (profile.medical_registration_number if profile else None) or f"DOC-{doc_user.id}"
            if npi in blocked_reg_nos or npi in seen_npis:
                continue
            seen_npis.add(npi)

            specialization = (profile.specialization if profile else None) or 'General Practice'
            qualification = (profile.qualification if profile else None) or 'MBBS'
            years_exp = profile.years_of_experience if profile else 5
            
            hospital = "Clinical Health Practice"
            if profile:
                aff = profile.facility_affiliations.filter(verification_status='VERIFIED').first()
                if aff:
                    hospital = aff.facility.name

            doc_item = {
                'id': doc_user.id,
                'name': doc_user.full_name,
                'npi': npi,
                'specialization': specialization,
                'qualification': qualification,
                'status': 'VERIFIED',
                'hospital': hospital,
                'experience': years_exp,
                'bio': doc_user.bio or f"Attending {specialization} clinician."
            }

            if query:
                q_low = query.lower()
                if not (
                    q_low in doc_item['name'].lower() or
                    q_low in doc_item['npi'].lower() or
                    q_low in doc_item['specialization'].lower() or
                    q_low in doc_item['hospital'].lower()
                ):
                    continue

            data.append(doc_item)

        # 2. Query SyntheticNPI clinicians for reference verification doctors (excluding blocked)
        synth_docs = SyntheticNPI.objects.exclude(npi__in=blocked_reg_nos).order_by('name')
        for s in synth_docs:
            if s.npi in seen_npis:
                continue
            seen_npis.add(s.npi)

            doc_item = {
                'id': f"synth-{s.npi}",
                'name': s.name,
                'npi': s.npi,
                'specialization': 'Consulting Physician',
                'qualification': 'MBBS, MD',
                'status': 'VERIFIED',
                'hospital': s.hospital or 'General Hospital',
                'experience': 10,
                'bio': 'Consulting clinician in remote patient monitoring network.'
            }

            if query:
                q_low = query.lower()
                if not (
                    q_low in doc_item['name'].lower() or
                    q_low in doc_item['npi'].lower() or
                    q_low in doc_item['specialization'].lower() or
                    q_low in doc_item['hospital'].lower()
                ):
                    continue

            data.append(doc_item)

        return Response(data, status=status.HTTP_200_OK)

class HealthFacilityListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        facilities = HealthFacility.objects.filter(verification_status='VERIFIED').order_by('name')
        data = []
        for f in facilities:
            data.append({
                'id': f.id,
                'name': f.name,
                'facilityType': f.facility_type,
                'address': f.address,
                'city': f.city,
                'state': f.state,
                'registrationIdentifier': f.registration_identifier,
                'contact': f.contact,
                'website': f.website
            })
        return Response(data, status=status.HTTP_200_OK)
