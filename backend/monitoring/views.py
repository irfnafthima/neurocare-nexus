from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from monitoring.models import SensorReading
from patients.models import Patient
from accounts.models import AuditLog
from alerts.models import Alert
from decimal import Decimal

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

        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response("Patient not found.", status=status.HTTP_404_NOT_FOUND)

        # Extract vitals mapping
        max30102 = vitals.get('max30102', {})
        ds18b20 = vitals.get('ds18b20', {})
        mpu6050 = vitals.get('mpu6050', {})
        esp32 = vitals.get('esp32', {})

        # Create telemetry SensorReading record
        reading = SensorReading.objects.create(
            patient=patient,
            heart_rate=max30102.get('heartRate'),
            spo2=max30102.get('spo2'),
            temperature=Decimal(str(ds18b20.get('temperature', 36.80))),
            accel_x=Decimal(str(mpu6050.get('accelX', 0.05))),
            accel_y=Decimal(str(mpu6050.get('accelY', 0.98))),
            accel_z=Decimal(str(mpu6050.get('accelZ', 0.04))),
            gyro_x=Decimal(str(mpu6050.get('gyroX', 0.50))),
            gyro_y=Decimal(str(mpu6050.get('gyroY', -1.20))),
            gyro_z=Decimal(str(mpu6050.get('gyroZ', 0.30))),
            fall_detected=mpu6050.get('fallDetected', False),
            esp32_connected=esp32.get('connected', True),
            esp32_battery=esp32.get('battery', 100),
            esp32_rssi=esp32.get('rssi', -55)
        )

        # Update patient risk score and status
        patient.risk = risk_score
        patient.status = status_state
        patient.save()

        # Log HIPAA audit trail
        AuditLog.objects.create(
            username=user_name,
            action=audit_action,
            target=f"Room Patient ID: {patient_id}",
            status='Success'
        )

        # 1. Emergency Button Bypass Rule:
        # Check if emergency_pressed is present and true (either in root or in esp32 payload)
        emergency_pressed = data.get('emergency_pressed') or esp32.get('emergency_pressed') or vitals.get('emergency_pressed')
        
        if emergency_pressed:
            # Immediately generate CRITICAL alert, bypass normal thresholds
            Alert.objects.create(
                patient=patient,
                type='Emergency',
                severity='CRITICAL',
                message='Emergency distress signal initiated via wearable emergency button.',
                status='Active',
                source='Wearable'
            )
        else:
            # Fall Detected check
            if mpu6050.get('fallDetected'):
                Alert.objects.create(
                    patient=patient,
                    type='Fall',
                    severity='CRITICAL',
                    message='Postural sensor triggered fall notification.',
                    status='Active',
                    source='Wearable'
                )
            # Biometric threshold checks:
            hr = max30102.get('heartRate')
            spo2 = max30102.get('spo2')
            if hr and (hr < 50 or hr > 110):
                Alert.objects.create(
                    patient=patient,
                    type='Heart Rate',
                    severity='CRITICAL' if (hr < 45 or hr > 120) else 'WARNING',
                    message=f'Heart rate threshold warning: {hr} BPM.',
                    status='Active',
                    source='System'
                )
            if spo2 and spo2 < 95:
                Alert.objects.create(
                    patient=patient,
                    type='SpO2',
                    severity='CRITICAL' if spo2 < 90 else 'WARNING',
                    message=f'Oxygen saturation dip registered: {spo2}%.',
                    status='Active',
                    source='System'
                )

        return Response("Simulated telemetry update recorded.", status=status.HTTP_200_OK)
