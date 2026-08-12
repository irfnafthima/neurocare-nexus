from django.test import TestCase
from doctors.utils import verify_doctor_credentials
from doctors.models import ReferenceDoctorRegistry, DoctorDisciplinaryRecord

class DoctorVerificationEngineTest(TestCase):
    def setUp(self):
        # Create test reference doctor records
        self.doc1 = ReferenceDoctorRegistry.objects.create(
            registration_number="REF-12345",
            council="Maharashtra Medical Council",
            doctor_name="Arvind Kulkarni",
            qualification="MBBS, MD",
            registration_year=2012
        )
        self.doc2 = ReferenceDoctorRegistry.objects.create(
            registration_number="REF-67890",
            council="Karnataka Medical Council",
            doctor_name="Ananya Sen",
            qualification="MBBS",
            registration_year=2018
        )
        # Disciplinary record for doc2
        DoctorDisciplinaryRecord.objects.create(
            disciplinary_id="DISC-101",
            doctor=self.doc2,
            registration_number="REF-67890",
            doctor_name="Ananya Sen",
            state_medical_council="Karnataka Medical Council",
            action_type="SUSPENSION",
            status="ACTIVE"
        )

    def test_1_exact_match(self):
        # Real registration number + matching name
        res = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertEqual(res['result'], 'EXACT_MATCH')
        self.assertIsNotNone(res['reference_record'])
        self.assertEqual(res['reference_record'].registration_number, "REF-12345")

    def test_2_likely_match(self):
        # Same registration number + normalized name variation
        res = verify_doctor_credentials("REF-12345", "Dr. Arvind K. Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertEqual(res['result'], 'LIKELY_MATCH')

    def test_3_wrong_name_mismatch(self):
        # Correct registration number + wrong name
        res = verify_doctor_credentials("REF-12345", "Sanjay Gupta", "Maharashtra Medical Council", "MBBS")
        self.assertEqual(res['result'], 'MISMATCH')

    def test_4_not_found(self):
        # Registration number not present in database
        res = verify_doctor_credentials("REF-99999", "Unknown Doctor", "Maharashtra Medical Council", "MBBS")
        self.assertEqual(res['result'], 'NOT_FOUND')
        self.assertIsNone(res['reference_record'])

    def test_5_active_disciplinary_block(self):
        # Correct doctor with active disciplinary block
        res = verify_doctor_credentials("REF-67890", "Ananya Sen", "Karnataka Medical Council", "MBBS")
        self.assertEqual(res['result'], 'STATUS_BLOCKED')
        self.assertEqual(res['checks']['disciplinary_check'], 'BLOCKED')

    def test_6_wrong_state_council(self):
        # Wrong state medical council
        res = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Tamil Nadu Medical Council", "MBBS")
        self.assertIn(res['result'], ['MANUAL_REVIEW', 'MISMATCH'])
        self.assertEqual(res['checks']['council_check'], 'MISMATCH')

    def test_7_qualification_mismatch(self):
        # Qualification mismatch
        res = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "BAMS")
        self.assertEqual(res['checks']['qualification_check'], 'MISMATCH')

    def test_8_reference_record_db_confirmation_and_dynamic_change(self):
        # 1. Verify exact match against current DB record
        res1 = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertEqual(res1['result'], 'EXACT_MATCH')
        self.assertEqual(res1['reference_record'].doctor_name, "Arvind Kulkarni")

        # 2. Dynamically modify the database record in PostgreSQL
        self.doc1.doctor_name = "Different Doctor Name"
        self.doc1.save()

        # 3. Run the exact same verification request again -> Result MUST change
        res2 = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertNotEqual(res2['result'], 'EXACT_MATCH')
        self.assertEqual(res2['result'], 'MISMATCH')
        self.assertEqual(res2['reference_record'].doctor_name, "Different Doctor Name")


from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.models import CustomUser
from doctors.models import DoctorProfile, DoctorPatientLink, DoctorConnectionRequest
from accounts.views import (
    RegisterView, AdminPendingDoctorsView, AdminDoctorApproveView, 
    AdminDoctorRejectView, AdminStatsView, AdminUserListView
)
from doctors.views import DoctorListView, ConnectionRequestListCreateView, ConnectionRequestDetailView

class AdminApprovalAndConnectionWorkflowTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # Create Admin
        self.admin_user = CustomUser.objects.create_user(
            email='admin_test@nexus.com', password='Password@123',
            full_name='Admin User', role='admin', approved=True, status='ACTIVE', access_key='ADM-90210'
        )
        # Create Reference Doctor for exact match
        self.ref_doc = ReferenceDoctorRegistry.objects.create(
            registration_number="SYN-REG-100",
            council="Delhi Medical Council",
            doctor_name="Dr. Reg Test",
            qualification="MBBS",
            registration_year=2015,
            registration_status="ACTIVE"
        )
        # Create Reference Doctor with Disciplinary Block
        self.ref_blocked = ReferenceDoctorRegistry.objects.create(
            registration_number="SYN-BLK-100",
            council="Delhi Medical Council",
            doctor_name="Dr. Blocked Test",
            qualification="MBBS",
            registration_year=2010,
            registration_status="SUSPENDED"
        )
        DoctorDisciplinaryRecord.objects.create(
            disciplinary_id="DISC-999",
            doctor=self.ref_blocked,
            registration_number="SYN-BLK-100",
            doctor_name="Dr. Blocked Test",
            state_medical_council="Delhi Medical Council",
            action_type="SUSPENSION",
            status="ACTIVE",
            remarks="Suspended for testing"
        )

    def test_admin_approval_queue_and_connection_workflow(self):
        # 1. Register a real Doctor
        doc_payload = {
            'fullName': 'Dr. Reg Test',
            'email': 'real_doctor@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': '9876543210',
            'medicalRegistrationNumber': 'UNKNOWN-999999',
            'stateMedicalCouncil': 'Delhi Medical Council',
            'qualification': 'MBBS'
        }
        reg_req = self.factory.post('/api/auth/register', doc_payload, format='json')
        reg_res = RegisterView.as_view()(reg_req)
        self.assertIn(reg_res.status_code, [200, 201])

        doc_user = CustomUser.objects.get(email='real_doctor@nexus.com')
        doc_profile = doc_user.doctor_profile

        # Test Requirement 1: Doctor initially appears in pending queue
        pending_req = self.factory.get('/api/admin/doctors/pending')
        force_authenticate(pending_req, user=self.admin_user)
        pending_res = AdminPendingDoctorsView.as_view()(pending_req)
        self.assertEqual(pending_res.status_code, 200)
        pending_ids = [d['id'] for d in pending_res.data]
        self.assertIn(doc_user.id, pending_ids)

        # Test Requirement 5 & 8: Approval updates PostgreSQL persistently
        appr_req = self.factory.put(f'/api/admin/doctors/{doc_user.id}/approve', {'notes': 'Verified'}, format='json')
        force_authenticate(appr_req, user=self.admin_user)
        appr_res = AdminDoctorApproveView.as_view()(appr_req, id=doc_user.id)
        self.assertEqual(appr_res.status_code, 200)

        doc_user.refresh_from_db()
        doc_profile.refresh_from_db()
        self.assertTrue(doc_user.approved)
        self.assertEqual(doc_user.status, 'ACTIVE')
        self.assertEqual(doc_profile.verification_status, 'VERIFIED')

        # Test Requirement 2: Approved doctor does NOT appear in pending queue
        pending_req2 = self.factory.get('/api/admin/doctors/pending')
        force_authenticate(pending_req2, user=self.admin_user)
        pending_res2 = AdminPendingDoctorsView.as_view()(pending_req2)
        pending_ids2 = [d['id'] for d in pending_res2.data]
        self.assertNotIn(doc_user.id, pending_ids2)

        # Test Requirement 7: Admin stats API reflects correct active & pending counts
        stats_req = self.factory.get('/api/admin/stats')
        force_authenticate(stats_req, user=self.admin_user)
        stats_res = AdminStatsView.as_view()(stats_req)
        self.assertEqual(stats_res.status_code, 200)
        self.assertGreaterEqual(stats_res.data['activeDoctors'], 1)

        # Test Requirement 12 & 13: Patient can search and request real approved doctor
        patient_payload = {
            'fullName': 'Real Patient Alpha',
            'email': 'real_patient_alpha@nexus.com',
            'password': 'Password@123',
            'role': 'patient',
            'phone': '9876543211',
            'deviceId': 'NP-101'
        }
        pat_reg_req = self.factory.post('/api/auth/register', patient_payload, format='json')
        RegisterView.as_view()(pat_reg_req)
        patient_user = CustomUser.objects.get(email='real_patient_alpha@nexus.com')

        search_req = self.factory.get('/api/doctors/search?query=Reg')
        force_authenticate(search_req, user=patient_user)
        search_res = DoctorListView.as_view()(search_req)
        self.assertEqual(search_res.status_code, 200)
        searched_doc_ids = [d['id'] for d in search_res.data]
        self.assertIn(doc_user.id, searched_doc_ids)

        conn_req = self.factory.post('/api/doctors/connect-requests', {'doctorNpi': doc_user.npi or doc_profile.medical_registration_number}, format='json')
        force_authenticate(conn_req, user=patient_user)
        conn_res = ConnectionRequestListCreateView.as_view()(conn_req)
        self.assertEqual(conn_res.status_code, 201)

        from doctors.views import get_patient_id_for_user
        pat_id = get_patient_id_for_user(patient_user)
        req_obj = DoctorConnectionRequest.objects.get(patient_id=pat_id)
        self.assertEqual(req_obj.status.upper(), 'PENDING')

        # Test Requirement 14 & 15: Doctor accepts request, DoctorPatientLink created exactly once
        accept_req = self.factory.put(f'/api/doctors/connect-requests/{req_obj.id}', {'status': 'ACCEPTED'}, format='json')
        force_authenticate(accept_req, user=doc_user)
        accept_res = ConnectionRequestDetailView.as_view()(accept_req, id=req_obj.id)
        self.assertEqual(accept_res.status_code, 200)

        links_count = DoctorPatientLink.objects.filter(doctor=doc_user, patient=req_obj.patient).count()
        self.assertEqual(links_count, 1)

    def test_rejection_and_blocked_doctor_enforcement(self):
        # Create unapproved doctor
        doc_user = CustomUser.objects.create_user(
            email='mismatch_test@nexus.com', password='Password@123',
            full_name='Dr. Mismatch', role='doctor', npi='SYN-REG-100', approved=False, status='PENDING'
        )
        DoctorProfile.objects.create(
            user=doc_user, medical_registration_number='SYN-REG-100',
            state_medical_council='Delhi Medical Council', qualification='MBBS', verification_status='UNDER_REVIEW'
        )

        # Test Requirement 3 & 6: Rejection updates DB and removes from pending queue
        rej_req = self.factory.put(f'/api/admin/doctors/{doc_user.id}/reject', {'reason': 'Invalid credentials'}, format='json')
        force_authenticate(rej_req, user=self.admin_user)
        rej_res = AdminDoctorRejectView.as_view()(rej_req, id=doc_user.id)
        self.assertEqual(rej_res.status_code, 200)

        doc_user.refresh_from_db()
        self.assertFalse(doc_user.approved)
        self.assertEqual(doc_user.status, 'REJECTED')
        self.assertEqual(doc_user.doctor_profile.verification_status, 'REJECTED')

        pending_req = self.factory.get('/api/admin/doctors/pending')
        force_authenticate(pending_req, user=self.admin_user)
        pending_res = AdminPendingDoctorsView.as_view()(pending_req)
        pending_ids = [d['id'] for d in pending_res.data]
        self.assertNotIn(doc_user.id, pending_ids)

        # Test Requirement 4: Blocked doctor cannot be approved normally
        blocked_doc_user = CustomUser.objects.create_user(
            email='blocked_test@nexus.com', password='Password@123',
            full_name='Dr. Blocked Test', role='doctor', npi='SYN-BLK-100', approved=False, status='PENDING'
        )
        DoctorProfile.objects.create(
            user=blocked_doc_user, medical_registration_number='SYN-BLK-100',
            state_medical_council='Delhi Medical Council', qualification='MBBS', verification_status='UNDER_REVIEW'
        )

        appr_req = self.factory.put(f'/api/admin/doctors/{blocked_doc_user.id}/approve', {'notes': 'Try approve'}, format='json')
        force_authenticate(appr_req, user=self.admin_user)
        appr_res = AdminDoctorApproveView.as_view()(appr_req, id=blocked_doc_user.id)
        self.assertEqual(appr_res.status_code, 400)
        self.assertIn("active disciplinary block", str(appr_res.data))

        # Test Requirement 9 & 10: User directory contains CustomUser accounts only
        users_req = self.factory.get('/api/admin/users')
        force_authenticate(users_req, user=self.admin_user)
        users_res = AdminUserListView.as_view()(users_req)
        self.assertEqual(users_res.status_code, 200)
        user_emails = [u['email'] for u in users_res.data]
        self.assertIn('admin_test@nexus.com', user_emails)
        self.assertIn('mismatch_test@nexus.com', user_emails)



