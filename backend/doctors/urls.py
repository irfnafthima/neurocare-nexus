from django.urls import path
from doctors.views import (
    NPILookupView, ConnectionRequestListCreateView, ConnectionRequestDetailView, 
    DoctorListView, HealthFacilityListView, DoctorVerificationStatusView,
    DoctorDocumentUploadView, DoctorDocumentDownloadView,
    AdminDoctorDocumentRequestView, AdminDoctorDocumentReviewView,
    AdminDoctorDocumentDownloadView
)

urlpatterns = [
    path('doctors', DoctorListView.as_view(), name='doctor-list'),
    path('doctors/', DoctorListView.as_view(), name='doctor-list-slash'),
    path('doctors/directory', DoctorListView.as_view(), name='doctor-directory'),
    path('doctors/directory/', DoctorListView.as_view(), name='doctor-directory-slash'),
    path('facilities', HealthFacilityListView.as_view(), name='facilities-list'),
    path('facilities/', HealthFacilityListView.as_view(), name='facilities-list-slash'),
    path('npis/<str:npi>', NPILookupView.as_view(), name='npi-lookup'),
    path('connections/requests', ConnectionRequestListCreateView.as_view(), name='connection-requests'),
    path('connections/requests/', ConnectionRequestListCreateView.as_view(), name='connection-requests-slash'),
    path('connections/requests/<int:id>', ConnectionRequestDetailView.as_view(), name='connection-request-detail'),
    path('connections/requests/<int:id>/', ConnectionRequestDetailView.as_view(), name='connection-request-detail-slash'),
    path('doctor-requests', ConnectionRequestListCreateView.as_view(), name='doctor-requests'),
    path('doctor-requests/', ConnectionRequestListCreateView.as_view(), name='doctor-requests-slash'),
    path('doctor-requests/<int:id>', ConnectionRequestDetailView.as_view(), name='doctor-requests-detail'),
    path('doctor-requests/<int:id>/', ConnectionRequestDetailView.as_view(), name='doctor-requests-detail-slash'),
    
    # Doctor Verification & Document Upload routes
    path('doctor/verification-status', DoctorVerificationStatusView.as_view(), name='doctor-verification-status'),
    path('doctor/verification-status/', DoctorVerificationStatusView.as_view(), name='doctor-verification-status-slash'),
    path('doctor/documents/upload', DoctorDocumentUploadView.as_view(), name='doctor-document-upload'),
    path('doctor/documents/upload/', DoctorDocumentUploadView.as_view(), name='doctor-document-upload-slash'),
    path('doctor/documents/<int:id>/download', DoctorDocumentDownloadView.as_view(), name='doctor-document-download'),
    path('doctor/documents/<int:id>/download/', DoctorDocumentDownloadView.as_view(), name='doctor-document-download-slash'),
    path('doctor/documents/download/<int:id>', DoctorDocumentDownloadView.as_view(), name='doctor-document-download-alt'),
    path('doctor/documents/download/<int:id>/', DoctorDocumentDownloadView.as_view(), name='doctor-document-download-alt-slash'),
    
    # Admin Document Management routes
    path('admin/doctors/<int:id>/request-document', AdminDoctorDocumentRequestView.as_view(), name='admin-doctor-request-document'),
    path('admin/doctors/<int:id>/request-document/', AdminDoctorDocumentRequestView.as_view(), name='admin-doctor-request-document-slash'),
    path('admin/doctors/<int:id>/request-documents', AdminDoctorDocumentRequestView.as_view(), name='admin-doctor-request-documents'),
    path('admin/doctors/<int:id>/request-documents/', AdminDoctorDocumentRequestView.as_view(), name='admin-doctor-request-documents-slash'),
    path('admin/doctors/documents/<int:id>/review', AdminDoctorDocumentReviewView.as_view(), name='admin-doctor-document-review'),
    path('admin/doctors/documents/<int:id>/review/', AdminDoctorDocumentReviewView.as_view(), name='admin-doctor-document-review-slash'),
    path('admin/doctors/documents/<int:id>/download', AdminDoctorDocumentDownloadView.as_view(), name='admin-doctor-document-download'),
    path('admin/doctors/documents/<int:id>/download/', AdminDoctorDocumentDownloadView.as_view(), name='admin-doctor-document-download-slash'),
]

