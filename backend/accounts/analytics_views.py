"""
NeuroCare Nexus — Platform Activity Pipeline (Phase C)
Admin Analytics Views

Protected Admin-only endpoints delivering platform usage, session aggregation,
role distribution, and live presence metrics.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.views import IsAdminRole
from accounts.analytics_service import (
    get_platform_overview_analytics,
    get_role_platform_analytics,
    get_session_aggregate_analytics,
    get_activity_trends_analytics,
    get_live_online_users_list,
    get_individual_user_platform_analytics
)


class AdminAnalyticsOverviewView(APIView):
    """
    GET /api/admin/analytics/overview
    Returns high-level aggregate platform activity and session metrics.
    Strictly Admin-only.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        data = get_platform_overview_analytics()
        return Response(data, status=status.HTTP_200_OK)


class AdminAnalyticsRolesView(APIView):
    """
    GET /api/admin/analytics/roles
    Returns role-wise platform activity statistics (Patient, Doctor, Caregiver, Family, Admin).
    Strictly Admin-only; zero clinical information.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        data = get_role_platform_analytics()
        return Response(data, status=status.HTTP_200_OK)


class AdminAnalyticsSessionsView(APIView):
    """
    GET /api/admin/analytics/sessions?range=7d
    Provides aggregated session duration and distribution metrics.
    Supports range: 'today', '7d', '30d'.
    Strictly Admin-only.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        range_param = request.query_params.get('range', '7d')
        data = get_session_aggregate_analytics(range_str=range_param)
        return Response(data, status=status.HTTP_200_OK)


class AdminAnalyticsTrendsView(APIView):
    """
    GET /api/admin/analytics/trends?range=7d
    Provides time-bucketed login and session activity trends based on actual records.
    Supports range: 'today', '7d', '30d'.
    Strictly Admin-only.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        range_param = request.query_params.get('range', '7d')
        data = get_activity_trends_analytics(range_str=range_param)
        return Response(data, status=status.HTTP_200_OK)


class AdminAnalyticsOnlineUsersView(APIView):
    """
    GET /api/admin/analytics/online-users
    Returns current active and idle sessions with live presence and duration.
    Strictly Admin-only; zero clinical data.
    """
    permission_classes = [IsAdminRole]

    def get(self, request):
        data = get_live_online_users_list()
        return Response(data, status=status.HTTP_200_OK)


class AdminAnalyticsUserDetailView(APIView):
    """
    GET /api/admin/analytics/users/<int:user_id>
    Returns individual platform usage and session history for a specific user ID.
    Strictly Admin-only; zero clinical data.
    """
    permission_classes = [IsAdminRole]

    def get(self, request, user_id):
        data = get_individual_user_platform_analytics(user_id=user_id)
        if not data:
            return Response(
                {"error": f"User with ID {user_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(data, status=status.HTTP_200_OK)
