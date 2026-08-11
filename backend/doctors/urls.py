from django.urls import path
from doctors.views import NPILookupView, ConnectionRequestListCreateView, ConnectionRequestDetailView, DoctorListView, HealthFacilityListView

urlpatterns = [
    path('doctors', DoctorListView.as_view(), name='doctor-list'),
    path('facilities', HealthFacilityListView.as_view(), name='facilities-list'),
    path('npis/<str:npi>', NPILookupView.as_view(), name='npi-lookup'),
    path('connections/requests', ConnectionRequestListCreateView.as_view(), name='connection-requests'),
    path('connections/requests/<int:id>', ConnectionRequestDetailView.as_view(), name='connection-request-detail'),
]
