from django.urls import path
from ai_services.views import (
    ChatView, MedicationGuidanceView, DoctorMedicationReviewRequestView, RAGEvaluationView
)

urlpatterns = [
    path('chat', ChatView.as_view(), name='ai-chat'),
    path('ai/medication-guidance', MedicationGuidanceView.as_view(), name='ai-medication-guidance'),
    path('ai/request-doctor-review', DoctorMedicationReviewRequestView.as_view(), name='ai-request-doctor-review'),
    path('ai/medication-reviews', DoctorMedicationReviewRequestView.as_view(), name='ai-medication-reviews'),
    path('ai/rag-evaluation', RAGEvaluationView.as_view(), name='ai-rag-evaluation'),
]
