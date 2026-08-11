from django.urls import path
from accounts.views import (
    RegisterView, LoginView, AdminStatsView, AdminUserListView,
    AdminUserDeleteView, AdminPendingDoctorsView, AdminDoctorApproveView,
    AdminDoctorRejectView, AdminDoctorSuspendView, AdminDoctorVerifyAffiliationView,
    AdminDoctorDetailView, AuditLogListCreateView
)

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('admin/stats', AdminStatsView.as_view(), name='admin-stats'),
    path('admin/users', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:id>', AdminUserDeleteView.as_view(), name='admin-user-delete'),
    path('admin/pending-doctors', AdminPendingDoctorsView.as_view(), name='admin-pending-doctors'),
    path('admin/doctors/<int:id>/details', AdminDoctorDetailView.as_view(), name='admin-doctor-details'),
    path('admin/doctors/<int:id>/approve', AdminDoctorApproveView.as_view(), name='admin-doctor-approve'),
    path('admin/doctors/<int:id>/reject', AdminDoctorRejectView.as_view(), name='admin-doctor-reject'),
    path('admin/doctors/<int:id>/suspend', AdminDoctorSuspendView.as_view(), name='admin-doctor-suspend'),
    path('admin/doctors/<int:id>/verify-affiliation', AdminDoctorVerifyAffiliationView.as_view(), name='admin-doctor-verify-affiliation'),
    path('audit-logs', AuditLogListCreateView.as_view(), name='audit-logs'),
]
