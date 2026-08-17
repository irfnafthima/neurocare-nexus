import re
from django.db import models
from patients.models import Patient, FamilyPatientLink
from prescriptions.models import Prescription
from medical_records.models import PatientAllergy, PatientCondition, MedicalDocument, VitalMeasurement
from doctors.models import DoctorPatientLink, DoctorConnectionRequest
from caregivers.models import CaregiverPatientLink
from ai_services.models import MedicationKnowledgeBase
from medical_records.views import is_user_authorized_for_patient

SAFETY_DISCLAIMER_NO_CONFLICT = "No relevant conflict was identified in the available records and reference information. This does not confirm that the medicine is appropriate for you. Please consult your doctor or pharmacist."
SAFETY_DISCLAIMER_GENERAL = "This information is provided for educational and safety checking purposes only and does not replace advice from your doctor or pharmacist."

PRESCRIBE_INTENT_PATTERN = re.compile(r'\b(can you prescribe|please prescribe|issue a prescription|prescribe me|prescribe for me|increase my dose|increase dose|decrease my dose|decrease dose|change my dose|change dose|discontinue my|stop taking my|give me a prescription)\b', re.IGNORECASE)

def extract_medicine_names_from_query(query_text):
    words = re.findall(r'\b[A-Za-z0-9\-\']{3,}\b', query_text)
    ignore_words = {'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how', 'can', 'could', 'would', 'should', 'have', 'take', 'using', 'with', 'about', 'doctor', 'patient', 'medicine', 'drug', 'pill', 'tablet', 'allergy', 'allergic', 'side', 'effect', 'effects', 'dose', 'dosage', 'taking', 'before', 'discussing', 'know'}
    candidates = [w for w in words if w.lower() not in ignore_words]
    return candidates

def get_authorized_patient_context(user, target_patient_id):
    if not is_user_authorized_for_patient(user, target_patient_id):
        return None

    patient = Patient.objects.filter(id=target_patient_id).first()
    if not patient:
        return None

    allergies = list(PatientAllergy.objects.filter(patient=patient).values('id', 'allergen', 'reaction', 'severity'))
    conditions = list(PatientCondition.objects.filter(patient=patient).values('id', 'condition_name', 'status', 'description'))
    prescriptions = list(Prescription.objects.filter(patient=patient).values('id', 'medicines', 'dosage', 'frequency', 'prescribing_doctor_name'))
    
    # Authorized Uploaded Documents
    docs = list(MedicalDocument.objects.filter(patient=patient).values('id', 'title', 'document_type', 'description'))

    return {
        'patient_id': patient.id,
        'patient_name': patient.name,
        'age': patient.age,
        'gender': patient.gender,
        'allergies': allergies,
        'conditions': conditions,
        'prescriptions': prescriptions,
        'documents': docs
    }

def retrieve_medication_knowledge(query_text):
    candidates = extract_medicine_names_from_query(query_text)
    matched_entries = []

    for name in candidates:
        kb_matches = MedicationKnowledgeBase.objects.filter(
            models.Q(generic_name__icontains=name) | models.Q(brand_names__icontains=name)
        )
        for entry in kb_matches:
            if entry not in matched_entries:
                matched_entries.append(entry)

    if not matched_entries and len(candidates) > 0:
        # Check all KB entries for substring matches
        all_entries = MedicationKnowledgeBase.objects.all()
        for entry in all_entries:
            if any(c.lower() in entry.generic_name.lower() or c.lower() in entry.brand_names.lower() for c in candidates):
                if entry not in matched_entries:
                    matched_entries.append(entry)

    return matched_entries

