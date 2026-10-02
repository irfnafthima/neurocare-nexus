import json
import asyncio
from decimal import Decimal
from django.test import TransactionTestCase
from django.utils import timezone
from urllib.parse import unquote, urlparse
from asgiref.testing import ApplicationCommunicator
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import CustomUser
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorPatientLink
from caregivers.models import CaregiverPatientLink
from monitoring.models import SensorReading
from monitoring.telemetry_packet import TelemetryPacket
from monitoring.telemetry_service import process_telemetry
from core.asgi import application



class WebsocketCommunicator(ApplicationCommunicator):
    """
    Lightweight WebSocket communicator subclassing asgiref.testing.ApplicationCommunicator.
    Does not require daphne installed for testing.
    """
    def __init__(self, application, path, headers=None, subprotocols=None, spec_version=None):
        if not isinstance(path, str):
            raise TypeError(f"Expected str, got {type(path)}")
        parsed = urlparse(path)
        self.scope = {
            "type": "websocket",
            "path": unquote(parsed.path),
            "query_string": parsed.query.encode("utf-8"),
            "headers": headers or [],
            "subprotocols": subprotocols or [],
        }
        if spec_version:
            self.scope["spec_version"] = spec_version
        super().__init__(application, self.scope)
        self.response_headers = None

    async def connect(self, timeout=2):
        await self.send_input({"type": "websocket.connect"})
        response = await self.receive_output(timeout)
        if response["type"] == "websocket.close":
            return (False, response.get("code", 1000))
        else:
            assert response["type"] == "websocket.accept"
            self.response_headers = response.get("headers", [])
            return (True, response.get("subprotocol", None))

    async def send_to(self, text_data=None, bytes_data=None):
        assert bool(text_data) != bool(bytes_data), "You must supply exactly one of text_data or bytes_data"
        if text_data:
            await self.send_input({"type": "websocket.receive", "text": text_data})
        else:
            await self.send_input({"type": "websocket.receive", "bytes": bytes_data})

    async def send_json_to(self, data):
        await self.send_to(text_data=json.dumps(data))

    async def receive_from(self, timeout=2):
        response = await self.receive_output(timeout)
        assert response["type"] == "websocket.send", f"Expected type 'websocket.send', but was '{response['type']}'"
        if "text" in response:
            return response["text"]
        else:
            return response["bytes"]

    async def receive_json_from(self, timeout=2):
        payload = await self.receive_from(timeout)
        return json.loads(payload)

    async def disconnect(self, code=1000, timeout=2):
        await self.send_input({"type": "websocket.disconnect", "code": code})
        await self.wait(timeout)




class TelemetryWebSocketSecurityAndRoutingTest(TransactionTestCase):

    def setUp(self):
        # 1. Create Patient records
        self.patient_a = Patient.objects.create(id="P-WS-101", name="Alice Patient", age=45, gender="Female")
        self.patient_b = Patient.objects.create(id="P-WS-102", name="Bob Patient", age=50, gender="Male")

        # 2. Patient User Account (Alice)
        self.patient_user = CustomUser.objects.create_user(
            email="alice.patient@ws.test",
            password="TestPassword@123",
            full_name="Alice Patient",
            role="patient",
            patient_id="P-WS-101",
            approved=True,
            status="ACTIVE"
        )
        self.patient_token = str(AccessToken.for_user(self.patient_user))

        # 3. Doctor User Account (Linked only to Patient A)
        self.doctor_user = CustomUser.objects.create_user(
            email="dr.smith@ws.test",
            password="DocPassword@123",
            full_name="Dr. Smith",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )
        DoctorPatientLink.objects.create(doctor=self.doctor_user, patient=self.patient_a)
        self.doctor_token = str(AccessToken.for_user(self.doctor_user))

        # 4. Caregiver User Account (Assigned only to Patient A)
        self.caregiver_user = CustomUser.objects.create_user(
            email="caregiver.anna@ws.test",
            password="CgPassword@123",
            full_name="Caregiver Anna",
            role="caregiver",
            approved=True,
            status="ACTIVE"
        )
        CaregiverPatientLink.objects.create(caregiver=self.caregiver_user, patient=self.patient_a, is_approved=True)
        self.caregiver_token = str(AccessToken.for_user(self.caregiver_user))

        # 5. Family User Account (Linked only to Patient A)
        self.family_user = CustomUser.objects.create_user(
            email="family.john@ws.test",
            password="FamPassword@123",
            full_name="John Family",
            role="family",
            patient_id="P-WS-101",
            approved=True,
            status="ACTIVE"
        )
        FamilyPatientLink.objects.create(family=self.family_user, patient=self.patient_a, is_approved=True)
        self.family_token = str(AccessToken.for_user(self.family_user))

    async def test_unauthenticated_connection_is_rejected(self):
        """Unauthenticated WebSocket connection is closed with 4001."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_patient_can_connect_to_own_telemetry(self):
        """Authenticated patient successfully connects to their own telemetry room and receives snapshot/NO_DATA."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/?token={self.patient_token}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Receives initial snapshot or NO_DATA status
        response = await communicator.receive_json_from()
        self.assertIn(response['type'], ['telemetry', 'telemetry_status'])
        await communicator.disconnect()

    async def test_patient_cannot_connect_to_other_patient_telemetry(self):
        """Authenticated patient attempting to connect to another patient's stream is rejected with 4003."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_b.id}/?token={self.patient_token}")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

    async def test_doctor_can_connect_to_linked_patient(self):
        """Authorized doctor successfully connects to linked patient."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/?token={self.doctor_token}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_doctor_cannot_connect_to_unlinked_patient(self):
        """Doctor attempting to connect to an unlinked patient is rejected with 4003."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_b.id}/?token={self.doctor_token}")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

    async def test_caregiver_can_connect_to_delegated_patient(self):
        """Authorized caregiver connects to delegated patient."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/?token={self.caregiver_token}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_caregiver_cannot_connect_to_unassigned_patient(self):
        """Caregiver is rejected when connecting to unassigned patient."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_b.id}/?token={self.caregiver_token}")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)

    async def test_family_can_connect_to_linked_patient(self):
        """Authorized family member connects to linked patient."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/?token={self.family_token}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_family_cannot_connect_to_unlinked_patient(self):
        """Family member is rejected when connecting to unlinked patient."""
        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_b.id}/?token={self.family_token}")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)


