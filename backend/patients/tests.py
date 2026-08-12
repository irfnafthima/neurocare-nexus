from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser, AuditLog
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorConnectionRequest, DoctorPatientLink, SyntheticNPI, DoctorProfile

class PatientsModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="pat_fam@gmail.com",
            password="password123",
            full_name="Patient Family Test",
            role="patient",
            device_id="NP-601"
        )
        self.patient_record = Patient.objects.create(
            id="P-601",
            name="Patient Family Test",
            age=50,
            gender="Male",
            room="601",
            condition="Post-Op Recovery"
        )
        self.family_user = CustomUser.objects.create_user(
            email="fam_test@gmail.com",
            password="password123",
            full_name="Family Member Test",
            role="family",
            patient_id="P-601"
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doc_link@gmail.com",
            password="password123",
            full_name="Dr. Attending Link",
            role="doctor",
            npi="REG-601"
        )
        self.synth_npi = SyntheticNPI.objects.create(
            npi="REG-601",
            name="Dr. Attending Link",
            hospital="Metro Clinic"
        )
        self.other_doctor_user = CustomUser.objects.create_user(
            email="doc_other@gmail.com",
            password="password123",
            full_name="Dr. Other Clinician",
            role="doctor",
            npi="REG-602"
        )
        self.synth_npi_other = SyntheticNPI.objects.create(
            npi="REG-602",
            name="Dr. Other Clinician",
            hospital="City Hospital"
        )

    def test_family_and_doctor_connection_workflows(self):
        # 1. Family Requests Connection
        self.client.force_authenticate(user=self.family_user)
        res_fam_req = self.client.post('/api/family/requests', {'patientId': 'P-601'})
        self.assertEqual(res_fam_req.status_code, status.HTTP_200_OK)
        fam_link_id = res_fam_req.data['id']

        # 2. Patient Approves Family Link
        self.client.force_authenticate(user=self.patient_user)
        res_fam_appr = self.client.put(f'/api/family/requests/{fam_link_id}', {'approved': True})
        self.assertEqual(res_fam_appr.status_code, status.HTTP_200_OK)
        self.assertTrue(FamilyPatientLink.objects.get(id=fam_link_id).is_approved)

        # 3. Patient Revokes Family Link
        res_fam_rev = self.client.delete(f'/api/family/requests/{fam_link_id}')
        self.assertEqual(res_fam_rev.status_code, status.HTTP_200_OK)
        self.assertFalse(FamilyPatientLink.objects.filter(id=fam_link_id).exists())

    def test_patient_doctor_request_lifecycle_and_security(self):
        # 1. Patient creates connection request
        self.client.force_authenticate(user=self.patient_user)
        res_req = self.client.post('/api/connections/requests', {'doctorNpi': 'REG-601'})
        self.assertEqual(res_req.status_code, status.HTTP_201_CREATED)
        req_id = res_req.data['id']

        # 2. Persisted in PostgreSQL & initial status is PENDING
        req_db = DoctorConnectionRequest.objects.get(id=req_id)
        self.assertEqual(req_db.status, 'Pending')
        self.assertEqual(req_db.patient_id, 'P-601')
        self.assertEqual(req_db.doctor_npi_id, 'REG-601')

        # 3. AuditLog created for request creation
        self.assertTrue(AuditLog.objects.filter(action='Dispatched Connection Request').exists())

        # 4. Duplicate request protection (patient cannot create duplicate pending request)
        res_dup = self.client.post('/api/connections/requests', {'doctorNpi': 'REG-601'})
        self.assertEqual(res_dup.status_code, status.HTTP_200_OK)
        self.assertEqual(DoctorConnectionRequest.objects.filter(patient_id='P-601', doctor_npi_id='REG-601').count(), 1)

        # 5. Patient status check via API refresh
        res_pat_get = self.client.get('/api/connections/requests')
        self.assertEqual(res_pat_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pat_get.data[0]['status'], 'Pending')

        # 6. Doctor retrieval (only assigned doctor gets their requests)
        self.client.force_authenticate(user=self.other_doctor_user)
        res_other_doc = self.client.get('/api/connections/requests')
        self.assertEqual(len(res_other_doc.data), 0) # Other doctor gets 0 requests

        self.client.force_authenticate(user=self.doctor_user)
        res_doc_get = self.client.get('/api/connections/requests')
        self.assertEqual(len(res_doc_get.data), 1)
        self.assertEqual(res_doc_get.data[0]['patientId'], 'P-601')

        # 7. Unlinked Doctor CANNOT access patient clinical data
        res_unlinked = self.client.get('/api/patients?doctorNpi=REG-602')
        self.assertEqual(res_unlinked.status_code, status.HTTP_200_OK)
        p_ids = [p['id'] for p in res_unlinked.data]
        self.assertNotIn('P-601', p_ids)

        # 8. Doctor accepts request
        res_appr = self.client.put(f'/api/connections/requests/{req_id}', {'status': 'Approved'})
        self.assertEqual(res_appr.status_code, status.HTTP_200_OK)

        # 9. ACCEPT creates exactly one DoctorPatientLink & status becomes Approved
        self.assertEqual(DoctorPatientLink.objects.filter(doctor=self.doctor_user, patient=self.patient_record).count(), 1)
        req_db.refresh_from_db()
        self.assertEqual(req_db.status, 'Approved')

        # 10. AuditLog created for approval
        self.assertTrue(AuditLog.objects.filter(action='Approved Connection Request').exists())

        # 11. Patient sees Approved/Connected status on API refresh
        self.client.force_authenticate(user=self.patient_user)
        res_pat_appr = self.client.get('/api/connections/requests')
        self.assertEqual(res_pat_appr.data[0]['status'], 'Approved')

        # 12. Doctor CAN now access linked patient
        self.client.force_authenticate(user=self.doctor_user)
        res_linked = self.client.get('/api/patients?doctorNpi=REG-601')
        self.assertEqual(res_linked.status_code, status.HTTP_200_OK)
        linked_p_ids = [p['id'] for p in res_linked.data]
        self.assertIn('P-601', linked_p_ids)

    def test_patient_doctor_decline_workflow(self):
        # Create new request
        self.client.force_authenticate(user=self.patient_user)
        res_req = self.client.post('/api/connections/requests', {'doctorNpi': 'REG-602'})
        req_id = res_req.data['id']

        # Doctor declines request
        self.client.force_authenticate(user=self.other_doctor_user)
        res_dec = self.client.put(f'/api/connections/requests/{req_id}', {'status': 'Declined'})
        self.assertEqual(res_dec.status_code, status.HTTP_200_OK)

        # DECLINE does not create DoctorPatientLink
        self.assertFalse(DoctorPatientLink.objects.filter(doctor=self.other_doctor_user, patient=self.patient_record).exists())

        # Patient receives DECLINED status
        self.client.force_authenticate(user=self.patient_user)
        res_pat_dec = self.client.get('/api/connections/requests')
        req_item = next(r for r in res_pat_dec.data if r['id'] == req_id)
        self.assertEqual(req_item['status'], 'Declined')

        # AuditLog created for decline
        self.assertTrue(AuditLog.objects.filter(action='Declined Connection Request').exists())

        # Doctor cannot access declined patient data
        self.client.force_authenticate(user=self.other_doctor_user)
        res_dec_access = self.client.get('/api/patients?doctorNpi=REG-602')
        p_ids = [p['id'] for p in res_dec_access.data]
        self.assertNotIn('P-601', p_ids)

