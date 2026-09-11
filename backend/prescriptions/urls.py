from django.urls import path
from prescriptions.views import PrescriptionListCreateView, PrescriptionDetailView

urlpatterns = [
    path('prescriptions', PrescriptionListCreateView.as_view(), name='prescriptions-list-create'),
    path('prescriptions/', PrescriptionListCreateView.as_view(), name='prescriptions-list-create-slash'),
    path('prescriptions/<int:id>', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('prescriptions/<int:id>/', PrescriptionDetailView.as_view(), name='prescription-detail-slash'),
]
