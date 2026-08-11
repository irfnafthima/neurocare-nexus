from django.urls import path
from patients.views import (
    PatientListView, PatientNotesView, PatientNotesUpdateView, 
    PatientDoctorUpdateView, PatientAccessControlsView, 
    FamilyRequestView, FamilyRequestApprovalView
)

urlpatterns = [
    path('patients', PatientListView.as_view(), name='patient-list'),
    path('patients/notes', PatientNotesView.as_view(), name='patient-notes'),
    path('patients/access-controls', PatientAccessControlsView.as_view(), name='patient-access-controls'),
    path('patients/<str:id>/notes', PatientNotesUpdateView.as_view(), name='patient-notes-update'),
    path('patients/<str:id>/doctor', PatientDoctorUpdateView.as_view(), name='patient-doctor-update'),
    path('family/requests', FamilyRequestView.as_view(), name='family-requests'),
    path('family/requests/<int:id>', FamilyRequestApprovalView.as_view(), name='family-request-approval'),
]
