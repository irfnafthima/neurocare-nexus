from django.urls import path, re_path
from medical_records.views import (
    PatientHealthRecordView, PatientHealthRecordDetailView, 
    MedicalDocumentView, MedicalDocumentDetailView, MedicalDocumentDownloadView, PatientVitalsView
)

urlpatterns = [
    re_path(r'^health-records/?$', PatientHealthRecordView.as_view(), name='patient-health-records'),
    re_path(r'^health-records/(?P<item_type>[^/]+)/(?P<pk>\d+)/?$', PatientHealthRecordDetailView.as_view(), name='patient-health-record-detail'),
    re_path(r'^vitals/?$', PatientVitalsView.as_view(), name='patient-vitals'),
    re_path(r'^(?:medical-)?documents/?$', MedicalDocumentView.as_view(), name='patient-documents'),
    re_path(r'^(?:medical-)?documents/(?P<id>\d+)/?$', MedicalDocumentDetailView.as_view(), name='patient-document-detail'),
    re_path(r'^(?:medical-)?documents/(?P<id>\d+)/download/?$', MedicalDocumentDownloadView.as_view(), name='download-document'),
]

