from django.urls import path
from prescriptions.views import PrescriptionListCreateView

urlpatterns = [
    path('prescriptions', PrescriptionListCreateView.as_view(), name='prescriptions-list-create'),
]
