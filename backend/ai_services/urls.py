from django.urls import path
from ai_services.views import (
    ChatView, MedicationGuidanceView, DoctorMedicationReviewRequestView, RAGEvaluationView,
    DoctorRiskReviewsView, DoctorPatientSummaryView
)

urlpatterns = [
    path('chat', ChatView.as_view(), name='ai-chat'),
    path('ai/medication-guidance', MedicationGuidanceView.as_view(), name='ai-medication-guidance'),
    path('ai/request-doctor-review', DoctorMedicationReviewRequestView.as_view(), name='ai-request-doctor-review'),
    path('ai/medication-reviews', DoctorMedicationReviewRequestView.as_view(), name='ai-medication-reviews'),
    path('ai/rag-evaluation', RAGEvaluationView.as_view(), name='ai-rag-evaluation'),
    path('ai/doctor-risk-reviews', DoctorRiskReviewsView.as_view(), name='ai-doctor-risk-reviews'),
    path('ai/patient-summary/<str:patient_id>', DoctorPatientSummaryView.as_view(), name='ai-patient-summary-id'),
    path('ai/patient-summary', DoctorPatientSummaryView.as_view(), name='ai-patient-summary'),
    path('doctors/ai-risk-reviews', DoctorRiskReviewsView.as_view(), name='doctors-ai-risk-reviews'),
    path('doctors/patients/<str:patient_id>/ai-summary', DoctorPatientSummaryView.as_view(), name='doctors-patient-ai-summary'),
]
