from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from caregivers.models import CaregiverPatientLink, SyntheticCaregiver
from patients.models import Patient
from accounts.models import CustomUser
from accounts.utils import log_audit_trail
from patients.views import find_patient_by_identifier, find_patient_record_for_user, get_patient_ids_for_user
from notifications.utils import create_notification

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
                    'caregiverName': l.caregiver.full_name or l.caregiver.email,
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

        patient_id_input = request.data.get('patientId')
        if not patient_id_input:
            return Response("Patient ID / Access Code is required.", status=status.HTTP_400_BAD_REQUEST)

        patient = find_patient_by_identifier(patient_id_input)
        if not patient:
            return Response("Patient not found for the provided Access Code.", status=status.HTTP_404_NOT_FOUND)

        link, created = CaregiverPatientLink.objects.get_or_create(
            caregiver=request.user,
            patient=patient,
            defaults={
                'is_approved': False,
                'is_read_only': False
            }
        )

        log_audit_trail(
            request=request,
            action='Requested Caregiver Patient Link',
            target=f"Caregiver: {request.user.email} -> Patient ID: {patient.id} ({patient.name})",
            result='Success'
        )

        # Notify patient users matching this patient record
        patient_users = CustomUser.objects.filter(role='patient')
        for pu in patient_users:
            if find_patient_record_for_user(pu) == patient or pu.patient_id == patient.id:
                create_notification(
                    user=pu,
                    title="New Caregiver Access Request",
                    message=f"Caregiver {request.user.full_name or request.user.email} has requested access using your Patient Access Code.",
                    category="connection",
                    target_id=link.id
                )

        return Response({
            'id': link.id,
            'patientId': link.patient_id,
            'patientName': patient.name,
            'isApproved': link.is_approved,
            'isReadOnly': link.is_read_only,
            'message': 'Connection request sent to patient. Access will activate once accepted.'
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CaregiverRequestApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        try:
            link = CaregiverPatientLink.objects.select_related('patient', 'caregiver').get(id=id)
        except CaregiverPatientLink.DoesNotExist:
            return Response("Link not found.", status=status.HTTP_404_NOT_FOUND)

        is_admin = (request.user.role == 'admin')
        user_p_ids = get_patient_ids_for_user(request.user) if request.user.role == 'patient' else []
        is_patient = (request.user.role == 'patient' and (link.patient_id in user_p_ids or find_patient_record_for_user(request.user) == link.patient))

        if not (is_admin or is_patient):
            return Response("Unauthorized to approve this link request.", status=status.HTTP_403_FORBIDDEN)

        approved = request.data.get('approved', True)
        read_only = request.data.get('readOnly', False)

        link.is_approved = approved
        link.is_read_only = read_only
        link.save()

        log_audit_trail(
            request=request,
            action='Updated Caregiver Patient Link Status',
            target=f"Caregiver: {link.caregiver.email} -> Patient: {link.patient_id} (Approved: {approved})",
            result='Success'
        )

        if approved:
            create_notification(
                user=link.caregiver,
                title="Caregiver Access Granted",
                message=f"Patient {link.patient.name} ({link.patient.id}) has approved your connection request.",
                category="connection",
                target_id=link.id
            )

        return Response("Caregiver patient link status updated successfully.", status=status.HTTP_200_OK)

    def delete(self, request, id):
        try:
            link = CaregiverPatientLink.objects.select_related('patient', 'caregiver').get(id=id)
        except CaregiverPatientLink.DoesNotExist:
            return Response("Link not found.", status=status.HTTP_404_NOT_FOUND)

        is_admin = (request.user.role == 'admin')
        user_p_ids = get_patient_ids_for_user(request.user) if request.user.role == 'patient' else []
        is_patient = (request.user.role == 'patient' and (link.patient_id in user_p_ids or find_patient_record_for_user(request.user) == link.patient))

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

