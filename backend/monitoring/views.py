from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from monitoring.models import SensorReading
from patients.models import Patient
from accounts.models import AuditLog
from alerts.models import Alert
from decimal import Decimal

def dispatch_critical_alert_notifications(patient, alert_type, alert_message, event_type='CRITICAL_PATIENT_ALERT', target_id=None):
    """
    Dispatches unified in-app notifications and simulated critical alert emails
    to authorized patient, treating doctors, assigned caregivers, and family members.
    """
    from notifications.notification_service import dispatch_event_notification
    dispatch_event_notification(
        event_type=event_type,
        patient_or_id=patient,
        title=f"Critical Alert: {alert_type}",
        message=alert_message,
        category="alarm",
        target_id=target_id or patient.id,
        context_data={
            'alert_type': alert_type,
            'alert_message': alert_message,
            'patient_id': patient.id,
            'patient_name': patient.name
        }
    )


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
        emergency_pressed = data.get('emergency_pressed') or esp32.get('emergency_pressed') or vitals.get('emergency_pressed')
        
        if emergency_pressed:
            # Immediately generate CRITICAL alert, bypass normal thresholds
            msg = 'Emergency distress signal initiated via wearable emergency button.'
            alt = Alert.objects.create(
                patient=patient,
                type='Emergency',
                severity='CRITICAL',
                message=msg,
                status='Active',
                source='Wearable'
            )
            dispatch_critical_alert_notifications(patient, 'Emergency Distress Button', msg, event_type='CRITICAL_PATIENT_ALERT', target_id=alt.id)
        else:
            # Fall Detected check
            if mpu6050.get('fallDetected'):
                msg = 'Postural sensor triggered fall notification.'
                alt = Alert.objects.create(
                    patient=patient,
                    type='Fall',
                    severity='CRITICAL',
                    message=msg,
                    status='Active',
                    source='Wearable'
                )
                dispatch_critical_alert_notifications(patient, 'Fall Detection Alarm', msg, event_type='FALL_ALERT', target_id=alt.id)

            # Biometric threshold checks:
            hr = max30102.get('heartRate')
            spo2 = max30102.get('spo2')
            if hr and (hr < 50 or hr > 110):
                is_crit = (hr < 45 or hr > 120)
                msg = f'Heart rate threshold warning: {hr} BPM.'
                alt = Alert.objects.create(
                    patient=patient,
                    type='Heart Rate',
                    severity='CRITICAL' if is_crit else 'WARNING',
                    message=msg,
                    status='Active',
                    source='System'
                )
                if is_crit:
                    dispatch_critical_alert_notifications(patient, 'Severe Heart Rate Abnormality', msg, event_type='CRITICAL_PATIENT_ALERT', target_id=alt.id)

            if spo2 and spo2 < 95:
                is_crit = (spo2 < 90)
                msg = f'Oxygen saturation dip registered: {spo2}%.'
                alt = Alert.objects.create(
                    patient=patient,
                    type='SpO2',
                    severity='CRITICAL' if is_crit else 'WARNING',
                    message=msg,
                    status='Active',
                    source='System'
                )
                if is_crit:
                    dispatch_critical_alert_notifications(patient, 'Critical Hypoxemia (SpO2 Dip)', msg, event_type='CRITICAL_PATIENT_ALERT', target_id=alt.id)

        return Response("Simulated telemetry update recorded.", status=status.HTTP_200_OK)

