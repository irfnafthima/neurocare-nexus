from django.urls import path
from prescriptions.views import PrescriptionListCreateView, PrescriptionDetailView

urlpatterns = [
    path('prescriptions', PrescriptionListCreateView.as_view(), name='prescriptions-list-create'),
    path('prescriptions/<int:id>', PrescriptionDetailView.as_view(), name='prescription-detail'),
]
