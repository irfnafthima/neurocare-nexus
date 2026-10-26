from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from decimal import Decimal, InvalidOperation
from monitoring.models import SensorReading
from monitoring.telemetry_packet import TelemetryPacket
from monitoring.telemetry_service import process_telemetry, dispatch_critical_alert_notifications
from devices.models import WearableDevice, DeviceAssignment
from medical_records.views import is_user_authorized_for_patient
from patients.views import find_patient_by_identifier


def authenticate_physical_device(device_id: str, device_key: str):
    """
    Validates machine-to-machine authentication credentials for incoming physical IoT telemetry.
    Returns (device, error_status, error_message).
    """
    if not device_id or not device_key:
        return None, status.HTTP_401_UNAUTHORIZED, "Missing X-Device-ID or X-Device-Key header."

    try:
        device = WearableDevice.objects.select_related('assignment__patient').get(serial=str(device_id).strip())
    except WearableDevice.DoesNotExist:
        return None, status.HTTP_401_UNAUTHORIZED, "Device not registered."

    if device.status.lower() != 'active':
        return None, status.HTTP_403_FORBIDDEN, "Device is inactive or decommissioned."

    if not device.check_device_key(str(device_key).strip()):
        return None, status.HTTP_401_UNAUTHORIZED, "Invalid device credentials."

    if not hasattr(device, 'assignment') or not device.assignment or not device.assignment.patient:
        return None, status.HTTP_403_FORBIDDEN, "Device is not assigned to an active patient."

    return device, None, None


class SimulationTriggerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        patient_id = data.get('patientId')
        vitals = data.get('vitals', {})
        risk_score = data.get('riskScore', 0)
        status_state = data.get('statusState', 'Normal')
        audit_action = data.get('auditAction', 'Simulated Telemetry Update')
        user_name = data.get('userName', 'Telemetry Simulator')

        max30102 = vitals.get('max30102', {})
        ds18b20 = vitals.get('ds18b20', {})
        mpu6050 = vitals.get('mpu6050', {})
        esp32 = vitals.get('esp32', {})

        emergency_pressed = bool(data.get('emergency_pressed') or esp32.get('emergency_pressed') or vitals.get('emergency_pressed'))

        packet = TelemetryPacket(
            patient_id=patient_id,
            device_id=f"SIM-DEVICE-{patient_id}",
            source="SIMULATED",
            heart_rate=max30102.get('heartRate'),
            spo2=max30102.get('spo2'),
            temperature=Decimal(str(ds18b20.get('temperature', 36.80))) if ds18b20.get('temperature') is not None else Decimal("36.80"),
            accel_x=Decimal(str(mpu6050.get('accelX', 0.05))) if mpu6050.get('accelX') is not None else Decimal("0.05"),
            accel_y=Decimal(str(mpu6050.get('accelY', 0.98))) if mpu6050.get('accelY') is not None else Decimal("0.98"),
            accel_z=Decimal(str(mpu6050.get('accelZ', 0.04))) if mpu6050.get('accelZ') is not None else Decimal("0.04"),
            gyro_x=Decimal(str(mpu6050.get('gyroX', 0.50))) if mpu6050.get('gyroX') is not None else Decimal("0.50"),
            gyro_y=Decimal(str(mpu6050.get('gyroY', -1.20))) if mpu6050.get('gyroY') is not None else Decimal("-1.20"),
            gyro_z=Decimal(str(mpu6050.get('gyroZ', 0.30))) if mpu6050.get('gyroZ') is not None else Decimal("0.30"),
            fall_detected=bool(mpu6050.get('fallDetected', False)),
            esp32_connected=bool(esp32.get('connected', True)),
            esp32_battery=esp32.get('battery', 100),
            esp32_rssi=esp32.get('rssi', -55),
            emergency_pressed=emergency_pressed,
            risk_score=risk_score,
            status_state=status_state,
            audit_action=audit_action,
            user_name=user_name
        )

        try:
            reading, alerts = process_telemetry(packet)
            return Response("Simulated telemetry update recorded.", status=status.HTTP_200_OK)
        except ValueError as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)


