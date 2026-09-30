import os
import uuid
from django.conf import settings
from django.http import FileResponse, HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from doctors.models import (
    SyntheticNPI, DoctorConnectionRequest, DoctorPatientLink, 
    ReferenceDoctorRegistry, HealthFacility, DoctorProfile, 
    DoctorFacilityAffiliation, VerificationRecord, DoctorVerificationDocument
)
from patients.models import Patient
from accounts.models import CustomUser
from accounts.utils import log_audit_trail
from accounts.views import IsAdminRole
from notifications.email_service import send_nexus_email


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


class DoctorVerificationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'doctor':
            return Response("Unauthorized: Doctor profile required.", status=status.HTTP_403_FORBIDDEN)

        profile = getattr(user, 'doctor_profile', None)
        if not profile:
            return Response("Doctor profile not found.", status=status.HTTP_404_NOT_FOUND)

        # Fetch doctor's own documents
        docs = DoctorVerificationDocument.objects.filter(doctor=profile).order_by('-submitted_at')
        docs_data = []
        for d in docs:
            docs_data.append({
                'id': d.id,
                'documentType': d.document_type,
                'document_type': d.document_type,
                'title': d.title,
                'fileName': d.file_name,
                'file_name': d.file_name,
                'original_filename': d.file_name or d.title,
                'fileSize': d.file_size,
                'file_size': d.file_size,
                'file_size_bytes': d.file_size,
                'mimeType': d.mime_type,
                'mime_type': d.mime_type,
                'status': d.status,
                'adminNotes': d.admin_notes,
                'admin_notes': d.admin_notes,
                'admin_review_notes': d.admin_notes,
                'requestedAt': d.requested_at.isoformat() if d.requested_at else None,
                'requested_at': d.requested_at.isoformat() if d.requested_at else None,
                'submittedAt': d.submitted_at.isoformat() if d.submitted_at else None,
                'submitted_at': d.submitted_at.isoformat() if d.submitted_at else None,
                'created_at': d.submitted_at.isoformat() if d.submitted_at else None,
                'reviewedAt': d.reviewed_at.isoformat() if d.reviewed_at else None,
                'reviewed_at': d.reviewed_at.isoformat() if d.reviewed_at else None,
                'downloadUrl': f"/api/doctor/documents/{d.id}/download",
                'download_url': f"/api/doctor/documents/{d.id}/download"
            })

        latest_record = VerificationRecord.objects.filter(user=user).order_by('-verified_at').first()

        return Response({
            'doctorId': user.id,
            'fullName': user.full_name,
            'email': user.email,
            'phone': user.phone or '',
            'medicalRegistrationNumber': profile.medical_registration_number,
            'stateMedicalCouncil': profile.state_medical_council,
            'qualification': profile.qualification,
            'specialization': profile.specialization,
            'verificationStatus': profile.verification_status,
            'verification_status': profile.verification_status,
            'is_restricted': profile.verification_status != 'VERIFIED',
            'approved': user.approved,
            'submissionDate': user.date_joined.isoformat(),
            'latestAdminMessage': latest_record.remarks if latest_record else '',
            'requested_document_notes': latest_record.remarks if latest_record else '',
            'documents': docs_data
        }, status=status.HTTP_200_OK)


class DoctorDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user
        if user.role != 'doctor':
            return Response("Unauthorized: Only doctors can upload verification documents.", status=status.HTTP_403_FORBIDDEN)

        profile = getattr(user, 'doctor_profile', None)
        if not profile:
            return Response("Doctor profile not found.", status=status.HTTP_404_NOT_FOUND)

        uploaded_file = request.FILES.get('document_file') or request.FILES.get('file') or request.FILES.get('document')
        if not uploaded_file:
            return Response("No file was uploaded. Expected form field 'document_file' or 'file'.", status=status.HTTP_400_BAD_REQUEST)

        # 1. Size check (Max 10 MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return Response("File size exceeds 10MB limit.", status=status.HTTP_400_BAD_REQUEST)

        # 2. Extension check
        orig_name = uploaded_file.name
        ext = os.path.splitext(orig_name)[1].lower().replace('.', '')
        allowed_exts = {'pdf', 'png', 'jpg', 'jpeg'}
        if ext not in allowed_exts:
            return Response("Invalid file format. Allowed formats: PDF, PNG, JPG, JPEG.", status=status.HTTP_400_BAD_REQUEST)

        # 3. Content inspection
        content_header = uploaded_file.read(512)
        uploaded_file.seek(0)
        dangerous_signatures = [b'MZ', b'<!DOCTYPE html', b'<html', b'<script', b'<?php', b'#!/bin/', b'\x7fELF']
        if any(sig in content_header for sig in dangerous_signatures):
            return Response("Invalid or unsafe file content detected.", status=status.HTTP_400_BAD_REQUEST)

        doc_type = request.data.get('documentType') or request.data.get('document_type') or 'OTHER'
        title = request.data.get('title', '').strip() or request.data.get('notes', '').strip() or f"{doc_type.replace('_', ' ').title()} Document"
        doc_id = request.data.get('documentId') or request.data.get('document_id')

        # Save to private media directory safely
        private_dir = getattr(settings, 'PRIVATE_MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'private_media'))
        target_dir = os.path.join(private_dir, 'doctor_documents')
        os.makedirs(target_dir, exist_ok=True)

        safe_filename = f"doc_{user.id}_{uuid.uuid4().hex[:12]}.{ext}"
        safe_filepath = os.path.join(target_dir, safe_filename)

        with open(safe_filepath, 'wb') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Create or update document record
        if doc_id:
            try:
                doc_record = DoctorVerificationDocument.objects.get(id=doc_id, doctor=profile)
                doc_record.file.name = f"doctor_documents/{safe_filename}"
                doc_record.file_name = orig_name
                doc_record.file_size = uploaded_file.size
                doc_record.mime_type = uploaded_file.content_type or f"application/{ext}"
                doc_record.status = 'SUBMITTED'
                doc_record.save()
            except DoctorVerificationDocument.DoesNotExist:
                doc_record = DoctorVerificationDocument.objects.create(
                    doctor=profile,
                    document_type=doc_type,
                    title=title,
                    file=f"doctor_documents/{safe_filename}",
                    file_name=orig_name,
                    file_size=uploaded_file.size,
                    mime_type=uploaded_file.content_type or f"application/{ext}",
                    status='SUBMITTED'
                )
        else:
            doc_record = DoctorVerificationDocument.objects.create(
                doctor=profile,
                document_type=doc_type,
                title=title,
                file=f"doctor_documents/{safe_filename}",
                file_name=orig_name,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type or f"application/{ext}",
                status='SUBMITTED'
            )

        # Transition doctor status to UNDER_REVIEW if it was in DOCUMENTS_REQUESTED
        if profile.verification_status == 'DOCUMENTS_REQUESTED':
            profile.verification_status = 'UNDER_REVIEW'
            profile.save()

        VerificationRecord.objects.create(
            user=user,
            verification_type='ADMIN_REVIEW',
            source='Doctor Verification Dashboard',
            result='MANUAL_REVIEW',
            remarks=f"Doctor uploaded verification document: {title} ({orig_name})"
        )

        log_audit_trail(
            request=request,
            action='Doctor Verification Document Uploaded',
            target=f"{user.full_name} - {title}",
            result='Success',
            actor=user
        )

        # Dispatch email to administrator
        send_nexus_email(
            'DOCTOR_DOCUMENTS_SUBMITTED',
            getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'neurocarenexus@gmail.com') or 'neurocarenexus@gmail.com',
            {
                'doctor_name': user.full_name,
                'medical_registration_number': profile.medical_registration_number,
                'document_title': title,
                'document_type': doc_type,
            }
        )

        return Response({
            'message': 'Document uploaded successfully.',
            'documentId': doc_record.id,
            'title': doc_record.title,
            'status': doc_record.status,
            'fileName': orig_name
        }, status=status.HTTP_201_CREATED)


class DoctorDocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        user = request.user
        try:
            doc_record = DoctorVerificationDocument.objects.select_related('doctor__user').get(id=id)
        except DoctorVerificationDocument.DoesNotExist:
            return Response("Document not found.", status=status.HTTP_404_NOT_FOUND)

        # Strict ownership check: only owning doctor or admin can download
        if doc_record.doctor.user != user and user.role != 'admin':
            return Response("Unauthorized: You cannot access this document.", status=status.HTTP_403_FORBIDDEN)

        private_dir = getattr(settings, 'PRIVATE_MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'private_media'))
        file_path = os.path.join(private_dir, str(doc_record.file))

        if not os.path.exists(file_path):
            file_path = os.path.join(settings.MEDIA_ROOT, str(doc_record.file))
            if not os.path.exists(file_path):
                return Response("Document file not found on server.", status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(open(file_path, 'rb'), content_type=doc_record.mime_type or 'application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="{doc_record.file_name or "document.pdf"}"'
        return response


class AdminDoctorDocumentRequestView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        try:
            doc_user = CustomUser.objects.get(id=id, role='doctor')
            profile = doc_user.doctor_profile
        except (CustomUser.DoesNotExist, DoctorProfile.DoesNotExist):
            return Response("Doctor profile not found.", status=status.HTTP_404_NOT_FOUND)

        raw_types = request.data.get('document_types') or request.data.get('documentTypes')
        if not raw_types:
            single_type = request.data.get('documentType') or request.data.get('document_type') or 'OTHER'
            doc_types = [single_type]
        elif isinstance(raw_types, list):
            doc_types = raw_types
        else:
            doc_types = [str(raw_types)]

        notes = request.data.get('notes', '').strip() or request.data.get('reason', '').strip()
        created_docs = []

        type_label_map = {
            'MEDICAL_LICENSE': 'Medical Registration Certificate',
            'MEDICAL_COUNCIL_CERTIFICATE': 'Medical Registration Certificate',
            'BOARD_CERTIFICATION': 'Board Degree / Qualification Certificate',
            'DEGREE_CERTIFICATE': 'Board Degree / Qualification Certificate',
            'IDENTITY_PROOF': 'Government Photo ID',
            'GOVERNMENT_ID': 'Government Photo ID',
            'CLINICAL_EXPERIENCE': 'Clinical Experience Proof',
            'HOSPITAL_ID': 'Hospital Affiliation ID',
            'OTHER': 'Supporting Document'
        }

        for dt in doc_types:
            label = type_label_map.get(dt, dt.replace('_', ' ').title())
            title = f"Requested: {label}"
            doc_record = DoctorVerificationDocument.objects.create(
                doctor=profile,
                document_type=dt,
                title=title,
                status='REQUESTED',
                admin_notes=notes,
                requested_by=request.user,
                requested_at=timezone.now()
            )
            created_docs.append(doc_record)

        profile.verification_status = 'DOCUMENTS_REQUESTED'
        profile.save()

        doc_summary = ", ".join([type_label_map.get(dt, dt) for dt in doc_types])

        VerificationRecord.objects.create(
            user=doc_user,
            verification_type='ADMIN_REVIEW',
            source='Admin Verification Dashboard',
            result='MANUAL_REVIEW',
            verified_by=request.user,
            remarks=f"Administrator requested documents: {doc_summary}. Notes: {notes}"
        )

        log_audit_trail(
            request=request,
            action='Requested Doctor Verification Document',
            target=f"{doc_user.full_name} - {doc_summary}",
            result='Success',
            actor=request.user
        )

        # Dispatch email to doctor
        send_nexus_email(
            'DOCTOR_DOCUMENTS_REQUESTED',
            doc_user.email,
            {
                'doctor_name': doc_user.full_name,
                'medical_registration_number': profile.medical_registration_number,
                'document_title': doc_summary,
                'document_type': "Verification Documents",
                'admin_notes': notes
            }
        )

        return Response({
            'message': 'Document request sent to doctor.',
            'documentIds': [d.id for d in created_docs],
            'status': 'REQUESTED'
        }, status=status.HTTP_201_CREATED)


class AdminDoctorDocumentReviewView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request, id):
        return self.put(request, id)

    def put(self, request, id):
        try:
            doc_record = DoctorVerificationDocument.objects.select_related('doctor__user').get(id=id)
            profile = doc_record.doctor
            doc_user = profile.user
        except DoctorVerificationDocument.DoesNotExist:
            return Response("Document not found.", status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action', '').upper()
        if not action:
            req_status = request.data.get('status', '').upper()
            if req_status == 'ACCEPTED':
                action = 'ACCEPT'
            elif req_status in ['RESUBMISSION_REQUIRED', 'REJECT']:
                action = 'REQUEST_RESUBMISSION'

        notes = request.data.get('notes', '').strip() or request.data.get('reason', '').strip()

        if action == 'ACCEPT':
            doc_record.status = 'ACCEPTED'
            doc_record.admin_notes = notes or 'Accepted by administrator.'
            doc_record.reviewed_at = timezone.now()
            doc_record.save()

            VerificationRecord.objects.create(
                user=doc_user,
                verification_type='ADMIN_REVIEW',
                source='Admin Verification Dashboard',
                result='EXACT_MATCH',
                verified_by=request.user,
                remarks=f"Accepted document: {doc_record.title}. {notes}"
            )

            log_audit_trail(
                request=request,
                action='Accepted Doctor Verification Document',
                target=f"{doc_user.full_name} - {doc_record.title}",
                result='Success',
                actor=request.user
            )

            send_nexus_email(
                'DOCTOR_DOCUMENT_ACCEPTED',
                doc_user.email,
                {
                    'doctor_name': doc_user.full_name,
                    'document_title': doc_record.title,
                    'admin_notes': notes
                }
            )

            return Response({
                'message': 'Document accepted successfully. (Doctor account remains in review until final approval).',
                'documentId': doc_record.id,
                'status': 'ACCEPTED'
            }, status=status.HTTP_200_OK)

        elif action in ['REQUEST_RESUBMISSION', 'REJECT']:
            doc_record.status = 'RESUBMISSION_REQUIRED'
            doc_record.admin_notes = notes or 'Resubmission required by administrator.'
            doc_record.reviewed_at = timezone.now()
            doc_record.save()

            profile.verification_status = 'DOCUMENTS_REQUESTED'
            profile.save()

            VerificationRecord.objects.create(
                user=doc_user,
                verification_type='ADMIN_REVIEW',
                source='Admin Verification Dashboard',
                result='MISMATCH',
                verified_by=request.user,
                remarks=f"Requested resubmission for document: {doc_record.title}. Notes: {notes}"
            )

            log_audit_trail(
                request=request,
                action='Requested Doctor Document Resubmission',
                target=f"{doc_user.full_name} - {doc_record.title}",
                result='Success',
                actor=request.user
            )

            send_nexus_email(
                'DOCTOR_DOCUMENT_RESUBMISSION_REQUIRED',
                doc_user.email,
                {
                    'doctor_name': doc_user.full_name,
                    'document_title': doc_record.title,
                    'admin_notes': notes
                }
            )

            return Response({
                'message': 'Document resubmission requested.',
                'documentId': doc_record.id,
                'status': 'RESUBMISSION_REQUIRED'
            }, status=status.HTTP_200_OK)

        return Response("Invalid review action. Expected 'ACCEPT' or 'REQUEST_RESUBMISSION'.", status=status.HTTP_400_BAD_REQUEST)


class AdminDoctorDocumentDownloadView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, id):
        try:
            doc_record = DoctorVerificationDocument.objects.get(id=id)
        except DoctorVerificationDocument.DoesNotExist:
            return Response("Document not found.", status=status.HTTP_404_NOT_FOUND)

        private_dir = getattr(settings, 'PRIVATE_MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'private_media'))
        file_path = os.path.join(private_dir, str(doc_record.file))

        if not os.path.exists(file_path):
            file_path = os.path.join(settings.MEDIA_ROOT, str(doc_record.file))
            if not os.path.exists(file_path):
                return Response("Document file not found on server.", status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(open(file_path, 'rb'), content_type=doc_record.mime_type or 'application/octet-stream')
        response['Content-Disposition'] = f'inline; filename="{doc_record.file_name or "document.pdf"}"'
        return response

