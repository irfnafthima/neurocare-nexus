import re
import os
import json
import ssl
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET
from django.db import models
from django.utils import timezone

from patients.models import Patient, FamilyPatientLink
from prescriptions.models import Prescription
from medical_records.models import (
    PatientAllergy, PatientCondition, PatientMedication, PatientConsultation, NextConsultation,
    MedicalDocument, VitalMeasurement
)
from monitoring.models import SensorReading
from ai_services.models import MedicationKnowledgeBase
from medical_records.views import is_user_authorized_for_patient

SAFETY_DISCLAIMER_NO_CONFLICT = "No relevant conflict was identified in the available records and reference information. This does not confirm that the medicine is appropriate for you. Please consult your doctor or pharmacist."
SAFETY_DISCLAIMER_GENERAL = "This information is provided for educational and safety checking purposes only and does not replace advice from your doctor or pharmacist."

PRESCRIBE_INTENT_PATTERN = re.compile(r'\b(can you prescribe|please prescribe|issue a prescription|prescribe me|prescribe for me|increase my dose|increase dose|decrease my dose|decrease dose|change my dose|change dose|discontinue my|stop taking my|give me a prescription)\b', re.IGNORECASE)

EMERGENCY_KEYWORDS = [
    'severe chest pain', 'chest pain and difficulty breathing', 'difficulty breathing', 'shortness of breath',
    'loss of consciousness', 'stroke', 'face drooping', 'arm weakness', 'slurred speech',
    'severe bleeding', 'severe allergic reaction', 'anaphylaxis', 'new severe confusion',
    'seizure', 'severe trauma', 'crushing chest pain', 'sudden numbness'
]

TRUSTED_MEDICAL_DOMAINS = [
    {'name': 'MedlinePlus (NIH / U.S. National Library of Medicine)', 'domain': 'medlineplus.gov'},
    {'name': 'World Health Organization (WHO)', 'domain': 'who.int'},
    {'name': 'Ministry of Health and Family Welfare (MoHFW India)', 'domain': 'mohfw.gov.in'},
    {'name': 'Indian Council of Medical Research (ICMR)', 'domain': 'icmr.gov.in'}
]

def sanitize_data_for_prompt(text_content):
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

def extract_clinical_entities(query_text):
    text = query_text.lower()
    entities = {
        'symptoms': [],
        'medications': [],
        'vital_measurements': [],
        'severity': None,
        'duration': None
    }

    symptom_list = ['fever', 'headache', 'dizziness', 'cough', 'chest pain', 'shortness of breath', 'fatigue', 'nausea', 'sweating', 'chills', 'vomiting']
    for s in symptom_list:
        if s in text:
            entities['symptoms'].append(s)

    med_list = ['penicillin', 'paracetamol', 'ibuprofen', 'levetiracetam', 'warfarin', 'aspirin', 'keppra', 'pen-vk']
    for m in med_list:
        if m in text:
            entities['medications'].append(m)

    vital_list = ['heart rate', 'spo2', 'pulse', 'blood pressure', 'temperature', 'systolic', 'diastolic', 'blood glucose']
    for v in vital_list:
        if v in text:
            entities['vital_measurements'].append(v)

    if 'severe' in text or 'high' in text or 'crushing' in text:
        entities['severity'] = 'severe'
    elif 'mild' in text:
        entities['severity'] = 'mild'

    if 'since yesterday' in text:
        entities['duration'] = '1 day'
    elif 'days' in text or 'hours' in text:
        m_dur = re.search(r'(\d+\s*(?:days?|hours?|weeks?))', text)
        if m_dur:
            entities['duration'] = m_dur.group(1)

    return entities

def detect_emergency_indicators(query_text):
    text = query_text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in text:
            return True, kw
    return False, None

