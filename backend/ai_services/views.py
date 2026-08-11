import os
import time
import requests
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import CustomUser

chat_rate_limits = {}

def get_simulated_chatbot_response(message, user_context):
    msg_lower = message.lower()
    
    if 'appointment' in msg_lower:
        if user_context['appointments']:
            lst = "\n".join([f"- {a['details']} at {a['time']}" for a in user_context['appointments']])
            return f"According to your files, you have the following upcoming appointments:\n{lst}\n\nIs there anything specific you would like to prepare for these sessions?"
        return "I don't see any upcoming appointments scheduled in your local file. If you need to book a consultation, please contact Riverside General Hospital administration."
        
    if any(x in msg_lower for x in ['alert', 'vitals', 'heart', 'spo2', 'pulse']):
        if user_context['alerts']:
            recent = user_context['alerts'][0]
            return f"Checking your wearable telemetry:\n- Heart Rate: {recent['heart_rate'] or 'N/A'} BPM\n- SpO₂: {recent['spo2'] or 'N/A'}%\n- Temperature: {recent['temperature'] or 'N/A'}°C\n\nYour biometric streams appear stable. Please note that this is a simulated reading. If you are experiencing symptoms, please seek professional care."
        return "No active telemetry alerts are on file for your wearable node. Ensure your NeuroPatch device is correctly connected and synced."
        
    if 'fall' in msg_lower:
        return "The MPU6050 accelerometer sensor tracks sudden changes in velocity. I do not see any fall events logged in your audit ledger. Always wear the device securely on your wrist."
        
    return f"Hello {user_context['name']}! I am your NeuroCare clinical assistant. I can help explain your wearable vitals (heart rate, SpO₂), track upcoming consultations, or answer general wellness questions. \n\n*General questions only — not medical advice.*"

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message')
        if not message or str(message).strip() == '':
            return Response("Message body is required.", status=status.HTTP_400_BAD_REQUEST)

        user_id = request.user.id
        role = request.user.role
        name = request.user.full_name

        # 1. Enforce rate limiting: max 20 requests per hour per user
        now = time.time()
        limit_window = 3600 # 1 hour
        limit_count = 20

        if user_id not in chat_rate_limits:
            chat_rate_limits[user_id] = {'count': 1, 'window_start': now}
        else:
            limit = chat_rate_limits[user_id]
            if now - limit['window_start'] > limit_window:
                limit['count'] = 1
                limit['window_start'] = now
            else:
                if limit['count'] >= limit_count:
                    return Response("Rate limit exceeded: Max 20 chatbot queries per hour.", status=status.HTTP_429_TOO_MANY_REQUESTS)
                limit['count'] += 1

        try:
            patient_id = None
            patient_context_str = ''
            user_context = {'name': name, 'role': role, 'appointments': [], 'alerts': []}

            # 2. Determine authorized patient ID based on role permissions
            if role == 'patient':
                patient_id = request.user.device_id.upper().replace('NP-', 'P-') if request.user.device_id else 'P-100'
            elif role == 'family':
                from patients.models import FamilyPatientLink
                link = FamilyPatientLink.objects.filter(family=request.user, is_approved=True).first()
                if link:
                    patient_id = link.patient_id
            elif role == 'caregiver':
                from caregivers.models import CaregiverPatientLink
                link = CaregiverPatientLink.objects.filter(caregiver=request.user, is_approved=True).first()
                if link:
                    patient_id = link.patient_id
            elif role == 'doctor':
                from doctors.models import DoctorPatientLink
                link = DoctorPatientLink.objects.filter(doctor=request.user).first()
                if link:
                    patient_id = link.patient_id

            # 3. Query PostgreSQL health records if authorized patient ID exists
            if patient_id:
                from patients.models import Patient
                from medical_records.models import (
                    PatientCondition, PatientAllergy, PatientMedication, 
                    PatientConsultation, NextConsultation, MedicalDocument
                )
                from monitoring.models import SensorReading

                patient = Patient.objects.filter(id=patient_id).first()
                if patient:
                    conditions = list(PatientCondition.objects.filter(patient=patient).values_list('condition_name', flat=True))
                    allergies = list(PatientAllergy.objects.filter(patient=patient, is_active=True).values_list('allergen', flat=True))
                    meds = list(PatientMedication.objects.filter(patient=patient, is_active=True).values_list('medicine_name', 'dosage', 'frequency'))
                    consultations = list(PatientConsultation.objects.filter(patient=patient).values_list('reason', 'consultation_date'))
                    next_c = NextConsultation.objects.filter(patient=patient).order_by('-consultation_date').first()
                    docs = list(MedicalDocument.objects.filter(patient=patient).values_list('title', 'document_type'))
                    telemetry = SensorReading.objects.filter(patient=patient).order_by('-timestamp').first()

                    cond_str = ", ".join(conditions) if conditions else "None recorded"
                    allg_str = ", ".join(allergies) if allergies else "No known allergies"
                    med_str = ", ".join([f"{m[0]} ({m[1]}, {m[2]})" for m in meds]) if meds else "No active medications"
                    cons_str = ", ".join([f"{c[0]} on {c[1]}" for c in consultations]) if consultations else "None on file"
                    next_str = f"{next_c.consultation_date} ({next_c.time}) with {next_c.doctor_name or 'Clinician'}" if next_c else "None scheduled"
                    doc_str = ", ".join([f"{d[0]} ({d[1]})" for d in docs]) if docs else "No documents uploaded"
                    vitals_str = f"Heart Rate: {telemetry.heart_rate} BPM, SpO2: {telemetry.spo2}%, Temp: {telemetry.temperature}°C" if telemetry else "No live vitals stream"

                    patient_context_str = (
                        f"\n\nAUTHORISED PATIENT HEALTH FILE (Patient ID: {patient.id}, Name: {patient.name}):\n"
                        f"- Current Conditions: {cond_str}\n"
                        f"- Active Allergies: {allg_str}\n"
                        f"- Prescribed Medications & Instructions: {med_str}\n"
                        f"- Recent Consultations: {cons_str}\n"
                        f"- Scheduled Next Consultation: {next_str}\n"
                        f"- Uploaded Medical Reports: {doc_str}\n"
                        f"- Latest Biometric Telemetry: {vitals_str}\n"
                    )

            # 4. Assemble Safety System Prompt
            system_prompt = f"""You are the NeuroCare Nexus NON-CLINICAL SUPPORT ASSISTANT, an empathetic, professional health companion.
- User Role: {role}
- User Name: {name}{patient_context_str}

CRITICAL SAFETY & SCOPE RULES:
1. You are a NON-CLINICAL SUPPORT ASSISTANT. You CANNOT diagnose diseases, prescribe medications, or independently alter medication dosages.
2. If the user presents urgent or life-threatening symptoms (e.g. chest pain, severe dyspnea, stroke signs), immediately instruct them to call 112 or emergency services.
3. You MAY summarize stored health records, explain medication instructions in plain language, remind about upcoming consultations, and summarize uploaded document titles/metadata.
4. Maintain a warm, reassuring, and concise tone with clean markdown formatting."""

            # 5. Request completion from LLM API or fallback to simulation
            assistant_message = ""
            api_key = os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY')

            if api_key:
                is_groq = bool(os.getenv('GROQ_API_KEY'))
                url = 'https://api.groq.com/openai/v1/chat/completions' if is_groq else 'https://api.openai.com/v1/chat/completions'
                model = 'llama-3.3-70b-specdec' if is_groq else 'gpt-4o-mini'
                
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }
                payload = {
                    'model': model,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': message}
                    ],
                    'temperature': 0.7
                }
                try:
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        assistant_message = data['choices'][0]['message']['content']
                    else:
                        assistant_message = get_simulated_chatbot_response(message, user_context)
                except Exception as e:
                    assistant_message = get_simulated_chatbot_response(message, user_context)
            else:
                assistant_message = get_simulated_chatbot_response(message, user_context)

            return Response({'response': assistant_message}, status=status.HTTP_200_OK)
        except Exception as e:
            print("Chatbot API Error:", e)
            return Response("Failed to process request.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
