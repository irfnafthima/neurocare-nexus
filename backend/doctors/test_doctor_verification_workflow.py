import io
import os
from django.test import TestCase
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from doctors.models import (
    DoctorProfile, DoctorVerificationDocument, VerificationRecord, ReferenceDoctorRegistry
)
from patients.models import Patient
from prescriptions.models import Prescription


class DoctorVerificationWorkflowAndSecurityTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

        # 1. Create Administrator
        self.admin = CustomUser.objects.create_user(
            email="admin_verif@nexus.test",
            password="AdminPassword@123",
            full_name="Admin Director",
            role="admin",
            approved=True,
            status="ACTIVE",
            access_key="ADM-90210"
        )

        # 2. Create Approved Doctor
        self.approved_doctor = CustomUser.objects.create_user(
            email="approved_doc@nexus.test",
            password="DocPassword@123",
            full_name="Dr. Approved Clinician",
            role="doctor",
            approved=True,
            status="ACTIVE",
            npi="MRN-APP-001"
        )
        self.approved_profile = DoctorProfile.objects.create(
            user=self.approved_doctor,
            medical_registration_number="MRN-APP-001",
            state_medical_council="Maharashtra Medical Council",
            qualification="MBBS, MD",
            specialization="Neurology",
            verification_status="VERIFIED"
        )

        # 3. Create Pending Doctor
        self.pending_doctor = CustomUser.objects.create_user(
            email="pending_doc@nexus.test",
            password="DocPassword@123",
            full_name="Dr. Pending Candidate",
            role="doctor",
            approved=False,
            status="PENDING",
            npi="MRN-PEND-002"
        )
        self.pending_profile = DoctorProfile.objects.create(
            user=self.pending_doctor,
            medical_registration_number="MRN-PEND-002",
            state_medical_council="Delhi Medical Council",
            qualification="MBBS",
            specialization="General Medicine",
            verification_status="PENDING"
        )

        # 4. Create Suspended Doctor
        self.suspended_doctor = CustomUser.objects.create_user(
            email="suspended_doc@nexus.test",
            password="DocPassword@123",
            full_name="Dr. Suspended Doctor",
            role="doctor",
            approved=False,
            status="PENDING",
            npi="MRN-SUSP-003"
        )
        self.suspended_profile = DoctorProfile.objects.create(
            user=self.suspended_doctor,
            medical_registration_number="MRN-SUSP-003",
            state_medical_council="Karnataka Medical Council",
            qualification="MBBS",
            specialization="Surgery",
            verification_status="SUSPENDED"
        )

        # 5. Create Patient
        self.patient = Patient.objects.create(
            id="P-999",
            name="Confidential Patient",
            age=45,
            gender="Male",
            condition="Post-Stroke Care"
        )

    def test_1_approved_doctor_login_normal_access(self):
        """Approved doctors must log in normally and receive full clinical JWT."""
        res = self.client.post('/api/auth/login', {
            'email': 'approved_doc@nexus.test',
            'password': 'DocPassword@123',
            'role': 'doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['approved'])
        self.assertFalse(res.data['isRestricted'])
        self.assertIn('token', res.data)

    def test_2_pending_doctor_restricted_login(self):
        """Pending doctors receive restricted session token for verification dashboard only."""
        res = self.client.post('/api/auth/login', {
            'email': 'pending_doc@nexus.test',
            'password': 'DocPassword@123',
            'role': 'doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['approved'])
        self.assertTrue(res.data['isRestricted'])
        self.assertEqual(res.data['status'], 'PENDING')
        self.assertIn('token', res.data)

    def test_3_suspended_doctor_blocked(self):
        """Suspended doctors are strictly forbidden from logging in."""
        res = self.client.post('/api/auth/login', {
            'email': 'suspended_doc@nexus.test',
            'password': 'DocPassword@123',
            'role': 'doctor'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('suspended', str(res.data).lower())

    def test_4_pending_doctor_clinical_api_denial(self):
        """Pending doctors cannot access patient rosters or clinical records."""
        self.client.force_authenticate(user=self.pending_doctor)
        
        # Access patients list
        res_pat = self.client.get('/api/patients')
        self.assertEqual(res_pat.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_pat.data), 0) # Returns empty list due to get_authorized_patients

        # Attempt to issue a prescription
        res_rx = self.client.post('/api/prescriptions', {
            'patientId': 'P-999',
            'medicines': 'Aspirin 75mg'
        })
        self.assertEqual(res_rx.status_code, status.HTTP_403_FORBIDDEN)

    def test_5_doctor_verification_status_endpoint(self):
        """Pending doctor can inspect their own verification status and documents."""
        self.client.force_authenticate(user=self.pending_doctor)
        res = self.client.get('/api/doctor/verification-status')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['medicalRegistrationNumber'], 'MRN-PEND-002')
        self.assertEqual(res.data['verificationStatus'], 'PENDING')
        self.assertEqual(res.data['documents'], [])

    def test_6_admin_document_request_workflow(self):
        """Admin requests verification document; status becomes DOCUMENTS_REQUESTED; email triggered."""
        mail.outbox = []
        self.client.force_authenticate(user=self.admin)
        
        res = self.client.post(f'/api/admin/doctors/{self.pending_doctor.id}/request-document', {
            'documentType': 'MEDICAL_COUNCIL_CERTIFICATE',
            'title': 'State Medical Council Certificate',
            'notes': 'Please provide the 2024 annual registration renewal certificate.'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.pending_profile.refresh_from_db()
        self.assertEqual(self.pending_profile.verification_status, 'DOCUMENTS_REQUESTED')
        
        # Verify email dispatched to doctor
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verification Documents Requested', mail.outbox[0].subject)
        self.assertIn(self.pending_doctor.email, mail.outbox[0].to)

    def test_7_doctor_document_upload_and_security_validation(self):
        """Doctor uploads requested document; transitions to UNDER_REVIEW; rejects dangerous files."""
        # 1. Reject invalid file format
        self.client.force_authenticate(user=self.pending_doctor)
        bad_file = SimpleUploadedFile("script.exe", b"MZexecutabledata", content_type="application/x-msdownload")
        res_bad = self.client.post('/api/doctor/documents/upload', {
            'documentType': 'DEGREE_CERTIFICATE',
            'title': 'Medical Degree',
            'file': bad_file
        }, format='multipart')
        self.assertEqual(res_bad.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Upload valid PDF
        mail.outbox = []
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        good_file = SimpleUploadedFile("degree_certificate.pdf", pdf_content, content_type="application/pdf")
        
        res_good = self.client.post('/api/doctor/documents/upload', {
            'documentType': 'DEGREE_CERTIFICATE',
            'title': 'Medical Degree Certificate',
            'file': good_file
        }, format='multipart')
        self.assertEqual(res_good.status_code, status.HTTP_201_CREATED)

        doc_id = res_good.data['documentId']
        doc_record = DoctorVerificationDocument.objects.get(id=doc_id)
        self.assertEqual(doc_record.status, 'SUBMITTED')
        self.assertEqual(doc_record.file_name, 'degree_certificate.pdf')

        # Verify email dispatched to admin
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verification Document Submitted', mail.outbox[0].subject)

    def test_8_document_download_authorization(self):
        """Only the owning doctor and admin can download verification documents."""
        # Upload a document
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        file_obj = SimpleUploadedFile("council_cert.pdf", pdf_content, content_type="application/pdf")
        self.client.force_authenticate(user=self.pending_doctor)
        res_up = self.client.post('/api/doctor/documents/upload', {
            'documentType': 'MEDICAL_COUNCIL_CERTIFICATE',
            'title': 'Council Cert',
            'file': file_obj
        }, format='multipart')
        doc_id = res_up.data['documentId']

        # 1. Owning doctor download -> OK
        res_own = self.client.get(f'/api/doctor/documents/{doc_id}/download')
        self.assertEqual(res_own.status_code, status.HTTP_200_OK)

        # 2. Other doctor download -> Forbidden
        self.client.force_authenticate(user=self.approved_doctor)
        res_other = self.client.get(f'/api/doctor/documents/{doc_id}/download')
        self.assertEqual(res_other.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Admin download -> OK
        self.client.force_authenticate(user=self.admin)
        res_admin = self.client.get(f'/api/admin/doctors/documents/{doc_id}/download')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

    def test_9_document_acceptance_does_not_auto_approve_account(self):
        """Accepting a document updates document status but preserves doctor pending state."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        file_obj = SimpleUploadedFile("council_cert.pdf", pdf_content, content_type="application/pdf")
        self.client.force_authenticate(user=self.pending_doctor)
        res_up = self.client.post('/api/doctor/documents/upload', {
            'documentType': 'MEDICAL_COUNCIL_CERTIFICATE',
            'title': 'Council Cert',
            'file': file_obj
        }, format='multipart')
        doc_id = res_up.data['documentId']

        # Admin accepts document
        mail.outbox = []
        self.client.force_authenticate(user=self.admin)
        res_review = self.client.put(f'/api/admin/doctors/documents/{doc_id}/review', {
            'action': 'ACCEPT',
            'notes': 'Document matches state medical council records.'
        })
        self.assertEqual(res_review.status_code, status.HTTP_200_OK)

        doc_record = DoctorVerificationDocument.objects.get(id=doc_id)
        self.assertEqual(doc_record.status, 'ACCEPTED')

        # Crucial: Doctor account must NOT be approved yet
        self.pending_doctor.refresh_from_db()
        self.pending_profile.refresh_from_db()
        self.assertFalse(self.pending_doctor.approved)
        self.assertNotEqual(self.pending_profile.verification_status, 'VERIFIED')

        # Verify acceptance email sent to doctor
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Verification Document Accepted', mail.outbox[0].subject)

    def test_10_admin_approval_and_rejection_workflow(self):
        """Admin approval enables full clinical access; admin rejection preserves restrictions."""
        # 1. Admin Approves doctor
        mail.outbox = []
        self.client.force_authenticate(user=self.admin)
        res_app = self.client.put(f'/api/admin/doctors/{self.pending_doctor.id}/approve', {
            'notes': 'All credentials and hospital affiliations confirmed.'
        })
        self.assertEqual(res_app.status_code, status.HTTP_200_OK)

        self.pending_doctor.refresh_from_db()
        self.pending_profile.refresh_from_db()
        self.assertTrue(self.pending_doctor.approved)
        self.assertEqual(self.pending_profile.verification_status, 'VERIFIED')

        # Verify approval email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Application Approved', mail.outbox[0].subject)

        # Doctor now logs in with full access
        res_login = self.client.post('/api/auth/login', {
            'email': 'pending_doc@nexus.test',
            'password': 'DocPassword@123',
            'role': 'doctor'
        })
        self.assertEqual(res_login.status_code, status.HTTP_200_OK)
        self.assertTrue(res_login.data['approved'])
        self.assertFalse(res_login.data['isRestricted'])