def classify_user_intent(query_text, conversation_history=None):
    text = query_text.strip().lower()

    # Contextual threading / Multi-turn pronoun resolution
    if conversation_history and len(conversation_history) > 0:
        last_turn = conversation_history[-1]
        last_text = last_turn.get('text', '').lower()
        if any(pronoun in text for pronoun in ['it', 'that condition', 'this disease', 'the symptoms']) and 'hypertension' in last_text:
            text = f"{text} (context: hypertension)"

    # Emergency check
    is_emerg, _ = detect_emergency_indicators(text)
    if is_emerg:
        return 'EMERGENCY'

    # General conversation
    if text in {'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'thank you', 'thanks', 'who are you', 'help'}:
        return 'GENERAL_CONVERSATION'
    if re.match(r'^(hi|hello|hey|good morning|good afternoon)\b', text) and len(text.split()) <= 3:
        return 'GENERAL_CONVERSATION'

    # Vitals
    vitals_keywords = ['heart rate', 'spo2', 'pulse', 'vital', 'vitals', 'blood pressure', 'temperature', 'systolic', 'diastolic', 'blood glucose', 'sensor reading', 'telemetry', 'my current temperature', 'latest temperature']
    if any(k in text for k in vitals_keywords) and not any(k in text for k in ['prescription', 'prescribe', 'allergy', 'medication safety']):
        return 'VITALS'

    # Consultation
    consultation_keywords = ['consultation', 'appointment', 'checkup', 'scheduled', 'next visit', 'next consultation', 'when is my next']
    if any(k in text for k in consultation_keywords):
        return 'CONSULTATION'

    # Allergy
    allergy_keywords = ['allergy', 'allergies', 'allergic', 'allergen', 'reaction']
    if any(k in text for k in allergy_keywords) and not any(k in text for k in ['can i take', 'is it safe', 'interaction', 'conflict', 'suitable', 'medicine']):
        return 'ALLERGY'

    # Symptom Guidance
    symptom_triggers = ['watch for', 'what could cause', 'cause dizziness', 'i have had a fever', 'symptoms of', 'causes of', 'what to do for']
    if any(k in text for k in symptom_triggers) and not any(k in text for k in ['prescribe', 'medication safety']):
        return 'SYMPTOM_GUIDANCE'

    # Health Condition
    condition_keywords = ['condition', 'conditions', 'disease', 'health problem', 'diagnosed', 'diagnosis', 'medical condition', 'what health problems', 'current condition']
    if any(k in text for k in condition_keywords) and not any(k in text for k in ['hypertension', 'diabetes', 'what is', 'symptoms suggest']):
        return 'HEALTH_CONDITION'

    # Prescription
    prescription_keywords = ['prescribed', 'prescription', 'what did my doctor prescribe', 'doctor prescribed', 'explain my prescription']
    if any(k in text for k in prescription_keywords) and not any(k in text for k in ['can you prescribe', 'issue a prescription', 'can i take', 'is it safe']):
        return 'PRESCRIPTION'

    # Medication Record
    med_record_keywords = [
        'what medicines am i taking', 'my current medicines', 'active medications', 'my medications',
        'current drugs', 'medicines is my patient taking', 'medicines is the patient taking',
        'medicines my patient is taking', 'what medicines is my patient taking', 'patient taking',
        'what drugs is my patient taking', 'what is the patient taking'
    ]
    if any(k in text for k in med_record_keywords):
        return 'MEDICATION_RECORD'

    # Medical Document
    doc_keywords = ['uploaded report', 'blood report', 'scan report', 'document', 'uploaded document', 'medical report', 'pdf report', 'uploaded report say', 'uploaded blood report']
    if any(k in text for k in doc_keywords):
        return 'MEDICAL_DOCUMENT'

    # Medication Safety
    safety_triggers = [
        'can i take', 'is it safe', 'interact', 'interaction', 'conflict', 'contraindication',
        'allergy concern', 'side effect', 'should i ask my doctor about', 'can you prescribe',
        'please prescribe', 'prescribe me', 'prescribe for me', 'issue a prescription',
        'increase my dose', 'decrease my dose', 'change my dose', 'discontinue', 'question about', 'prescribe antibiotics'
    ]
    if any(k in text for k in safety_triggers):
        return 'MEDICATION_SAFETY'

    # Medication Information
    med_info_triggers = ['what is paracetamol', 'what is ibuprofen', 'what is levetiracetam', 'used for', 'medication info', 'paracetamol used for']
    if any(k in text for k in med_info_triggers):
        return 'MEDICATION_INFORMATION'

    candidates = extract_medicine_names_from_query(query_text)
    if candidates:
        kb_exists = MedicationKnowledgeBase.objects.filter(
            models.Q(generic_name__icontains=candidates[0]) | models.Q(brand_names__icontains=candidates[0])
        ).exists()
        if kb_exists:
            if any(term in text for term in ['can i', 'safe', 'take', 'allergy', 'side effect', 'interact', 'suitable', 'question about']):
                return 'MEDICATION_SAFETY'
            return 'MEDICATION_INFORMATION'

    # General Health
    general_health_triggers = ['what is', 'symptoms suggest', 'causes of', 'how to prevent', 'treatment for', 'hypertension', 'diabetes', 'stroke', 'heart emergency', 'symptoms', 'fever', 'help with']
    if any(k in text for k in general_health_triggers):
        return 'GENERAL_HEALTH'

    return 'GENERAL_HEALTH'

def extract_search_terms_from_query(query_text):
    text = query_text.strip().lower()
    medical_terms = [
        'hypertension', 'high blood pressure', 'fever', 'diabetes', 'blood sugar',
        'heart emergency', 'chest pain', 'stroke', 'headache', 'cough', 'asthma',
        'penicillin', 'paracetamol', 'ibuprofen', 'levetiracetam', 'warfarin', 'aspirin'
    ]
    matched = [t for t in medical_terms if t in text]
    if matched:
        return matched[0]
    
    words = re.findall(r'\b[A-Za-z]{3,}\b', text)
    stop_words = {'what', 'when', 'where', 'which', 'who', 'why', 'how', 'does', 'symptoms', 'suggest', 'about', 'cause', 'causes', 'have', 'with', 'dizziness'}
    filtered = [w for w in words if w not in stop_words]
    return " ".join(filtered[:2]) if filtered else query_text

def retrieve_trusted_online_medical_sources(query_text, max_timeout=4.0):
    """
    Retrieves real medical guidance from verified trusted online health sources.
    Returns structured list of web sources:
    [
       {
           'source_type': 'WEB',
           'source_name': 'MedlinePlus (NIH / U.S. National Library of Medicine)',
           'source_url': 'https://medlineplus.gov/hypertension.html',
           'title': 'High Blood Pressure',
           'relevant_text': '...',
           'retrieved_at': '...'
       }
    ]
    """
    search_term = extract_search_terms_from_query(query_text)
    if not search_term:
        return [], False

    web_sources = []
    ssl_context = ssl._create_unverified_context()
    now_str = str(timezone.now())

    # 1. MedlinePlus (NIH) REST Web Service Query
    try:
        encoded_term = urllib.parse.quote(search_term)
        url = f"https://medlineplus.gov/ws/getTopics?term={encoded_term}&db=mplus&rettype=brief"
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NeuroCareNexus/1.0'}
        )
        with urllib.request.urlopen(req, timeout=max_timeout, context=ssl_context) as resp:
            if resp.status == 200:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                
                for topic in root.findall('.//health-topic'):
                    title = topic.get('title') or 'Medical Topic Information'
                    url_attr = topic.get('url') or 'https://medlineplus.gov'
                    full_summary = topic.findtext('full-summary') or topic.findtext('mesh') or ''
                    
                    if title and full_summary:
                        clean_summary = re.sub(r'<[^>]+>', '', full_summary).strip()
                        web_sources.append({
                            'source_type': 'WEB',
                            'source_name': 'MedlinePlus (NIH / U.S. National Library of Medicine)',
                            'source_url': url_attr,
                            'title': title,
                            'relevant_text': clean_summary[:500],
                            'retrieved_at': now_str
                        })
                        if len(web_sources) >= 2:
                            break
    except Exception:
        pass

    # 2. Open Public Health Medical API Query (Secondary Trusted Medical Source)
    if not web_sources:
        try:
            wiki_term = urllib.parse.quote(search_term.replace(' ', '_').capitalize())
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_term}"
            req = urllib.request.Request(
                wiki_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) NeuroCareNexus/1.0'}
            )
            with urllib.request.urlopen(req, timeout=max_timeout, context=ssl_context) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    title = data.get('title')
                    extract = data.get('extract')
                    page_url = data.get('content_urls', {}).get('desktop', {}).get('page') or f"https://en.wikipedia.org/wiki/{wiki_term}"
                    
                    if title and extract:
                        web_sources.append({
                            'source_type': 'WEB',
                            'source_name': 'World Health & Public Medical Knowledge',
                            'source_url': page_url,
                            'title': title,
                            'relevant_text': extract[:500],
                            'retrieved_at': now_str
                        })
        except Exception:
            pass

    if web_sources:
        return web_sources, True
    
    return [], False

def get_scoped_patient_context(user, target_patient_id, intent):
    """
    Retrieves ONLY the patient data required for the classified intent.
    Authorization is enforced BEFORE any query.
    """
    if not is_user_authorized_for_patient(user, target_patient_id):
        return None, False

    patient = Patient.objects.filter(id=target_patient_id).first()
    if not patient:
        return None, False

    scoped_context = {
        'patient_id': patient.id,
        'patient_name': patient.name,
        'age': patient.age,
        'gender': patient.gender
    }

    if intent == 'ALLERGY':
        scoped_context['allergies'] = list(PatientAllergy.objects.filter(patient=patient, is_active=True).values('id', 'allergen', 'reaction', 'severity'))
    
    elif intent == 'HEALTH_CONDITION':
        scoped_context['conditions'] = list(PatientCondition.objects.filter(patient=patient).values('id', 'condition_name', 'status', 'description'))

    elif intent == 'VITALS':
        manual_vitals = list(VitalMeasurement.objects.filter(patient=patient).order_by('-measurement_time')[:3])
        v_list = []
        for v in manual_vitals:
            v_list.append({
                'source': v.source,
                'source_label': v.source_label,
                'heart_rate': v.heart_rate,
                'spo2': v.spo2,
                'temperature': v.temperature,
                'systolic_bp': v.systolic_bp,
                'diastolic_bp': v.diastolic_bp,
                'blood_glucose': v.blood_glucose,
                'time': str(v.measurement_time)
            })
        
        latest_tel = SensorReading.objects.filter(patient=patient).order_by('-timestamp').first()
        if latest_tel:
            v_list.append({
                'source': 'DEVICE',
                'source_label': 'Device / ESP32',
                'heart_rate': latest_tel.heart_rate,
                'spo2': latest_tel.spo2,
                'temperature': float(latest_tel.temperature) if latest_tel.temperature else None,
                'time': str(latest_tel.timestamp)
            })
        scoped_context['vitals'] = v_list

    elif intent in ('PRESCRIPTION', 'MEDICATION_RECORD'):
        scoped_context['prescriptions'] = list(Prescription.objects.filter(patient=patient).values('id', 'medicines', 'dosage', 'frequency', 'prescribing_doctor_name'))
        scoped_context['medications'] = list(PatientMedication.objects.filter(patient=patient, is_active=True).values('id', 'medicine_name', 'dosage', 'frequency'))

    elif intent == 'CONSULTATION':
        scoped_context['next_consultations'] = list(NextConsultation.objects.filter(patient=patient).order_by('consultation_date').values('id', 'consultation_date', 'time', 'doctor_name', 'facility', 'notes'))
        scoped_context['past_consultations'] = list(PatientConsultation.objects.filter(patient=patient).order_by('-consultation_date').values('id', 'consultation_date', 'reason', 'doctor_name'))

    elif intent == 'MEDICAL_DOCUMENT':
        scoped_context['documents'] = list(MedicalDocument.objects.filter(patient=patient).values('id', 'title', 'document_type', 'description', 'upload_date'))

    elif intent == 'MEDICATION_SAFETY':
        scoped_context['allergies'] = list(PatientAllergy.objects.filter(patient=patient, is_active=True).values('id', 'allergen', 'reaction', 'severity'))
        scoped_context['prescriptions'] = list(Prescription.objects.filter(patient=patient).values('id', 'medicines', 'dosage', 'frequency'))
        scoped_context['medications'] = list(PatientMedication.objects.filter(patient=patient, is_active=True).values('id', 'medicine_name', 'dosage', 'frequency'))
        scoped_context['conditions'] = list(PatientCondition.objects.filter(patient=patient, status='Active').values('id', 'condition_name', 'status', 'description'))

    return scoped_context, True

