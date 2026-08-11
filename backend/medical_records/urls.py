from django.urls import path
from medical_records.views import (
    PatientHealthRecordView, MedicalDocumentView, MedicalDocumentDownloadView
)

urlpatterns = [
    path('health-records', PatientHealthRecordView.as_view(), name='patient-health-records'),
    path('documents', MedicalDocumentView.as_view(), name='patient-documents'),
    path('documents/<int:id>/download', MedicalDocumentDownloadView.as_view(), name='download-document'),
]
