from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from monitoring.models import SensorReading
from monitoring.telemetry_packet import TelemetryPacket
from patients.models import Patient
from accounts.models import AuditLog
from alerts.models import Alert
from notifications.notification_service import dispatch_event_notification


def dispatch_critical_alert_notifications(patient, alert_type, alert_message, event_type='CRITICAL_PATIENT_ALERT', target_id=None):
    """
    Dispatches unified in-app notifications and simulated critical alert emails
    to authorized patient, treating doctors, assigned caregivers, and family members.
    """
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


def evaluate_telemetry_anomalies(patient: Patient, packet: TelemetryPacket) -> list:
    """
    Applies the existing, verified physiological and safety thresholds
    to a TelemetryPacket. Creates Alert records and dispatches notifications
    where appropriate.
    Returns list of generated Alert instances.
    """
    generated_alerts = []

    # 1. Emergency Button Bypass Rule:
    if packet.emergency_pressed:
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
        generated_alerts.append(alt)
        return generated_alerts

    # 2. Fall Detected Check
    if packet.fall_detected:
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
        generated_alerts.append(alt)

    # 3. Heart Rate Thresholds
    hr = packet.heart_rate
    if hr is not None and (hr < 50 or hr > 110):
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
        generated_alerts.append(alt)

    # 4. SpO2 Thresholds
    spo2 = packet.spo2
    if spo2 is not None and spo2 < 95:
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
        generated_alerts.append(alt)

    return generated_alerts


def broadcast_telemetry_event(patient_id: str, payload: dict):
    """
    Broadcasts a normalized telemetry packet to the patient-specific Django Channels group.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            group_name = f"telemetry_patient_{patient_id}"
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'telemetry_message',
                    'data': payload
                }
            )
    except Exception as e:
        # Non-fatal: WebSocket broadcast error should not interrupt pipeline persistence
        print(f"[Telemetry Broadcast Error] Patient {patient_id}: {e}")


def process_telemetry(packet: TelemetryPacket) -> Tuple[SensorReading, list]:
    """
    Unified entry point for all telemetry ingestion (SIMULATED, REAL_DEVICE, REPLAY).
    Responsibilities:
    1. Resolve & validate patient
    2. Persist SensorReading row
    3. Update Patient risk score and status
    4. Log AuditLog
    5. Evaluate anomaly thresholds & generate alerts
    6. Broadcast telemetry event to authorized WebSocket subscribers
    Returns: (SensorReading, list_of_alerts)
    """
    try:
        patient = Patient.objects.get(id=packet.patient_id)
    except Patient.DoesNotExist:
        raise ValueError(f"Patient with ID {packet.patient_id} not found.")

    # Normalize Decimals for SensorReading
    temp_val = Decimal(str(packet.temperature)) if packet.temperature is not None else Decimal("36.80")
    ax_val = Decimal(str(packet.accel_x)) if packet.accel_x is not None else Decimal("0.05")
    ay_val = Decimal(str(packet.accel_y)) if packet.accel_y is not None else Decimal("0.98")
    az_val = Decimal(str(packet.accel_z)) if packet.accel_z is not None else Decimal("0.04")
    gx_val = Decimal(str(packet.gyro_x)) if packet.gyro_x is not None else Decimal("0.50")
    gy_val = Decimal(str(packet.gyro_y)) if packet.gyro_y is not None else Decimal("-1.20")
    gz_val = Decimal(str(packet.gyro_z)) if packet.gyro_z is not None else Decimal("0.30")

    # 1. Persist SensorReading
    reading = SensorReading.objects.create(
        patient=patient,
        heart_rate=packet.heart_rate,
        spo2=packet.spo2,
        temperature=temp_val,
        accel_x=ax_val,
        accel_y=ay_val,
        accel_z=az_val,
        gyro_x=gx_val,
        gyro_y=gy_val,
        gyro_z=gz_val,
        fall_detected=packet.fall_detected,
        esp32_connected=packet.esp32_connected,
        esp32_battery=packet.esp32_battery if packet.esp32_battery is not None else 100,
        esp32_rssi=packet.esp32_rssi if packet.esp32_rssi is not None else -55
    )

    # 2. Update patient risk & status if specified
    if packet.risk_score != patient.risk or packet.status_state != patient.status:
        patient.risk = packet.risk_score
        patient.status = packet.status_state
        patient.save(update_fields=['risk', 'status'])

    # 3. Log HIPAA Audit Trail
    AuditLog.objects.create(
        username=packet.user_name,
        action=packet.audit_action,
        target=f"Room Patient ID: {packet.patient_id}",
        status='Success'
    )

    # 4. Evaluate Anomaly Detection
    alerts = evaluate_telemetry_anomalies(patient, packet)

    # 5. Broadcast to Django Channels WebSocket group
    payload = packet.to_dict()
    payload['type'] = 'telemetry'
    payload['alerts_count'] = len(alerts)
    broadcast_telemetry_event(str(packet.patient_id), payload)

    return reading, alerts
