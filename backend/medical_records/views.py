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
    PatientMedication, PatientConsultation, NextConsultation, MedicalDocument, VitalMeasurement
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

class VitalMeasurementSerializer(serializers.ModelSerializer):
    source_label = serializers.ReadOnlyField()
    entered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = VitalMeasurement
        fields = '__all__'

    def get_entered_by_name(self, obj):
        if obj.entered_by:
            return obj.entered_by.full_name or obj.entered_by.email
        return obj.entered_by_name or 'System'

PHYSIOLOGICAL_INPUT_RANGES = {
    'heart_rate': (20.0, 300.0),
    'spo2': (30.0, 100.0),
    'temperature': (25.0, 45.0),
    'respiratory_rate': (3, 80),
    'systolic_bp': (40, 300),
    'diastolic_bp': (20, 200),
    'weight': (1.0, 500.0),
    'blood_glucose': (10.0, 1000.0),
}

UNUSUAL_THRESHOLDS = {
    'heart_rate': lambda v: v < 50 or v > 110,
    'spo2': lambda v: v < 92,
    'temperature': lambda v: v < 35.5 or v > 38.0,
    'respiratory_rate': lambda v: v < 10 or v > 24,
    'systolic_bp': lambda v: v < 90 or v > 140,
    'diastolic_bp': lambda v: v < 60 or v > 90,
    'blood_glucose': lambda v: v < 70 or v > 180,
}

def get_authorized_patient_id(request):
    user = request.user
    role = user.role
    req_pid = request.query_params.get('patientId') or request.data.get('patientId')
    if req_pid:
        from patients.views import find_patient_by_identifier
        p = find_patient_by_identifier(req_pid)
        return p.id if p else req_pid

    if role == 'patient':
        from patients.views import find_patient_by_identifier
        p = find_patient_by_identifier(user.full_name) or find_patient_by_identifier(user.patient_id) or find_patient_by_identifier(user.device_id)
        if p:
            return p.id
        return user.patient_id or None
    elif role == 'family':
        from patients.views import find_patient_by_identifier
        p = find_patient_by_identifier(user.patient_id)
        if p:
            return p.id
        return user.patient_id or None
    elif role == 'caregiver':
        cg_link = CaregiverPatientLink.objects.filter(caregiver=user, is_approved=True).first()
        if cg_link:
            return cg_link.patient_id
    return None

def is_user_authorized_for_patient(user, patient_id):
    if not patient_id:
        return False
    if user.role == 'admin':
        return True
    
    from patients.views import find_patient_by_identifier
    patient_obj = find_patient_by_identifier(patient_id)
    real_patient_id = patient_obj.id if patient_obj else patient_id

    if user.role == 'patient':
        user_p = find_patient_by_identifier(user.full_name) or find_patient_by_identifier(user.patient_id) or find_patient_by_identifier(user.device_id)
        if user_p:
            return user_p.id == real_patient_id
        return (user.patient_id == real_patient_id) or (user.device_id and user.device_id.upper().replace('NP-', 'P-') == real_patient_id)

    if user.role == 'doctor':
        return DoctorPatientLink.objects.filter(doctor=user, patient_id=real_patient_id).exists() or Patient.objects.filter(id=real_patient_id, doctor_npi__npi=user.npi).exists()
    
    if user.role == 'caregiver':
        return CaregiverPatientLink.objects.filter(caregiver=user, patient_id=real_patient_id, is_approved=True).exists()

    if user.role == 'family':
        return FamilyPatientLink.objects.filter(family=user, patient_id=real_patient_id, is_approved=True).exists()

    return False

