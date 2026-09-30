import os
from datetime import datetime, date, time, timedelta
import zoneinfo
from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import CustomUser
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorProfile, DoctorPatientLink
from caregivers.models import CaregiverProfile, CaregiverPatientLink
from prescriptions.models import Prescription, MedicationSchedule, MedicationDoseLog
from notifications.models import Notification, NotificationPreference, MedicationReminderEvent
from notifications.notification_service import (
    get_user_notification_preferences,
    dispatch_medication_reminder_event,
    retry_failed_reminder_emails,
    resolve_patient_recipients,
)

APP_TIMEZONE = zoneinfo.ZoneInfo('Asia/Kolkata')


class MedicationRemindersAndPreferencesTests(TestCase):
    def setUp(self):
        mail.outbox = []

        # Create Patient User & Patient Record
        self.patient_user = CustomUser.objects.create_user(
            username='stage4_patient@test.com',
            email='stage4_patient@test.com',
            password='Password123!',
            role='patient',
            full_name='Stage4 Test Patient',
            patient_id='P-STG4-001',
            is_active=True
        )
        self.patient = Patient.objects.create(
            id='P-STG4-001',
            name='Stage4 Test Patient',
            age=55,
            gender='Female',
            condition='Parkinsons'
        )

        # Create Doctor User
        self.doctor_user = CustomUser.objects.create_user(
            username='stage4_doctor@test.com',
            email='stage4_doctor@test.com',
            password='Password123!',
            role='doctor',
            full_name='Dr. Stage4 Specialist',
            approved=True,
            status='ACTIVE',
            is_active=True
        )
        self.doc_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_registration_number='MRN-STG4-999',
            state_medical_council='Delhi Medical Council',
            specialization='Neurology',
            qualification='MBBS, MD',
            verification_status='VERIFIED'
        )
        DoctorPatientLink.objects.create(
            doctor=self.doctor_user,
            patient=self.patient
        )

        # Create Approved Caregiver
        self.caregiver_user = CustomUser.objects.create_user(
            username='stage4_caregiver@test.com',
            email='stage4_caregiver@test.com',
            password='Password123!',
            role='caregiver',
            full_name='Stage4 Caregiver',
            is_active=True
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.caregiver_user,
            patient=self.patient,
            is_approved=True
        )

        # Create Unapproved Caregiver
        self.unapproved_caregiver = CustomUser.objects.create_user(
            username='stage4_unapproved_cg@test.com',
            email='stage4_unapproved_cg@test.com',
            password='Password123!',
            role='caregiver',
            full_name='Unapproved Caregiver',
            is_active=True
        )
        CaregiverPatientLink.objects.create(
            caregiver=self.unapproved_caregiver,
            patient=self.patient,
            is_approved=False
        )

        # Create Family Member
        self.family_user = CustomUser.objects.create_user(
            username='stage4_family@test.com',
            email='stage4_family@test.com',
            password='Password123!',
            role='family',
            full_name='Stage4 Family Member',
            is_active=True
        )
        FamilyPatientLink.objects.create(
            family=self.family_user,
            patient=self.patient,
            is_approved=True
        )

        # Create Active Prescription & MedicationSchedule (08:00 AM)
        self.today = timezone.now().astimezone(APP_TIMEZONE).date()
        self.prescription = Prescription.objects.create(
            patient=self.patient,
            prescribing_doctor=self.doctor_user,
            prescribing_doctor_name=self.doctor_user.full_name,
            prescription_date=self.today,
            medicines='Levodopa 100mg',
            dosage='1 tablet',
            frequency='Once daily',
            duration='30 days',
            status='Active'
        )
        self.schedule_morning = MedicationSchedule.objects.create(
            prescription=self.prescription,
            scheduled_time=time(8, 0),
            time_label='Morning',
            start_date=self.today,
            is_active=True
        )

        self.client = APIClient()

    # =========================================================================
    # 1. NOTIFICATION PREFERENCES TESTS
    # =========================================================================
    def test_default_preferences_without_db_row(self):
        """User without DB row should receive role-tailored default preferences."""
        self.assertEqual(NotificationPreference.objects.filter(user=self.patient_user).count(), 0)
        prefs = get_user_notification_preferences(self.patient_user)
        self.assertTrue(prefs['critical_alerts_in_app'])
        self.assertTrue(prefs['critical_alerts_email'])
        self.assertTrue(prefs['medication_reminder_in_app'])
        self.assertFalse(prefs['medication_reminder_email'])  # Default OFF
        self.assertTrue(prefs['missed_dose_in_app'])
        self.assertTrue(prefs['missed_dose_email'])

    def test_get_preferences_endpoint(self):
        """GET /api/notifications/preferences/ returns preferences."""
        self.client.force_authenticate(user=self.patient_user)
        res = self.client.get('/api/notifications/preferences/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['critical_alerts_in_app'])
        self.assertFalse(res.data['medication_reminder_email'])

    def test_update_preferences_endpoint(self):
        """PUT /api/notifications/preferences/ updates and persists preferences."""
        self.client.force_authenticate(user=self.patient_user)
        payload = {
            'medication_reminder_email': True,
            'missed_dose_email': False,
            'critical_alerts_in_app': False  # Attempt to disable mandatory alert
        }
        res = self.client.put('/api/notifications/preferences/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Critical in-app must remain True (mandatory safety invariant)
        self.assertTrue(res.data['critical_alerts_in_app'])
        self.assertTrue(res.data['medication_reminder_email'])
        self.assertFalse(res.data['missed_dose_email'])

        # Verify persisted in database
        db_pref = NotificationPreference.objects.get(user=self.patient_user)
        self.assertTrue(db_pref.critical_alerts_in_app)
        self.assertTrue(db_pref.medication_reminder_email)
        self.assertFalse(db_pref.missed_dose_email)

    # =========================================================================
    # 2. UPCOMING REMINDERS TESTS
    # =========================================================================
    def test_upcoming_reminder_30m_window(self):
        """At 07:45 AM (15 mins prior to 08:00), patient receives upcoming reminder."""
        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='07:45'
        )

        # Patient receives in-app notification
        notifs = Notification.objects.filter(user=self.patient_user)
        self.assertEqual(notifs.count(), 1)
        self.assertIn("Reminder: Dose of Levodopa 100mg", notifs.first().message)

        # MedicationReminderEvent is recorded
        ev = MedicationReminderEvent.objects.filter(
            schedule=self.schedule_morning,
            scheduled_date=self.today,
            event_type='MEDICATION_UPCOMING_REMINDER',
            recipient=self.patient_user
        ).first()
        self.assertIsNotNone(ev)
        self.assertEqual(ev.in_app_status, 'SENT')
        self.assertEqual(ev.email_status, 'NOT_REQUIRED')  # Email was default OFF

    def test_upcoming_reminder_idempotency(self):
        """Running scheduler multiple times within window generates exactly 1 reminder."""
        for t in ['07:35', '07:40', '07:45']:
            call_command(
                'process_medication_reminders',
                force_date=str(self.today),
                force_time=t
            )

        self.assertEqual(Notification.objects.filter(user=self.patient_user).count(), 1)
        self.assertEqual(
            MedicationReminderEvent.objects.filter(
                schedule=self.schedule_morning,
                scheduled_date=self.today,
                event_type='MEDICATION_UPCOMING_REMINDER'
            ).count(),
            1
        )

    def test_taken_dose_suppresses_upcoming_reminder(self):
        """If dose is TAKEN before 07:45 AM, no upcoming reminder is generated."""
        MedicationDoseLog.objects.create(
            schedule=self.schedule_morning,
            scheduled_date=self.today,
            status='TAKEN',
            action_at=timezone.now(),
            marked_by=self.patient_user
        )

        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='07:45'
        )

        self.assertEqual(Notification.objects.filter(user=self.patient_user).count(), 0)
        self.assertEqual(MedicationReminderEvent.objects.count(), 0)

    # =========================================================================
    # 3. MISSED-DOSE NOTIFICATIONS TESTS
    # =========================================================================
    def test_overdue_unresolved_dose_triggers_missed_notice(self):
        """At 10:30 AM (150 mins after 08:00, past 120m grace), dose triggers missed notice."""
        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='10:30'
        )

        # Patient receives in-app + email (default ON)
        patient_notifs = Notification.objects.filter(user=self.patient_user)
        self.assertEqual(patient_notifs.count(), 1)
        self.assertIn("was not recorded", patient_notifs.first().message)

        # Approved Caregiver receives in-app + email
        cg_notifs = Notification.objects.filter(user=self.caregiver_user)
        self.assertEqual(cg_notifs.count(), 1)

        # Unapproved Caregiver receives NOTHING
        self.assertEqual(Notification.objects.filter(user=self.unapproved_caregiver).count(), 0)

        # Family & Doctor do not receive routine single missed dose alerts
        self.assertEqual(Notification.objects.filter(user=self.family_user).count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.doctor_user).count(), 0)

    def test_skipped_dose_is_not_missed(self):
        """If dose is SKIPPED, scheduler does NOT generate MISSED_DOSE notice."""
        MedicationDoseLog.objects.create(
            schedule=self.schedule_morning,
            scheduled_date=self.today,
            status='SKIPPED',
            action_at=timezone.now(),
            marked_by=self.patient_user
        )

        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='10:30'
        )

        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(MedicationReminderEvent.objects.count(), 0)

    # =========================================================================
    # 4. ADHERENCE ESCALATION TESTS
    # =========================================================================
    def test_repeated_missed_dose_adherence_escalation(self):
        """3 missed doses in 7 days triggers Medication Adherence Notice to Patient, Caregiver, Doctor."""
        self.schedule_morning.start_date = self.today - timedelta(days=10)
        self.schedule_morning.save()

        # 3 distinct missed occurrences
        call_command(
            'process_medication_reminders',
            force_date=str(self.today - timedelta(days=2)),
            force_time='11:00'
        )
        call_command(
            'process_medication_reminders',
            force_date=str(self.today - timedelta(days=1)),
            force_time='11:00'
        )
        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='11:00'
        )

        # Check escalation event dispatched
        escalation_events = MedicationReminderEvent.objects.filter(
            event_type='MEDICATION_ADHERENCE_NOTICE'
        )
        self.assertTrue(escalation_events.exists())

        # Escalation recipients: Patient, Caregiver, Doctor
        recip_roles = set(escalation_events.values_list('recipient__role', flat=True))
        self.assertIn('patient', recip_roles)
        self.assertIn('caregiver', recip_roles)
        self.assertIn('doctor', recip_roles)

        # Check notification message terminology is non-emergency
        notif = Notification.objects.filter(user=self.doctor_user).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, "Medication Adherence Notice")
        self.assertIn("Medication Adherence Notice", notif.message)
        self.assertNotIn("Emergency", notif.message)
        self.assertNotIn("Critical Alert", notif.message)

    def test_escalation_cooldown_prevents_duplicate_spam(self):
        """Escalation is throttled by 3-day cooldown."""
        self.schedule_morning.start_date = self.today - timedelta(days=10)
        self.schedule_morning.save()

        # Day 1: 3 missed doses -> triggers escalation
        for d in [self.today - timedelta(days=2), self.today - timedelta(days=1), self.today]:
            call_command('process_medication_reminders', force_date=str(d), force_time='11:00')

        initial_count = MedicationReminderEvent.objects.filter(event_type='MEDICATION_ADHERENCE_NOTICE').count()
        self.assertGreater(initial_count, 0)

        # Re-run same day -> no additional escalation
        call_command('process_medication_reminders', force_date=str(self.today), force_time='11:30')
        self.assertEqual(
            MedicationReminderEvent.objects.filter(event_type='MEDICATION_ADHERENCE_NOTICE').count(),
            initial_count
        )

    # =========================================================================
    # 5. DELIVERY STATUS & EMAIL RETRY TESTS
    # =========================================================================
    def test_bounded_email_retry_does_not_duplicate_in_app(self):
        """Failed email retry attempts up to max_attempts without duplicating in-app alerts."""
        # Create an event where in-app was sent but email failed
        ev = MedicationReminderEvent.objects.create(
            schedule=self.schedule_morning,
            scheduled_date=self.today,
            event_type='MEDICATION_MISSED_DOSE',
            recipient=self.patient_user,
            recipient_role_snapshot='patient',
            in_app_status='SENT',
            email_status='FAILED',
            email_attempt_count=1,
            last_error='SMTP connection refused'
        )
        Notification.objects.create(
            user=self.patient_user,
            title="Missed Medication Notice",
            message="Initial notice"
        )
        self.assertEqual(Notification.objects.filter(user=self.patient_user).count(), 1)

        # Run retry
        res = retry_failed_reminder_emails(max_attempts=3)
        self.assertEqual(res['retried_count'], 1)
        self.assertEqual(res['success_count'], 1)

        ev.refresh_from_db()
        self.assertEqual(ev.email_status, 'SENT')
        self.assertEqual(ev.email_attempt_count, 2)
        self.assertEqual(ev.last_error, '')

        # In-app notifications MUST NOT be duplicated
        self.assertEqual(Notification.objects.filter(user=self.patient_user).count(), 1)

    # =========================================================================
    # 6. LIFECYCLE & BOUNDARY TESTS
    # =========================================================================
    def test_discontinued_prescription_produces_zero_reminders(self):
        """Discontinued prescriptions generate 0 reminders."""
        self.prescription.status = 'Discontinued'
        self.prescription.save()

        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='07:45'
        )
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(MedicationReminderEvent.objects.count(), 0)

    def test_inactive_schedule_produces_zero_reminders(self):
        """Inactive schedules generate 0 reminders."""
        self.schedule_morning.is_active = False
        self.schedule_morning.save()

        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='07:45'
        )
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(MedicationReminderEvent.objects.count(), 0)

    def test_outside_schedule_dates_produces_zero_reminders(self):
        """Schedules with start_date in future produce 0 reminders."""
        self.schedule_morning.start_date = self.today + timedelta(days=5)
        self.schedule_morning.save()

        call_command(
            'process_medication_reminders',
            force_date=str(self.today),
            force_time='07:45'
        )
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(MedicationReminderEvent.objects.count(), 0)

    # =========================================================================
    # 7. GET REQUEST SIDE-EFFECT SAFETY
    # =========================================================================
    def test_get_requests_create_no_reminder_events(self):
        """GET /api/medications/today/ or /api/notifications/ creates 0 reminder events."""
        self.client.force_authenticate(user=self.patient_user)
        self.client.get('/api/medications/today/')
        self.client.get('/api/notifications/')
        self.client.get('/api/notifications/preferences/')

        self.assertEqual(MedicationReminderEvent.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)
