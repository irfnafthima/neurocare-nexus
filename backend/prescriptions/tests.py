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

    def test_prescription_patient_isolation(self):
        pat2_user = CustomUser.objects.create_user(email="patient2_rx@gmail.com", password="password123", full_name="Rx Patient Two", role="patient", device_id="NP-802")
        pat2_rec = Patient.objects.create(id="P-802", name="Rx Patient Two", age=35, gender="Female")
        DoctorPatientLink.objects.create(doctor=self.doctor_user, patient=pat2_rec)

        # Issue prescription for Patient P-801
        self.client.force_authenticate(user=self.doctor_user)
        self.client.post('/api/prescriptions', {'patientId': 'P-801', 'medicines': 'Atorvastatin 10mg'})

        # Patient 1 views -> receives 1 prescription
        self.client.force_authenticate(user=self.patient_user)
        res1 = self.client.get('/api/prescriptions')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data), 1)

        # Patient 2 views -> receives 0 prescriptions (No leakage)
        self.client.force_authenticate(user=pat2_user)
        res2 = self.client.get('/api/prescriptions')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.data), 0)

    def test_prescription_modification_prevention_and_caregiver_authorization(self):
        from caregivers.models import CaregiverPatientLink
        from accounts.models import AuditLog

        cg_auth = CustomUser.objects.create_user(email="cg_auth@gmail.com", password="password123", full_name="Auth Caregiver", role="caregiver")
        cg_unauth = CustomUser.objects.create_user(email="cg_unauth@gmail.com", password="password123", full_name="Unauth Caregiver", role="caregiver")
        CaregiverPatientLink.objects.create(caregiver=cg_auth, patient=self.patient_record, is_approved=True)

        # Doctor issues prescription
        self.client.force_authenticate(user=self.doctor_user)
        res_post = self.client.post('/api/prescriptions', {'patientId': 'P-801', 'medicines': 'Aspirin 81mg', 'dosage': '1 tablet'})
        rx_id = res_post.data['id']

        # Audit log verified
        self.assertTrue(AuditLog.objects.filter(action='Issued Prescription').exists())

        # Authorized Caregiver views prescription -> 200 OK
        self.client.force_authenticate(user=cg_auth)
        res_cg_view = self.client.get('/api/prescriptions?patientId=P-801')
        self.assertEqual(res_cg_view.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_cg_view.data), 1)

        # Unauthorized Caregiver views prescription -> 403 Forbidden
        self.client.force_authenticate(user=cg_unauth)
        res_unauth_view = self.client.get('/api/prescriptions?patientId=P-801')
        self.assertEqual(res_unauth_view.status_code, status.HTTP_403_FORBIDDEN)

        # Patient attempts to MODIFY doctor's prescription -> 403 Forbidden
        self.client.force_authenticate(user=self.patient_user)
        res_mod = self.client.put(f'/api/prescriptions/{rx_id}', {'medicines': 'Altered Medicine'})
        self.assertEqual(res_mod.status_code, status.HTTP_403_FORBIDDEN)

        # Patient attempts to DELETE doctor's prescription -> 403 Forbidden
        res_del = self.client.delete(f'/api/prescriptions/{rx_id}')
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

        # Authorized Caregiver attempts to MODIFY prescription -> 403 Forbidden
        self.client.force_authenticate(user=cg_auth)
        res_cg_mod = self.client.put(f'/api/prescriptions/{rx_id}', {'medicines': 'Altered Medicine'})
        self.assertEqual(res_cg_mod.status_code, status.HTTP_403_FORBIDDEN)
