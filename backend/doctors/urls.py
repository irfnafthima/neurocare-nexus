from django.urls import path
from doctors.views import NPILookupView, ConnectionRequestListCreateView, ConnectionRequestDetailView, DoctorListView, HealthFacilityListView

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
]
