from django.urls import path
from medical_records.views import (
    PatientHealthRecordView, PatientHealthRecordDetailView, MedicalDocumentView, MedicalDocumentDownloadView
)

urlpatterns = [
    path('health-records', PatientHealthRecordView.as_view(), name='patient-health-records'),
    path('health-records/<str:item_type>/<int:pk>', PatientHealthRecordDetailView.as_view(), name='patient-health-record-detail'),
    path('documents', MedicalDocumentView.as_view(), name='patient-documents'),
    path('documents/<int:id>/download', MedicalDocumentDownloadView.as_view(), name='download-document'),
]
