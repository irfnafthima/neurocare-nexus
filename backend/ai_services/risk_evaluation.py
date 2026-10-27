from django.utils import timezone
from datetime import timedelta
from patients.models import Patient
from medical_records.models import VitalMeasurement, PatientCondition, PatientAllergy, MedicalDocument
from prescriptions.models import Prescription
from monitoring.models import SensorReading
from notifications.models import Notification

def calculate_patient_clinical_risk(patient):
    """
    Deterministic clinical risk calculation layer for patient telemetry and medical records.
    Does NOT diagnose medical conditions.
    Calculates structured risk indicators based on objective clinical thresholds.
    """
    if not patient:
        return {
            'risk_level': 'LOW',
            'reasons': ['No patient profile found.'],
            'latest_evidence': {},
            'recommended_action': 'Verify patient registration.',
            'disclaimer': 'AI-generated risk flag for clinician review.'
        }

    reasons = []
    evidence = {}
    is_high_risk = False
    is_moderate_risk = False

    # 1. Evaluate Recent Vital Measurements (Manual and IoT)
    recent_manual = VitalMeasurement.objects.filter(patient=patient).order_by('-measurement_time')[:3]
    recent_telemetry = SensorReading.objects.filter(patient=patient).order_by('-timestamp').first()

    latest_hr = None
    latest_spo2 = None
    latest_body_temp = None
    body_temp_source = None
    latest_bp = None
    latest_glucose = None

    if recent_telemetry:
        if recent_telemetry.heart_rate:
            latest_hr = recent_telemetry.heart_rate
        if recent_telemetry.spo2:
            latest_spo2 = recent_telemetry.spo2
        # CRITICAL CLINICAL FIX:
        # The physical ESP32 sends MPU6050 internal board/sensor temperature (~30°C).
        # DS18B20 clinical body temperature sensor is NOT physically installed on this node.
        # MPU6050 board temperature is strictly diagnostic and MUST NEVER be evaluated as patient body temperature.
        if recent_telemetry.temperature is not None:
            try:
                evidence['mpu6050_board_temp'] = f"{float(recent_telemetry.temperature):.1f}°C (Diagnostic Only)"
            except (ValueError, TypeError):
                pass
        evidence['telemetry_time'] = str(recent_telemetry.timestamp)[:19]

    # Clinical Patient Body Temperature Priority:
    # 1. DS18B20 body temperature if physically connected and valid (currently not installed)
    # 2. Latest valid MANUAL body temperature from VitalMeasurement
    # 3. Otherwise no clinical body-temperature value
    if recent_manual:
        for m in recent_manual:
            if m.temperature is not None and latest_body_temp is None:
                latest_body_temp = float(m.temperature)
                body_temp_source = 'MANUAL'
                evidence['body_temperature_source'] = 'MANUAL'
            if m.heart_rate and latest_hr is None:
                latest_hr = m.heart_rate
            if m.spo2 and latest_spo2 is None:
                latest_spo2 = m.spo2
            if m.systolic_bp and m.diastolic_bp and latest_bp is None:
                latest_bp = (m.systolic_bp, m.diastolic_bp)
            if m.blood_glucose and latest_glucose is None:
                latest_glucose = m.blood_glucose
            if 'manual_vitals_time' not in evidence:
                evidence['manual_vitals_time'] = str(m.measurement_time)[:19]

    # Threshold evaluations
    if latest_spo2 is not None:
        evidence['spo2'] = f"{latest_spo2}%"
        if latest_spo2 < 90:
            is_high_risk = True
            reasons.append(f"Critical Hypoxemia: Oxygen Saturation is {latest_spo2}% (< 90%).")
        elif latest_spo2 < 95:
            is_moderate_risk = True
            reasons.append(f"Borderline Oxygen Saturation: {latest_spo2}% (90-94%).")

    if latest_hr is not None:
        evidence['heart_rate'] = f"{latest_hr} BPM"
        if latest_hr > 120:
            is_high_risk = True
            reasons.append(f"Severe Tachycardia: Heart rate is {latest_hr} BPM (> 120 BPM).")
        elif latest_hr < 50:
            is_high_risk = True
            reasons.append(f"Severe Bradycardia: Heart rate is {latest_hr} BPM (< 50 BPM).")
        elif latest_hr > 100:
            is_moderate_risk = True
            reasons.append(f"Elevated Heart Rate: {latest_hr} BPM (101-120 BPM).")

    # Clinical Patient Body Temperature Threshold Evaluations:
    # ONLY evaluated if a legitimate patient body temperature reading exists.
    if latest_body_temp is not None:
        evidence['temperature'] = f"{latest_body_temp:.1f}°C"
        evidence['body_temperature'] = f"{latest_body_temp:.1f}°C ({body_temp_source})"
        if latest_body_temp >= 39.0:
            is_high_risk = True
            reasons.append(f"High Fever: Body temperature is {latest_body_temp:.1f}°C (≥ 39.0°C).")
        elif latest_body_temp <= 35.0:
            is_high_risk = True
            reasons.append(f"Hypothermia: Body temperature is {latest_body_temp:.1f}°C (≤ 35.0°C).")
        elif latest_body_temp >= 38.0:
            is_moderate_risk = True
            reasons.append(f"Elevated Body Temperature: {latest_body_temp:.1f}°C (38.0-38.9°C).")

    if latest_bp is not None:
        sys_bp, dia_bp = latest_bp
        evidence['blood_pressure'] = f"{sys_bp}/{dia_bp} mmHg"
        if sys_bp >= 160 or dia_bp >= 100:
            is_high_risk = True
            reasons.append(f"Severe Hypertension (Stage 2 / Crisis): Blood pressure is {sys_bp}/{dia_bp} mmHg.")
        elif sys_bp <= 90 or dia_bp <= 60:
            is_high_risk = True
            reasons.append(f"Hypotension: Blood pressure is {sys_bp}/{dia_bp} mmHg.")
        elif sys_bp >= 140 or dia_bp >= 90:
            is_moderate_risk = True
            reasons.append(f"Elevated Blood Pressure (Stage 1): {sys_bp}/{dia_bp} mmHg.")

    if latest_glucose is not None:
        evidence['blood_glucose'] = f"{latest_glucose} mg/dL"
        if latest_glucose >= 250:
            is_high_risk = True
            reasons.append(f"Critical Hyperglycemia: Blood glucose is {latest_glucose} mg/dL (≥ 250 mg/dL).")
        elif latest_glucose <= 60:
            is_high_risk = True
            reasons.append(f"Hypoglycemia: Blood glucose is {latest_glucose} mg/dL (≤ 60 mg/dL).")
        elif latest_glucose >= 140:
            is_moderate_risk = True
            reasons.append(f"Elevated Blood Glucose: {latest_glucose} mg/dL.")

    # 2. Evaluate Telemetry Fall Alarms
    if recent_telemetry and recent_telemetry.fall_detected:
        is_high_risk = True
        reasons.append("IoT Device Alert: Sudden fall impact detected by MPU6050 accelerometer.")

    # 3. Document Findings
    recent_docs = MedicalDocument.objects.filter(patient=patient).order_by('-upload_date')[:2]
    for doc in recent_docs:
        desc = (doc.description or '').lower()
        if 'below reference range' in desc or 'above reference range' in desc or 'abnormal' in desc or 'critical' in desc:
            is_moderate_risk = True
            evidence['recent_document'] = f"{doc.title} ({doc.document_type})"

    # Determine final risk level
    if is_high_risk:
        risk_level = 'HIGH'
        recommended_action = "Priority clinical evaluation recommended. Review the patient's current telemetry and clinical records."
    elif is_moderate_risk:
        risk_level = 'MODERATE'
        recommended_action = "Review patient trends and ongoing clinical monitoring."
    else:
        risk_level = 'LOW'
        recommended_action = "Maintain routine clinical supervision."
        if not reasons:
            reasons.append("All recent vital parameters and alert streams are within baseline reference thresholds.")

    return {
        'patient_id': patient.id,
        'patient_name': patient.name,
        'age': patient.age,
        'gender': patient.gender,
        'risk_level': risk_level,
        'reasons': reasons,
        'latest_evidence': evidence,
        'recommended_action': recommended_action,
        'disclaimer': 'AI-generated risk flag for clinician review.'
    }
