from django.urls import path
from accounts.views import (
    RegisterView, LoginView, LogoutView, HeartbeatView, CheckEmailAvailabilityView, AdminStatsView, AdminUserListView,
    AdminUserDeleteView, AdminPendingDoctorsView, AdminDoctorApproveView,
    AdminDoctorRejectView, AdminDoctorSuspendView, AdminDoctorVerifyAffiliationView,
    AdminDoctorDetailView, AdminDevicesListView, AuditLogListCreateView
)
from accounts.profile_views import UserProfileMeView
from accounts.analytics_views import (
    AdminAnalyticsOverviewView,
    AdminAnalyticsRolesView,
    AdminAnalyticsSessionsView,
    AdminAnalyticsTrendsView,
    AdminAnalyticsOnlineUsersView,
    AdminAnalyticsUserDetailView
)

urlpatterns = [
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/logout/', LogoutView.as_view(), name='logout-slash'),
    path('auth/check-email', CheckEmailAvailabilityView.as_view(), name='check-email'),

    path('presence/heartbeat', HeartbeatView.as_view(), name='presence-heartbeat'),
    path('presence/heartbeat/', HeartbeatView.as_view(), name='presence-heartbeat-slash'),

    # Admin Platform Activity Analytics Endpoints (Phase C)
    path('admin/analytics/overview', AdminAnalyticsOverviewView.as_view(), name='admin-analytics-overview'),
    path('admin/analytics/overview/', AdminAnalyticsOverviewView.as_view(), name='admin-analytics-overview-slash'),
    path('admin/analytics/roles', AdminAnalyticsRolesView.as_view(), name='admin-analytics-roles'),
    path('admin/analytics/roles/', AdminAnalyticsRolesView.as_view(), name='admin-analytics-roles-slash'),
    path('admin/analytics/sessions', AdminAnalyticsSessionsView.as_view(), name='admin-analytics-sessions'),
    path('admin/analytics/sessions/', AdminAnalyticsSessionsView.as_view(), name='admin-analytics-sessions-slash'),
    path('admin/analytics/trends', AdminAnalyticsTrendsView.as_view(), name='admin-analytics-trends'),
    path('admin/analytics/trends/', AdminAnalyticsTrendsView.as_view(), name='admin-analytics-trends-slash'),
    path('admin/analytics/online-users', AdminAnalyticsOnlineUsersView.as_view(), name='admin-analytics-online-users'),
    path('admin/analytics/online-users/', AdminAnalyticsOnlineUsersView.as_view(), name='admin-analytics-online-users-slash'),
    path('admin/analytics/users/<int:user_id>', AdminAnalyticsUserDetailView.as_view(), name='admin-analytics-user-detail'),
    path('admin/analytics/users/<int:user_id>/', AdminAnalyticsUserDetailView.as_view(), name='admin-analytics-user-detail-slash'),

    path('profile/me', UserProfileMeView.as_view(), name='user-profile-me'),
    path('profile/me/', UserProfileMeView.as_view(), name='user-profile-me-slash'),
    path('admin/stats', AdminStatsView.as_view(), name='admin-stats'),
    path('admin-stats', AdminStatsView.as_view(), name='admin-stats-alias'),
    path('admin/devices', AdminDevicesListView.as_view(), name='admin-devices'),
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

