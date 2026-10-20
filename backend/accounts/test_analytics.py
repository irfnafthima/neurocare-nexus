import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CustomUser, AuditLog, UserSession
from accounts.analytics_service import (
    get_platform_overview_analytics,
    get_role_platform_analytics,
    get_session_aggregate_analytics,
    get_activity_trends_analytics,
    get_live_online_users_list,
    get_individual_user_platform_analytics
)


def get_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class AdminPlatformAnalyticsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Admin user
        self.admin_user = CustomUser.objects.create_user(
            email="admin.analytics@nexus.test",
            password="StrongPassword@123",
            full_name="Admin Analytics",
            role="admin",
            approved=True,
            status="ACTIVE"
        )
        self.token_admin = get_jwt_token(self.admin_user)

        # 2. Patient user
        self.patient_user = CustomUser.objects.create_user(
            email="patient.analytics@nexus.test",
            password="StrongPassword@123",
            full_name="Patient Analytics",
            role="patient",
            approved=True,
            status="ACTIVE"
        )
        self.token_patient = get_jwt_token(self.patient_user)

        # 3. Doctor user
        self.doctor_user = CustomUser.objects.create_user(
            email="doctor.analytics@nexus.test",
            password="StrongPassword@123",
            full_name="Dr. Analytics",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )
        self.token_doctor = get_jwt_token(self.doctor_user)

        # 4. Caregiver user
        self.caregiver_user = CustomUser.objects.create_user(
            email="caregiver.analytics@nexus.test",
            password="StrongPassword@123",
            full_name="Caregiver Analytics",
            role="caregiver",
            approved=True,
            status="ACTIVE"
        )
        self.token_caregiver = get_jwt_token(self.caregiver_user)

        # 5. Family user
        self.family_user = CustomUser.objects.create_user(
            email="family.analytics@nexus.test",
            password="StrongPassword@123",
            full_name="Family Analytics",
            role="family",
            approved=True,
            status="ACTIVE"
        )
        self.token_family = get_jwt_token(self.family_user)

        self.now = timezone.now()

        # Create defined sessions for presence & duration testing:
        # Patient: 1 ACTIVE session (heartbeat 20s ago, activity 30s ago)
        self.session_patient_active = UserSession.objects.create(
            user=self.patient_user,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(minutes=15),
            last_heartbeat_at=self.now - timedelta(seconds=20),
            last_activity_at=self.now - timedelta(seconds=30),
            status="ACTIVE"
        )

        # Doctor: 1 IDLE session (heartbeat 20s ago, activity 6 minutes ago)
        self.session_doctor_idle = UserSession.objects.create(
            user=self.doctor_user,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(minutes=40),
            last_heartbeat_at=self.now - timedelta(seconds=20),
            last_activity_at=self.now - timedelta(minutes=6),
            status="ACTIVE"
        )

        # Caregiver: 1 OFFLINE session (closed 1 hour ago, duration 30 mins)
        self.session_caregiver_closed = UserSession.objects.create(
            user=self.caregiver_user,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(hours=2),
            ended_at=self.now - timedelta(hours=1, minutes=30),
            last_heartbeat_at=self.now - timedelta(hours=1, minutes=30),
            last_activity_at=self.now - timedelta(hours=1, minutes=30),
            status="CLOSED"
        )

        # Family: 1 OFFLINE session due to stale heartbeat (heartbeat 10 minutes ago)
        self.session_family_stale = UserSession.objects.create(
            user=self.family_user,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(hours=1),
            last_heartbeat_at=self.now - timedelta(minutes=10),
            last_activity_at=self.now - timedelta(minutes=10),
            status="ACTIVE"
        )

    # -------------------------------------------------------------------------
    # 1 - 6. Role Authorization Security Tests
    # -------------------------------------------------------------------------
    def test_admin_can_access_overview(self):
        """Admin with valid credentials can access overview with HTTP 200."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', resp.data)
        self.assertIn('online_users', resp.data)

    def test_patient_cannot_access_overview(self):
        """Patient role is rejected with HTTP 403 Forbidden."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_patient}")
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_access_overview(self):
        """Doctor role is rejected with HTTP 403 Forbidden."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_doctor}")
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_caregiver_cannot_access_overview(self):
        """Caregiver role is rejected with HTTP 403 Forbidden."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_caregiver}")
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_family_cannot_access_overview(self):
        """Family role is rejected with HTTP 403 Forbidden."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_family}")
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_request_rejected(self):
        """Unauthenticated request is rejected with HTTP 401 Unauthorized."""
        self.client.credentials()
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 7 - 10. Overview Counts & Presence Aggregation Tests
    # -------------------------------------------------------------------------
    def test_overview_counts_and_presence_aggregation(self):
        """Overview metrics accurately compute total, active, idle, and offline users."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get('/api/admin/analytics/overview')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        # 5 users created in setUp (admin, patient, doctor, caregiver, family)
        self.assertEqual(data['total_users'], 5)
        # 1 user is active (patient)
        self.assertEqual(data['online_users'], 1)
        self.assertEqual(data['active_users'], 1)
        # 1 user is idle (doctor)
        self.assertEqual(data['idle_users'], 1)
        # 3 users are offline (caregiver with closed session, family with stale heartbeat, admin with no session)
        self.assertEqual(data['offline_users'], 3)
        # Total sessions = 4 created in setUp
        self.assertEqual(data['total_sessions'], 4)

    # -------------------------------------------------------------------------
    # 11. Multi-session User Isolation & No Double Counting
    # -------------------------------------------------------------------------
    def test_multi_session_user_not_double_counted(self):
        """User with both ACTIVE and IDLE sessions counts as ACTIVE once, not twice."""
        # Patient opens a second session that is IDLE
        UserSession.objects.create(
            user=self.patient_user,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(minutes=20),
            last_heartbeat_at=self.now - timedelta(seconds=20),
            last_activity_at=self.now - timedelta(minutes=7), # IDLE
            status="ACTIVE"
        )

        overview = get_platform_overview_analytics(current_time=self.now)
        # Patient should still count as 1 online/active user, not 2
        self.assertEqual(overview['online_users'], 1)
        # Doctor is idle (1), patient is not counted under idle because active takes priority
        self.assertEqual(overview['idle_users'], 1)

    # -------------------------------------------------------------------------
    # 12 & 13. Closed and Active Session Durations
    # -------------------------------------------------------------------------
    def test_session_durations_calculated_accurately(self):
        """Closed session duration uses ended_at; active session uses current_time."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get('/api/admin/analytics/sessions?range=7d')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(data['range'], '7d')
        self.assertEqual(data['session_count'], 4)
        self.assertEqual(data['completed_sessions'], 1)
        self.assertEqual(data['active_sessions'], 3)

        # Closed caregiver session was exactly 30 minutes = 1800 seconds
        self.assertEqual(data['shortest_duration_seconds'], 1800.0)
        self.assertGreater(data['total_usage_seconds'], 1800.0)

    # -------------------------------------------------------------------------
    # 14. Sessions Today Aggregation
    # -------------------------------------------------------------------------
    def test_sessions_today_calculated_correctly(self):
        """Sessions started today are counted correctly."""
        overview = get_platform_overview_analytics(current_time=self.now)
        self.assertEqual(overview['sessions_today'], 4)

        # Create a session from 2 days ago
        UserSession.objects.create(
            user=self.patient_user,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(days=2),
            ended_at=self.now - timedelta(days=2, hours=-1),
            status="CLOSED"
        )

        overview_after = get_platform_overview_analytics(current_time=self.now)
        self.assertEqual(overview_after['total_sessions'], 5)
        # Today's sessions remain 4
        self.assertEqual(overview_after['sessions_today'], 4)

    # -------------------------------------------------------------------------
    # 15. Role Analytics Aggregation
    # -------------------------------------------------------------------------
    def test_role_platform_analytics(self):
        """Role analytics correctly groups by patient, doctor, caregiver, family, admin."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get('/api/admin/analytics/roles')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        roles_list = resp.data
        self.assertEqual(len(roles_list), 5)

        roles_dict = {item['role_key']: item for item in roles_list}
        self.assertIn('patient', roles_dict)
        self.assertIn('doctor', roles_dict)
        self.assertIn('caregiver', roles_dict)
        self.assertIn('family', roles_dict)
        self.assertIn('admin', roles_dict)

        self.assertEqual(roles_dict['patient']['total_users'], 1)
        self.assertEqual(roles_dict['patient']['active_now'], 1)
        self.assertEqual(roles_dict['doctor']['idle_now'], 1)
        self.assertEqual(roles_dict['caregiver']['offline'], 1)
        self.assertEqual(roles_dict['admin']['offline'], 1)

    # -------------------------------------------------------------------------
    # 16. Trend Aggregation Using Real Records
    # -------------------------------------------------------------------------
    def test_trends_aggregation_uses_real_records(self):
        """Trends endpoint returns time-bucketed login and session numbers."""
        # Log a real login audit event
        AuditLog.objects.create(
            username=self.patient_user.full_name,
            actor=self.patient_user,
            action="Login Session Initiated",
            target="PATIENT Portal Access",
            status="Success"
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get('/api/admin/analytics/trends?range=7d')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(data['range'], '7d')
        self.assertEqual(len(data['data']), 7)

        # Check today's bucket
        today_bucket = data['data'][-1]
        self.assertEqual(today_bucket['date'], self.now.date().isoformat())
        self.assertGreaterEqual(today_bucket['logins'], 1)
        self.assertGreaterEqual(today_bucket['sessions_started'], 4)

    # -------------------------------------------------------------------------
    # 17. Online-users Endpoint Returns Only Live Sessions
    # -------------------------------------------------------------------------
    def test_online_users_endpoint_returns_only_live_sessions(self):
        """Online-users endpoint returns active and idle sessions, not closed or stale ones."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get('/api/admin/analytics/online-users')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        sessions = resp.data
        # Should only contain patient (ACTIVE) and doctor (IDLE).
        # Caregiver is CLOSED, Family is stale heartbeat (> 2 min).
        self.assertEqual(len(sessions), 2)

        session_ids = [s['sessionId'] for s in sessions]
        self.assertIn(str(self.session_patient_active.session_id), session_ids)
        self.assertIn(str(self.session_doctor_idle.session_id), session_ids)
        self.assertNotIn(str(self.session_caregiver_closed.session_id), session_ids)
        self.assertNotIn(str(self.session_family_stale.session_id), session_ids)

        # Verify sorted ACTIVE first
        self.assertEqual(sessions[0]['presence'], 'ACTIVE')

    # -------------------------------------------------------------------------
    # 18. Individual User Analytics
    # -------------------------------------------------------------------------
    def test_individual_user_platform_analytics(self):
        """Individual user endpoint returns accurate platform session stats."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        resp = self.client.get(f'/api/admin/analytics/users/{self.patient_user.id}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.data
        self.assertEqual(data['userId'], self.patient_user.id)
        self.assertEqual(data['email'], self.patient_user.email)
        self.assertEqual(data['role'], 'patient')
        self.assertEqual(data['currentPresence'], 'ACTIVE')
        self.assertEqual(data['totalSessions'], 1)
        self.assertIsNotNone(data['activeSession'])
        self.assertEqual(data['activeSession']['sessionId'], str(self.session_patient_active.session_id))

        # Nonexistent user returns 404
        resp_404 = self.client.get('/api/admin/analytics/users/999999')
        self.assertEqual(resp_404.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 19. Privacy: Zero Clinical Data Leaks
    # -------------------------------------------------------------------------
    def test_zero_clinical_data_leaks_in_analytics(self):
        """Analytics responses never contain clinical fields like vitals, diagnosis, prescriptions."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_admin}")
        forbidden_keys = [
            'heart_rate', 'spo2', 'temperature', 'diagnosis', 'vitals',
            'prescription', 'prescriptions', 'fall_detected', 'clinical_note', 'medical_records'
        ]

        endpoints = [
            '/api/admin/analytics/overview',
            '/api/admin/analytics/roles',
            '/api/admin/analytics/sessions',
            '/api/admin/analytics/trends',
            '/api/admin/analytics/online-users',
            f'/api/admin/analytics/users/{self.patient_user.id}'
        ]

        for ep in endpoints:
            resp = self.client.get(ep)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            resp_str = str(resp.data).lower()
            for key in forbidden_keys:
                self.assertNotIn(f"'{key}'", resp_str)
