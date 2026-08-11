from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from caregivers.models import CaregiverPatientLink, SyntheticCaregiver
from patients.models import Patient
from accounts.models import CustomUser
from accounts.utils import log_audit_trail

class CaregiverRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = request.user.role
        if role == 'caregiver':
            links = CaregiverPatientLink.objects.filter(caregiver=request.user).order_by('-created_at')
            data = []
            for l in links:
                data.append({
                    'id': l.id,
                    'patientId': l.patient_id,
                    'patientName': l.patient.name,
                    'isApproved': l.is_approved,
                    'isReadOnly': l.is_read_only,
                    'createdAt': l.created_at.isoformat()
                })
            return Response(data, status=status.HTTP_200_OK)
        elif role == 'admin':
            links = CaregiverPatientLink.objects.all().order_by('-created_at')
            data = []
            for l in links:
                data.append({
                    'id': l.id,
                    'caregiverEmail': l.caregiver.email,
                    'caregiverName': l.caregiver.full_name,
                    'patientId': l.patient_id,
                    'patientName': l.patient.name,
                    'isApproved': l.is_approved,
                    'isReadOnly': l.is_read_only,
                    'createdAt': l.created_at.isoformat()
                })
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response("Access Denied.", status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        if request.user.role != 'caregiver':
            return Response("Only caregivers can request links.", status=status.HTTP_403_FORBIDDEN)

        patient_id = request.data.get('patientId')
        if not patient_id:
            return Response("Patient ID is required.", status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response("Patient not found in validation registry.", status=status.HTTP_404_NOT_FOUND)

        link, created = CaregiverPatientLink.objects.get_or_create(
            caregiver=request.user,
            patient=patient,
            defaults={
                'is_approved': False,
                'is_read_only': True
            }
        )

        log_audit_trail(
            request=request,
            action='Requested Caregiver Patient Link',
            target=f"Patient ID: {patient_id}",
            result='Success'
        )

        return Response({
            'id': link.id,
            'patientId': link.patient_id,
            'isApproved': link.is_approved,
            'isReadOnly': link.is_read_only
        }, status=status.HTTP_200_OK)

class CaregiverRequestApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        # Admins or the patient themselves can approve the caregiver link
        try:
            link = CaregiverPatientLink.objects.get(id=id)
        except CaregiverPatientLink.DoesNotExist:
            return Response("Link not found.", status=status.HTTP_404_NOT_FOUND)

        # Access check: admin or patient
        is_admin = (request.user.role == 'admin')
        derived_patient_id = request.user.device_id.upper().replace('NP-', 'P-') if (request.user.role == 'patient' and request.user.device_id) else None
        is_patient = (request.user.role == 'patient' and derived_patient_id == link.patient_id)

        if not (is_admin or is_patient):
            return Response("Unauthorized to approve this link request.", status=status.HTTP_403_FORBIDDEN)

        approved = request.data.get('approved', True)
        read_only = request.data.get('readOnly', True)

        link.is_approved = approved
        link.is_read_only = read_only
        link.save()

        log_audit_trail(
            request=request,
            action='Updated Caregiver Patient Link Status',
            target=f"Caregiver: {link.caregiver.email} -> Patient: {link.patient_id} (Approved: {approved})",
            result='Success'
        )

        return Response("Caregiver patient link status updated successfully.", status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            link = CaregiverPatientLink.objects.get(id=id)
        except CaregiverPatientLink.DoesNotExist:
            return Response("Link not found.", status=status.HTTP_404_NOT_FOUND)

        is_admin = (request.user.role == 'admin')
        derived_patient_id = request.user.device_id.upper().replace('NP-', 'P-') if (request.user.role == 'patient' and request.user.device_id) else None
        is_patient = (request.user.role == 'patient' and (derived_patient_id == link.patient_id or link.patient.name.lower() in request.user.full_name.lower()))

        if not (is_admin or is_patient):
            return Response("Unauthorized to revoke this caregiver link.", status=status.HTTP_403_FORBIDDEN)

        cg_email = link.caregiver.email
        pat_id = link.patient_id
        link.delete()

        log_audit_trail(
            request=request,
            action='Revoked Caregiver Patient Link',
            target=f"Caregiver: {cg_email} -> Patient: {pat_id}",
            result='Success'
        )

        return Response("Caregiver link revoked successfully.", status=status.HTTP_200_OK)
