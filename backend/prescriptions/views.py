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
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to view patient prescriptions.", status=status.HTTP_403_FORBIDDEN)

        rx_list = Prescription.objects.filter(patient_id=patient_id).order_by('-prescription_date')
        return Response(PrescriptionSerializer(rx_list, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Only licensed doctors can issue prescriptions.", status=status.HTTP_403_FORBIDDEN)

        patient_id = request.data.get('patientId') or get_authorized_patient_id(request)
        
        # Verify doctor is linked to patient
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: Doctor must be linked to patient to issue a prescription.", status=status.HTTP_403_FORBIDDEN)

        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        rx = Prescription.objects.create(
            patient=patient,
            prescribing_doctor=request.user,
            prescribing_doctor_name=request.user.full_name,
            medicines=request.data.get('medicines', 'Paracetamol 500mg'),
            dosage=request.data.get('dosage', '1 tablet'),
            frequency=request.data.get('frequency', 'Twice daily'),
            duration=request.data.get('duration', '7 days'),
            instructions=request.data.get('instructions', 'Take after meals with water.')
        )

        log_audit_trail(
            request=request,
            action='Issued Prescription',
            target=f"Prescription: {rx.medicines} for Patient {patient.id}",
            result='Success'
        )

        return Response(PrescriptionSerializer(rx).data, status=status.HTTP_201_CREATED)
