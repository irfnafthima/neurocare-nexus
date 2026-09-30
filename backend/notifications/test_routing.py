import os
from unittest.mock import patch
from django.test import TestCase
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorPatientLink, DoctorProfile, SyntheticNPI
from caregivers.models import CaregiverPatientLink
from prescriptions.models import Prescription
from alerts.models import Alert
from notifications.models import Notification
from notifications.notification_service import (
    resolve_patient_recipients, 
    dispatch_event_notification,
    should_send_email_for_event
)


class NotificationRoutingAndEmailPolicyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

        # -------------------------------------------------------------
        # 1. PATIENT A CARE TEAM (Authorized)
        # -------------------------------------------------------------
        self.patient_a_record = Patient.objects.create(
            id="P-101",
            name="Alice Patient",
            age=45,
            gender="Female",
            room="101"
        )
        self.patient_a_user = CustomUser.objects.create_user(
            email="alice.patient@nexus.test",
            password="Password@123",
            full_name="Alice Patient",
            role="patient",
            patient_id="P-101"
        )

        self.doctor_a_user = CustomUser.objects.create_user(
            email="dr.alice.doc@nexus.test",
            password="Password@123",
            full_name="Dr. Alice Neurologist",
            role="doctor",
            approved=True,
            status="ACTIVE",
            npi="MRN-DOC-A"
        )
        self.doctor_a_profile = DoctorProfile.objects.create(
            user=self.doctor_a_user,
            medical_registration_number="MRN-DOC-A",
            state_medical_council="Maharashtra Medical Council",
            qualification="MBBS, MD",
            specialization="Neurology",
            verification_status="VERIFIED"
        )
        DoctorPatientLink.objects.create(doctor=self.doctor_a_user, patient=self.patient_a_record)

        self.caregiver_a_user = CustomUser.objects.create_user(
            email="caregiver.a@nexus.test",
            password="Password@123",
            full_name="Caregiver Anna",
            role="caregiver",
            approved=True,
            status="ACTIVE"
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.caregiver_a_user,
            patient=self.patient_a_record,
            is_approved=True
        )

        self.family_a_user = CustomUser.objects.create_user(
            email="family.a@nexus.test",
            password="Password@123",
            full_name="Frank Family",
            role="family",
            approved=True,
            status="ACTIVE",
            patient_id="P-101"
        )
        FamilyPatientLink.objects.create(
            family=self.family_a_user,
            patient=self.patient_a_record,
            is_approved=True
        )

        # -------------------------------------------------------------
        # 2. PATIENT B CARE TEAM (Unrelated)
        # -------------------------------------------------------------
        self.patient_b_record = Patient.objects.create(
            id="P-202",
            name="Bob Patient",
            age=60,
            gender="Male",
            room="202"
        )
        self.patient_b_user = CustomUser.objects.create_user(
            email="bob.patient@nexus.test",
            password="Password@123",
            full_name="Bob Patient",
            role="patient",
            patient_id="P-202"
        )
        self.doctor_b_user = CustomUser.objects.create_user(
            email="dr.bob.doc@nexus.test",
            password="Password@123",
            full_name="Dr. Bob Clinician",
            role="doctor",
            approved=True,
            status="ACTIVE",
            npi="MRN-DOC-B"
        )
        DoctorPatientLink.objects.create(doctor=self.doctor_b_user, patient=self.patient_b_record)

        self.caregiver_b_user = CustomUser.objects.create_user(
            email="caregiver.b@nexus.test",
            password="Password@123",
            full_name="Caregiver Brian",
            role="caregiver",
            approved=True,
            status="ACTIVE"
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.caregiver_b_user,
            patient=self.patient_b_record,
            is_approved=True
        )

        self.family_b_user = CustomUser.objects.create_user(
            email="family.b@nexus.test",
            password="Password@123",
            full_name="Fiona Family",
            role="family",
            approved=True,
            status="ACTIVE",
            patient_id="P-202"
        )
        FamilyPatientLink.objects.create(
            family=self.family_b_user,
            patient=self.patient_b_record,
            is_approved=True
        )

        # -------------------------------------------------------------
        # 3. UNAPPROVED / SUSPENDED ACCOUNTS FOR PATIENT A
        # -------------------------------------------------------------
        # Unapproved Caregiver
        self.unapproved_caregiver = CustomUser.objects.create_user(
            email="unapproved.cg@nexus.test",
            password="Password@123",
            full_name="Unapproved Caregiver",
            role="caregiver",
            approved=True,
            status="ACTIVE"
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.unapproved_caregiver,
            patient=self.patient_a_record,
            is_approved=False
        )

        # Unapproved Family
        self.unapproved_family = CustomUser.objects.create_user(
            email="unapproved.fam@nexus.test",
            password="Password@123",
            full_name="Unapproved Family",
            role="family",
            approved=True,
            status="ACTIVE",
            patient_id="P-101"
        )
        FamilyPatientLink.objects.create(
            family=self.unapproved_family,
            patient=self.patient_a_record,
            is_approved=False
        )

        # Suspended Doctor
        self.suspended_doctor = CustomUser.objects.create_user(
            email="suspended.doc@nexus.test",
            password="Password@123",
            full_name="Dr. Suspended Doc",
            role="doctor",
            approved=False,
            status="PENDING",
            npi="MRN-SUSP-99"
        )
        DoctorProfile.objects.create(
            user=self.suspended_doctor,
            medical_registration_number="MRN-SUSP-99",
            state_medical_council="Delhi Medical Council",
            qualification="MBBS",
            specialization="Neurology",
            verification_status="SUSPENDED"
        )
        DoctorPatientLink.objects.create(doctor=self.suspended_doctor, patient=self.patient_a_record)

    def test_1_recipient_resolution_authorization_and_isolation(self):
        """
        Verify that resolve_patient_recipients for Patient A returns ONLY authorized active users:
        - Patient A
        - Doctor A
        - Caregiver A (is_approved=True)
        - Family A (is_approved=True)
        and strictly excludes:
        - Unrelated Patient B care team (Doctor B, Caregiver B, Family B, Patient B)
        - Unapproved Caregiver (is_approved=False)
        - Unapproved Family (is_approved=False)
        - Suspended Doctor
        """
        recipients = resolve_patient_recipients(self.patient_a_record)
        recipient_emails = {u.email for u in recipients}

        expected_emails = {
            "alice.patient@nexus.test",
            "dr.alice.doc@nexus.test",
            "caregiver.a@nexus.test",
            "family.a@nexus.test",
        }
        self.assertEqual(recipient_emails, expected_emails)

        # Explicit non-inclusion assertions
        self.assertNotIn("bob.patient@nexus.test", recipient_emails)
        self.assertNotIn("dr.bob.doc@nexus.test", recipient_emails)
        self.assertNotIn("caregiver.b@nexus.test", recipient_emails)
        self.assertNotIn("family.b@nexus.test", recipient_emails)
        self.assertNotIn("unapproved.cg@nexus.test", recipient_emails)
        self.assertNotIn("unapproved.fam@nexus.test", recipient_emails)
        self.assertNotIn("suspended.doc@nexus.test", recipient_emails)

    def test_2_prescription_creation_flow_and_email_dispatch(self):
        """
        Doctor A issues prescription for Patient A:
        - Prescription persists in DB.
        - Patient A, Caregiver A, Family A receive in-app notification & email.
        - Prescribing Doctor A is excluded from redundant self-notification email.
        - Unrelated Patient B care team receives nothing.
        """
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor_a_user)
        
        res = self.client.post('/api/prescriptions', {
            'patientId': 'P-101',
            'medicines': 'Oxcarbazepine 300mg',
            'dosage': '1 tablet',
            'frequency': 'Twice daily',
            'duration': '14 days',
            'instructions': 'Take with evening meal.'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Check in-app notifications
        pat_notifs = Notification.objects.filter(user=self.patient_a_user, category="prescription")
        cg_notifs = Notification.objects.filter(user=self.caregiver_a_user, category="prescription")
        fam_notifs = Notification.objects.filter(user=self.family_a_user, category="prescription")
        self.assertTrue(pat_notifs.exists())
        self.assertTrue(cg_notifs.exists())
        self.assertTrue(fam_notifs.exists())

        # Unrelated users get 0 in-app notifications
        self.assertEqual(Notification.objects.filter(user=self.doctor_b_user, category="prescription").count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.caregiver_b_user, category="prescription").count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.family_b_user, category="prescription").count(), 0)

        # Check emails dispatched
        sent_to = [m.to[0] for m in mail.outbox]
        self.assertIn("alice.patient@nexus.test", sent_to)
        self.assertIn("caregiver.a@nexus.test", sent_to)
        self.assertIn("family.a@nexus.test", sent_to)
        
        # Prescribing Doctor A does NOT receive an email about their own action
        self.assertNotIn("dr.alice.doc@nexus.test", sent_to)

        # Email content privacy verification
        for msg in mail.outbox:
            self.assertIn("New Prescription Available", msg.subject)
            self.assertIn("Alice Patient", msg.subject)
            self.assertIn("Please sign in securely to NeuroCare Nexus", msg.body)

    def test_3_prescription_update_and_discontinuation_flow(self):
        """
        Doctor A updates and subsequently discontinues a prescription:
        - Updates trigger PRESCRIPTION_UPDATED email to Patient A, Caregiver A, Family A.
        - Deletion triggers PRESCRIPTION_DISCONTINUED email.
        """
        # 1. Create prescription
        rx = Prescription.objects.create(
            patient=self.patient_a_record,
            prescribing_doctor=self.doctor_a_user,
            prescribing_doctor_name=self.doctor_a_user.full_name,
            medicines="Levetiracetam 500mg",
            dosage="1 tab",
            frequency="Daily"
        )

        # 2. Update prescription
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor_a_user)
        res_put = self.client.put(f'/api/prescriptions/{rx.id}', {
            'dosage': '2 tabs',
            'frequency': 'Twice daily'
        })
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)

        sent_to = [m.to[0] for m in mail.outbox]
        self.assertIn("alice.patient@nexus.test", sent_to)
        self.assertIn("caregiver.a@nexus.test", sent_to)
        self.assertIn("family.a@nexus.test", sent_to)
        self.assertIn("Prescription Update Notice", mail.outbox[0].subject)

        # 3. Discontinue / Delete prescription
        mail.outbox = []
        res_del = self.client.delete(f'/api/prescriptions/{rx.id}')
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)

        sent_del_to = [m.to[0] for m in mail.outbox]
        self.assertIn("alice.patient@nexus.test", sent_del_to)
        self.assertIn("caregiver.a@nexus.test", sent_del_to)
        self.assertIn("family.a@nexus.test", sent_del_to)
        self.assertIn("Prescription Discontinuation Notice", mail.outbox[0].subject)

    def test_4_get_endpoints_have_zero_side_effects(self):
        """
        GET requests (reading prescriptions or alerts) must NEVER generate notifications or emails.
        """
        mail.outbox = []
        init_notif_count = Notification.objects.count()

        self.client.force_authenticate(user=self.patient_a_user)
        res_rx = self.client.get('/api/prescriptions')
        self.assertEqual(res_rx.status_code, status.HTTP_200_OK)

        res_alerts = self.client.get('/api/alerts')
        self.assertEqual(res_alerts.status_code, status.HTTP_200_OK)

        # Verify 0 emails sent and 0 notifications created
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Notification.objects.count(), init_notif_count)

    def test_5_critical_physiological_alert_dispatch(self):
        """
        Simulated critical telemetry alarm triggers:
        - In-app notification for Patient A, Doctor A, Caregiver A, Family A.
        - Email with [DEMO/TEST] subject to Patient A, Doctor A, Caregiver A, Family A.
        """
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor_a_user)

        # Trigger severe bradycardia simulation (HR < 45)
        res = self.client.post('/api/simulation/trigger', {
            'patientId': 'P-101',
            'vitals': {
                'max30102': {'heartRate': 40, 'spo2': 98},
                'ds18b20': {'temperature': 37.0},
                'mpu6050': {'fallDetected': False}
            },
            'riskScore': 85,
            'statusState': 'Critical'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify alert in DB
        self.assertTrue(Alert.objects.filter(patient=self.patient_a_record, severity='CRITICAL').exists())

        # Verify in-app notifications
        for u in [self.patient_a_user, self.doctor_a_user, self.caregiver_a_user, self.family_a_user]:
            self.assertTrue(Notification.objects.filter(user=u, category="alarm").exists())

        # Verify emails
        sent_to = [m.to[0] for m in mail.outbox]
        self.assertIn("alice.patient@nexus.test", sent_to)
        self.assertIn("dr.alice.doc@nexus.test", sent_to)
        self.assertIn("caregiver.a@nexus.test", sent_to)
        self.assertIn("family.a@nexus.test", sent_to)

        # Verify [DEMO/TEST] prefix
        for msg in mail.outbox:
            self.assertTrue(msg.subject.startswith('[DEMO/TEST]'))
            self.assertIn('Simulated Telemetry Alert', msg.body)

    def test_6_fall_detection_alarm_dispatch(self):
        """
        Postural fall detection triggers FALL_ALERT:
        - In-app notification for Patient A, Doctor A, Caregiver A, Family A.
        - Email with [DEMO/TEST] subject and Fall Alarm label.
        """
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor_a_user)

        # Trigger fall detection
        res = self.client.post('/api/simulation/trigger', {
            'patientId': 'P-101',
            'vitals': {
                'max30102': {'heartRate': 75, 'spo2': 98},
                'ds18b20': {'temperature': 36.8},
                'mpu6050': {'fallDetected': True}
            },
            'riskScore': 90,
            'statusState': 'Critical'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify alert in DB
        self.assertTrue(Alert.objects.filter(patient=self.patient_a_record, type='Fall').exists())

        # Verify emails
        sent_to = [m.to[0] for m in mail.outbox]
        self.assertIn("alice.patient@nexus.test", sent_to)
        self.assertIn("dr.alice.doc@nexus.test", sent_to)
        self.assertIn("caregiver.a@nexus.test", sent_to)
        self.assertIn("family.a@nexus.test", sent_to)

        for msg in mail.outbox:
            self.assertTrue(msg.subject.startswith('[DEMO/TEST]'))
            self.assertIn('Fall Detection Alert', msg.subject)

    def test_7_email_failure_does_not_rollback_prescription(self):
        """
        If email dispatch fails (e.g. network/SMTP outage),
        the prescription must STILL persist successfully in the database.
        """
        self.client.force_authenticate(user=self.doctor_a_user)

        # Mock send_mail to simulate network error
        with patch('notifications.email_service.send_mail', side_effect=Exception("SMTP Connection Timed Out")):
            res = self.client.post('/api/prescriptions', {
                'patientId': 'P-101',
                'medicines': 'Sodium Valproate 500mg',
                'dosage': '1 tab',
                'frequency': 'Twice daily'
            })
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            
            # Verify prescription exists in database
            self.assertTrue(Prescription.objects.filter(patient=self.patient_a_record, medicines='Sodium Valproate 500mg').exists())
            
            # In-app notification still created
            self.assertTrue(Notification.objects.filter(user=self.patient_a_user, category="prescription").exists())

    def test_8_email_deduplication(self):
        """
        If a user has multiple links to the same patient (e.g. Doctor linked via DoctorPatientLink and npi),
        they must receive only ONE in-app notification and ONE email per event.
        """
        # Assign doctor_npi to patient record
        synth_npi = SyntheticNPI.objects.create(npi="MRN-DOC-A", name="Dr. Alice", hospital="Metro")
        self.patient_a_record.doctor_npi = synth_npi
        self.patient_a_record.save()

        mail.outbox = []
        # Dispatch event directly
        res = dispatch_event_notification(
            event_type='CRITICAL_PATIENT_ALERT',
            patient_or_id=self.patient_a_record,
            title="Critical Vitals Alert",
            message="Immediate attention required.",
            category="alarm"
        )

        # Check doctor notifications
        doc_notifs = Notification.objects.filter(user=self.doctor_a_user, title="Critical Vitals Alert")
        self.assertEqual(doc_notifs.count(), 1)

        # Check doctor emails
        doc_emails = [m for m in mail.outbox if m.to[0] == "dr.alice.doc@nexus.test"]
        self.assertEqual(len(doc_emails), 1)