def can_user_edit_patient_clinical(user, patient_id):
    if not patient_id:
        return False
    
    from patients.views import find_patient_by_identifier
    patient_obj = find_patient_by_identifier(patient_id)
    real_patient_id = patient_obj.id if patient_obj else patient_id

    if user.role == 'patient':
        user_p = find_patient_by_identifier(user.full_name) or find_patient_by_identifier(user.patient_id) or find_patient_by_identifier(user.device_id)
        if user_p:
            return user_p.id == real_patient_id
        return (user.patient_id == real_patient_id) or (user.device_id and user.device_id.upper().replace('NP-', 'P-') == real_patient_id)

    if user.role == 'caregiver':
        return CaregiverPatientLink.objects.filter(caregiver=user, patient_id=real_patient_id, is_approved=True, is_read_only=False).exists()

    if user.role == 'family':
        return FamilyPatientLink.objects.filter(family=user, patient_id=real_patient_id, is_approved=True, can_edit_clinical=True).exists()

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

        conditions = PatientConditionSerializer(patient.conditions.all().order_by('-created_at'), many=True).data
        allergies = PatientAllergySerializer(patient.allergies.all().order_by('-created_at'), many=True).data
        medications = PatientMedicationSerializer(patient.medications.all().order_by('-created_at'), many=True).data
        consultations = PatientConsultationSerializer(patient.consultations.all().order_by('-consultation_date'), many=True).data
        next_consultation = NextConsultationSerializer(patient.next_consultations.order_by('-consultation_date').first()).data if patient.next_consultations.exists() else None
        vitals = VitalMeasurementSerializer(patient.vitals.all().order_by('-measurement_time'), many=True).data

        log_audit_trail(request, 'Accessed Clinical Record', f"Health records for Patient {patient.id}", 'Success')

        return Response({
            'patientId': patient.id,
            'patientName': patient.name,
            'conditions': conditions,
            'allergies': allergies,
            'medications': medications,
            'consultations': consultations,
            'nextConsultation': next_consultation,
            'manualVitals': vitals,
            'vitals': vitals
        }, status=status.HTTP_200_OK)

    def post(self, request):
        patient_id = get_authorized_patient_id(request)
        if not can_user_edit_patient_clinical(request.user, patient_id):
            return Response("Unauthorized: Permission denied to modify patient clinical records.", status=status.HTTP_403_FORBIDDEN)

        record_type = request.data.get('type') # 'condition', 'allergy', 'manual_vital', 'medication', 'consultation', 'next_consultation'
        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        if record_type == 'manual_vital' or record_type == 'vital':
            hr = request.data.get('heartRate') if request.data.get('heartRate') is not None else request.data.get('heart_rate')
            spo2 = request.data.get('spo2')
            temp = request.data.get('temperature')
            rr = request.data.get('respiratoryRate') if request.data.get('respiratoryRate') is not None else request.data.get('respiratory_rate')
            sys_bp = request.data.get('systolicBp') if request.data.get('systolicBp') is not None else request.data.get('systolic_bp')
            dia_bp = request.data.get('diastolicBp') if request.data.get('diastolicBp') is not None else request.data.get('diastolic_bp')
            wt = request.data.get('weight')
            glucose = request.data.get('bloodGlucose') if request.data.get('bloodGlucose') is not None else request.data.get('blood_glucose')
            notes = request.data.get('notes', '')

            # Parse numbers safely
            parsed_vals = {}
            for name, raw in [
                ('heart_rate', hr), ('spo2', spo2), ('temperature', temp),
                ('respiratory_rate', rr), ('systolic_bp', sys_bp), ('diastolic_bp', dia_bp),
                ('weight', wt), ('blood_glucose', glucose)
            ]:
                if raw is not None and str(raw).strip() != '':
                    try:
                        parsed_vals[name] = float(raw) if name in ['heart_rate', 'spo2', 'temperature', 'weight', 'blood_glucose'] else int(raw)
                    except (ValueError, TypeError):
                        return Response(f"Invalid numeric input for {name}.", status=status.HTTP_400_BAD_REQUEST)
                else:
                    parsed_vals[name] = None

            # Integrity Check: At least 1 vital value must be present
            if not any(v is not None for v in parsed_vals.values()):
                return Response("At least one clinical vital measurement value must be provided.", status=status.HTTP_400_BAD_REQUEST)

            # Input Range Integrity Check
            unusual_detected = False
            for name, val in parsed_vals.items():
                if val is not None:
                    min_v, max_v = PHYSIOLOGICAL_INPUT_RANGES[name]
                    if val < min_v or val > max_v:
                        return Response(f"Invalid input for {name}: {val}. Value must be within reasonable physiological range ({min_v} to {max_v}).", status=status.HTTP_400_BAD_REQUEST)
                    if name in UNUSUAL_THRESHOLDS and UNUSUAL_THRESHOLDS[name](val):
                        unusual_detected = True

            # SECURITY ENFORCEMENT: Normal manual entry endpoint forces source = 'MANUAL'
            vital_obj = VitalMeasurement.objects.create(
                patient=patient,
                source='MANUAL',
                entered_by=request.user,
                entered_by_name=request.user.full_name,
                heart_rate=parsed_vals['heart_rate'],
                spo2=parsed_vals['spo2'],
                temperature=parsed_vals['temperature'],
                respiratory_rate=parsed_vals['respiratory_rate'],
                systolic_bp=parsed_vals['systolic_bp'],
                diastolic_bp=parsed_vals['diastolic_bp'],
                weight=parsed_vals['weight'],
                blood_glucose=parsed_vals['blood_glucose'],
                notes=notes
            )

            log_audit_trail(request, 'Recorded Manual Vital Measurement', f"Vital ID {vital_obj.id} (MANUAL) for Patient {patient.id}", 'Success')
            resp_data = VitalMeasurementSerializer(vital_obj).data
            if unusual_detected:
                resp_data['warning'] = "Please verify this measurement."
            return Response(resp_data, status=status.HTTP_201_CREATED)

        elif record_type == 'condition':
            c = PatientCondition.objects.create(
                patient=patient,
                condition_name=request.data.get('conditionName') or request.data.get('condition_name', 'General Evaluation'),
                description=request.data.get('description', ''),
                diagnosis_date=request.data.get('diagnosisDate') or request.data.get('diagnosis_date') or None,
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
                consultation_date=request.data.get('consultationDate') or timezone.now().date(),
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

class PatientHealthRecordDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_type, pk):
        model_map = {
            'condition': PatientCondition,
            'allergy': PatientAllergy,
            'vital': VitalMeasurement,
            'manual_vital': VitalMeasurement,
            'medication': PatientMedication,
            'consultation': PatientConsultation,
            'next_consultation': NextConsultation,
        }
        model_cls = model_map.get(item_type)
        if not model_cls:
            return Response("Invalid record type.", status=status.HTTP_400_BAD_REQUEST)

        obj = model_cls.objects.filter(pk=pk).first()
        if not obj:
            return Response("Record item not found.", status=status.HTTP_404_NOT_FOUND)

        if not can_user_edit_patient_clinical(request.user, obj.patient_id):
            return Response("Unauthorized: Permission denied to delete this clinical record.", status=status.HTTP_403_FORBIDDEN)

        obj.delete()
        log_audit_trail(request, f"Deleted Patient {item_type.capitalize()}", f"Item ID {pk} for Patient {obj.patient_id}", 'Success')
        return Response("Record deleted successfully.", status=status.HTTP_200_OK)

    def put(self, request, item_type, pk):
        model_map = {
            'condition': (PatientCondition, PatientConditionSerializer),
            'allergy': (PatientAllergy, PatientAllergySerializer),
            'vital': (VitalMeasurement, VitalMeasurementSerializer),
            'manual_vital': (VitalMeasurement, VitalMeasurementSerializer),
            'medication': (PatientMedication, PatientMedicationSerializer),
            'consultation': (PatientConsultation, PatientConsultationSerializer),
            'next_consultation': (NextConsultation, NextConsultationSerializer),
        }
        entry = model_map.get(item_type)
        if not entry:
            return Response("Invalid record type.", status=status.HTTP_400_BAD_REQUEST)

        model_cls, serializer_cls = entry
        obj = model_cls.objects.filter(pk=pk).first()
        if not obj:
            return Response("Record item not found.", status=status.HTTP_404_NOT_FOUND)

        if not can_user_edit_patient_clinical(request.user, obj.patient_id):
            return Response("Unauthorized: Permission denied to update this clinical record.", status=status.HTTP_403_FORBIDDEN)

        serializer = serializer_cls(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_audit_trail(request, f"Updated Patient {item_type.capitalize()}", f"Item ID {pk} for Patient {obj.patient_id}", 'Success')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientVitalsView(APIView):
    """
    ML/IoT Data Pipeline Compatible API
    Supports querying vitals filtered by source=MANUAL, source=DEVICE, or source=all
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: Permission denied to access patient vitals.", status=status.HTTP_403_FORBIDDEN)

        source_filter = request.query_params.get('source', 'all').upper()
        queryset = VitalMeasurement.objects.filter(patient_id=patient_id)

        if source_filter in ['MANUAL', 'DEVICE']:
            queryset = queryset.filter(source=source_filter)

        queryset = queryset.order_by('-measurement_time')
        data = VitalMeasurementSerializer(queryset, many=True).data
        return Response(data, status=status.HTTP_200_OK)


class MedicalDocumentView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        patient_id = get_authorized_patient_id(request)
        if not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: No permission to access patient documents.", status=status.HTTP_403_FORBIDDEN)

        docs = MedicalDocument.objects.filter(patient_id=patient_id).order_by('-upload_date')
        log_audit_trail(request, 'Accessed Document Metadata', f"Document list for Patient {patient_id}", 'Success')
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
        doc_type = request.data.get('documentType') or request.data.get('document_type', 'Other')
        desc = request.data.get('description', '')
        consultation_id = request.data.get('consultationId') or request.data.get('consultation')

        if not file_obj:
            return Response("Document file is required.", status=status.HTTP_400_BAD_REQUEST)

        consultation_obj = None
        if consultation_id:
            consultation_obj = PatientConsultation.objects.filter(id=consultation_id, patient=patient).first()

        doc = MedicalDocument.objects.create(
            patient=patient,
            uploaded_by=request.user,
            document_type=doc_type,
            title=title,
            description=desc,
            file=file_obj,
            consultation=consultation_obj
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
