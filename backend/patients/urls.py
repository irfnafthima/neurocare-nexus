from django.urls import path
from patients.views import (
    PatientListView, PatientNotesView, PatientNotesUpdateView, 
    PatientDoctorUpdateView, PatientAccessControlsView, 
    FamilyRequestView, FamilyRequestApprovalView, PatientProfileUpdateView,
    PatientCaregiverLinkView, PatientCaregiverRevokeView,
    PatientFamilyLinkView, PatientFamilyRevokeView
)

urlpatterns = [
    path('patients', PatientListView.as_view(), name='patient-list'),
    path('patients/', PatientListView.as_view(), name='patient-list-slash'),
    path('patients/notes', PatientNotesView.as_view(), name='patient-notes'),
    path('patients/notes/', PatientNotesView.as_view(), name='patient-notes-slash'),
    path('patients/access-controls', PatientAccessControlsView.as_view(), name='patient-access-controls'),
    path('patients/access-controls/', PatientAccessControlsView.as_view(), name='patient-access-controls-slash'),
    path('access-controls', PatientAccessControlsView.as_view(), name='access-controls'),
    path('access-controls/', PatientAccessControlsView.as_view(), name='access-controls-slash'),
    path('access-controls/caregiver', PatientCaregiverLinkView.as_view(), name='access-controls-caregiver'),
    path('access-controls/caregiver/', PatientCaregiverLinkView.as_view(), name='access-controls-caregiver-slash'),
    path('access-controls/caregiver/<int:id>', PatientCaregiverRevokeView.as_view(), name='access-controls-caregiver-revoke'),
    path('access-controls/caregiver/<int:id>/', PatientCaregiverRevokeView.as_view(), name='access-controls-caregiver-revoke-slash'),
    path('access-controls/family', PatientFamilyLinkView.as_view(), name='access-controls-family'),
    path('access-controls/family/', PatientFamilyLinkView.as_view(), name='access-controls-family-slash'),
    path('access-controls/family/<int:id>', PatientFamilyRevokeView.as_view(), name='access-controls-family-revoke'),
    path('access-controls/family/<int:id>/', PatientFamilyRevokeView.as_view(), name='access-controls-family-revoke-slash'),
    path('patients/<str:id>/profile', PatientProfileUpdateView.as_view(), name='patient-profile-update'),
    path('patients/<str:id>/profile/', PatientProfileUpdateView.as_view(), name='patient-profile-update-slash'),
    path('patients/<str:id>/notes', PatientNotesUpdateView.as_view(), name='patient-notes-update'),
    path('patients/<str:id>/notes/', PatientNotesUpdateView.as_view(), name='patient-notes-update-slash'),
    path('patients/<str:id>/doctor', PatientDoctorUpdateView.as_view(), name='patient-doctor-update'),
    path('patients/<str:id>/doctor/', PatientDoctorUpdateView.as_view(), name='patient-doctor-update-slash'),
    path('family/requests', FamilyRequestView.as_view(), name='family-requests'),
    path('family/requests/', FamilyRequestView.as_view(), name='family-requests-slash'),
    path('family/requests/<int:id>', FamilyRequestApprovalView.as_view(), name='family-request-approval'),
    path('family/requests/<int:id>/', FamilyRequestApprovalView.as_view(), name='family-request-approval-slash'),
]

