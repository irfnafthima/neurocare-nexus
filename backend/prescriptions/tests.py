from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from doctors.models import DoctorPatientLink
from prescriptions.models import Prescription

class PrescriptionsModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="patient_rx@gmail.com",
            password="password123",
            full_name="Rx Patient",
            role="patient",
            device_id="NP-801"
        )
        self.patient_record = Patient.objects.create(
            id="P-801",
            name="Rx Patient",
            age=40,
            gender="Male",
            room="801",
            condition="Post-Op"
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doc_rx@gmail.com",
            password="password123",
            full_name="Dr. Rx Specialist",
            role="doctor",
            npi="REG-801"
        )
        self.unlinked_doctor = CustomUser.objects.create_user(
            email="unlinked_rx_doc@gmail.com",
            password="password123",
            full_name="Dr. Unlinked Rx",
            role="doctor",
            npi="REG-802"
        )

        DoctorPatientLink.objects.create(doctor=self.doctor_user, patient=self.patient_record)

    def test_prescription_creation_and_permission_rules(self):
        # 1. Linked Doctor creates prescription -> Success
        self.client.force_authenticate(user=self.doctor_user)
        res = self.client.post('/api/prescriptions', {
            'patientId': 'P-801',
            'medicines': 'Metoprolol 25mg',
            'dosage': '1 tablet',
            'frequency': 'Once daily',
            'duration': '14 days',
            'instructions': 'Take in morning with food'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Prescription.objects.count(), 1)

        # 2. Patient Views prescription -> Success
        self.client.force_authenticate(user=self.patient_user)
        res_view = self.client.get('/api/prescriptions')
        self.assertEqual(res_view.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_view.data), 1)

        # 3. Patient tries to CREATE prescription -> Denied 403
        res_patient_create = self.client.post('/api/prescriptions', {'patientId': 'P-801', 'medicines': 'Aspirin'})
        self.assertEqual(res_patient_create.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Unlinked Doctor tries to CREATE prescription -> Denied 403
        self.client.force_authenticate(user=self.unlinked_doctor)
        res_unlinked_create = self.client.post('/api/prescriptions', {'patientId': 'P-801', 'medicines': 'Aspirin'})
        self.assertEqual(res_unlinked_create.status_code, status.HTTP_403_FORBIDDEN)
