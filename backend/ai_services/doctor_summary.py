import hashlib
import json
from django.utils import timezone
from patients.models import Patient
from medical_records.models import (
    PatientCondition, PatientAllergy, PatientMedication, PatientConsultation,
    NextConsultation, MedicalDocument, VitalMeasurement
)
from prescriptions.models import Prescription
from monitoring.models import SensorReading
from notifications.models import Notification
from medical_records.views import is_user_authorized_for_patient
from ai_services.rag_engine import sanitize_data_for_prompt
from ai_services.risk_evaluation import calculate_patient_clinical_risk

# In-memory LRU cache for generated notes: { patient_id: { 'hash': '...', 'note': '...', 'generated_at': '...' } }
DOCTOR_AI_NOTE_CACHE = {}

def compute_patient_data_signature(patient):
    """
    Computes a cryptographic fingerprint of the patient's current records.
    When any record changes (new vital, alert, document, prescription, allergy, condition),
    the fingerprint changes, invalidating stale cache.
    """
    elements = [str(patient.id)]

    latest_vital = VitalMeasurement.objects.filter(patient=patient).order_by('-measurement_time').first()
    if latest_vital:
        elements.append(f"vital:{latest_vital.id}:{latest_vital.measurement_time.isoformat()}")

    latest_telemetry = SensorReading.objects.filter(patient=patient).order_by('-timestamp').first()
    if latest_telemetry:
        elements.append(f"telemetry:{latest_telemetry.id}:{latest_telemetry.timestamp.isoformat()}:{latest_telemetry.fall_detected}")

    elements.append(f"conditions_cnt:{PatientCondition.objects.filter(patient=patient).count()}")
    elements.append(f"allergies_cnt:{PatientAllergy.objects.filter(patient=patient).count()}")
    elements.append(f"prescriptions_cnt:{Prescription.objects.filter(patient=patient).count()}")
    elements.append(f"docs_cnt:{MedicalDocument.objects.filter(patient=patient).count()}")

    sig_str = "|".join(elements)
    return hashlib.sha256(sig_str.encode('utf-8')).hexdigest()