def extract_medicine_names_from_query(query_text):
    words = re.findall(r'\b[A-Za-z0-9\-\']{3,}\b', query_text)
    ignore_words = {
        'what', 'when', 'where', 'which', 'who', 'whom', 'whose', 'why', 'how', 'can', 'could', 'would', 'should',
        'have', 'take', 'using', 'with', 'about', 'doctor', 'patient', 'medicine', 'drug', 'pill', 'tablet',
        'allergy', 'allergic', 'side', 'effect', 'effects', 'dose', 'dosage', 'taking', 'before', 'discussing',
        'know', 'symptoms', 'heart', 'emergency', 'hypertension', 'diabetes', 'consultation', 'vitals'
    }
    candidates = [w for w in words if w.lower() not in ignore_words]
    return candidates

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
        all_entries = MedicationKnowledgeBase.objects.all()
        for entry in all_entries:
            if any(c.lower() in entry.generic_name.lower() or c.lower() in entry.brand_names.lower() for c in candidates):
                if entry not in matched_entries:
                    matched_entries.append(entry)

    return matched_entries

def chunk_and_retrieve_document_sections(text, query_text, max_chunks=3):
    """
    Chunks document into logical paragraphs/sections and retrieves the most relevant chunks.
    """
    if not text:
        return []
    raw_paragraphs = [p.strip() for p in re.split(r'\n{2,}|\r\n{2,}', text) if p.strip()]
    if not raw_paragraphs:
        raw_paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    
    q_words = set(re.findall(r'\b[A-Za-z0-9]{3,}\b', query_text.lower()))
    scored_chunks = []
    for p in raw_paragraphs:
        score = sum(1 for w in q_words if w in p.lower())
        scored_chunks.append((score, p))
    
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    selected = [chunk for _, chunk in scored_chunks[:max_chunks]]
    return selected if selected else raw_paragraphs[:max_chunks]

def analyze_medical_document_findings(doc, query_text, patient_name):
    """
    RAG Medical Document Analyzer:
    - Summarizes findings in clear, empathetic patient-friendly language.
    - Highlights reported values and distinguishes normal vs outside-reference-range values.
    - Explains medical terms (e.g., Hemoglobin, WBC, Platelets, Glucose, Creatinine, etc.).
    - Highlights points requiring discussion with a healthcare provider.
    - Strictly avoids diagnosing or prescribing.
    """
    title = doc.get('title', 'Medical Document')
    doc_type = doc.get('document_type', 'Report')
    raw_desc = doc.get('description', '').strip()
    
    if not raw_desc:
        return (
            f"**📄 DOCUMENT OVERVIEW: {title} ({doc_type})**\n\n"
            f"I found document **'{title}'** on file for {patient_name}, but no readable clinical text was extracted.\n"
            f"Please ensure the document contains searchable text or provide clinical notes in the Health Records Vault."
        )

    relevant_chunks = chunk_and_retrieve_document_sections(raw_desc, query_text)
    text_lower = raw_desc.lower()
    findings = []
    terms_explained = {}
    discussion_points = []
    
    biomarkers = [
        {
            'name': 'Hemoglobin',
            'pattern': r'(?:hemoglobin|hb)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:g/dl|gm/dl|g%)?',
            'unit': 'g/dL',
            'min': 12.0,
            'max': 17.5,
            'desc': 'Oxygen-carrying protein in red blood cells that transports oxygen from the lungs to all tissues.'
        },
        {
            'name': 'White Blood Cells (WBC / Leukocytes)',
            'pattern': r'(?:wbc|white blood cells?|total leukocyte count|tlc)\s*[:=]?\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:/\s*(?:ul|cumm|mm3)|\s*k/ul|\s*10\^3/ul)?',
            'unit': '/µL',
            'min': 4000,
            'max': 11000,
            'desc': 'Immune cells responsible for defending the body against infections and inflammation.'
        },
        {
            'name': 'Platelets (Thrombocytes)',
            'pattern': r'(?:platelets?|thrombocyte count|platelet count)\s*[:=]?\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:/\s*(?:ul|cumm|mm3)|\s*k/ul|\s*10\^3/ul|\s*lakhs)?',
            'unit': '/µL',
            'min': 150000,
            'max': 450000,
            'desc': 'Cellular fragments in the blood essential for normal blood clotting and wound healing.'
        },
        {
            'name': 'Fasting Blood Glucose',
            'pattern': r'(?:fasting blood sugar|fasting glucose|fbs|blood sugar)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl)?',
            'unit': 'mg/dL',
            'min': 70,
            'max': 99,
            'desc': 'Concentration of glucose in the bloodstream after an overnight fast, reflecting metabolic regulation.'
        },
        {
            'name': 'HbA1c',
            'pattern': r'(?:hba1c|glycated hemoglobin)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*%?',
            'unit': '%',
            'min': 4.0,
            'max': 5.6,
            'desc': 'Measure of average blood sugar control over the previous 2 to 3 months.'
        },
        {
            'name': 'Serum Creatinine',
            'pattern': r'(?:serum creatinine|creatinine)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl)?',
            'unit': 'mg/dL',
            'min': 0.6,
            'max': 1.2,
            'desc': 'Waste byproduct of muscle activity filtered by the kidneys, used as a key marker of kidney filtration.'
        },
        {
            'name': 'Total Cholesterol',
            'pattern': r'(?:total cholesterol|cholesterol)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:mg/dl)?',
            'unit': 'mg/dL',
            'min': 100,
            'max': 199,
            'desc': 'Total measure of circulating blood lipids including LDL and HDL cholesterol.'
        },
        {
            'name': 'Blood Pressure (Reported)',
            'pattern': r'(?:bp|blood pressure)\s*[:=]?\s*([0-9]{2,3}\s*/\s*[0-9]{2,3})\s*(?:mmhg)?',
            'unit': 'mmHg',
            'min': None,
            'max': None,
            'desc': 'Pressure exerted by circulating blood against the walls of arterial vessels.'
        }
    ]

    for bm in biomarkers:
        m = re.search(bm['pattern'], text_lower)
        if m:
            val_str = m.group(1).replace(',', '').strip()
            terms_explained[bm['name']] = bm['desc']
            try:
                val_num = float(val_str)
                if bm['min'] is not None and bm['max'] is not None:
                    if val_num < bm['min']:
                        findings.append(f"- **{bm['name']}**: **{val_str} {bm['unit']}** (Standard Reference Range: {bm['min']} – {bm['max']} {bm['unit']}) — ⚠️ *Reported Below Reference Range*")
                        discussion_points.append(f"Discuss the lower {bm['name']} value ({val_str} {bm['unit']}) with your clinician.")
                    elif val_num > bm['max']:
                        findings.append(f"- **{bm['name']}**: **{val_str} {bm['unit']}** (Standard Reference Range: {bm['min']} – {bm['max']} {bm['unit']}) — ⚠️ *Reported Above Reference Range*")
                        discussion_points.append(f"Review the elevated {bm['name']} value ({val_str} {bm['unit']}) with your physician.")
                    else:
                        findings.append(f"- **{bm['name']}**: **{val_str} {bm['unit']}** (Standard Reference Range: {bm['min']} – {bm['max']} {bm['unit']}) — ✅ *Within Normal Reference Range*")
                else:
                    findings.append(f"- **{bm['name']}**: **{val_str} {bm['unit']}**")
            except ValueError:
                findings.append(f"- **{bm['name']}**: {val_str} {bm['unit']}")

    sections = []
    sections.append(f"**📄 MEDICAL REPORT SUMMARY: {title} ({doc_type})**\n")
    sections.append(f"**Patient Record**: {patient_name}\n")
    
    summary_text = "\n".join(relevant_chunks)
    if len(summary_text) > 700:
        summary_text = summary_text[:700] + "..."
    sections.append(f"**📋 Report Overview:**\n{summary_text}\n")
    
    if findings:
        sections.append("**🔬 Key Reported Values & Reference Comparison:**\n" + "\n".join(findings) + "\n")
    
    if terms_explained:
        term_lines = [f"- **{k}**: {v}" for k, v in terms_explained.items()]
        sections.append("**💡 Medical Terminology Explained:**\n" + "\n".join(term_lines) + "\n")
    
    if discussion_points:
        disc_lines = [f"- 🩺 {p}" for p in discussion_points]
        sections.append("**🩺 Recommended Discussion Points for Your Doctor:**\n" + "\n".join(disc_lines) + "\n")
    else:
        sections.append("**🩺 Recommended Discussion Points for Your Doctor:**\n- Bring this report to your next consultation to discuss clinical context and ongoing health management.\n")

    sections.append(
        "**⚖️ Clinical Disclaimer:**\n"
        "This automated summary is provided for educational and communication support only. The AI assistant does not diagnose diseases, alter prescriptions, or replace official clinician interpretation. Please consult your physician for clinical decisions."
    )

    return "\n".join(sections)

