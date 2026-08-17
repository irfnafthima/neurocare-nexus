import io
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from accounts.models import CustomUser, AuditLog
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorPatientLink, SyntheticNPI
from caregivers.models import CaregiverPatientLink
from chat.models import Conversation, ConversationParticipant, Message
from chat.views import sync_conversation_participants

class CareTeamChatModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # 1. Primary Patient (Patient A)
        self.patient_a_user = CustomUser.objects.create_user(
            email="patient_a@gmail.com", password="password123",
            full_name="Patient Alpha", role="patient", patient_id="P-101"
        )
        self.patient_a_record = Patient.objects.create(
            id="P-101", name="Patient Alpha", age=30, gender="Male"
        )

        # 2. Linked Doctor (Doctor A)
        self.doctor_a_user = CustomUser.objects.create_user(
            email="doctor_a@gmail.com", password="password123",
            full_name="Dr. Doctor Alpha", role="doctor", npi="REG-101"
        )
        self.syn_npi_a = SyntheticNPI.objects.create(
            npi="REG-101", name="Dr. Doctor Alpha", hospital="General Hospital"
        )
        DoctorPatientLink.objects.create(doctor=self.doctor_a_user, patient=self.patient_a_record)

        # 3. Approved Caregiver (Caregiver A)
        self.caregiver_a_user = CustomUser.objects.create_user(
            email="caregiver_a@gmail.com", password="password123",
            full_name="Caregiver Alpha", role="caregiver"
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.caregiver_a_user, patient=self.patient_a_record, is_approved=True
        )

        # 4. Authorized Family (Family A)
        self.family_a_user = CustomUser.objects.create_user(
            email="family_a@gmail.com", password="password123",
            full_name="Family Alpha", role="family"
        )
        FamilyPatientLink.objects.create(
            family=self.family_a_user, patient=self.patient_a_record, is_approved=True
        )

        # 5. Unlinked Doctor B
        self.doctor_b_user = CustomUser.objects.create_user(
            email="doctor_b@gmail.com", password="password123",
            full_name="Dr. Doctor Beta", role="doctor", npi="REG-202"
        )

        # 6. Revoked / Pending Caregiver B
        self.caregiver_b_user = CustomUser.objects.create_user(
            email="caregiver_b@gmail.com", password="password123",
            full_name="Caregiver Beta", role="caregiver"
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.caregiver_b_user, patient=self.patient_a_record, is_approved=False # Pending/Revoked
        )

        # 7. Revoked / Pending Family B
        self.family_b_user = CustomUser.objects.create_user(
            email="family_b@gmail.com", password="password123",
            full_name="Family Beta", role="family"
        )
        FamilyPatientLink.objects.create(
            family=self.family_b_user, patient=self.patient_a_record, is_approved=False # Pending/Revoked
        )

        # Initialize Conversation for Patient A
        self.conv = Conversation.objects.create(patient=self.patient_a_record, status='ACTIVE')
        sync_conversation_participants(self.conv)

    def test_authorized_care_team_conversation_access(self):
        # Patient A -> PASS
        self.client.force_authenticate(user=self.patient_a_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Doctor A linked -> PASS
        self.client.force_authenticate(user=self.doctor_a_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Approved Caregiver A -> PASS
        self.client.force_authenticate(user=self.caregiver_a_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Authorized Family A -> PASS
        self.client.force_authenticate(user=self.family_a_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthorized_users_denied_403(self):
        # Unlinked Doctor B -> 403
        self.client.force_authenticate(user=self.doctor_b_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Revoked / Pending Caregiver B -> 403
        self.client.force_authenticate(user=self.caregiver_b_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Revoked / Pending Family B -> 403
        self.client.force_authenticate(user=self.family_b_user)
        res = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_message_persistence_and_emergency_flag(self):
        self.client.force_authenticate(user=self.doctor_a_user)
        
        # Send normal message
        res_norm = self.client.post(f'/api/chat/conversations/{self.conv.id}/messages', {
            'content': 'Please record your morning blood pressure.',
            'priority': 'NORMAL'
        })
        self.assertEqual(res_norm.status_code, status.HTTP_201_CREATED)
        self.assertFalse(res_norm.data['is_emergency'])

        # Send emergency message
        res_emerg = self.client.post(f'/api/chat/conversations/{self.conv.id}/messages', {
            'content': 'Patient reporting severe chest discomfort.',
            'priority': 'EMERGENCY'
        })
        self.assertEqual(res_emerg.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_emerg.data['is_emergency'])
        self.assertEqual(res_emerg.data['priority'], 'EMERGENCY')

        # Verify offline recipient loads messages from PostgreSQL
        self.client.force_authenticate(user=self.patient_a_user)
        res_list = self.client.get(f'/api/chat/conversations/{self.conv.id}/messages')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 2)

    def test_secure_attachment_upload_and_authorization(self):
        # Doctor A uploads PDF attachment
        self.client.force_authenticate(user=self.doctor_a_user)
        pdf_file = SimpleUploadedFile("lab_results.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        
        res_upload = self.client.post(f'/api/chat/conversations/{self.conv.id}/messages', {
            'content': 'Attached EEG evaluation report.',
            'attachment': pdf_file
        }, format='multipart')

        self.assertEqual(res_upload.status_code, status.HTTP_201_CREATED)
        msg_id = res_upload.data['id']
        download_url = res_upload.data['attachment_url']

        # Patient A accesses attachment -> PASS
        self.client.force_authenticate(user=self.patient_a_user)
        res_dl_p = self.client.get(download_url)
        self.assertEqual(res_dl_p.status_code, status.HTTP_200_OK)

        # Unlinked Doctor B accesses attachment -> 403 FORBIDDEN
        self.client.force_authenticate(user=self.doctor_b_user)
        res_dl_b = self.client.get(download_url)
        self.assertEqual(res_dl_b.status_code, status.HTTP_403_FORBIDDEN)

        # Revoked Caregiver B accesses attachment -> 403 FORBIDDEN
        self.client.force_authenticate(user=self.caregiver_b_user)
        res_dl_cg = self.client.get(download_url)
        self.assertEqual(res_dl_cg.status_code, status.HTTP_403_FORBIDDEN)

    def test_prohibited_executable_upload_rejected(self):
        self.client.force_authenticate(user=self.patient_a_user)
        exe_file = SimpleUploadedFile("malware.exe", b"executable content", content_type="application/x-msdownload")
        
        res = self.client.post(f'/api/chat/conversations/{self.conv.id}/messages', {
            'content': 'Try running this script',
            'attachment': exe_file
        }, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_audit_logging_for_chat_events(self):
        self.client.force_authenticate(user=self.patient_a_user)
        self.client.post(f'/api/chat/conversations/{self.conv.id}/messages', {
            'content': 'Urgent question regarding dosage',
            'priority': 'URGENT'
        })

        self.assertTrue(AuditLog.objects.filter(action='Sent Chat Message').exists())
