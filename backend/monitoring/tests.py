from django.test import TestCase
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from doctors.models import DoctorPatientLink
from caregivers.models import CaregiverPatientLink


class MonitoringCriticalAlertEmailTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

        # 1. Create Patient
        self.patient = Patient.objects.create(
            id="P-ALERT-101",
            name="Alert Test Patient",
            age=50,
            gender="Male"
        )

        # 2. Create Assigned Doctor
        self.doctor = CustomUser.objects.create_user(
            email="assigned_doctor@example.com",
            password="DocPassword@123",
            full_name="Dr. Assigned Doctor",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )
        DoctorPatientLink.objects.create(doctor=self.doctor, patient=self.patient)

        # 3. Create Assigned Caregiver
        self.caregiver = CustomUser.objects.create_user(
            email="assigned_caregiver@example.com",
            password="CgPassword@123",
            full_name="Caregiver Anna",
            role="caregiver",
            approved=True,
            status="ACTIVE"
        )
        CaregiverPatientLink.objects.create(caregiver=self.caregiver, patient=self.patient, is_approved=True)

        # 4. Create Unassigned Doctor (Should NOT receive alert emails)
        self.other_doc = CustomUser.objects.create_user(
            email="unassigned_doc@example.com",
            password="DocPassword@123",
            full_name="Dr. Unassigned",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )

    def test_emergency_button_triggers_critical_alert_and_emails(self):
        """Emergency button press triggers CRITICAL alert and sends emails with [DEMO/TEST] subject to assigned doc & caregiver."""
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor)

        payload = {
            'patientId': 'P-ALERT-101',
            'emergency_pressed': True,
            'vitals': {
                'max30102': {'heartRate': 75, 'spo2': 98},
                'ds18b20': {'temperature': 36.8},
                'mpu6050': {'fallDetected': False},
                'esp32': {'connected': True}
            }
        }
        res = self.client.post('/api/simulation/trigger', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify emails were sent only to assigned doctor and caregiver
        self.assertEqual(len(mail.outbox), 2)
        recipients = [m.to[0] for m in mail.outbox]
        self.assertIn('assigned_doctor@example.com', recipients)
        self.assertIn('assigned_caregiver@example.com', recipients)
        self.assertNotIn('unassigned_doc@example.com', recipients)

        # Verify subject has [DEMO/TEST] tag
        for m in mail.outbox:
            self.assertTrue(m.subject.startswith('[DEMO/TEST]'))
            self.assertIn('P-ALERT-101', m.subject)

    def test_non_critical_vitals_do_not_send_alert_emails(self):
        """Normal vitals do not generate emails."""
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor)

        payload = {
            'patientId': 'P-ALERT-101',
            'vitals': {
                'max30102': {'heartRate': 72, 'spo2': 98},
                'ds18b20': {'temperature': 36.6},
                'mpu6050': {'fallDetected': False},
                'esp32': {'connected': True}
            }
        }
        res = self.client.post('/api/simulation/trigger', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