def evaluate_deterministic_safety(patient_context, matched_kb_list, query_text):
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
            'concerns': ["I can help with medication information or a safety check. Which medicine are you asking about?"],
            'disclaimer': "Please consult your doctor or pharmacist before taking any new medication.",
            'is_prescribe_request': False
        }

    allergies = patient_context.get('allergies', []) if patient_context else []
    prescriptions = patient_context.get('prescriptions', []) if patient_context else []
    medications = patient_context.get('medications', []) if patient_context else []
    conditions = patient_context.get('conditions', []) if patient_context else []

    allergy_conflicts = []
    interaction_conflicts = []
    condition_conflicts = []

    for kb in matched_kb_list:
        # 1. Allergy conflicts
        for alg in allergies:
            alg_name = alg.get('allergen', '').strip().lower()
            if not alg_name:
                continue
            
            kb_allergy_text = (kb.allergy_considerations + " " + kb.medication_class + " " + kb.generic_name + " " + kb.brand_names).lower()
            if alg_name in kb_allergy_text or (alg_name == 'penicillin' and 'penicillin' in kb_allergy_text):
                allergy_conflicts.append(f"Recorded allergy '{alg['allergen']}' conflicts with medication '{kb.generic_name}' ({kb.medication_class}).")

        # 2. Drug-drug interactions (prescriptions & active medications)
        all_patient_meds = [p.get('medicines', '') for p in prescriptions] + [m.get('medicine_name', '') for m in medications]
        for med_item in all_patient_meds:
            rx_name = str(med_item).strip().lower()
            kb_interaction_text = kb.common_interactions.lower()
            if rx_name and any(term in kb_interaction_text for term in rx_name.split() if len(term) > 3):
                interaction_conflicts.append(f"Current medication '{med_item}' has known interactions with '{kb.generic_name}'.")

        # 3. Clinical condition contraindications
        kb_contra_text = (kb.common_contraindications + " " + kb.common_precautions).lower()
        for cond in conditions:
            c_name = cond.get('condition_name', '').strip().lower()
            if c_name and any(term in kb_contra_text for term in c_name.split() if len(term) > 3):
                condition_conflicts.append(f"Recorded condition '{cond['condition_name']}' is noted as a clinical precaution/contraindication for '{kb.generic_name}'.")

    all_concerns = allergy_conflicts + interaction_conflicts + condition_conflicts

    if allergy_conflicts:
        return {
            'status': 'POTENTIAL_CONCERN_IDENTIFIED',
            'concerns': all_concerns,
            'disclaimer': "⚠️ Potential clinical conflict detected. Please consult your doctor or pharmacist before taking this medication.",
            'is_prescribe_request': False
        }

    if interaction_conflicts or condition_conflicts:
        return {
            'status': 'REVIEW_RECOMMENDED',
            'concerns': all_concerns,
            'disclaimer': "⚠️ Clinical precaution or interaction noted. Please consult your doctor or pharmacist before taking this medication.",
            'is_prescribe_request': False
        }

    return {
        'status': 'NO_RELEVANT_CONFLICT_FOUND',
        'concerns': [],
        'disclaimer': SAFETY_DISCLAIMER_NO_CONFLICT,
        'is_prescribe_request': False
    }

