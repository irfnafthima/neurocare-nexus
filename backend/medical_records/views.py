import os
from django.http import HttpResponse, Http404
from rest_framework import status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorPatientLink
from caregivers.models import CaregiverPatientLink
from accounts.models import CustomUser, AuditLog
from accounts.utils import log_audit_trail
from medical_records.models import (
    MedicalRecord, PatientCondition, PatientAllergy, 
    PatientMedication, PatientConsultation, NextConsultation, MedicalDocument
)

class PatientConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientCondition
        fields = '__all__'

class PatientAllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientAllergy
        fields = '__all__'

class PatientMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientMedication
        fields = '__all__'

class PatientConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientConsultation
        fields = '__all__'

class NextConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextConsultation
        fields = '__all__'

class MedicalDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)
    class Meta:
        model = MedicalDocument
        fields = ['id', 'patient', 'uploaded_by', 'uploaded_by_name', 'document_type', 'title', 'upload_date', 'description', 'file', 'consultation']

def get_authorized_patient_id(request):
    user = request.user
    role = user.role
    if role == 'patient':
        patient = Patient.objects.filter(name__iexact=user.full_name).first()
        if patient:
            return patient.id
        if user.device_id:
            return user.device_id.upper().replace('NP-', 'P-')
        patient_partial = Patient.objects.filter(name__icontains=user.full_name).first()
        return patient_partial.id if patient_partial else 'P-100'
    elif role == 'family':
        return user.patient_id or 'P-100'
    return request.query_params.get('patientId') or 'P-100'

def is_user_authorized_for_patient(user, patient_id):
    if user.role == 'admin':
        return True
    if user.role == 'patient':
        bound_id = (user.device_id or '').upper().replace('NP-', 'P-')
        return bound_id == patient_id or Patient.objects.filter(id=patient_id, name__icontains=user.full_name).exists()
    if user.role == 'doctor':
        return DoctorPatientLink.objects.filter(doctor=user, patient_id=patient_id).exists() or Patient.objects.filter(id=patient_id, doctor_npi__npi=user.npi).exists()
    if user.role == 'caregiver':
        return CaregiverPatientLink.objects.filter(caregiver=user, patient_id=patient_id, is_approved=True).exists()
    if user.role == 'family':
        return FamilyPatientLink.objects.filter(family=user, patient_id=patient_id, is_approved=True).exists()
    return False

class PatientHealthRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No approved relationship with patient.", status=status.HTTP_403_FORBIDDEN)

        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient health record not found.", status=status.HTTP_404_NOT_FOUND)

        conditions = PatientConditionSerializer(patient.conditions.all(), many=True).data
        allergies = PatientAllergySerializer(patient.allergies.all(), many=True).data
        medications = PatientMedicationSerializer(patient.medications.all(), many=True).data
        consultations = PatientConsultationSerializer(patient.consultations.all(), many=True).data
        next_consultation = NextConsultationSerializer(patient.next_consultations.order_by('-consultation_date').first()).data if patient.next_consultations.exists() else None

        return Response({
            'patientId': patient.id,
            'patientName': patient.name,
            'conditions': conditions,
            'allergies': allergies,
            'medications': medications,
            'consultations': consultations,
            'nextConsultation': next_consultation
        }, status=status.HTTP_200_OK)

    def post(self, request):
        patient_id = get_authorized_patient_id(request)
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No approved permission to modify patient record.", status=status.HTTP_403_FORBIDDEN)

        record_type = request.data.get('type') # 'condition', 'allergy', 'medication', 'consultation', 'next_consultation'
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        if record_type == 'condition':
            c = PatientCondition.objects.create(
                patient=patient,
                condition_name=request.data.get('conditionName', 'General Evaluation'),
                description=request.data.get('description', ''),
                diagnosis_date=request.data.get('diagnosisDate') or None,
                status=request.data.get('status', 'Active'),
                notes=request.data.get('notes', '')
            )
            log_audit_trail(request, 'Added Patient Condition', f"{c.condition_name} for {patient.id}", 'Success')
            return Response(PatientConditionSerializer(c).data, status=status.HTTP_201_CREATED)

        elif record_type == 'allergy':
            a = PatientAllergy.objects.create(
                patient=patient,
                allergen=request.data.get('allergen', 'Unspecified'),
                reaction=request.data.get('reaction', ''),
                severity=request.data.get('severity', 'Moderate'),
                notes=request.data.get('notes', '')
            )
            log_audit_trail(request, 'Added Patient Allergy Record', f"{a.allergen} for {patient.id}", 'Success')
            return Response(PatientAllergySerializer(a).data, status=status.HTTP_201_CREATED)

        elif record_type == 'medication':
            m = PatientMedication.objects.create(
                patient=patient,
                medicine_name=request.data.get('medicineName', 'Paracetamol'),
                dosage=request.data.get('dosage', '500 mg'),
                dosage_unit=request.data.get('dosageUnit', 'mg'),
                frequency=request.data.get('frequency', 'Twice daily'),
                route=request.data.get('route', 'Oral'),
                start_date=request.data.get('startDate') or None,
                end_date=request.data.get('endDate') or None,
                prescribing_doctor_name=request.data.get('prescribingDoctorName', request.user.full_name),
                instructions=request.data.get('instructions', '')
            )
            log_audit_trail(request, 'Added Patient Medication', f"{m.medicine_name} for {patient.id}", 'Success')
            return Response(PatientMedicationSerializer(m).data, status=status.HTTP_201_CREATED)

        elif record_type == 'consultation':
            c = PatientConsultation.objects.create(
                patient=patient,
                doctor=request.user if request.user.role == 'doctor' else None,
                doctor_name=request.data.get('doctorName', request.user.full_name),
                consultation_date=request.data.get('consultationDate') or None,
                reason=request.data.get('reason', 'Routine Checkup'),
                clinical_notes=request.data.get('clinicalNotes', ''),
                follow_up_notes=request.data.get('followUpNotes', ''),
                next_consultation_date=request.data.get('nextConsultationDate') or None
            )
            log_audit_trail(request, 'Recorded Patient Consultation', f"Consultation on {c.consultation_date} for {patient.id}", 'Success')
            return Response(PatientConsultationSerializer(c).data, status=status.HTTP_201_CREATED)

        elif record_type == 'next_consultation':
            nc = NextConsultation.objects.create(
                patient=patient,
                doctor=request.user if request.user.role == 'doctor' else None,
                doctor_name=request.data.get('doctorName', request.user.full_name),
                consultation_date=request.data.get('consultationDate'),
                time=request.data.get('time', '10:00 AM'),
                facility=request.data.get('facility', 'Specialty Clinic'),
                notes=request.data.get('notes', '')
            )
            log_audit_trail(request, 'Scheduled Next Consultation', f"Next Consultation on {nc.consultation_date} for {patient.id}", 'Success')
            return Response(NextConsultationSerializer(nc).data, status=status.HTTP_201_CREATED)

        return Response("Invalid health record type.", status=status.HTTP_400_BAD_REQUEST)

class MedicalDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to access patient documents.", status=status.HTTP_403_FORBIDDEN)

        docs = MedicalDocument.objects.filter(patient_id=patient_id).order_by('-upload_date')
        return Response(MedicalDocumentSerializer(docs, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        patient_id = get_authorized_patient_id(request)
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to upload document for patient.", status=status.HTTP_403_FORBIDDEN)

        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        file_obj = request.FILES.get('file')
        title = request.data.get('title', 'Medical Report')
        doc_type = request.data.get('documentType', 'Other')
        desc = request.data.get('description', '')

        if not file_obj:
            return Response("Document file is required.", status=status.HTTP_400_BAD_REQUEST)

        doc = MedicalDocument.objects.create(
            patient=patient,
            uploaded_by=request.user,
            document_type=doc_type,
            title=title,
            description=desc,
            file=file_obj
        )

        log_audit_trail(
            request=request,
            action='Uploaded Medical Document',
            target=f"Document: {doc.title} ({doc.document_type}) for Patient {patient.id}",
            result='Success'
        )

        return Response(MedicalDocumentSerializer(doc).data, status=status.HTTP_201_CREATED)

class MedicalDocumentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        doc = MedicalDocument.objects.filter(id=id).first()
        if not doc:
            raise Http404("Document not found.")

        if not is_user_authorized_for_patient(request.user, doc.patient_id):
            log_audit_trail(request, 'Denied Document Access', f"Document ID: {id} for Patient: {doc.patient_id}", 'Unauthorized Block')
            return Response("Unauthorized: Access to this protected medical document is restricted.", status=status.HTTP_403_FORBIDDEN)

        log_audit_trail(request, 'Retrieved Protected Document', f"Document ID: {id} ({doc.title}) for Patient: {doc.patient_id}", 'Success')
        
        file_path = doc.file.path
        if not os.path.exists(file_path):
            raise Http404("Document file missing from secure storage.")

        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