def evaluate_deterministic_safety(patient_context, matched_kb_list, query_text):
    """
    Structured Deterministic Safety Evaluator.
    Evaluates:
    1. Allergy Conflict Rule
    2. Interaction Conflict Rule
    3. Autonomous Prescribing Rule
    4. Insufficient Information Rule
    5. Default No Relevant Conflict Rule
    """
    if PRESCRIBE_INTENT_PATTERN.search(query_text):
        return {
            'status': 'REVIEW_RECOMMENDED',
            'concerns': ['Autonomous prescribing and dosage modification are prohibited for AI. Official prescriptions must be issued by a physician.'],
            'disclaimer': SAFETY_DISCLAIMER_GENERAL,
            'is_prescribe_request': True
        }

    if not matched_kb_list:
        return {
            'status': 'INSUFFICIENT_INFORMATION',
            'concerns': ["I don't have enough verified information to answer that safely."],
            'disclaimer': SAFETY_DISCLAIMER_GENERAL,
            'is_prescribe_request': False
        }

    allergies = patient_context.get('allergies', []) if patient_context else []
    prescriptions = patient_context.get('prescriptions', []) if patient_context else []

    allergy_conflicts = []
    interaction_conflicts = []

    for kb in matched_kb_list:
        # Check Allergy Conflicts
        for alg in allergies:
            alg_name = alg.get('allergen', '').strip().lower()
            if not alg_name:
                continue
            
            kb_allergy_text = (kb.allergy_considerations + " " + kb.medication_class + " " + kb.generic_name + " " + kb.brand_names).lower()
            if alg_name in kb_allergy_text or (alg_name == 'penicillin' and 'penicillin' in kb_allergy_text):
                allergy_conflicts.append(f"Recorded allergy '{alg['allergen']}' conflicts with medication '{kb.generic_name}' ({kb.medication_class}).")

        # Check Interaction Conflicts
        for rx in prescriptions:
            rx_name = rx.get('medicines', '').strip().lower()
            kb_interaction_text = kb.common_interactions.lower()
            if rx_name and any(term in kb_interaction_text for term in rx_name.split()):
                interaction_conflicts.append(f"Current prescription '{rx['medicines']}' has known interactions with '{kb.generic_name}'.")

    if allergy_conflicts:
        return {
            'status': 'POTENTIAL_CONCERN_IDENTIFIED',
            'concerns': allergy_conflicts,
            'disclaimer': SAFETY_DISCLAIMER_GENERAL,
            'is_prescribe_request': False
        }

    if interaction_conflicts:
        return {
            'status': 'REVIEW_RECOMMENDED',
            'concerns': interaction_conflicts,
            'disclaimer': SAFETY_DISCLAIMER_GENERAL,
            'is_prescribe_request': False
        }

    return {
        'status': 'NO_RELEVANT_CONFLICT_FOUND',
        'concerns': [],
        'disclaimer': SAFETY_DISCLAIMER_NO_CONFLICT,
        'is_prescribe_request': False
    }

def sanitize_data_for_prompt(text_content):
    """
    Sanitizes retrieved text content to prevent prompt injection attacks.
    Removes directive keywords such as 'ignore previous instructions'.
    """
    if not text_content:
        return ""
    sanitized = str(text_content)
    injection_patterns = [
        r'ignore\s+all\s+previous\s+instructions',
        r'system\s+instruction',
        r'you\s+are\s+now\s+a',
        r'override\s+safety'
    ]
    for pat in injection_patterns:
        sanitized = re.sub(pat, '[REDACTED INJECTION ATTEMPT]', sanitized, flags=re.IGNORECASE)
    return sanitized