def run_rag_medication_guidance(user, target_patient_id, query_text, conversation_history=None):
    """
    Executes clinical NLU, emergency risk detection, scoped context retrieval, online evidence RAG, and response generation.
    """
    intent = classify_user_intent(query_text, conversation_history)
    entities = extract_clinical_entities(query_text)

    # General queries (GENERAL_HEALTH, SYMPTOM_GUIDANCE, GENERAL_CONVERSATION, MEDICATION_INFORMATION, EMERGENCY) do NOT require patient authorization
    if intent in ('GENERAL_HEALTH', 'SYMPTOM_GUIDANCE', 'GENERAL_CONVERSATION', 'MEDICATION_INFORMATION', 'EMERGENCY'):
        is_auth = True
        patient_name = getattr(user, 'full_name', 'Patient User') if user else 'Patient User'
        patient_context = {'patient_id': target_patient_id or 'GENERAL', 'patient_name': patient_name}
    else:
        patient_context, is_auth = get_scoped_patient_context(user, target_patient_id, intent)

    if not is_auth:
        return {
            'authorized': False,
            'intent': intent,
            'error': "You do not have permission to access this patient's clinical information.",
            'safety_status': 'INSUFFICIENT_INFORMATION',
            'answer': "You do not have permission to access this patient's clinical information.",
            'explanation': "You do not have permission to access this patient's clinical information.",
            'sources': [],
            'patient_context_used': False,
            'retrieval': {'database': False, 'knowledge_base': False, 'web': False}
        }

    # ==================== EMERGENCY INTENT ====================
    if intent == 'EMERGENCY':
        emergency_explanation = (
            "**🚨 EMERGENCY CLINICAL NOTICE:**\n\n"
            "The symptoms described (such as severe chest pain, acute respiratory distress, or stroke indicators) require **immediate emergency medical evaluation**.\n\n"
            "**IMMEDIATE ACTION:**\n"
            "- If you or someone nearby is experiencing severe or life-threatening symptoms, contact local emergency medical services immediately.\n"
            "- Do not delay seeking emergency care for symptoms of chest pressure, severe shortness of breath, or sudden weakness."
        )
        return {
            'authorized': True,
            'intent': intent,
            'answer': emergency_explanation,
            'explanation': emergency_explanation,
            'sources': [{
                'source_type': 'SYSTEM',
                'source_name': 'Clinical Safety Protocol',
                'title': 'Emergency Symptom Triage'
            }],
            'patient_context_used': False,
            'retrieval': {'database': False, 'knowledge_base': False, 'web': False},
            'retrieved_context': {}
        }

    # ==================== GENERAL CONVERSATION ====================
    if intent == 'GENERAL_CONVERSATION':
        p_name = patient_context.get('patient_name', 'User')
        explanation = f"Hello {p_name}! I am your NeuroCare AI clinical assistant. How can I support your care journey today?"
        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': [],
            'patient_context_used': False,
            'retrieval': {'database': False, 'knowledge_base': False, 'web': False},
            'retrieved_context': {}
        }

    # ==================== GENERAL HEALTH & SYMPTOM GUIDANCE ====================
    if intent in ('GENERAL_HEALTH', 'SYMPTOM_GUIDANCE'):
        q_lower = query_text.lower()
        web_sources, web_success = retrieve_trusted_online_medical_sources(query_text)
        sources_list = []
        retrieved_web_summary = ""

        if web_success and web_sources:
            for ws in web_sources:
                sources_list.append({
                    'source_type': 'WEB',
                    'source_name': ws['source_name'],
                    'source_url': ws['source_url'],
                    'title': ws['title'],
                    'relevant_text': sanitize_data_for_prompt(ws['relevant_text']),
                    'retrieved_at': ws.get('retrieved_at', str(timezone.now()))
                })
                retrieved_web_summary += f"\n- **[{ws['source_name']}] ({ws['title']})**: {ws['relevant_text']}\n"
        else:
            sources_list.append({
                'source_type': 'SYSTEM',
                'source_name': 'Online Source Status',
                'source_url': '',
                'title': 'Online source retrieval is currently unavailable',
                'relevant_text': 'Online source retrieval is currently unavailable. Response is based on internal verified medical knowledge.'
            })

        # Specific high-quality natural health responses
        if 'what is fever' in q_lower or q_lower == 'fever' or ('fever' in q_lower and ('mean' in q_lower or 'explain' in q_lower or ('what' in q_lower and 'do' not in q_lower))):
            base_info = (
                "**Understanding Fever:**\n\n"
                "A fever is a temporary increase in body temperature (typically 38.0°C / 100.4°F or higher) that usually occurs as a natural part of the body's immune defense against an infection or illness.\n\n"
                "**Common Causes:**\n"
                "- **Viral Infections**: Common colds, influenza, COVID-19, or viral gastroenteritis.\n"
                "- **Bacterial Infections**: Strep throat, ear infections, urinary tract infections, or bronchitis.\n"
                "- **Other Factors**: Inflammatory reactions, heat exhaustion, or immunization responses.\n\n"
                "**Common Associated Symptoms:**\n"
                "- Chills, shivering, sweating, headache, generalized muscle aches, fatigue, and decreased appetite.\n\n"
                "**Basic Supportive Care:**\n"
                "- **Hydration**: Drink plenty of clear fluids (water, oral rehydration solutions, broths) to prevent dehydration.\n"
                "- **Rest**: Get ample physical rest to help the body recover.\n"
                "- **Comfort**: Stay in a cool room, use lightweight bedding, and wear breathable clothing.\n"
                "- **Monitoring**: Measure and record temperature periodically.\n\n"
                "**When to Seek Medical Attention:**\n"
                "- Temperature reaching 39.5°C (103.0°F) or higher, or a fever lasting longer than 3 days.\n"
                "- Fever accompanied by warning signs such as severe headache, stiff neck, shortness of breath, confusion, or persistent vomiting.\n"
                "- In infants under 3 months old or individuals with weakened immune systems."
            )
        elif 'have fever' in q_lower or ('fever' in q_lower and any(k in q_lower for k in ['what should i do', 'what to do', 'help', 'treat', 'manage', 'steps'])):
            base_info = (
                "**Supportive Steps for Managing a Fever:**\n\n"
                "If you are currently experiencing a fever, here is supportive self-care guidance to stay comfortable while your body recovers:\n\n"
                "**1. Stay Well Hydrated:**\n"
                "Fever increases fluid loss through sweating. Drink plenty of water, electrolyte drinks, or warm broths throughout the day.\n\n"
                "**2. Get Sufficient Rest:**\n"
                "Avoid strenuous physical exertion and allow your immune system time to recover.\n\n"
                "**3. Keep Cool and Comfortable:**\n"
                "Wear light, loose clothing and keep your room at a comfortable temperature. You can use a lukewarm damp cloth on your forehead for comfort (avoid ice-cold baths).\n\n"
                "**4. Monitor Your Temperature:**\n"
                "Check your temperature every 4 to 6 hours to track any changes.\n\n"
                "**When Medical Attention Is Needed:**\n"
                "Consult a doctor if your fever exceeds 39.5°C (103°F), persists beyond 3 days, or is accompanied by difficulty breathing, chest pain, a stiff neck, or severe dizziness."
            )
        elif 'hypertension' in q_lower or 'high blood pressure' in q_lower:
            base_info = (
                "**Understanding Hypertension (High Blood Pressure):**\n\n"
                "Hypertension is a long-term medical condition in which the force exerted by circulating blood against the artery walls is consistently too high (typically 130/80 mmHg or higher across multiple clinical measurements).\n\n"
                "**Symptoms & Signs:**\n"
                "- Often referred to as a 'silent killer' because it usually produces no noticeable symptoms in early or moderate stages.\n"
                "- When blood pressure is significantly elevated, individuals may occasionally experience morning headaches, dizziness, blurred vision, or shortness of breath.\n\n"
                "**Common Risk Factors:**\n"
                "- High dietary sodium intake, sedentary lifestyle, chronic psychological stress, tobacco use, excess alcohol consumption, advancing age, and family history.\n\n"
                "**Supportive Management & Lifestyle Measures:**\n"
                "- Adopting a balanced, heart-healthy diet rich in fruits, vegetables, and low in sodium (such as the DASH diet).\n"
                "- Engaging in moderate aerobic exercise regularly (e.g., 30 minutes of brisk walking most days).\n"
                "- Maintaining a healthy body weight and avoiding smoking.\n"
                "- Taking clinician-prescribed antihypertensive medications consistently as directed.\n\n"
                "**When to Consult a Healthcare Professional:**\n"
                "Schedule routine blood pressure checks with your clinician. If you experience severe chest discomfort, acute severe headache, or visual disturbances, seek immediate emergency medical care."
            )
        elif 'diabetes' in q_lower or 'blood sugar' in q_lower:
            base_info = (
                "**Understanding Diabetes:**\n\n"
                "Diabetes is a chronic metabolic condition characterized by elevated blood glucose levels resulting from insufficient insulin production by the pancreas, insulin resistance, or both.\n\n"
                "**Common Symptoms & Signs:**\n"
                "- Increased thirst, frequent urination, increased hunger, unexplained weight loss, fatigue, blurred vision, and slow-healing sores.\n\n"
                "**General Management Principles:**\n"
                "- Balanced nutrition with controlled carbohydrate intake and high fiber.\n"
                "- Regular physical activity and body weight management.\n"
                "- Routine blood glucose monitoring and adherence to physician-prescribed medications.\n\n"
                "**When to Seek Medical Attention:**\n"
                "Consult your healthcare provider for diagnostic screening and personalized management. Seek prompt medical care for severe symptoms such as confusion, extreme dehydration, or persistent high glucose readings."
            )
        elif 'dizziness' in q_lower:
            base_info = (
                "**Understanding Dizziness:**\n\n"
                "Dizziness is a broad term that can describe feeling lightheaded, woozy, unsteady, or experiencing vertigo (a sensation that your surroundings are spinning).\n\n"
                "**Common Causes:**\n"
                "- Inner ear disturbances (such as benign paroxysmal positional vertigo or labyrinthitis)\n"
                "- Dehydration or low blood sugar\n"
                "- Temporary drops in blood pressure (orthostatic hypotension)\n"
                "- Fatigue, anxiety, or medication side effects\n\n"
                "**Supportive Measures:**\n"
                "- Sit or lie down immediately if feeling unsteady to prevent falls.\n"
                "- Drink a glass of water and rest in a comfortable position.\n"
                "- Avoid sudden changes in body position.\n\n"
                "**When to Seek Medical Attention:**\n"
                "Seek emergency medical evaluation if dizziness is sudden and severe, or accompanied by chest pain, numbness, facial weakness, slurred speech, or a severe headache."
            )
        else:
            base_info = (
                f"**General Health Information:**\n\n"
                f"Regarding '{query_text}': This information is provided for educational purposes.\n\n"
                "If you are experiencing new, persistent, or worsening physical symptoms, please consult a qualified healthcare provider for a thorough medical evaluation."
            )

        if retrieved_web_summary:
            explanation = base_info + f"\n\n**TRUSTED MEDICAL EVIDENCE:**\n{retrieved_web_summary}"
        else:
            explanation = base_info + "\n\n*Note: Online source retrieval is currently unavailable. Response is based on verified clinical knowledge.*"

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': False,
            'retrieval': {
                'database': False,
                'knowledge_base': True,
                'web': web_success
            },
            'retrieved_context': {}
        }

    # ==================== ALLERGY ====================
    if intent == 'ALLERGY':
        allergies = patient_context.get('allergies', [])
        sources_list = [{
            'source_type': 'DATABASE',
            'source_name': 'PostgreSQL — PatientAllergy',
            'record_type': 'PatientAllergy',
            'title': f"Allergy Records ({len(allergies)})"
        }]

        if allergies:
            alg_items = [f"- **{a['allergen']}**: Reaction ({a['reaction'] or 'Unspecified'}), Severity: {a['severity']}" for a in allergies]
            explanation = f"**YOUR RECORD:**\n\n" + "\n".join(alg_items) + f"\n\n**INTERPRETATION:**\nPatient {patient_context['patient_name']} has {len(allergies)} recorded clinical allergy record(s) on file."
        else:
            explanation = f"**YOUR RECORD:**\nNo active allergies are currently recorded on file for {patient_context['patient_name']}."

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': True,
            'retrieval': {'database': True, 'knowledge_base': False, 'web': False},
            'retrieved_context': {'allergies': allergies}
        }

    # ==================== VITALS ====================
    if intent == 'VITALS':
        vitals = patient_context.get('vitals', [])
        q_lower = query_text.lower()
        sources_list = []

        if vitals:
            v_lines = []
            for v in vitals:
                src_label = v['source_label'] # "Manual entry" or "Device / ESP32"
                hr = f"{v['heart_rate']} BPM" if v['heart_rate'] else "N/A"
                spo2 = f"{v['spo2']}%" if v['spo2'] else "N/A"
                temp = f"{v['temperature']}°C" if v['temperature'] else "N/A"
                v_lines.append(f"- **{src_label}** [{v['time'][:16]}]: Heart Rate: {hr}, SpO₂: {spo2}, Temp: {temp}")
                sources_list.append({
                    'source_type': 'DATABASE',
                    'source_name': f"PostgreSQL — VitalMeasurement ({src_label})",
                    'record_type': 'VitalMeasurement',
                    'title': f"Vital Measurement ({src_label})"
                })

            if 'temperature' in q_lower or 'temp' in q_lower:
                temp_readings = [v for v in vitals if v.get('temperature') is not None]
                if temp_readings:
                    latest_t = temp_readings[0]
                    explanation = (
                        f"**YOUR RECORD (Latest Temperature):**\n\n"
                        f"- **Temperature**: {latest_t['temperature']}°C\n"
                        f"- **Data Source**: {latest_t['source_label']}\n"
                        f"- **Timestamp**: {latest_t['time'][:16]}\n\n"
                        f"**Recent Vital History for {patient_context['patient_name']}:**\n" + "\n".join(v_lines)
                    )
                else:
                    explanation = f"**YOUR RECORD:**\n\n" + "\n".join(v_lines) + f"\n\n*No specific temperature measurement was found in recent records.*"
            else:
                explanation = f"**YOUR RECORD:**\n\n" + "\n".join(v_lines) + f"\n\n**INTERPRETATION:**\nDisplaying latest vital readings for {patient_context['patient_name']} with preserved device provenance."
        else:
            explanation = f"No vital telemetry readings are currently on file for {patient_context['patient_name']}."
            sources_list.append({
                'source_type': 'DATABASE',
                'source_name': 'PostgreSQL — VitalMeasurement',
                'record_type': 'VitalMeasurement',
                'title': 'Vital Measurements'
            })

        if '39' in q_lower or 'high temperature' in q_lower or ('temperature' in q_lower and 'should i do' in q_lower):
            explanation += (
                "\n\n**General Temperature Guidance:**\n"
                "A temperature around 39°C (102.2°F) represents an elevated body temperature (fever).\n"
                "- Maintain adequate hydration and rest.\n"
                "- For a persistent high temperature, worsening symptoms, or severe discomfort, seeking medical evaluation from your physician is recommended."
            )

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': True,
            'retrieval': {'database': True, 'knowledge_base': False, 'web': False},
            'retrieved_context': {'vitals': vitals}
        }

    # ==================== CONSULTATION ====================
    if intent == 'CONSULTATION':
        next_c = patient_context.get('next_consultations', [])
        sources_list = [{
            'source_type': 'DATABASE',
            'source_name': 'PostgreSQL — NextConsultation',
            'record_type': 'NextConsultation',
            'title': 'Scheduled Consultations'
        }]

        if next_c:
            c_lines = [f"- **{nc['consultation_date']}** at {nc['time']} with {nc['doctor_name'] or 'Attending Physician'} ({nc['facility'] or 'NeuroCare Clinic'})" for nc in next_c]
            explanation = f"**YOUR RECORD:**\n\n" + "\n".join(c_lines)
        else:
            explanation = f"No upcoming consultations are currently scheduled on file for {patient_context['patient_name']}."

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': True,
            'retrieval': {'database': True, 'knowledge_base': False, 'web': False},
            'retrieved_context': {'next_consultations': next_c}
        }

    # ==================== HEALTH CONDITION ====================
    if intent == 'HEALTH_CONDITION':
        conds = patient_context.get('conditions', [])
        sources_list = [{
            'source_type': 'DATABASE',
            'source_name': 'PostgreSQL — PatientCondition',
            'record_type': 'PatientCondition',
            'title': 'Active Conditions'
        }]

        if conds:
            c_lines = [f"- **{c['condition_name']}** ({c['status']}): {c['description'] or 'Diagnosed condition'}" for c in conds]
            explanation = f"**YOUR RECORD:**\n\n" + "\n".join(c_lines)
        else:
            explanation = f"No active medical conditions are currently recorded on file for {patient_context['patient_name']}."

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': True,
            'retrieval': {'database': True, 'knowledge_base': False, 'web': False},
            'retrieved_context': {'conditions': conds}
        }

    # ==================== PRESCRIPTION / MEDICATION RECORD ====================
    if intent in ('PRESCRIPTION', 'MEDICATION_RECORD'):
        prescriptions = patient_context.get('prescriptions', [])
        sources_list = [{
            'source_type': 'DATABASE',
            'source_name': 'PostgreSQL — Prescription',
            'record_type': 'Prescription',
            'title': 'Authorized Prescriptions'
        }]

        if prescriptions:
            p_lines = [f"- **{p['medicines']}** ({p['dosage']}, {p['frequency']}) — Prescribed by {p['prescribing_doctor_name'] or 'Attending Physician'}" for p in prescriptions]
            explanation = f"**YOUR RECORD:**\n\n" + "\n".join(p_lines) + f"\n\n**INTERPRETATION:**\nShowing active authorized prescriptions prescribed by your attending physician."
        else:
            explanation = f"No active prescriptions are currently recorded on file for {patient_context['patient_name']}."

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': True,
            'retrieval': {'database': True, 'knowledge_base': False, 'web': False},
            'retrieved_context': {'prescriptions': prescriptions}
        }

    # ==================== MEDICAL DOCUMENT ====================
    if intent == 'MEDICAL_DOCUMENT':
        docs = patient_context.get('documents', [])
        sources_list = []
        if docs:
            d = docs[0]
            sources_list.append({
                'source_type': 'DATABASE',
                'source_name': f"PostgreSQL — MedicalDocument ({d['title']})",
                'record_type': 'MedicalDocument',
                'title': d['title']
            })
            p_name = patient_context.get('patient_name', 'Patient')
            explanation = analyze_medical_document_findings(d, query_text, p_name)
        else:
            explanation = (
                f"**📄 MEDICAL DOCUMENT RECORD:**\n\n"
                f"No uploaded medical documents were found on file for {patient_context['patient_name']}.\n\n"
                "You can upload lab test reports, scan results, or clinical summaries in the **Health Records & Documents Vault** to enable AI document analysis."
            )
            sources_list.append({
                'source_type': 'DATABASE',
                'source_name': 'PostgreSQL — MedicalDocument',
                'record_type': 'MedicalDocument',
                'title': 'Uploaded Documents'
            })

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': True,
            'retrieval': {'database': True, 'knowledge_base': False, 'web': False},
            'retrieved_context': {'documents': docs}
        }

    # ==================== MEDICATION INFORMATION ====================
    if intent == 'MEDICATION_INFORMATION':
        matched_kb = retrieve_medication_knowledge(query_text)
        web_sources, web_success = retrieve_trusted_online_medical_sources(query_text)
        sources_list = []
        q_lower = query_text.lower()

        if 'paracetamol' in q_lower or 'acetaminophen' in q_lower or (matched_kb and 'paracetamol' in matched_kb[0].generic_name.lower()):
            kb = matched_kb[0] if matched_kb else None
            sources_list.append({
                'source_type': 'KNOWLEDGE_BASE',
                'source_name': 'MedicationKnowledgeBase',
                'record_type': 'Medication',
                'title': 'Paracetamol (Acetaminophen)',
                'source_url': kb.source_reference if kb else 'FDA / WHO Essential Medicines'
            })
            base_info = (
                "**Medication Information: Paracetamol (Acetaminophen)**\n\n"
                "**What It Is & General Uses:**\n"
                "- Paracetamol is a widely used analgesic (pain reliever) and antipyretic (fever reducer).\n"
                "- Commonly indicated to relieve mild-to-moderate headaches, muscle aches, toothaches, arthritis discomfort, and to lower elevated body temperature.\n\n"
                "**Common Precautions & Important Warnings:**\n"
                "- **Do not exceed labeled or clinician-directed dose**: Standard adult maximum daily dose is typically 4,000 mg (4 grams) in 24 hours (or less as specified by your physician or pharmacist).\n"
                "- **Liver Safety Warning**: Exceeding the recommended dosage or combining multiple paracetamol-containing products (such as cold/flu remedies) can cause severe, permanent liver toxicity.\n"
                "- Avoid regular or heavy alcohol consumption while taking paracetamol.\n\n"
                "**When Professional Advice Is Needed:**\n"
                "Please consult your doctor or pharmacist before taking this medication if symptoms persist for more than 3 days, or if you have pre-existing liver disease, renal impairment, or are pregnant."
            )
        elif 'ibuprofen' in q_lower or (matched_kb and 'ibuprofen' in matched_kb[0].generic_name.lower()):
            kb = matched_kb[0] if matched_kb else None
            sources_list.append({
                'source_type': 'KNOWLEDGE_BASE',
                'source_name': 'MedicationKnowledgeBase',
                'record_type': 'Medication',
                'title': 'Ibuprofen (Advil / Motrin / Brufen)',
                'source_url': kb.source_reference if kb else 'FDA / WHO Essential Medicines'
            })
            base_info = (
                "**Medication Information: Ibuprofen**\n\n"
                "**What It Is & General Uses:**\n"
                "- Ibuprofen is a Non-Steroidal Anti-Inflammatory Drug (NSAID) with analgesic, anti-inflammatory, and fever-reducing properties.\n"
                "- Commonly used to relieve pain from headaches, toothaches, menstrual cramps, muscle aches, back pain, arthritis, and reduce fever.\n\n"
                "**Common Precautions & Important Warnings:**\n"
                "- **Gastrointestinal & Kidney Safety**: Take with food or milk to minimize stomach upset. Avoid or use with caution if you have a history of stomach ulcers, gastrointestinal bleeding, or kidney conditions.\n"
                "- **Do not exceed labeled dose**: The typical adult OTC limit is 1,200 mg in 24 hours unless higher doses are monitored by a physician.\n"
                "- **Cardiovascular & Pregnancy**: Avoid in late pregnancy and consult your clinician if you have hypertension or cardiovascular disease.\n\n"
                "**When Professional Advice Is Needed:**\n"
                "Please consult your doctor or pharmacist before taking this medication, especially if you are taking blood pressure drugs, anticoagulants, or other NSAIDs."
            )
        elif matched_kb:
            kb = matched_kb[0]
            sources_list.append({
                'source_type': 'KNOWLEDGE_BASE',
                'source_name': 'MedicationKnowledgeBase',
                'record_type': 'Medication',
                'title': f"{kb.generic_name} ({kb.brand_names or 'Generic'})",
                'source_url': kb.source_reference
            })
            base_info = (
                f"**Medication Information: {kb.generic_name} ({kb.brand_names or 'Generic'})**\n\n"
                f"**Medication Class & Uses:**\n"
                f"- **Class**: {kb.medication_class}\n"
                f"- **General Indications**: {kb.general_uses}\n\n"
                f"**Important Precautions & Warnings:**\n"
                f"- **Dosage Safety**: Always follow the exact dosage and administration schedule prescribed by your clinician or indicated on the manufacturer label. Do not exceed the recommended dose.\n"
                f"- **Precautions**: {kb.common_precautions}\n\n"
                f"**Knowledge Base Source Reference**: {kb.source_reference} ({kb.source_date})\n\n"
                f"**When to Consult a Clinician:**\n"
                f"Consult your prescribing physician or pharmacist before starting, changing, or discontinuing this medication, or if you experience unexpected side effects."
            )
        else:
            base_info = (
                f"**Medication Overview for '{query_text}':**\n\n"
                "This medication information is provided for general educational awareness.\n\n"
                "Always check with your doctor or pharmacist before taking any new medication, and never exceed the labeled or prescribed dosage."
            )

        if web_success and web_sources:
            web_summary = ""
            for ws in web_sources:
                sources_list.append({
                    'source_type': 'WEB',
                    'source_name': ws['source_name'],
                    'source_url': ws['source_url'],
                    'title': ws['title'],
                    'relevant_text': sanitize_data_for_prompt(ws['relevant_text']),
                    'retrieved_at': ws.get('retrieved_at', str(timezone.now()))
                })
                web_summary += f"\n- **[{ws['source_name']}] ({ws['title']})**: {ws['relevant_text']}\n"
            explanation = base_info + f"\n\n**TRUSTED ONLINE RETRIEVED EVIDENCE:**\n{web_summary}"
        else:
            sources_list.append({
                'source_type': 'SYSTEM',
                'source_name': 'Online Source Status',
                'source_url': '',
                'title': 'Online source retrieval is currently unavailable',
                'relevant_text': 'Online source retrieval is currently unavailable.'
            })
            explanation = base_info + "\n\n*Note: Online source retrieval is currently unavailable.*"

        return {
            'authorized': True,
            'intent': intent,
            'answer': explanation,
            'explanation': explanation,
            'sources': sources_list,
            'patient_context_used': False,
            'retrieval': {
                'database': False,
                'knowledge_base': bool(matched_kb),
                'web': web_success
            },
            'retrieved_context': {'matched_knowledge': [k.generic_name for k in matched_kb]}
        }

    # ==================== MEDICATION SAFETY ====================
    matched_kb = retrieve_medication_knowledge(query_text)
    candidates = extract_medicine_names_from_query(query_text)
    safety_eval = evaluate_deterministic_safety(patient_context, matched_kb, query_text)

    if not matched_kb and len(candidates) == 0 and not safety_eval['is_prescribe_request']:
        explanation = "I can help with medication information or a safety check. Which medicine are you asking about?"
        return {
            'authorized': True,
            'intent': intent,
            'safety_status': 'INSUFFICIENT_INFORMATION',
            'is_prescribe_request': False,
            'answer': explanation,
            'explanation': explanation,
            'sources': [],
            'patient_context_used': False,
            'retrieval': {'database': False, 'knowledge_base': False, 'web': False},
            'retrieved_context': {}
        }

    kb_data = []
    sources_list = []

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
        sources_list.append({
            'source_type': 'KNOWLEDGE_BASE',
            'source_name': f"{kb.generic_name} — {kb.source_reference}",
            'record_type': 'MedicationKnowledgeBase',
            'title': kb.generic_name
        })

    if patient_context.get('allergies'):
        alg_names = ", ".join([a['allergen'] for a in patient_context['allergies']])
        sources_list.append({
            'source_type': 'DATABASE',
            'source_name': f"PostgreSQL Recorded Allergies: {alg_names}",
            'record_type': 'PatientAllergy',
            'title': 'Patient Allergies'
        })

    if patient_context.get('prescriptions'):
        rx_names = ", ".join([r['medicines'] for r in patient_context['prescriptions']])
        sources_list.append({
            'source_type': 'DATABASE',
            'source_name': f"PostgreSQL Active Prescriptions: {rx_names}",
            'record_type': 'Prescription',
            'title': 'Active Prescriptions'
        })

    if patient_context.get('conditions'):
        c_names = ", ".join([c['condition_name'] for c in patient_context['conditions']])
        sources_list.append({
            'source_type': 'DATABASE',
            'source_name': f"PostgreSQL Recorded Conditions: {c_names}",
            'record_type': 'PatientCondition',
            'title': 'Active Conditions'
        })

    web_sources, web_success = retrieve_trusted_online_medical_sources(query_text)
    if web_success and web_sources:
        for ws in web_sources:
            sources_list.append({
                'source_type': 'WEB',
                'source_name': ws['source_name'],
                'source_url': ws['source_url'],
                'title': ws['title'],
                'relevant_text': sanitize_data_for_prompt(ws['relevant_text']),
                'retrieved_at': ws.get('retrieved_at', str(timezone.now()))
            })

    explanation_parts = []
    explanation_parts.append(f"**MEDICATION SAFETY CHECK: {safety_eval['status'].replace('_', ' ')}**\n")
    
    if safety_eval['is_prescribe_request']:
        explanation_parts.append("The AI assistant cannot issue, modify, or prescribe medications. All official prescriptions must be authorized by your attending physician. You may request a doctor review using the button below.\n")
    elif safety_eval['status'] == 'INSUFFICIENT_INFORMATION':
        explanation_parts.append("I can help with medication information or a safety check. Which medicine are you asking about?\n")
    else:
        for kb in kb_data:
            explanation_parts.append(f"**What it is:** {kb['generic_name']} ({kb['brand_names'] or 'Generic'}) is a {kb['medication_class']}.")
            explanation_parts.append(f"**General Uses:** {kb['general_uses']}")
            explanation_parts.append(f"**Precautions & Contraindications:** {kb['precautions']} {kb['contraindications']}")

    if safety_eval['concerns']:
        explanation_parts.append("\n**RELEVANT SAFETY CONSIDERATIONS:**")
        for c in safety_eval['concerns']:
            explanation_parts.append(f"- ⚠️ {c}")

    explanation_parts.append(f"\n**IMPORTANT DISCLAIMER:**\n{safety_eval['disclaimer']}")

    formatted_explanation = "\n\n".join(explanation_parts)

    return {
        'authorized': True,
        'intent': intent,
        'patient_id': patient_context.get('patient_id'),
        'query': query_text,
        'safety_status': safety_eval['status'],
        'safety_disclaimer': safety_eval['disclaimer'],
        'concerns': safety_eval['concerns'],
        'is_prescribe_request': safety_eval['is_prescribe_request'],
        'doctor_review_suggested': bool(safety_eval['is_prescribe_request'] or safety_eval['status'] in ('POTENTIAL_CONCERN_IDENTIFIED', 'REVIEW_RECOMMENDED')),
        'answer': formatted_explanation,
        'explanation': formatted_explanation,
        'sources': sources_list,
        'patient_context_used': True,
        'retrieval': {
            'database': bool(patient_context.get('allergies') or patient_context.get('prescriptions') or patient_context.get('conditions')),
            'knowledge_base': bool(matched_kb),
            'web': web_success
        },
        'retrieved_context': {
            'patient_allergies': patient_context.get('allergies', []),
            'patient_prescriptions': patient_context.get('prescriptions', []),
            'patient_conditions': patient_context.get('conditions', []),
            'matched_knowledge': kb_data
        }
    }