class DeviceTelemetryIngestView(APIView):
    """
    Dedicated physical machine-to-machine telemetry ingestion endpoint.
    Authenticates physical IoT nodes via X-Device-ID and X-Device-Key HTTP headers.
    Directly feeds the existing, unified process_telemetry() pipeline.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Machine-to-Machine Header Authentication
        device_id = request.headers.get('X-Device-ID') or request.META.get('HTTP_X_DEVICE_ID')
        device_key = request.headers.get('X-Device-Key') or request.META.get('HTTP_X_DEVICE_KEY')

        device, err_status, err_msg = authenticate_physical_device(device_id, device_key)
        if err_status:
            return Response({'error': err_msg}, status=err_status)

        # 2. Payload Validation & Sanitization
        data = request.data
        if not isinstance(data, dict):
            return Response({'error': 'Malformed telemetry packet; expected JSON object.'}, status=status.HTTP_400_BAD_REQUEST)

        assigned_patient = device.assignment.patient

        # Anti-spoofing check: If payload includes patient_id, it must match assigned patient
        payload_patient_id = data.get('patient_id')
        if payload_patient_id and str(payload_patient_id) != str(assigned_patient.id):
            return Response(
                {'error': f"Device {device.serial} is not authorized for patient {payload_patient_id}."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Numeric Parsing & Validation
        try:
            # HR & SpO2
            hr_val = data.get('heart_rate')
            hr = int(hr_val) if hr_val is not None else None
            spo2_val = data.get('spo2')
            spo2 = int(spo2_val) if spo2_val is not None else None

            # Temperature
            temp_val = data.get('temperature')
            temp = Decimal(str(temp_val)) if temp_val is not None else None

            # 6-Axis Motion
            ax_val = data.get('accel_x')
            ax = Decimal(str(ax_val)) if ax_val is not None else None
            ay_val = data.get('accel_y')
            ay = Decimal(str(ay_val)) if ay_val is not None else None
            az_val = data.get('accel_z')
            az = Decimal(str(az_val)) if az_val is not None else None

            gx_val = data.get('gyro_x')
            gx = Decimal(str(gx_val)) if gx_val is not None else None
            gy_val = data.get('gyro_y')
            gy = Decimal(str(gy_val)) if gy_val is not None else None
            gz_val = data.get('gyro_z')
            gz = Decimal(str(gz_val)) if gz_val is not None else None

            # Battery & RSSI
            battery_val = data.get('battery_pct') if data.get('battery_pct') is not None else data.get('esp32_battery')
            battery = int(battery_val) if battery_val is not None else None

            rssi_val = data.get('rssi') if data.get('rssi') is not None else data.get('esp32_rssi')
            rssi = int(rssi_val) if rssi_val is not None else -55
        except (ValueError, TypeError, InvalidOperation) as val_err:
            return Response(
                {'error': f"Invalid numeric value in telemetry payload: {val_err}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse timestamp if sent, otherwise fallback to timezone.now()
        ts_raw = data.get('timestamp')
        ts = parse_datetime(str(ts_raw)) if ts_raw else timezone.now()
        if ts is None:
            ts = timezone.now()

        # 4. Construct Canonical TelemetryPacket (source="REAL_DEVICE")
        packet = TelemetryPacket(
            patient_id=str(assigned_patient.id),
            device_id=device.serial,
            source="REAL_DEVICE",
            timestamp=ts,
            heart_rate=hr,
            spo2=spo2,
            temperature=temp,
            accel_x=ax,
            accel_y=ay,
            accel_z=az,
            gyro_x=gx,
            gyro_y=gy,
            gyro_z=gz,
            fall_detected=bool(data.get('fall_detected', False)),
            signal_quality=str(data.get('signal_quality', 'GOOD')),
            esp32_connected=bool(data.get('esp32_connected', True)),
            esp32_battery=battery,
            esp32_rssi=rssi,
            emergency_pressed=bool(data.get('emergency_pressed', False)),
            risk_score=assigned_patient.risk,
            status_state=assigned_patient.status,
            audit_action=f"Physical ESP32 Ingestion ({device.serial})",
            user_name=f"Device {device.serial}"
        )

        # 5. Ingest through existing process_telemetry() pipeline
        try:
            reading, alerts = process_telemetry(packet)

            # Update device last_seen_at timestamp
            device.last_seen_at = timezone.now()
            device.save(update_fields=['last_seen_at'])

            return Response({
                'status': 'success',
                'device_id': device.serial,
                'patient_id': assigned_patient.id,
                'reading_id': reading.id,
                'alerts_generated': len(alerts),
                'timestamp': reading.timestamp.isoformat()
            }, status=status.HTTP_200_OK)
        except ValueError as err:
            return Response({'error': str(err)}, status=status.HTTP_404_NOT_FOUND)


class PatientLatestTelemetryView(APIView):
    """
    Dedicated REST endpoint for querying the latest verified REAL_DEVICE telemetry.
    Acts as a resilient database polling fallback alongside the WebSocket stream.
    Enforces clinical authorization checks.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        patient = find_patient_by_identifier(patient_id)
        if not patient:
            return Response(
                {'error': f"Patient '{patient_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 1. Authorization: patient can only see their own telemetry; doctor/caregiver must be authorized
        if not is_user_authorized_for_patient(request.user, patient.id):
            return Response(
                {'error': "Access Denied: You are not authorized to view this patient's telemetry."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Check physical wearable device assignment
        dev_assign = DeviceAssignment.objects.filter(patient=patient).select_related('device').first()
        if not dev_assign or not dev_assign.device:
            return Response({
                'status': 'NO_DEVICE',
                'patient_id': str(patient.id),
                'source': 'MANUAL'
            }, status=status.HTTP_200_OK)

        device = dev_assign.device

        # 3. Query the latest real sensor reading
        latest = SensorReading.objects.filter(patient=patient).order_by('-timestamp').first()
        if not latest:
            return Response({
                'status': 'NO_DATA',
                'patient_id': str(patient.id),
                'device_id': device.serial,
                'source': 'REAL_DEVICE'
            }, status=status.HTTP_200_OK)

        # 4. Return canonical real telemetry payload
        iso_time = latest.timestamp.isoformat()
        return Response({
            'status': 'success',
            'patient_id': str(patient.id),
            'device_id': device.serial,
            'source': 'REAL_DEVICE',
            'received_at': iso_time,
            'timestamp': iso_time,
            'heart_rate': latest.heart_rate,
            'spo2': latest.spo2,
            'temperature': float(latest.temperature) if latest.temperature is not None else None,
            'accel_x': float(latest.accel_x) if latest.accel_x is not None else None,
            'accel_y': float(latest.accel_y) if latest.accel_y is not None else None,
            'accel_z': float(latest.accel_z) if latest.accel_z is not None else None,
            'gyro_x': float(latest.gyro_x) if latest.gyro_x is not None else None,
            'gyro_y': float(latest.gyro_y) if latest.gyro_y is not None else None,
            'gyro_z': float(latest.gyro_z) if latest.gyro_z is not None else None,
            'fall_detected': bool(latest.fall_detected),
            'esp32_connected': bool(latest.esp32_connected),
            'esp32_battery': latest.esp32_battery if latest.esp32_battery is not None else 100,
            'esp32_rssi': latest.esp32_rssi if latest.esp32_rssi is not None else -55,
            'signal_quality': 'GOOD'
        }, status=status.HTTP_200_OK)

