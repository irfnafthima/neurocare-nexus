from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from medical_records.models import PatientCondition, PatientMedication

class ChatbotModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="chat_pat@gmail.com",
            password="password123",
            full_name="Chat Patient",
            role="patient",
            device_id="NP-501"
        )
        self.patient_record = Patient.objects.create(
            id="P-501",
            name="Chat Patient",
            age=45,
            gender="Female",
            room="501",
            condition="Migraine"
        )
        PatientCondition.objects.create(patient=self.patient_record, condition_name="Chronic Migraine", status="Active")
        PatientMedication.objects.create(patient=self.patient_record, medicine_name="Sumatriptan", dosage="50 mg", frequency="As needed")

    def test_chatbot_context_retrieval(self):
        self.client.force_authenticate(user=self.patient_user)
        res = self.client.post('/api/chat', {'message': 'What are my active medications?'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('response', res.data)
        self.assertTrue(len(res.data['response']) > 0)
