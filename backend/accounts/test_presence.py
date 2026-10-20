import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import CustomUser, AuditLog, UserSession
from accounts.presence_service import evaluate_session_presence, HEARTBEAT_TIMEOUT_SECONDS, ACTIVITY_IDLE_SECONDS
from doctors.models import DoctorProfile


def get_jwt_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class PresenceHeartbeatAndActivityTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # User 1: Alice (Patient)
        self.user_alice = CustomUser.objects.create_user(
            email="presence.alice@nexus.test",
            password="StrongPassword@123",
            full_name="Alice Presence",
            role="patient",
            approved=True,
            status="ACTIVE"
        )
        self.token_alice = get_jwt_token(self.user_alice)

        # User 2: Bob (Doctor)
        self.user_bob = CustomUser.objects.create_user(
            email="presence.bob@nexus.test",
            password="StrongPassword@123",
            full_name="Dr. Bob Presence",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )
        DoctorProfile.objects.create(
            user=self.user_bob,
            medical_registration_number="REG-PRES-101",
            state_medical_council="Delhi Medical Council",
            qualification="MBBS, MD",
            specialization="Neurology",
            years_of_experience=8,
            verification_status="VERIFIED"
        )
        self.token_bob = get_jwt_token(self.user_bob)

        # Create baseline active session for Alice
        self.now = timezone.now()
        self.session_alice = UserSession.objects.create(
            user=self.user_alice,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(minutes=10),
            last_heartbeat_at=self.now - timedelta(seconds=30),
            last_activity_at=self.now - timedelta(seconds=30),
            status="ACTIVE"
        )

        # Create baseline active session for Bob
        self.session_bob = UserSession.objects.create(
            user=self.user_bob,
            session_id=uuid.uuid4(),
            started_at=self.now - timedelta(minutes=5),
            last_heartbeat_at=self.now - timedelta(seconds=10),
            last_activity_at=self.now - timedelta(seconds=10),
            status="ACTIVE"
        )

    # -------------------------------------------------------------------------
    # 1. Authenticated heartbeat succeeds
    # -------------------------------------------------------------------------
    def test_authenticated_heartbeat_succeeds(self):
        """Authenticated heartbeat with valid sessionId succeeds with HTTP 200."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")
        resp = self.client.post(
            "/api/presence/heartbeat",
            {"sessionId": str(self.session_alice.session_id)},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data.get("success"))
        self.assertEqual(resp.data.get("sessionId"), str(self.session_alice.session_id))
        self.assertEqual(resp.data.get("presence"), "ACTIVE")

    # -------------------------------------------------------------------------
    # 2 & 3. Heartbeat updates existing UserSession in-place; no new session
    # -------------------------------------------------------------------------
    def test_heartbeat_updates_existing_session_without_creating_new_row(self):
        """Heartbeat updates the existing row in-place and never creates duplicates."""
        initial_count = UserSession.objects.count()
        old_heartbeat_time = self.session_alice.last_heartbeat_at

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")
        resp = self.client.post(
            "/api/presence/heartbeat",
            {"sessionId": str(self.session_alice.session_id)},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(UserSession.objects.count(), initial_count)

        self.session_alice.refresh_from_db()
        self.assertGreater(self.session_alice.last_heartbeat_at, old_heartbeat_time)

    # -------------------------------------------------------------------------
    # 4 & 5. last_heartbeat_at and last_activity_at are updated
    # -------------------------------------------------------------------------
    def test_last_heartbeat_at_and_last_activity_at_updated(self):
        """Supplied ISO activity timestamp updates last_activity_at."""
        activity_time = timezone.now() - timedelta(seconds=15)
        iso_str = activity_time.isoformat()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")
        resp = self.client.post(
            "/api/presence/heartbeat",
            {
                "sessionId": str(self.session_alice.session_id),
                "lastActivityAt": iso_str
            },
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.session_alice.refresh_from_db()
        self.assertIsNotNone(self.session_alice.last_heartbeat_at)
        self.assertIsNotNone(self.session_alice.last_activity_at)
        # Verify timestamp recorded
        time_diff = abs((self.session_alice.last_activity_at - activity_time).total_seconds())
        self.assertLess(time_diff, 1.0)

    # -------------------------------------------------------------------------
    # 6. Unauthenticated heartbeat rejected
    # -------------------------------------------------------------------------
    def test_unauthenticated_heartbeat_rejected(self):
        """Heartbeat request without JWT token is rejected with HTTP 401."""
        self.client.credentials()  # Clear credentials
        resp = self.client.post(
            "/api/presence/heartbeat",
            {"sessionId": str(self.session_alice.session_id)},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # -------------------------------------------------------------------------
    # 7. Invalid sessionId rejected (missing or invalid format)
    # -------------------------------------------------------------------------
    def test_missing_and_invalid_session_id_rejected(self):
        """Missing or malformed sessionId is rejected with HTTP 400."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")

        # Missing sessionId
        resp_missing = self.client.post("/api/presence/heartbeat", {}, format="json")
        self.assertEqual(resp_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", resp_missing.data)

        # Malformed UUID
        resp_bad = self.client.post("/api/presence/heartbeat", {"sessionId": "not-a-uuid"}, format="json")
        self.assertEqual(resp_bad.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 8. Cross-user isolation: user cannot heartbeat another user's session
    # -------------------------------------------------------------------------
    def test_cross_user_heartbeat_forbidden(self):
        """Alice cannot heartbeat Bob's session; returns HTTP 404 without mutation."""
        bob_heartbeat_before = self.session_bob.last_heartbeat_at

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")
        resp = self.client.post(
            "/api/presence/heartbeat",
            {"sessionId": str(self.session_bob.session_id)},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # Verify Bob's session was unaffected
        self.session_bob.refresh_from_db()
        self.assertEqual(self.session_bob.last_heartbeat_at, bob_heartbeat_before)

    # -------------------------------------------------------------------------
    # 9. Closed session cannot be revived
    # -------------------------------------------------------------------------
    def test_closed_session_cannot_be_revived(self):
        """Heartbeat against a CLOSED session is rejected and does not change status."""
        self.session_alice.status = "CLOSED"
        self.session_alice.ended_at = timezone.now() - timedelta(minutes=5)
        self.session_alice.save()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")
        resp = self.client.post(
            "/api/presence/heartbeat",
            {"sessionId": str(self.session_alice.session_id)},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data.get("status"), "CLOSED")
        self.assertEqual(resp.data.get("presence"), "OFFLINE")

        self.session_alice.refresh_from_db()
        self.assertEqual(self.session_alice.status, "CLOSED")

    # -------------------------------------------------------------------------
    # 10. Presence evaluation: Stale session is OFFLINE
    # -------------------------------------------------------------------------
    def test_stale_heartbeat_session_is_offline(self):
        """Session with heartbeat older than 120 seconds evaluates as OFFLINE."""
        curr = timezone.now()
        self.session_alice.last_heartbeat_at = curr - timedelta(seconds=130)  # > 2 mins
        self.session_alice.last_activity_at = curr - timedelta(seconds=10)
        self.session_alice.save()

        presence = evaluate_session_presence(self.session_alice, current_time=curr)
        self.assertEqual(presence, "OFFLINE")

    # -------------------------------------------------------------------------
    # 11. Presence evaluation: Recent heartbeat + Recent activity = ACTIVE
    # -------------------------------------------------------------------------
    def test_recent_heartbeat_and_recent_activity_is_active(self):
        """Heartbeat <= 2m and Activity <= 5m evaluates as ACTIVE."""
        curr = timezone.now()
        self.session_alice.last_heartbeat_at = curr - timedelta(seconds=30)   # <= 120s
        self.session_alice.last_activity_at = curr - timedelta(seconds=60)    # <= 300s
        self.session_alice.save()

        presence = evaluate_session_presence(self.session_alice, current_time=curr)
        self.assertEqual(presence, "ACTIVE")

    # -------------------------------------------------------------------------
    # 12. Presence evaluation: Recent heartbeat + Old activity = IDLE
    # -------------------------------------------------------------------------
    def test_recent_heartbeat_and_old_activity_is_idle(self):
        """Heartbeat <= 2m and Activity > 5m evaluates as IDLE."""
        curr = timezone.now()
        self.session_alice.last_heartbeat_at = curr - timedelta(seconds=30)   # <= 120s
        self.session_alice.last_activity_at = curr - timedelta(seconds=350)   # > 300s (5m 50s)
        self.session_alice.save()

        presence = evaluate_session_presence(self.session_alice, current_time=curr)
        self.assertEqual(presence, "IDLE")

    # -------------------------------------------------------------------------
    # 13. Presence evaluation: Stale heartbeat overrides activity = OFFLINE
    # -------------------------------------------------------------------------
    def test_stale_heartbeat_strictly_overrides_recent_activity(self):
        """OFFLINE strictly takes priority even if activity was recorded 5 seconds ago."""
        curr = timezone.now()
        self.session_alice.last_heartbeat_at = curr - timedelta(seconds=140)  # > 120s (OFFLINE)
        self.session_alice.last_activity_at = curr - timedelta(seconds=5)     # Very recent
        self.session_alice.save()

        presence = evaluate_session_presence(self.session_alice, current_time=curr)
        self.assertEqual(presence, "OFFLINE")

    # -------------------------------------------------------------------------
    # 14. Future / invalid activity timestamp handled safely
    # -------------------------------------------------------------------------
    def test_future_activity_timestamp_clamped_safely(self):
        """An arbitrary future timestamp (e.g. +10 days) is safely clamped to now."""
        future_time = timezone.now() + timedelta(days=10)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")

        resp = self.client.post(
            "/api/presence/heartbeat",
            {
                "sessionId": str(self.session_alice.session_id),
                "lastActivityAt": future_time.isoformat()
            },
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.session_alice.refresh_from_db()
        # Activity timestamp should be clamped close to now, not in the distant future
        delta = self.session_alice.last_activity_at - timezone.now()
        self.assertLess(delta.total_seconds(), 5.0)

    # -------------------------------------------------------------------------
    # 15. Multiple sessions remain isolated
    # -------------------------------------------------------------------------
    def test_multiple_sessions_remain_isolated(self):
        """Session A (ACTIVE) and Session B (IDLE) have independent presence evaluations."""
        curr = timezone.now()

        # Alice's Session A: ACTIVE
        self.session_alice.last_heartbeat_at = curr - timedelta(seconds=15)
        self.session_alice.last_activity_at = curr - timedelta(seconds=20)
        self.session_alice.save()

        # Alice's Session B (second tab/device): IDLE
        session_alice_b = UserSession.objects.create(
            user=self.user_alice,
            session_id=uuid.uuid4(),
            started_at=curr - timedelta(minutes=20),
            last_heartbeat_at=curr - timedelta(seconds=25),
            last_activity_at=curr - timedelta(minutes=8), # > 5 min -> IDLE
            status="ACTIVE"
        )

        status_a = evaluate_session_presence(self.session_alice, current_time=curr)
        status_b = evaluate_session_presence(session_alice_b, current_time=curr)

        self.assertEqual(status_a, "ACTIVE")
        self.assertEqual(status_b, "IDLE")

    # -------------------------------------------------------------------------
    # Operational cleanliness: No AuditLog generated on heartbeat
    # -------------------------------------------------------------------------
    def test_heartbeat_does_not_create_audit_logs(self):
        """Heartbeats are operational presence pings and must not spam the security AuditLog."""
        initial_audit_count = AuditLog.objects.count()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_alice}")
        resp = self.client.post(
            "/api/presence/heartbeat",
            {"sessionId": str(self.session_alice.session_id)},
            format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(AuditLog.objects.count(), initial_audit_count)