class TelemetryWebSocketBroadcastAndIsolationTest(TransactionTestCase):
    def setUp(self):
        self.patient_a = Patient.objects.create(id="P-BROAD-1", name="Broad A", age=30, gender="Female")
        self.patient_b = Patient.objects.create(id="P-BROAD-2", name="Broad B", age=40, gender="Male")

        self.user_a = CustomUser.objects.create_user(
            email="user.a@ws.test", password="Pass@123", full_name="User A", role="patient",
            patient_id="P-BROAD-1", approved=True, status="ACTIVE"
        )
        self.token_a = str(AccessToken.for_user(self.user_a))

        self.user_b = CustomUser.objects.create_user(
            email="user.b@ws.test", password="Pass@123", full_name="User B", role="patient",
            patient_id="P-BROAD-2", approved=True, status="ACTIVE"
        )
        self.token_b = str(AccessToken.for_user(self.user_b))

    async def test_initial_snapshot_returns_latest_real_reading(self):
        """Initial snapshot accurately returns the last persisted SensorReading."""
        # Create a reading for Patient A
        await database_sync_to_async(SensorReading.objects.create)(
            patient=self.patient_a,
            heart_rate=78,
            spo2=99,
            temperature=Decimal("36.70")
        )

        communicator = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/?token={self.token_a}")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        snapshot = await communicator.receive_json_from()
        self.assertEqual(snapshot['type'], 'telemetry')
        self.assertEqual(snapshot['patient_id'], 'P-BROAD-1')
        self.assertEqual(snapshot['heart_rate'], 78)
        self.assertEqual(snapshot['spo2'], 99)
        self.assertEqual(snapshot['is_snapshot'], True)
        await communicator.disconnect()

    async def test_process_telemetry_broadcasts_to_correct_patient_without_leakage(self):
        """process_telemetry() pushes event only to authorized subscriber, avoiding cross-patient leakage."""
        comm_a = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_a.id}/?token={self.token_a}")
        comm_b = WebsocketCommunicator(application, f"/ws/telemetry/patient/{self.patient_b.id}/?token={self.token_b}")

        conn_a, _ = await comm_a.connect()
        conn_b, _ = await comm_b.connect()
        self.assertTrue(conn_a)
        self.assertTrue(conn_b)

        # Clear initial snapshots
        await comm_a.receive_json_from()
        await comm_b.receive_json_from()

        # Ingest telemetry for Patient A
        packet_a = TelemetryPacket(
            patient_id=self.patient_a.id,
            heart_rate=82,
            spo2=98,
            temperature=Decimal("36.85")
        )
        await database_sync_to_async(process_telemetry)(packet_a)

        # Subscriber A must receive the live packet
        msg_a = await comm_a.receive_json_from(timeout=2.0)
        self.assertEqual(msg_a['type'], 'telemetry')
        self.assertEqual(msg_a['patient_id'], 'P-BROAD-1')
        self.assertEqual(msg_a['heart_rate'], 82)
        self.assertEqual(msg_a['spo2'], 98)

        # Subscriber B must NOT receive any message for Patient A
        has_msg_b = await comm_b.receive_nothing(timeout=0.5)
        self.assertTrue(has_msg_b, "Patient B unexpectedly received a message meant for Patient A (data leakage)")

        await comm_a.disconnect()
        await comm_b.disconnect()