def run_rag_medication_guidance(user, target_patient_id, query_text):
    """
    Executes the full grounded RAG Medication Guidance & Safety Check pipeline.
    Returns structured context, deterministic safety status, citations, and grounded explanation.
    """
    # 1. Authorization & Context Retrieval
    patient_context = get_authorized_patient_context(user, target_patient_id)
    if not patient_context:
        return {
            'authorized': False,
            'error': 'Unauthorized: Access denied to patient clinical context.',
            'safety_status': 'INSUFFICIENT_INFORMATION'
        }

    # 2. Medication Knowledge Base & Document Retrieval
    matched_kb = retrieve_medication_knowledge(query_text)
    
    # 3. Deterministic Safety Evaluation
    safety_eval = evaluate_deterministic_safety(patient_context, matched_kb, query_text)

    # 4. Construct Grounded RAG Context
    kb_data = []
    sources = []

    for kb in matched_kb:
        kb_data.append({
            'generic_name': kb.generic_name,
            'brand_names': kb.brand_names,
            'medication_class': kb.medication_class,
            'general_uses': sanitize_data_for_prompt(kb.general_uses),
            'precautions': sanitize_data_for_prompt(kb.common_precautions),
            'contraindications': sanitize_data_for_prompt(kb.common_contraindications),
            'allergy_considerations': sanitize_data_for_prompt(kb.allergy_considerations),
            'common_interactions': sanitize_data_for_prompt(kb.common_interactions),
            'dosage_reference': sanitize_data_for_prompt(kb.dosage_reference),
            'category': kb.category,
            'source_reference': kb.source_reference,
            'source_date': str(kb.source_date)
        })
        sources.append(f"{kb.generic_name} — {kb.source_reference} ({kb.source_date})")

    if patient_context.get('allergies'):
        alg_names = ", ".join([a['allergen'] for a in patient_context['allergies']])
        sources.append(f"PostgreSQL Recorded Allergies: {alg_names}")

    if patient_context.get('prescriptions'):
        rx_names = ", ".join([r['medicines'] for r in patient_context['prescriptions']])
        sources.append(f"PostgreSQL Active Prescriptions: {rx_names}")

    # 5. Build Grounded Explanation Output
    explanation_parts = []
    explanation_parts.append(f"**MEDICATION SAFETY CHECK: {safety_eval['status'].replace('_', ' ')}**\n")
    
    if safety_eval['is_prescribe_request']:
        explanation_parts.append("The AI assistant cannot issue, modify, or prescribe medications. All official prescriptions must be authorized by your attending physician. You may request a doctor review using the button below.\n")
    elif safety_eval['status'] == 'INSUFFICIENT_INFORMATION':
        explanation_parts.append("I don't have enough verified information to answer that safely. Please consult your doctor or pharmacist for guidance on this medication.\n")
    else:
        for kb in kb_data:
            explanation_parts.append(f"**What it is:** {kb['generic_name']} ({kb['brand_names'] or 'Generic'}) is a {kb['medication_class']}.")
            explanation_parts.append(f"**General Uses:** {kb['general_uses']}")
            explanation_parts.append(f"**Precautions & Contraindications:** {kb['precautions']} {kb['contraindications']}")
            if kb['allergy_considerations']:
                explanation_parts.append(f"**Allergy Considerations:** {kb['allergy_considerations']}")

    if safety_eval['concerns']:
        explanation_parts.append("\n**RELEVANT SAFETY CONSIDERATIONS:**")
        for c in safety_eval['concerns']:
            explanation_parts.append(f"- ⚠️ {c}")

    explanation_parts.append(f"\n**IMPORTANT DISCLAIMER:**\n{safety_eval['disclaimer']}")

    if sources:
        explanation_parts.append("\n**SOURCES & EVIDENCE:**")
        for s in sources:
            explanation_parts.append(f"- {s}")

    formatted_explanation = "\n\n".join(explanation_parts)

    return {
        'authorized': True,
        'patient_id': patient_context['patient_id'],
        'query': query_text,
        'safety_status': safety_eval['status'],
        'safety_disclaimer': safety_eval['disclaimer'],
        'concerns': safety_eval['concerns'],
        'is_prescribe_request': safety_eval['is_prescribe_request'],
        'explanation': formatted_explanation,
        'retrieved_context': {
            'patient_allergies': patient_context['allergies'],
            'patient_conditions': patient_context['conditions'],
            'patient_prescriptions': patient_context['prescriptions'],
            'matched_knowledge': kb_data,
            'sources': sources
        }
    }
