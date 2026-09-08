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
            'registrationYear': '2015',
            'experience': '5',
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


class DoctorPatientContextIsolationTests(TestCase):
    def setUp(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from accounts.models import CustomUser
        from patients.models import Patient
        from doctors.models import DoctorPatientLink
        from medical_records.models import PatientCondition, PatientAllergy, MedicalDocument, VitalMeasurement
        from medical_records.views import PatientHealthRecordView
        from ai_services.views import DoctorPatientSummaryView

        self.factory = APIRequestFactory()
        self.hr_view = PatientHealthRecordView.as_view()
        self.ai_summary_view = DoctorPatientSummaryView.as_view()

        # Create doctor
        self.doctor = CustomUser.objects.create_user(
            email='dr_context@nexus.com',
            password='Password@123',
            full_name='Dr. Context Specialist',
            role='doctor',
            approved=True
        )

        # Create 3 distinct patients
        self.p18 = Patient.objects.create(
            id='P-18', name='Sara John', age=42, gender='Female',
            room='101', condition='Post-stroke rehabilitation', blood_group='O+'
        )
        self.p13 = Patient.objects.create(
            id='P-13', name='Elizabeth Mathew', age=58, gender='Female',
            room='102', condition='Parkinsons Stage 2', blood_group='A+'
        )
        self.p50 = Patient.objects.create(
            id='P-50', name='Mathew S', age=65, gender='Male',
            room='103', condition='Refractory Epilepsy', blood_group='B+'
        )

        # Unlinked patient
        self.p_unlinked = Patient.objects.create(
            id='P-99', name='Unlinked Patient', age=30, gender='Male',
            room='104', condition='Healthy baseline'
        )

        # Link doctor to P-18, P-13, P-50
        DoctorPatientLink.objects.create(doctor=self.doctor, patient=self.p18)
        DoctorPatientLink.objects.create(doctor=self.doctor, patient=self.p13)
        DoctorPatientLink.objects.create(doctor=self.doctor, patient=self.p50)

        # Populate distinct clinical data
        PatientCondition.objects.create(patient=self.p18, condition_name="Stroke Recovery Hemiparesis", status="Active")
        PatientAllergy.objects.create(patient=self.p18, allergen="Penicillin G", reaction="Anaphylaxis", severity="Severe")

        PatientCondition.objects.create(patient=self.p13, condition_name="Tremor Dominant Parkinsonism", status="Active")
        PatientAllergy.objects.create(patient=self.p13, allergen="Sulfa Drugs", reaction="Skin Rash", severity="Moderate")

        PatientCondition.objects.create(patient=self.p50, condition_name="Focal Seizure Disorder", status="Active")

    def test_01_authorized_doctor_fetches_p18_correctly(self):
        from rest_framework.test import force_authenticate
        req = self.factory.get('/api/health-records?patientId=P-18')
        force_authenticate(req, user=self.doctor)
        res = self.hr_view(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['patientId'], 'P-18')
        self.assertEqual(res.data['patient']['name'], 'Sara John')
        self.assertEqual(res.data['patientName'], 'Sara John')
        self.assertTrue(any(c['condition_name'] == "Stroke Recovery Hemiparesis" for c in res.data['conditions']))
        self.assertFalse(any(c['condition_name'] == "Tremor Dominant Parkinsonism" for c in res.data['conditions']))

    def test_02_authorized_doctor_fetches_p13_correctly(self):
        from rest_framework.test import force_authenticate
        req = self.factory.get('/api/health-records?patientId=P-13')
        force_authenticate(req, user=self.doctor)
        res = self.hr_view(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['patientId'], 'P-13')
        self.assertEqual(res.data['patient']['name'], 'Elizabeth Mathew')
        self.assertTrue(any(c['condition_name'] == "Tremor Dominant Parkinsonism" for c in res.data['conditions']))
        self.assertFalse(any(c['condition_name'] == "Stroke Recovery Hemiparesis" for c in res.data['conditions']))

    def test_03_authorized_doctor_fetches_p50_correctly(self):
        from rest_framework.test import force_authenticate
        req = self.factory.get('/api/health-records?patientId=P-50')
        force_authenticate(req, user=self.doctor)
        res = self.hr_view(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['patientId'], 'P-50')
        self.assertEqual(res.data['patient']['name'], 'Mathew S')
        self.assertTrue(any(c['condition_name'] == "Focal Seizure Disorder" for c in res.data['conditions']))

    def test_04_doctor_accessing_unlinked_patient_denied_403(self):
        from rest_framework.test import force_authenticate
        req = self.factory.get('/api/health-records?patientId=P-99')
        force_authenticate(req, user=self.doctor)
        res = self.hr_view(req)
        self.assertEqual(res.status_code, 403)

    def test_05_invalid_patient_returns_404(self):
        from rest_framework.test import force_authenticate
        req = self.factory.get('/api/health-records?patientId=P-NONEXISTENT')
        force_authenticate(req, user=self.doctor)
        res = self.hr_view(req)
        self.assertEqual(res.status_code, 404)

    def test_06_manual_vital_saved_for_selected_patient_with_provenance(self):
        from rest_framework.test import force_authenticate
        from medical_records.models import VitalMeasurement
        payload = {
            'type': 'manual_vital',
            'patientId': 'P-18',
            'heartRate': 78.0,
            'spo2': 98.0,
            'temperature': 36.9,
            'notes': 'Recorded during clinical ward review'
        }
        req = self.factory.post('/api/health-records', payload, format='json')
        force_authenticate(req, user=self.doctor)
        res = self.hr_view(req)
        self.assertEqual(res.status_code, 201)
        
        # Verify saved record provenance
        vital = VitalMeasurement.objects.filter(patient=self.p18).order_by('-id').first()
        self.assertIsNotNone(vital)
        self.assertEqual(vital.patient_id, 'P-18')
        self.assertEqual(vital.source, 'MANUAL')
        self.assertEqual(vital.entered_by, self.doctor)
        self.assertEqual(vital.heart_rate, 78.0)

    def test_07_ai_patient_summary_scoped_strictly_to_selected_patient(self):
        from rest_framework.test import force_authenticate
        req = self.factory.get('/api/ai/patient-summary/P-18')
        force_authenticate(req, user=self.doctor)
        res = self.ai_summary_view(req, patient_id='P-18')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['patient_id'], 'P-18')
        self.assertEqual(res.data['patient_name'], 'Sara John')
        self.assertIn('Sara John', res.data['note'])
        self.assertIn('Penicillin G', res.data['note'])
        self.assertNotIn('Elizabeth Mathew', res.data['note'])


class DoctorRegistrationVerificationFeedbackTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        # Create Admin User
        self.admin = CustomUser.objects.create_user(
            email='admin_audit@nexus.com', password='Password@123',
            full_name='Admin Lead', role='admin', approved=True, status='ACTIVE', access_key='ADM-12345'
        )
        # Create Reference Record for Doctor A
        self.ref_match = ReferenceDoctorRegistry.objects.create(
            registration_number="MH-2015-8888",
            council="Maharashtra Medical Council",
            doctor_name="Dr. Sameer Joshi",
            qualification="MBBS, MS",
            registration_year=2015,
            registration_status="ACTIVE"
        )
        # Create Reference Record for Doctor C & D
        self.ref_council_test = ReferenceDoctorRegistry.objects.create(
            registration_number="KA-2016-9999",
            council="Karnataka Medical Council",
            doctor_name="Dr. Radhika Sharma",
            qualification="MBBS, MD",
            registration_year=2016,
            registration_status="ACTIVE"
        )
        # Create Existing Approved Doctor G
        self.existing_doc = CustomUser.objects.create_user(
            email='dr.nishant@nexus.com', password='Password@123',
            full_name='Dr. Nishant Raja', role='doctor', approved=True, status='ACTIVE', npi='DOC-NISHANT-01'
        )
        DoctorProfile.objects.create(
            user=self.existing_doc,
            medical_registration_number='DOC-NISHANT-01',
            state_medical_council='Maharashtra Medical Council',
            qualification='MBBS, MD',
            verification_status='VERIFIED'
        )

    def test_case_a_matching_reference_registration_and_blocked_login(self):
        """TEST A: Valid doctor + matching reference details -> category: MATCH, login blocked with PENDING, pending in admin queue"""
        payload = {
            'fullName': 'Dr. Sameer Joshi',
            'email': 'sameer.joshi@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': '9876543210',
            'medicalRegistrationNumber': 'MH-2015-8888',
            'stateMedicalCouncil': 'Maharashtra Medical Council',
            'registrationYear': '2015',
            'experience': '8',
            'qualification': 'MBBS, MS'
        }
        reg_req = self.factory.post('/api/auth/register', payload, format='json')
        reg_res = RegisterView.as_view()(reg_req)
        self.assertEqual(reg_res.status_code, 200)
        self.assertEqual(reg_res.data['category'], 'MATCH')
        self.assertEqual(reg_res.data['title'], 'Professional Verification Successful')
        self.assertEqual(reg_res.data['breakdown']['Account Registration'], 'COMPLETED')
        self.assertEqual(reg_res.data['breakdown']['Professional Verification'], 'VERIFIED')
        self.assertEqual(reg_res.data['breakdown']['Admin Approval'], 'PENDING')
        self.assertTrue(reg_res.data['isPendingApproval'])

        # Doctor login attempt must return 403 Forbidden with PENDING status
        login_req = self.factory.post('/api/auth/login', {
            'email': 'sameer.joshi@nexus.com',
            'password': 'Password@123',
            'role': 'doctor'
        }, format='json')
        from accounts.views import LoginView
        login_res = LoginView.as_view()(login_req)
        self.assertEqual(login_res.status_code, 403)
        self.assertEqual(login_res.data['status'], 'PENDING')
        self.assertEqual(login_res.data['category'], 'VERIFIED_WAITING_ADMIN')
        self.assertEqual(login_res.data['title'], 'Administrator Approval Pending')

        # Check doctor appears in admin pending queue
        pending_req = self.factory.get('/api/admin/doctors/pending')
        force_authenticate(pending_req, user=self.admin)
        pending_res = AdminPendingDoctorsView.as_view()(pending_req)
        self.assertEqual(pending_res.status_code, 200)
        doc_user = CustomUser.objects.get(email='sameer.joshi@nexus.com')
        self.assertIn(doc_user.id, [d['id'] for d in pending_res.data])

    def test_case_b_registration_number_not_found(self):
        """TEST B: Registration number not found -> category: NOT_FOUND, login blocked with UNDER_REVIEW"""
        payload = {
            'fullName': 'Dr. Unknown Doc',
            'email': 'unknown.doc@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': '9876543211',
            'medicalRegistrationNumber': 'UNKNOWN-REG-0000',
            'stateMedicalCouncil': 'Maharashtra Medical Council',
            'registrationYear': '2019',
            'experience': '4',
            'qualification': 'MBBS'
        }
        reg_req = self.factory.post('/api/auth/register', payload, format='json')
        reg_res = RegisterView.as_view()(reg_req)
        self.assertEqual(reg_res.status_code, 200)
        self.assertEqual(reg_res.data['category'], 'NOT_FOUND')
        self.assertEqual(reg_res.data['title'], 'Additional Verification Required')
        self.assertEqual(reg_res.data['breakdown']['Registration Verification'], 'REVIEW REQUIRED')

        # Login attempt must return 403 Forbidden with UNDER_REVIEW status
        login_req = self.factory.post('/api/auth/login', {
            'email': 'unknown.doc@nexus.com',
            'password': 'Password@123',
            'role': 'doctor'
        }, format='json')
        from accounts.views import LoginView
        login_res = LoginView.as_view()(login_req)
        self.assertEqual(login_res.status_code, 403)
        self.assertEqual(login_res.data['status'], 'UNDER_REVIEW')
        self.assertEqual(login_res.data['category'], 'UNDER_REVIEW')
        self.assertEqual(login_res.data['title'], 'Verification Under Review')

    def test_case_c_council_mismatch(self):
        """TEST C: Registration number found + council mismatch -> category: COUNCIL_MISMATCH"""
        payload = {
            'fullName': 'Dr. Radhika Sharma',
            'email': 'radhika.council@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': '9876543212',
            'medicalRegistrationNumber': 'KA-2016-9999',
            'stateMedicalCouncil': 'Delhi Medical Council',  # Expected: Karnataka Medical Council
            'registrationYear': '2016',
            'experience': '7',
            'qualification': 'MBBS, MD'
        }
        reg_req = self.factory.post('/api/auth/register', payload, format='json')
        reg_res = RegisterView.as_view()(reg_req)
        self.assertEqual(reg_res.status_code, 200)
        self.assertEqual(reg_res.data['category'], 'COUNCIL_MISMATCH')
        self.assertEqual(reg_res.data['title'], 'Medical Council Verification Required')
        self.assertEqual(reg_res.data['breakdown']['Medical Council'], 'REVIEW REQUIRED')

    def test_case_d_identity_mismatch(self):
        """TEST D: Identity / professional mismatch -> category: DETAILS_MISMATCH"""
        payload = {
            'fullName': 'Dr. Wrong Name',
            'email': 'wrong.name@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': '9876543213',
            'medicalRegistrationNumber': 'KA-2016-9999',
            'stateMedicalCouncil': 'Karnataka Medical Council',
            'registrationYear': '2016',
            'experience': '7',
            'qualification': 'MBBS, MD'
        }
        reg_req = self.factory.post('/api/auth/register', payload, format='json')
        reg_res = RegisterView.as_view()(reg_req)
        self.assertEqual(reg_res.status_code, 200)
        self.assertEqual(reg_res.data['category'], 'DETAILS_MISMATCH')
        self.assertEqual(reg_res.data['title'], 'Professional Details Require Review')
        self.assertEqual(reg_res.data['breakdown']['Professional Details'], 'REVIEW REQUIRED')

    def test_case_e_invalid_phone_rejected_without_account_creation(self):
        """TEST E: Invalid phone -> 400 Bad Request, no account created"""
        payload = {
            'fullName': 'Dr. Test Failure',
            'email': 'failure.phone@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': 'hdjdj267',  # Invalid phone
            'medicalRegistrationNumber': 'MH-2015-8888',
            'stateMedicalCouncil': 'Maharashtra Medical Council',
            'registrationYear': '2015',
            'experience': '5',
            'qualification': 'MBBS'
        }
        reg_req = self.factory.post('/api/auth/register', payload, format='json')
        reg_res = RegisterView.as_view()(reg_req)
        self.assertEqual(reg_res.status_code, 400)
        self.assertFalse(CustomUser.objects.filter(email='failure.phone@nexus.com').exists())

    def test_case_f_admin_approval_enables_successful_login(self):
        """TEST F: Admin approves doctor -> doctor logs in successfully -> 200 OK"""
        # Register doctor
        payload = {
            'fullName': 'Dr. Sameer Joshi',
            'email': 'sameer.approved@nexus.com',
            'password': 'Password@123',
            'role': 'doctor',
            'phone': '9876543214',
            'medicalRegistrationNumber': 'MH-2015-8888',
            'stateMedicalCouncil': 'Maharashtra Medical Council',
            'registrationYear': '2015',
            'experience': '8',
            'qualification': 'MBBS, MS'
        }
        reg_req = self.factory.post('/api/auth/register', payload, format='json')
        RegisterView.as_view()(reg_req)
        doc_user = CustomUser.objects.get(email='sameer.approved@nexus.com')

        # Admin approves
        appr_req = self.factory.put(f'/api/admin/doctors/{doc_user.id}/approve', {'notes': 'Verified credentials'}, format='json')
        force_authenticate(appr_req, user=self.admin)
        appr_res = AdminDoctorApproveView.as_view()(appr_req, id=doc_user.id)
        self.assertEqual(appr_res.status_code, 200)

        # Doctor logs in
        login_req = self.factory.post('/api/auth/login', {
            'email': 'sameer.approved@nexus.com',
            'password': 'Password@123',
            'role': 'doctor'
        }, format='json')
        from accounts.views import LoginView
        login_res = LoginView.as_view()(login_req)
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.data['approved'])
        self.assertIn('token', login_res.data)

    def test_case_g_existing_approved_doctor_logs_in_normally(self):
        """TEST G: Existing approved doctor (Dr. Nishant) logs in normally -> 200 OK"""
        login_req = self.factory.post('/api/auth/login', {
            'email': 'dr.nishant@nexus.com',
            'password': 'Password@123',
            'role': 'doctor'
        }, format='json')
        from accounts.views import LoginView
        login_res = LoginView.as_view()(login_req)
        self.assertEqual(login_res.status_code, 200)
        self.assertTrue(login_res.data['approved'])
        self.assertEqual(login_res.data['name'], 'Dr. Nishant Raja')
