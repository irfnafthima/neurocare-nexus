from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from doctors.models import DoctorPatientLink, SyntheticNPI
from caregivers.models import CaregiverPatientLink
from patients.models import FamilyPatientLink
from medical_records.models import (
    PatientCondition, PatientAllergy, PatientMedication, 
    PatientConsultation, NextConsultation, MedicalDocument
)

class MedicalRecordsModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="patient1@gmail.com",
            password="password123",
            full_name="Test Patient One",
            role="patient",
            device_id="NP-901"
        )
        self.patient_record = Patient.objects.create(
            id="P-901",
            name="Test Patient One",
            age=30,
            gender="Female",
            room="901",
            condition="Stable"
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doc1@gmail.com",
            password="password123",
            full_name="Dr. Attending Doctor",
            role="doctor",
            npi="REG-901"
        )
        self.unlinked_doctor = CustomUser.objects.create_user(
            email="unlinked_doc@gmail.com",
            password="password123",
            full_name="Dr. Unlinked",
            role="doctor",
            npi="REG-902"
        )
        self.caregiver_user = CustomUser.objects.create_user(
            email="cg1@gmail.com",
            password="password123",
            full_name="Caregiver One",
            role="caregiver"
        )
        self.family_user = CustomUser.objects.create_user(
            email="fam1@gmail.com",
            password="password123",
            full_name="Family Member One",
            role="family",
            patient_id="P-901"
        )

        # Approved links
        DoctorPatientLink.objects.create(doctor=self.doctor_user, patient=self.patient_record)
        CaregiverPatientLink.objects.create(caregiver=self.caregiver_user, patient=self.patient_record, is_approved=True)
        FamilyPatientLink.objects.create(family=self.family_user, patient=self.patient_record, is_approved=True)

    def test_health_record_crud(self):
        self.client.force_authenticate(user=self.patient_user)

        # 1. Add Condition
        res = self.client.post('/api/health-records', {'type': 'condition', 'conditionName': 'Hypertension', 'status': 'Active'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientCondition.objects.count(), 1)

        # 2. Add Allergy
        res = self.client.post('/api/health-records', {'type': 'allergy', 'allergen': 'Penicillin', 'severity': 'Severe'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientAllergy.objects.count(), 1)

        # 3. Add Medication
        res = self.client.post('/api/health-records', {'type': 'medication', 'medicineName': 'Amlodipine', 'dosage': '5 mg', 'frequency': 'Daily'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientMedication.objects.count(), 1)

        # 4. Add Consultation
        res = self.client.post('/api/health-records', {'type': 'consultation', 'consultationDate': '2026-08-10', 'reason': 'BP Review'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientConsultation.objects.count(), 1)

        # 5. Add Next Consultation
        res = self.client.post('/api/health-records', {'type': 'next_consultation', 'consultationDate': '2026-09-01', 'time': '10:30 AM', 'facility': 'City Hospital'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NextConsultation.objects.count(), 1)

        # 6. Retrieve Health Records
        res = self.client.get('/api/health-records')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['conditions']), 1)
        self.assertEqual(len(res.data['allergies']), 1)

    def test_secure_document_upload_and_access(self):
        # 1. Patient Uploads Document
        self.client.force_authenticate(user=self.patient_user)
        dummy_file = SimpleUploadedFile("report.pdf", b"PDF_CONTENT_TEST_DATA", content_type="application/pdf")
        res = self.client.post('/api/documents', {'title': 'Blood Test August', 'documentType': 'Blood Test', 'file': dummy_file})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        doc_id = res.data['id']

        # 2. Linked Doctor can retrieve document metadata and download file
        self.client.force_authenticate(user=self.doctor_user)
        res_get = self.client.get(f'/api/documents?patientId=P-901')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_get.data), 1)

        res_dl = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_dl.status_code, status.HTTP_200_OK)

        # 3. Unlinked Doctor is DENIED access
        self.client.force_authenticate(user=self.unlinked_doctor)
        res_unauth = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_unauth.status_code, status.HTTP_403_FORBIDDEN)
