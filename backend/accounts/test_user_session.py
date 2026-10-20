import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import CustomUser, AuditLog, UserSession
from doctors.models import DoctorProfile


class UserSessionAndAuthenticationActivityTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create active patient user
        self.patient_user = CustomUser.objects.create_user(
            email="patient.alice@nexus.test",
            password="StrongPassword@123",
            full_name="Alice Patient",
            role="patient",
            approved=True,
            status="ACTIVE"
        )

        # Create active doctor user with profile
        self.doctor_user = CustomUser.objects.create_user(
            email="dr.bob@nexus.test",
            password="StrongPassword@123",
            full_name="Dr. Bob Clinician",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_registration_number="REG-12345",
            state_medical_council="Delhi Medical Council",
            qualification="MBBS, MD",
            specialization="Neurology",
            years_of_experience=10,
            verification_status="VERIFIED"
        )

        # Create unverified doctor user (restricted)
        self.pending_doctor = CustomUser.objects.create_user(
            email="dr.pending@nexus.test",
            password="StrongPassword@123",
            full_name="Dr. Pending Clinician",
            role="doctor",
            approved=False,
            status="PENDING"
        )
        self.pending_profile = DoctorProfile.objects.create(
            user=self.pending_doctor,
            medical_registration_number="REG-99999",
            state_medical_council="Delhi Medical Council",
            qualification="MBBS",
            specialization="General Medicine",
            years_of_experience=2,
            verification_status="PENDING"
        )

    # -------------------------------------------------------------------------
    # 1. Login Session Creation & Updates
    # -------------------------------------------------------------------------
    def test_successful_login_creates_active_session_and_updates_last_login(self):
        """Successful login creates a UserSession and updates user.last_login."""
        self.assertIsNone(self.patient_user.last_login)
        initial_session_count = UserSession.objects.filter(user=self.patient_user).count()

        resp = self.client.post(
            '/api/auth/login',
            {
                'email': 'patient.alice@nexus.test',
                'password': 'StrongPassword@123',
                'role': 'patient'
            },
            format='json',
            HTTP_USER_AGENT='TestAgent/1.0',
            REMOTE_ADDR='192.168.1.100'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)
        self.assertIn('sessionId', resp.data)

        # Verify last_login updated
        self.patient_user.refresh_from_db()
        self.assertIsNotNone(self.patient_user.last_login)

        # Verify UserSession created
        session = UserSession.objects.filter(user=self.patient_user).latest('started_at')
        self.assertEqual(str(session.session_id), resp.data['sessionId'])
        self.assertEqual(session.status, 'ACTIVE')
        self.assertIsNone(session.ended_at)
        self.assertEqual(session.ip_address, '192.168.1.100')
        self.assertEqual(session.user_agent, 'TestAgent/1.0')
        self.assertEqual(UserSession.objects.filter(user=self.patient_user).count(), initial_session_count + 1)

    def test_session_id_is_unique_uuid(self):
        """Every login generates a cryptographically distinct UUID session_id."""
        resp1 = self.client.post('/api/auth/login', {'email': 'patient.alice@nexus.test', 'password': 'StrongPassword@123', 'role': 'patient'}, format='json')
        resp2 = self.client.post('/api/auth/login', {'email': 'patient.alice@nexus.test', 'password': 'StrongPassword@123', 'role': 'patient'}, format='json')

        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        self.assertNotEqual(resp1.data['sessionId'], resp2.data['sessionId'])

        # Verify UUID valid format
        uuid_obj1 = uuid.UUID(resp1.data['sessionId'])
        uuid_obj2 = uuid.UUID(resp2.data['sessionId'])
        self.assertIsInstance(uuid_obj1, uuid.UUID)
        self.assertIsInstance(uuid_obj2, uuid.UUID)

    def test_restricted_doctor_login_creates_session_and_updates_last_login(self):
        """Restricted doctor login still initializes a valid tracked UserSession."""
        resp = self.client.post(
            '/api/auth/login',
            {
                'email': 'dr.pending@nexus.test',
                'password': 'StrongPassword@123',
                'role': 'doctor'
            },
            format='json'
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get('isRestricted'))
        self.assertIn('sessionId', resp.data)

        self.pending_doctor.refresh_from_db()
        self.assertIsNotNone(self.pending_doctor.last_login)

        session = UserSession.objects.filter(user=self.pending_doctor).latest('started_at')
        self.assertEqual(str(session.session_id), resp.data['sessionId'])
        self.assertEqual(session.status, 'ACTIVE')

    # -------------------------------------------------------------------------
    # 2. Failed Login Auditing
    # -------------------------------------------------------------------------
    def test_failed_login_invalid_password_creates_audit_log_without_session(self):
        """Incorrect password logs Failed Login Attempt and creates no UserSession."""
        initial_sessions = UserSession.objects.count()

        resp = self.client.post(
            '/api/auth/login',
            {
                'email': 'patient.alice@nexus.test',
                'password': 'WrongPassword@999',
                'role': 'patient'
            },
            format='json'
        )

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(UserSession.objects.count(), initial_sessions)

        # Check AuditLog
        audit = AuditLog.objects.filter(actor=self.patient_user, action='Failed Login Attempt').latest('timestamp')
        self.assertEqual(audit.status, 'Failed')
        self.assertIn("Invalid credentials", audit.target)

    def test_failed_login_nonexistent_user_creates_audit_log(self):
        """Nonexistent email logs Failed Login Attempt without revealing account existence."""
        initial_sessions = UserSession.objects.count()

        resp = self.client.post(
            '/api/auth/login',
            {
                'email': 'nonexistent.ghost@nexus.test',
                'password': 'SomePassword@123',
                'role': 'patient'
            },
            format='json'
        )

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(UserSession.objects.count(), initial_sessions)

        audit = AuditLog.objects.filter(action='Failed Login Attempt', target__contains='nonexistent.ghost@nexus.test').latest('timestamp')
        self.assertEqual(audit.status, 'Failed')
        self.assertIsNone(audit.actor)

    def test_failed_login_role_mismatch_creates_audit_log(self):
        """Selecting wrong role tab logs Failed Login Attempt."""
        resp = self.client.post(
            '/api/auth/login',
            {
                'email': 'patient.alice@nexus.test',
                'password': 'StrongPassword@123',
                'role': 'doctor'  # Alice is a patient, not doctor
            },
            format='json'
        )

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        audit = AuditLog.objects.filter(action='Failed Login Attempt', actor=self.patient_user).latest('timestamp')
        self.assertEqual(audit.status, 'Failed')

    # -------------------------------------------------------------------------
    # 3. Logout & Session Closure
    # -------------------------------------------------------------------------
    def test_authenticated_logout_closes_session_and_records_ended_at(self):
        """Logout marks UserSession as CLOSED, records ended_at, and creates AuditLog."""
        # Log in first
        login_resp = self.client.post(
            '/api/auth/login',
            {'email': 'patient.alice@nexus.test', 'password': 'StrongPassword@123', 'role': 'patient'},
            format='json'
        )
        token = login_resp.data['token']
        session_id = login_resp.data['sessionId']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        logout_resp = self.client.post('/api/auth/logout', {'sessionId': session_id}, format='json')

        self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(logout_resp.data['status'], 'CLOSED')

        session = UserSession.objects.get(session_id=session_id)
        self.assertEqual(session.status, 'CLOSED')
        self.assertIsNotNone(session.ended_at)

        # AuditLog record
        audit = AuditLog.objects.filter(actor=self.patient_user, action='Logout Session Closed').latest('timestamp')
        self.assertEqual(audit.status, 'Success')

    def test_repeated_logout_is_idempotent_and_safe(self):
        """Calling logout repeatedly on an already closed session returns 200 without duplicate audit logs."""
        login_resp = self.client.post(
            '/api/auth/login',
            {'email': 'patient.alice@nexus.test', 'password': 'StrongPassword@123', 'role': 'patient'},
            format='json'
        )
        token = login_resp.data['token']
        session_id = login_resp.data['sessionId']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # First logout
        resp1 = self.client.post('/api/auth/logout', {'sessionId': session_id}, format='json')
        self.assertEqual(resp1.status_code, 200)
        close_logs_count_after_first = AuditLog.objects.filter(actor=self.patient_user, action='Logout Session Closed').count()

        # Second logout (repeated)
        resp2 = self.client.post('/api/auth/logout', {'sessionId': session_id}, format='json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.data['status'], 'CLOSED')

        close_logs_count_after_second = AuditLog.objects.filter(actor=self.patient_user, action='Logout Session Closed').count()
        self.assertEqual(close_logs_count_after_first, close_logs_count_after_second)

    def test_user_cannot_close_another_users_session(self):
        """User A providing User B's session_id cannot close User B's session."""
        # Alice logs in
        alice_login = self.client.post(
            '/api/auth/login',
            {'email': 'patient.alice@nexus.test', 'password': 'StrongPassword@123', 'role': 'patient'},
            format='json'
        )
        alice_token = alice_login.data['token']
        alice_session_id = alice_login.data['sessionId']

        # Bob logs in
        bob_login = self.client.post(
            '/api/auth/login',
            {'email': 'dr.bob@nexus.test', 'password': 'StrongPassword@123', 'role': 'doctor'},
            format='json'
        )
        bob_token = bob_login.data['token']
        bob_session_id = bob_login.data['sessionId']

        # Alice attempts to close Bob's session
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {alice_token}')
        resp = self.client.post('/api/auth/logout', {'sessionId': bob_session_id}, format='json')

        self.assertEqual(resp.status_code, 200)

        # Bob's session must still be ACTIVE
        bob_session = UserSession.objects.get(session_id=bob_session_id)
        self.assertEqual(bob_session.status, 'ACTIVE')
        self.assertIsNone(bob_session.ended_at)

    def test_logout_with_invalid_or_expired_jwt_is_rejected(self):
        """Logout without a valid authorization header returns 401."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.expired.token')
        resp = self.client.post('/api/auth/logout', {'sessionId': str(uuid.uuid4())}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_active_session_record_is_graceful(self):
        """Authenticated user logging out with no active sessions succeeds safely."""
        token = str(AccessToken.for_user(self.patient_user))
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        resp = self.client.post('/api/auth/logout', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'CLOSED')
