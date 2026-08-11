from django.urls import path
from caregivers.views import CaregiverRequestView, CaregiverRequestApprovalView

urlpatterns = [
    path('caregivers/requests', CaregiverRequestView.as_view(), name='caregiver-requests'),
    path('caregivers/requests/<int:id>', CaregiverRequestApprovalView.as_view(), name='caregiver-request-approve'),
]
