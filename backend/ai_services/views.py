import os
import time
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import CustomUser, AuditLog
from patients.models import Patient
from doctors.models import DoctorPatientLink
from ai_services.models import MedicationKnowledgeBase, DoctorMedicationReviewRequest
from ai_services.rag_engine import run_rag_medication_guidance
from ai_services.eval_dataset import run_rag_evaluation_suite
from medical_records.views import is_user_authorized_for_patient
from notifications.utils import create_notification
from accounts.utils import log_audit_trail

chat_rate_limits = {}

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        patient_id = request.data.get('patientId')

        if not message or str(message).strip() == '':
            return Response("Message body is required.", status=status.HTTP_400_BAD_REQUEST)

        user_id = request.user.id
        role = request.user.role

        # Rate limiting: max 30 queries/hr
        now = time.time()
        if user_id not in chat_rate_limits:
            chat_rate_limits[user_id] = {'count': 1, 'window_start': now}
        else:
            limit = chat_rate_limits[user_id]
            if now - limit['window_start'] > 3600:
                limit['count'] = 1
                limit['window_start'] = now
            else:
                if limit['count'] >= 30:
                    return Response("Rate limit exceeded: Max 30 chatbot queries per hour.", status=status.HTTP_429_TOO_MANY_REQUESTS)
                limit['count'] += 1

        # Determine target patient ID
        if not patient_id:
            if role == 'patient':
                from patients.views import find_patient_by_identifier
                p = find_patient_by_identifier(request.user.full_name) or find_patient_by_identifier(request.user.patient_id)
                patient_id = p.id if p else request.user.patient_id
            elif role == 'doctor':
                p = Patient.objects.first()
                patient_id = p.id if p else 'P-101'

        if not patient_id or not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: You do not have permission to access patient clinical context.", status=status.HTTP_403_FORBIDDEN)

        # Run RAG Medication Guidance Pipeline
        rag_res = run_rag_medication_guidance(request.user, patient_id, message)
        
        log_audit_trail(request, 'Executed RAG Chat Query', f"Query: {message[:50]}... for Patient {patient_id}", 'Success')

        return Response({
            'reply': rag_res.get('explanation'),
            'safety_status': rag_res.get('safety_status'),
            'safety_disclaimer': rag_res.get('safety_disclaimer'),
            'concerns': rag_res.get('concerns', []),
            'is_prescribe_request': rag_res.get('is_prescribe_request', False),
            'retrieved_context': rag_res.get('retrieved_context', {})
        }, status=status.HTTP_200_OK)


class MedicationGuidanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query') or request.data.get('message')
        patient_id = request.data.get('patientId')

        if not query or not str(query).strip():
            return Response("Query text is required.", status=status.HTTP_400_BAD_REQUEST)

        if not patient_id:
            if request.user.role == 'patient':
                from patients.views import find_patient_by_identifier
                p = find_patient_by_identifier(request.user.full_name) or find_patient_by_identifier(request.user.patient_id)
                patient_id = p.id if p else request.user.patient_id

        if not patient_id or not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: Access denied to patient medication context.", status=status.HTTP_403_FORBIDDEN)

        rag_res = run_rag_medication_guidance(request.user, patient_id, query)
        log_audit_trail(request, 'Requested RAG Medication Guidance', f"Medication query for Patient {patient_id}", 'Success')
        return Response(rag_res, status=status.HTTP_200_OK)


class DoctorMedicationReviewRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'doctor':
            return Response("Unauthorized: Attending doctor authentication required.", status=status.HTTP_403_FORBIDDEN)

        reviews = DoctorMedicationReviewRequest.objects.all().order_by('-created_at')
        data = [{
            'id': r.id,
            'patient_id': r.patient_id,
            'patient_name': r.patient.name,
            'requested_by': r.user.full_name or r.user.email,
            'medication_name': r.medication_name,
            'question': r.question,
            'safety_status': r.safety_status,
            'status': r.status,
            'created_at': r.created_at.isoformat()
        } for r in reviews]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        patient_id = request.data.get('patientId')
        medication_name = request.data.get('medicationName') or 'Unspecified Medication'
        question = request.data.get('question', '')
        safety_status = request.data.get('safetyStatus', 'REVIEW_RECOMMENDED')

        if not patient_id:
            if request.user.role == 'patient':
                from patients.views import find_patient_by_identifier
                p = find_patient_by_identifier(request.user.full_name) or find_patient_by_identifier(request.user.patient_id)
                patient_id = p.id if p else request.user.patient_id

        if not patient_id or not is_user_authorized_for_patient(request.user, patient_id):
            return Response("Unauthorized: Cannot request doctor review for unauthorized patient.", status=status.HTTP_403_FORBIDDEN)

        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        # Target Doctor: linked doctor or patient's doctor_npi
        target_doc = None
        link = DoctorPatientLink.objects.filter(patient=patient).first()
        if link:
            target_doc = link.doctor
        elif patient.doctor_npi:
            target_doc = CustomUser.objects.filter(npi=patient.doctor_npi.npi).first()

        review_req = DoctorMedicationReviewRequest.objects.create(
            patient=patient,
            user=request.user,
            doctor=target_doc,
            medication_name=medication_name,
            question=question,
            safety_status=safety_status,
            status='PENDING'
        )

        log_audit_trail(request, 'Requested Doctor Medication Review', f"Review Request {review_req.id} for {medication_name}", 'Success')

        # Trigger notification to doctor
        if target_doc:
            create_notification(
                user=target_doc,
                title="New Medication Review Request",
                message=f"Patient {patient.name} requested a medication safety review for {medication_name}.",
                category="prescription",
                target_id=review_req.id
            )

        return Response({
            'status': 'success',
            'id': review_req.id,
            'message': 'Medication review request submitted to doctor.'
        }, status=status.HTTP_201_CREATED)


class RAGEvaluationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        metrics = run_rag_evaluation_suite(request.user)
        return Response(metrics, status=status.HTTP_200_OK)
