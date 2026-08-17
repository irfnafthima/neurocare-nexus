from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from patients.models import Patient
from doctors.models import DoctorPatientLink
from prescriptions.models import Prescription
from medical_records.views import get_authorized_patient_id, is_user_authorized_for_patient
from accounts.utils import log_audit_trail

class PrescriptionSerializer(serializers.ModelSerializer):
    prescribing_doctor_email = serializers.CharField(source='prescribing_doctor.email', read_only=True)
    class Meta:
        model = Prescription
        fields = ['id', 'patient', 'prescribing_doctor', 'prescribing_doctor_email', 'prescribing_doctor_name', 'prescription_date', 'medicines', 'dosage', 'frequency', 'duration', 'instructions', 'document', 'status']

class PrescriptionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not patient_id:
            return Response([], status=status.HTTP_200_OK)

        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to view patient prescriptions.", status=status.HTTP_403_FORBIDDEN)

        rx_list = Prescription.objects.filter(patient_id=patient_id).order_by('-id')
        log_audit_trail(request, 'Accessed Patient Prescriptions', f"Prescriptions for Patient {patient_id}", 'Success')
        return Response(PrescriptionSerializer(rx_list, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Only licensed doctors can issue prescriptions.", status=status.HTTP_403_FORBIDDEN)

        raw_pid = request.data.get('patientId')
        if not raw_pid:
            return Response("Target patientId is required to issue a prescription.", status=status.HTTP_400_BAD_REQUEST)

        from patients.views import find_patient_by_identifier
        patient = find_patient_by_identifier(raw_pid)
        if not patient:
            return Response("Target patient not found.", status=status.HTTP_404_NOT_FOUND)

        # Verify doctor is linked to specific target patient
        if not is_user_authorized_for_patient(request.user, patient.id):
            return Response(f"Unauthorized: Doctor must be linked to patient {patient.id} to issue a prescription.", status=status.HTTP_403_FORBIDDEN)

        from django.utils import timezone
        rx = Prescription.objects.create(
            patient=patient,
            prescribing_doctor=request.user,
            prescribing_doctor_name=request.user.full_name,
            prescription_date=request.data.get('prescriptionDate') or timezone.now().date(),
            medicines=request.data.get('medicines', 'Paracetamol 500mg'),
            dosage=request.data.get('dosage', '1 tablet'),
            frequency=request.data.get('frequency', 'Twice daily'),
            duration=request.data.get('duration', '7 days'),
            instructions=request.data.get('instructions', 'Take after meals with water.')
        )

        log_audit_trail(
            request=request,
            action='Issued Prescription',
            target=f"Prescription: {rx.medicines} for Patient {patient.id} ({patient.name})",
            result='Success'
        )

        return Response(PrescriptionSerializer(rx).data, status=status.HTTP_201_CREATED)

class PrescriptionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, id):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Patients, caregivers, and family members cannot modify doctor prescriptions.", status=status.HTTP_403_FORBIDDEN)
        
        rx = Prescription.objects.filter(id=id).first()
        if not rx:
            return Response("Prescription not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, rx.patient_id):
            return Response("Unauthorized: Doctor must be linked to patient to update prescription.", status=status.HTTP_403_FORBIDDEN)

        serializer = PrescriptionSerializer(rx, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_audit_trail(request, 'Updated Prescription', f"Prescription ID {rx.id} for Patient {rx.patient_id}", 'Success')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Patients, caregivers, and family members cannot delete doctor prescriptions.", status=status.HTTP_403_FORBIDDEN)

        rx = Prescription.objects.filter(id=id).first()
        if not rx:
            return Response("Prescription not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, rx.patient_id):
            return Response("Unauthorized: Doctor must be linked to patient to delete prescription.", status=status.HTTP_403_FORBIDDEN)

        pid = rx.patient_id
        rx.delete()
        log_audit_trail(request, 'Revoked Prescription', f"Prescription ID {id} for Patient {pid}", 'Success')
        return Response("Prescription deleted successfully.", status=status.HTTP_200_OK)
