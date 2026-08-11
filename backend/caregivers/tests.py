from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from caregivers.models import CaregiverPatientLink, CaregiverProfile

class CaregiverModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="pat_cg@gmail.com",
            password="password123",
            full_name="Patient CG",
            role="patient",
            device_id="NP-701"
        )
        self.patient_record = Patient.objects.create(
            id="P-701",
            name="Patient CG",
            age=65,
            gender="Female",
            room="701",
            condition="Elderly Care"
        )
        self.caregiver_user = CustomUser.objects.create_user(
            email="cg_prof@gmail.com",
            password="password123",
            full_name="Caregiver Professional",
            role="caregiver",
            agency_id="CG-701"
        )
        self.caregiver_profile = CaregiverProfile.objects.create(
            user=self.caregiver_user,
            caregiver_type="PROFESSIONAL",
            full_name="Caregiver Professional",
            qualification="Certified RN",
            years_of_experience=5,
            current_agency="CarePlus Health"
        )

    def test_caregiver_workflow(self):
        # 1. Caregiver Requests Connection
        self.client.force_authenticate(user=self.caregiver_user)
        res_req = self.client.post('/api/caregivers/requests', {'patientId': 'P-701'})
        self.assertEqual(res_req.status_code, status.HTTP_200_OK)
        link_id = res_req.data['id']

        # 2. Patient Reviews & Approves Connection
        self.client.force_authenticate(user=self.patient_user)
        res_appr = self.client.put(f'/api/caregivers/requests/{link_id}', {'approved': True})
        self.assertEqual(res_appr.status_code, status.HTTP_200_OK)
        self.assertTrue(CaregiverPatientLink.objects.get(id=link_id).is_approved)

        # 3. Patient Revokes Connection
        res_revoke = self.client.delete(f'/api/caregivers/requests/{link_id}')
        self.assertEqual(res_revoke.status_code, status.HTTP_200_OK)
        self.assertFalse(CaregiverPatientLink.objects.filter(id=link_id).exists())