class CaregiverAndFamilyE2EWorkflowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="pat_e2e@nexus.com",
            password="Password@123",
            full_name="Patient Real E2E",
            role="patient",
            device_id="NP-808"
        )
        self.patient_record = Patient.objects.create(
            id="P-808",
            name="Patient Real E2E",
            age=42,
            gender="Female",
            room="808",
            condition="Post-Op Recovery"
        )
        self.caregiver_user = CustomUser.objects.create_user(
            email="cg_e2e@nexus.com",
            password="Password@123",
            full_name="Caregiver Real E2E",
            role="caregiver",
            agency_id="CG-808"
        )
        self.family_user = CustomUser.objects.create_user(
            email="fam_e2e@nexus.com",
            password="Password@123",
            full_name="Family Real E2E",
            role="family",
            patient_id="P-808"
        )
        self.unrelated_caregiver = CustomUser.objects.create_user(
            email="cg_unrelated@nexus.com",
            password="Password@123",
            full_name="Unrelated Caregiver",
            role="caregiver",
            agency_id="CG-999"
        )
        self.unrelated_family = CustomUser.objects.create_user(
            email="fam_unrelated@nexus.com",
            password="Password@123",
            full_name="Unrelated Family",
            role="family"
        )

    def test_caregiver_and_family_complete_15_regression_requirements(self):
        # 1. Multiple patient identifiers can be handled (P-808, NP-808, Name)
        self.client.force_authenticate(user=self.caregiver_user)
        res1 = self.client.post('/api/caregivers/requests', {'patientId': 'NP-808'})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        cg_link_id = res1.data['id']

        # 2. Caregiver can create request for valid patient
        self.assertFalse(res1.data['isApproved'])
        self.assertEqual(res1.data['patientId'], 'P-808')

        # 3. Patient receives caregiver request in Access Controls
        self.client.force_authenticate(user=self.patient_user)
        res_ctrl1 = self.client.get('/api/patients/access-controls')
        self.assertEqual(res_ctrl1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_ctrl1.data['caregivers']), 1)
        self.assertEqual(res_ctrl1.data['caregivers'][0]['caregiverEmail'], 'cg_e2e@nexus.com')

        # 12. Pending caregiver cannot access clinical data
        self.client.force_authenticate(user=self.caregiver_user)
        res_cg_pending = self.client.get('/api/patients')
        self.assertEqual(len(res_cg_pending.data), 0)

        # 4. Patient approval creates/updates approved relationship
        self.client.force_authenticate(user=self.patient_user)
        res_cg_appr = self.client.put(f'/api/caregivers/requests/{cg_link_id}', {'approved': True})
        self.assertEqual(res_cg_appr.status_code, status.HTTP_200_OK)

        # Caregiver can now access permitted patient data
        self.client.force_authenticate(user=self.caregiver_user)
        res_cg_approved = self.client.get('/api/patients')
        self.assertEqual(len(res_cg_approved.data), 1)
        self.assertEqual(res_cg_approved.data[0]['name'], 'Patient Real E2E')

        # 6. Revoked caregiver loses access
        self.client.force_authenticate(user=self.patient_user)
        res_cg_rev = self.client.delete(f'/api/caregivers/requests/{cg_link_id}')
        self.assertEqual(res_cg_rev.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.caregiver_user)
        res_cg_revoked = self.client.get('/api/patients')
        self.assertEqual(len(res_cg_revoked.data), 0)

        # 7. Family can create request using patient name
        self.client.force_authenticate(user=self.family_user)
        res_fam_req = self.client.post('/api/family/requests', {'patientId': 'Patient Real E2E'})
        self.assertEqual(res_fam_req.status_code, status.HTTP_200_OK)
        fam_link_id = res_fam_req.data['id']

        # 8. Patient receives family request
        self.client.force_authenticate(user=self.patient_user)
        res_ctrl2 = self.client.get('/api/patients/access-controls')
        self.assertEqual(len(res_ctrl2.data['familyMembers']), 1)
        self.assertEqual(res_ctrl2.data['familyMembers'][0]['familyEmail'], 'fam_e2e@nexus.com')

        # 13. Pending family cannot access protected patient context
        self.client.force_authenticate(user=self.family_user)
        res_fam_pending = self.client.get('/api/patients')
        self.assertEqual(len(res_fam_pending.data), 0)

        # 9. Patient approval creates approved FamilyPatientLink
        self.client.force_authenticate(user=self.patient_user)
        res_fam_appr = self.client.put(f'/api/family/requests/{fam_link_id}', {'approved': True})
        self.assertEqual(res_fam_appr.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.family_user)
        res_fam_appr_list = self.client.get('/api/patients')
        self.assertEqual(len(res_fam_appr_list.data), 1)

        # 11. Revoked family loses access
        self.client.force_authenticate(user=self.patient_user)
        res_fam_rev = self.client.delete(f'/api/family/requests/{fam_link_id}')
        self.assertEqual(res_fam_rev.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.family_user)
        res_fam_rev_list = self.client.get('/api/patients')
        self.assertEqual(len(res_fam_rev_list.data), 0)

        # 14 & 15. Unrelated caregiver & family member cannot access patient
        self.client.force_authenticate(user=self.unrelated_caregiver)
        self.assertEqual(len(self.client.get('/api/patients').data), 0)

        self.client.force_authenticate(user=self.unrelated_family)
        self.assertEqual(len(self.client.get('/api/patients').data), 0)

