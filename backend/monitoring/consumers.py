import json
import logging
from decimal import Decimal
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import CustomUser
from patients.models import Patient
from patients.views import find_patient_by_identifier
from monitoring.models import SensorReading
from medical_records.views import is_user_authorized_for_patient

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token_str: str):
    try:
        access_token = AccessToken(token_str)
        user_id = access_token['user_id']
        return CustomUser.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()


@database_sync_to_async
def check_patient_telemetry_authorization(user, patient_id: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    # Check if patient exists first without leaking details
    patient = find_patient_by_identifier(patient_id)
    if not patient:
        return False
    return is_user_authorized_for_patient(user, patient.id)


@database_sync_to_async
def get_latest_telemetry_snapshot(patient_id: str) -> dict:
    from devices.models import DeviceAssignment
    dev_assign = DeviceAssignment.objects.filter(patient_id=patient_id).select_related('device').first()
    has_real_dev = dev_assign is not None and dev_assign.device is not None
    real_serial = dev_assign.device.serial if has_real_dev else None

    latest = SensorReading.objects.filter(patient_id=patient_id).order_by('-timestamp').first()
    if not latest:
        return {
            'type': 'telemetry_status',
            'status': 'NO_DATA',
            'patient_id': str(patient_id),
            'has_device': has_real_dev,
            'device_id': real_serial
        }

    return {
        'type': 'telemetry',
        'patient_id': str(latest.patient_id),
        'device_id': real_serial or f"SIM-DEVICE-{latest.patient_id}",
        'source': 'REAL_DEVICE' if has_real_dev else 'DATABASE_SNAPSHOT',
        'timestamp': latest.timestamp.isoformat(),
        'heart_rate': latest.heart_rate,
        'spo2': latest.spo2,
        'temperature': float(latest.temperature) if latest.temperature is not None else None,
        'accel_x': float(latest.accel_x) if latest.accel_x is not None else None,
        'accel_y': float(latest.accel_y) if latest.accel_y is not None else None,
        'accel_z': float(latest.accel_z) if latest.accel_z is not None else None,
        'gyro_x': float(latest.gyro_x) if latest.gyro_x is not None else None,
        'gyro_y': float(latest.gyro_y) if latest.gyro_y is not None else None,
        'gyro_z': float(latest.gyro_z) if latest.gyro_z is not None else None,
        'fall_detected': latest.fall_detected,
        'signal_quality': 'GOOD',
        'esp32_connected': latest.esp32_connected,
        'esp32_battery': latest.esp32_battery,
        'esp32_rssi': latest.esp32_rssi,
        'has_device': has_real_dev,
        'is_snapshot': True
    }


class TelemetryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.patient_id = self.scope['url_route']['kwargs']['patient_id']
        self.room_group_name = f"telemetry_patient_{self.patient_id}"

        # 1. Extract and verify JWT from query param ?token=...
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        if token:
            self.scope['user'] = await get_user_from_token(token)

        user = self.scope.get('user', AnonymousUser())
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # Unauthorized
            return

        # 2. Strict Server-Side Clinical Authorization Check
        is_authorized = await check_patient_telemetry_authorization(user, self.patient_id)
        logger.info(f"[TELEMETRY WS] user={user.id} role={getattr(user, 'role', 'unknown')} patient={self.patient_id} authorized={is_authorized}")
        if not is_authorized:
            await self.close(code=4003)  # Forbidden
            return

        # 3. Join patient telemetry broadcast group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # 4. Send initial snapshot if available
        snapshot = await get_latest_telemetry_snapshot(self.patient_id)
        await self.send(text_data=json.dumps(snapshot))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        # Client messages can request a refresh or snapshot
        try:
            data = json.loads(text_data)
            req_type = data.get('type')
            if req_type == 'get_snapshot':
                user = self.scope.get('user', AnonymousUser())
                is_authorized = await check_patient_telemetry_authorization(user, self.patient_id)
                if is_authorized:
                    snapshot = await get_latest_telemetry_snapshot(self.patient_id)
                    await self.send(text_data=json.dumps(snapshot))
                else:
                    await self.close(code=4003)
        except Exception:
            pass

    async def telemetry_message(self, event):
        """
        Handler for group_send with type 'telemetry_message'.
        Pushes live telemetry packet directly to subscribed authorized WebSocket client.
        """
        payload = event.get('data', {})
        await self.send(text_data=json.dumps(payload))