def generate_doctor_ai_patient_note(user, target_patient_id):
    """
    Generates a structured, clinical-grade AI Patient Note / Clinical Summary for an authorized doctor/care-team user.
    """
    if not is_user_authorized_for_patient(user, target_patient_id):
        return {
            'authorized': False,
            'error': "You do not have permission to access this patient's clinical information.",
            'note': "You do not have permission to access this patient's clinical information.",
            'sources': [],
            'risk_review': None
        }

    patient = Patient.objects.filter(id=target_patient_id).first()
    if not patient:
        return {
            'authorized': False,
            'error': "Patient record not found.",
            'note': "Patient record not found.",
            'sources': [],
            'risk_review': None
        }

    # Cache validation
    current_sig = compute_patient_data_signature(patient)
    cached = DOCTOR_AI_NOTE_CACHE.get(patient.id)
    if cached and cached.get('hash') == current_sig:
        return {
            'authorized': True,
            'patient_id': patient.id,
            'patient_name': patient.name,
            'note': cached['note'],
            'sources': cached['sources'],
            'risk_review': cached['risk_review'],
            'cached': True,
            'generated_at': cached['generated_at']
        }

    sources_list = []

    # 1. Patient Overview: Conditions & Allergies
    conditions = list(PatientCondition.objects.filter(patient=patient).values('condition_name', 'status', 'description'))
    allergies = list(PatientAllergy.objects.filter(patient=patient, is_active=True).values('allergen', 'reaction', 'severity'))
    
    if conditions:
        sources_list.append({'source_type': 'DATABASE', 'source_name': f"PostgreSQL — PatientCondition ({len(conditions)} Active)", 'title': 'Documented Conditions'})
    if allergies:
        sources_list.append({'source_type': 'DATABASE', 'source_name': f"PostgreSQL — PatientAllergy ({len(allergies)} Allergies)", 'title': 'Recorded Allergies'})

    # 2. Current Status: Vitals & Trends
    vitals = list(VitalMeasurement.objects.filter(patient=patient).order_by('-measurement_time')[:3])
    latest_tel = SensorReading.objects.filter(patient=patient).order_by('-timestamp').first()

    if vitals or latest_tel:
        sources_list.append({'source_type': 'DATABASE', 'source_name': 'PostgreSQL — VitalMeasurement & IoT Telemetry', 'title': 'Telemetry Stream'})

    # 3. Medications & Prescriptions
    prescriptions = list(Prescription.objects.filter(patient=patient).values('medicines', 'dosage', 'frequency', 'prescribing_doctor_name'))
    active_meds = list(PatientMedication.objects.filter(patient=patient, is_active=True).values('medicine_name', 'dosage', 'frequency'))
    
    if prescriptions or active_meds:
        sources_list.append({'source_type': 'DATABASE', 'source_name': 'PostgreSQL — Prescription Records', 'title': 'Active Prescriptions'})

    # 4. Recent Findings: Alerts & Medical Documents
    recent_docs = list(MedicalDocument.objects.filter(patient=patient).order_by('-upload_date')[:2].values('title', 'document_type', 'description'))
    
    if recent_docs:
        sources_list.append({'source_type': 'DATABASE', 'source_name': f"PostgreSQL — MedicalDocument Vault ({len(recent_docs)} Docs)", 'title': 'Uploaded Lab Documents'})

    # 5. Deterministic Risk Review
    risk_data = calculate_patient_clinical_risk(patient)

    # ==================== BUILD STRUCTURED AI PATIENT NOTE ====================
    sections = []
    sections.append(f"# AI PATIENT NOTE\n**Patient**: {patient.name} (ID: {patient.id} | Age: {patient.age} | Gender: {patient.gender})\n")
    sections.append("> ⚠️ **AI-generated summary — requires clinician verification.**\n")

    # Overview
    sections.append("### 1. Patient Overview")
    if conditions:
        cond_str = ", ".join([f"{c['condition_name']} ({c['status']})" for c in conditions])
        sections.append(f"- **Documented Conditions**: {cond_str}")
    else:
        sections.append("- **Documented Conditions**: None actively recorded.")

    if allergies:
        alg_str = ", ".join([f"{a['allergen']} (Severity: {a['severity']}, Reaction: {a['reaction'] or 'Unspecified'})" for a in allergies])
        sections.append(f"- **Recorded Allergies**: {alg_str}")
    else:
        sections.append("- **Recorded Allergies**: No active allergies on file.")
    sections.append("")

    # Current Status
    sections.append("### 2. Current Status & Vitals")
    v_lines = []
    if latest_tel:
        hr = f"{latest_tel.heart_rate} BPM" if latest_tel.heart_rate else "N/A"
        spo2 = f"{latest_tel.spo2}%" if latest_tel.spo2 else "N/A"
        temp = f"{latest_tel.temperature}°C" if latest_tel.temperature else "N/A"
        fall_info = " [🚨 FALL DETECTED]" if latest_tel.fall_detected else ""
        v_lines.append(f"- **Latest IoT Telemetry** [{str(latest_tel.timestamp)[:16]}]: HR: {hr}, SpO₂: {spo2}, Temp: {temp}{fall_info} (Device / ESP32)")
    for v in vitals:
        hr = f"{v.heart_rate} BPM" if v.heart_rate else "N/A"
        spo2 = f"{v.spo2}%" if v.spo2 else "N/A"
        temp = f"{v.temperature}°C" if v.temperature else "N/A"
        bp = f"{v.systolic_bp}/{v.diastolic_bp} mmHg" if v.systolic_bp and v.diastolic_bp else "N/A"
        v_lines.append(f"- **{v.source_label}** [{str(v.measurement_time)[:16]}]: HR: {hr}, SpO₂: {spo2}, Temp: {temp}, BP: {bp}")

    if v_lines:
        sections.extend(v_lines)
    else:
        sections.append("- No recent vital readings on file.")
    sections.append("")

    # Medications
    sections.append("### 3. Medications & Prescriptions")
    m_lines = []
    for p in prescriptions:
        m_lines.append(f"- **{p['medicines']}** ({p['dosage']}, {p['frequency']}) — Prescribed by {p['prescribing_doctor_name'] or 'Attending Clinician'}")
    for m in active_meds:
        m_lines.append(f"- **{m['medicine_name']}** ({m['dosage']}, {m['frequency']}) [Active Medication]")
    
    if m_lines:
        sections.extend(m_lines)
    else:
        sections.append("- No active prescriptions or documented medications on file.")
    sections.append("")

    # Recent Findings & Alerts
    sections.append("### 4. Recent Findings & Alerts")
    if latest_tel and latest_tel.fall_detected:
        sections.append(f"- 🚨 **IoT Device Alert**: Sudden fall impact detected by accelerometer.")
    else:
        sections.append("- No active critical alarms or fall alerts.")

    if recent_docs:
        for d in recent_docs:
            d_desc = d['description'][:140] + "..." if len(d['description']) > 140 else d['description']
            sections.append(f"- 📄 **Document: {d['title']}** ({d['document_type']}): {d_desc or 'Document on file.'}")
    sections.append("")

    # AI-Identified Attention Points
    sections.append("### 5. AI-Identified Attention Points")
    attention_points = risk_data['reasons']
    for p in attention_points:
        sections.append(f"- ⚠️ {p}")
    sections.append("")

    # Suggested Clinical Review
    sections.append("### 6. Suggested Clinical Review")
    sections.append(f"- **Recommended Action**: {risk_data['recommended_action']}")
    sections.append("- Cross-reference vital stability trends with current pharmacological therapy.")
    sections.append("")

    # Source Evidence
    sections.append("### 7. Source Evidence")
    for s in sources_list:
        sections.append(f"- 🗄️ **{s['source_name']}** ({s['title']})")
    sections.append("")

    sections.append("*(Note: This AI note is an assistive synthesis for licensed clinicians. It does not replace independent clinical judgment or formal diagnostic examination.)*")

    full_note = "\n".join(sections)
    now_str = str(timezone.now())[:19]

    # Save in cache
    DOCTOR_AI_NOTE_CACHE[patient.id] = {
        'hash': current_sig,
        'note': full_note,
        'sources': sources_list,
        'risk_review': risk_data,
        'generated_at': now_str
    }

    return {
        'authorized': True,
        'patient_id': patient.id,
        'patient_name': patient.name,
        'note': full_note,
        'sources': sources_list,
        'risk_review': risk_data,
        'cached': False,
        'generated_at': now_str
    }
