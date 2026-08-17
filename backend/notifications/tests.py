from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from doctors.models import DoctorPatientLink, SyntheticNPI, DoctorConnectionRequest
from notifications.models import Notification
from notifications.utils import create_notification

class NotificationsModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="patient_notif@gmail.com",
            password="password123",
            full_name="Notif Patient",
            role="patient",
            patient_id="P-888"
        )
        self.patient_record = Patient.objects.create(
            id="P-888",
            name="Notif Patient",
            age=35,
            gender="Female",
            room="888"
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doc_notif@gmail.com",
            password="password123",
            full_name="Dr. Notif Doctor",
            role="doctor",
            npi="REG-888"
        )
        self.syn_npi = SyntheticNPI.objects.create(
            npi="REG-888",
            name="Dr. Notif Doctor",
            hospital="Metro Hospital"
        )
        self.other_user = CustomUser.objects.create_user(
            email="other_user@gmail.com",
            password="password123",
            full_name="Other User",
            role="patient"
        )

        DoctorPatientLink.objects.create(doctor=self.doctor_user, patient=self.patient_record)

    def test_notification_api_isolation_and_unread_count(self):
        # Create notifications for patient_user and other_user
        n1 = create_notification(self.patient_user, "New Medical Document", "A new medical document was uploaded.", category="document")
        n2 = create_notification(self.patient_user, "New Prescription", "Your doctor added a new prescription.", category="prescription")
        n_other = create_notification(self.other_user, "Other User Notif", "Private notification for other user.")

        # Authenticate as patient_user
        self.client.force_authenticate(user=self.patient_user)
        res = self.client.get('/api/notifications')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['notifications']), 2)
        self.assertEqual(res.data['unreadCount'], 2)

        # Ensure other_user notification is not present (Isolation Check)
        notif_ids = [n['id'] for n in res.data['notifications']]
        self.assertNotIn(n_other.id, notif_ids)

        # Mark n1 as read
        res_read = self.client.post(f'/api/notifications/{n1.id}/read')
        self.assertEqual(res_read.status_code, status.HTTP_200_OK)

        # Verify unread count decreases to 1
        res_after = self.client.get('/api/notifications')
        self.assertEqual(res_after.data['unreadCount'], 1)

        # Mark all as read
        res_all = self.client.post('/api/notifications/mark-all-read')
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)

        # Verify unread count becomes 0
        res_zero = self.client.get('/api/notifications')
        self.assertEqual(res_zero.data['unreadCount'], 0)

    def test_event_driven_notification_generation(self):
        # 1. Patient dispatches connection request -> Doctor receives notification
        self.client.force_authenticate(user=self.patient_user)
        res_conn = self.client.post('/api/connections/requests', {
            'doctorNpi': 'REG-888',
            'requestMessage': 'Please review my EEG telemetry'
        })
        self.assertEqual(res_conn.status_code, status.HTTP_201_CREATED)

        doc_notifs = Notification.objects.filter(user=self.doctor_user)
        self.assertTrue(doc_notifs.filter(title="New Doctor Connection Request").exists())

        # 2. Doctor issues prescription -> Patient receives notification
        self.client.force_authenticate(user=self.doctor_user)
        res_rx = self.client.post('/api/prescriptions', {
            'patientId': 'P-888',
            'medicines': 'Levetiracetam 500mg',
            'dosage': '1 tablet twice daily'
        })
        self.assertEqual(res_rx.status_code, status.HTTP_201_CREATED)

        pat_notifs = Notification.objects.filter(user=self.patient_user)
        self.assertTrue(pat_notifs.filter(title="New Prescription").exists())

    def test_no_sensitive_clinical_data_in_previews(self):
        # Trigger health record update notification
        self.client.force_authenticate(user=self.patient_user)
        self.client.post('/api/health-records', {
            'type': 'condition',
            'patientId': 'P-888',
            'conditionName': 'Temporal Lobe Epilepsy',
            'description': 'Complex partial seizures'
        })

        doc_notifs = Notification.objects.filter(user=self.doctor_user, category="record")
        self.assertTrue(doc_notifs.exists())
        notif = doc_notifs.first()
        # Verify title & preview do not leak sensitive raw metrics
        self.assertEqual(notif.title, "Health Record Updated")
        self.assertEqual(notif.message, "Patient health information was updated.")
