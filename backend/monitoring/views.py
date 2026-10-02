from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from monitoring.models import SensorReading
from monitoring.telemetry_packet import TelemetryPacket
from monitoring.telemetry_service import process_telemetry, dispatch_critical_alert_notifications


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


