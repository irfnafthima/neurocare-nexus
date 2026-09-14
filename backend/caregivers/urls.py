from django.urls import path
from caregivers.views import CaregiverRequestView, CaregiverRequestApprovalView

urlpatterns = [
    path('caregivers/requests', CaregiverRequestView.as_view(), name='caregiver-requests'),
    path('caregivers/requests/', CaregiverRequestView.as_view(), name='caregiver-requests-slash'),
    path('caregivers/requests/<int:id>', CaregiverRequestApprovalView.as_view(), name='caregiver-request-approve'),
    path('caregivers/requests/<int:id>/', CaregiverRequestApprovalView.as_view(), name='caregiver-request-approve-slash'),
    path('caregiver-requests', CaregiverRequestView.as_view(), name='caregiver-requests-alias'),
    path('caregiver-requests/', CaregiverRequestView.as_view(), name='caregiver-requests-alias-slash'),
    path('caregiver-requests/<int:id>', CaregiverRequestApprovalView.as_view(), name='caregiver-request-approve-alias'),
    path('caregiver-requests/<int:id>/', CaregiverRequestApprovalView.as_view(), name='caregiver-request-approve-alias-slash'),
]
