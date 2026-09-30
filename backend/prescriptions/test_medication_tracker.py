import os
from datetime import datetime, date, time, timedelta
import zoneinfo
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import CustomUser
from patients.models import Patient, FamilyPatientLink
from doctors.models import DoctorProfile, DoctorPatientLink, SyntheticNPI
from caregivers.models import CaregiverProfile, CaregiverPatientLink
from prescriptions.models import Prescription, MedicationSchedule, MedicationDoseLog

APP_TIMEZONE = zoneinfo.ZoneInfo('Asia/Kolkata')

class MedicationTrackerTestSuite(TestCase):
    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

        # Create Doctor
        self.doctor = CustomUser.objects.create_user(
            email='dr.house@nexus.test',
            password='Password123!',
            role='doctor',
            full_name='Dr. Gregory House',
            approved=True
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor,
            medical_registration_number='MED-12345',
            verification_status='VERIFIED'
        )
        self.synthetic_npi = SyntheticNPI.objects.create(
            npi='NPI-HOUSE-1',
            name='Dr. Gregory House',
            hospital='Princeton Plainsboro',
            status='Active'
        )

        # Create Patients
        self.patient_a = Patient.objects.create(
            id='P-101',
            name='Alice Wonderland',
            age=32,
            gender='Female',
            room='101-A',
            condition='Hypertension',
            doctor_npi=self.synthetic_npi
        )
        self.patient_b = Patient.objects.create(
            id='P-102',
            name='Bob Builder',
            age=45,
            gender='Male',
            room='102-B',
            condition='Post-Op Monitoring'
        )

        # Create Patient User Accounts
        self.user_patient_a = CustomUser.objects.create_user(
            email='alice@nexus.test',
            password='Password123!',
            role='patient',
            full_name='Alice Wonderland',
            patient_id='P-101'
        )
        self.user_patient_b = CustomUser.objects.create_user(
            email='bob@nexus.test',
            password='Password123!',
            role='patient',
            full_name='Bob Builder',
            patient_id='P-102'
        )

        # Create Caregiver
        self.caregiver_user = CustomUser.objects.create_user(
            email='clara.caregiver@nexus.test',
            password='Password123!',
            role='caregiver',
            full_name='Clara Barton'
        )
        self.cg_link_approved = CaregiverPatientLink.objects.create(
            caregiver=self.caregiver_user,
            patient=self.patient_a,
            is_approved=True
        )

        # Unapproved Caregiver
        self.unapproved_caregiver = CustomUser.objects.create_user(
            email='dan.unapproved@nexus.test',
            password='Password123!',
            role='caregiver',
            full_name='Dan Strangers'
        )
        self.cg_link_unapproved = CaregiverPatientLink.objects.create(
            caregiver=self.unapproved_caregiver,
            patient=self.patient_a,
            is_approved=False
        )

        # Create Family Member
        self.family_user = CustomUser.objects.create_user(
            email='fiona.family@nexus.test',
            password='Password123!',
            role='family',
            full_name='Fiona Wonderland',
            patient_id='P-101'
        )
        self.family_link = FamilyPatientLink.objects.create(
            family=self.family_user,
            patient=self.patient_a,
            is_approved=True
        )

        # Unrelated Doctor
        self.unrelated_doctor = CustomUser.objects.create_user(
            email='dr.stranger@nexus.test',
            password='Password123!',
            role='doctor',
            full_name='Dr. Stephen Stranger',
            approved=True
        )
        DoctorProfile.objects.create(
            user=self.unrelated_doctor,
            medical_registration_number='MED-99999',
            verification_status='VERIFIED'
        )

        # Link Doctor House to Patient A
        DoctorPatientLink.objects.create(doctor=self.doctor, patient=self.patient_a)

        # Create active prescription for Patient A
        self.rx = Prescription.objects.create(
            patient=self.patient_a,
            prescribing_doctor=self.doctor,
            prescribing_doctor_name=self.doctor.full_name,
            prescription_date=date.today(),
            medicines='Metformin 500mg',
            dosage='1 tablet',
            frequency='Twice daily',
            duration='30 days',
            instructions='Take with breakfast and dinner.',
            status='Active'
        )

        # Create Schedules for Rx: 08:00 and 20:00
        self.sch_morning = MedicationSchedule.objects.create(
            prescription=self.rx,
            scheduled_time=time(8, 0),
            time_label='Morning',
            start_date=date.today(),
            is_active=True
        )
        self.sch_evening = MedicationSchedule.objects.create(
            prescription=self.rx,
            scheduled_time=time(20, 0),
            time_label='Evening',
            start_date=date.today(),
            is_active=True
        )

    def test_patient_own_tracker(self):
        self.client.force_authenticate(user=self.user_patient_a)
        res = self.client.get('/api/medications/today/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(len(data['doses']), 2)
        self.assertEqual(data['doses'][0]['medicine_name'], 'Metformin 500mg')
        self.assertTrue(data['doses'][0]['is_actionable'])

    def test_patient_denied_other_patient_tracker(self):
        self.client.force_authenticate(user=self.user_patient_b)
        res = self.client.get('/api/medications/today/?patientId=P-101')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_verified_linked_doctor_access(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.get('/api/medications/today/?patientId=P-101')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(len(data['doses']), 2)

    def test_unrelated_doctor_denied(self):
        self.client.force_authenticate(user=self.unrelated_doctor)
        res = self.client.get('/api/medications/today/?patientId=P-101')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_caregiver_access_and_action(self):
        self.client.force_authenticate(user=self.caregiver_user)
        # View today
        res = self.client.get('/api/medications/today/?patientId=P-101')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Mark taken on behalf of patient
        action_res = self.client.post(
            f'/api/medications/doses/{self.sch_morning.id}/take/',
            {'notes': 'Assisted patient with morning water'},
            format='json'
        )
        self.assertEqual(action_res.status_code, status.HTTP_201_CREATED)
        log_data = action_res.json()
        self.assertEqual(log_data['status'], 'TAKEN')
        self.assertEqual(log_data['marked_by'], self.caregiver_user.id)
        self.assertEqual(log_data['marked_by_name'], 'Clara Barton')

    def test_unapproved_caregiver_denied(self):
        self.client.force_authenticate(user=self.unapproved_caregiver)
        res = self.client.get('/api/medications/today/?patientId=P-101')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        action_res = self.client.post(
            f'/api/medications/doses/{self.sch_morning.id}/take/',
            format='json'
        )
        self.assertEqual(action_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_approved_family_read_only_and_action_denied(self):
        self.client.force_authenticate(user=self.family_user)
        # Read-only access permitted
        res = self.client.get('/api/medications/today/?patientId=P-101')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Action modification denied for family
        action_res = self.client.post(
            f'/api/medications/doses/{self.sch_morning.id}/take/',
            format='json'
        )
        self.assertEqual(action_res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('read-only', action_res.json().lower())

    def test_doctor_action_denied_on_dose_logs(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post(
            f'/api/medications/doses/{self.sch_morning.id}/take/',
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_multiple_schedules_per_prescription(self):
        self.assertEqual(self.rx.schedules.count(), 2)

    def test_duplicate_schedule_time_prevention(self):
        self.client.force_authenticate(user=self.doctor)
        # Attempt to create existing active time 08:00
        res = self.client.post(
            '/api/medications/schedule/',
            {'prescriptionId': self.rx.id, 'scheduled_time': '08:00'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_schedule_start_end_date_validation(self):
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post(
            '/api/medications/schedule/',
            {
                'prescriptionId': self.rx.id,
                'scheduled_time': '14:00',
                'start_date': '2026-10-10',
                'end_date': '2026-10-01'
            },
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_taken_persistence_and_marked_by(self):
        self.client.force_authenticate(user=self.user_patient_a)
        res = self.client.post(
            f'/api/medications/doses/{self.sch_morning.id}/take/',
            {'notes': 'Taken with warm water'},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MedicationDoseLog.objects.filter(schedule=self.sch_morning, status='TAKEN').exists())

    def test_duplicate_taken_idempotency(self):
        self.client.force_authenticate(user=self.user_patient_a)
        # First call creates
        res1 = self.client.post(f'/api/medications/doses/{self.sch_morning.id}/take/', format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second exact duplicate call returns 200 OK without creating new row
        res2 = self.client.post(f'/api/medications/doses/{self.sch_morning.id}/take/', format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(MedicationDoseLog.objects.filter(schedule=self.sch_morning).count(), 1)

    def test_conflicting_taken_to_skipped_rejected(self):
        self.client.force_authenticate(user=self.user_patient_a)
        # First mark TAKEN
        res1 = self.client.post(f'/api/medications/doses/{self.sch_morning.id}/take/', format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Attempt to mark SKIPPED on same occurrence
        res2 = self.client.post(f'/api/medications/doses/{self.sch_morning.id}/skip/', format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)

    def test_conflicting_skipped_to_taken_rejected(self):
        self.client.force_authenticate(user=self.user_patient_a)
        # First mark SKIPPED
        res1 = self.client.post(f'/api/medications/doses/{self.sch_morning.id}/skip/', {'reason': 'Nauseous'}, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Attempt to mark TAKEN on same occurrence
        res2 = self.client.post(f'/api/medications/doses/{self.sch_morning.id}/take/', format='json')
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)

    def test_no_dose_log_created_from_get(self):
        self.client.force_authenticate(user=self.user_patient_a)
        initial_count = MedicationDoseLog.objects.count()
        res = self.client.get('/api/medications/today/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(MedicationDoseLog.objects.count(), initial_count)

    def test_zero_eligible_doses_adherence_null(self):
        # Create brand new patient with no active schedules
        new_patient = Patient.objects.create(id='P-999', name='Newborn Patient', age=1, gender='Other', room='999')
        CustomUser.objects.create_user(email='newborn@nexus.test', password='Password123!', role='patient', patient_id='P-999')
        DoctorPatientLink.objects.create(doctor=self.doctor, patient=new_patient)

        self.client.force_authenticate(user=self.doctor)
        res = self.client.get('/api/medications/adherence/?patientId=P-999&days=7')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data['eligible_doses'], 0)
        self.assertIsNone(data['adherence_rate'])

    def test_adherence_calculation_math(self):
        # Setup specific adherence test scenario: 8 Taken, 1 Skipped, 1 Missed = 80.0%
        yesterday = date.today() - timedelta(days=1)
        past_date_base = yesterday - timedelta(days=4) # 5 days: past_date_base, +1, +2, +3, +4(yesterday)
        
        # Dedicated prescription ending yesterday
        adh_rx = Prescription.objects.create(
            patient=self.patient_a,
            prescribing_doctor=self.doctor,
            prescription_date=past_date_base,
            medicines='Aspirin 81mg',
            status='Active'
        )
        adh_sch_am = MedicationSchedule.objects.create(
            prescription=adh_rx,
            scheduled_time=time(9, 0),
            start_date=past_date_base,
            end_date=yesterday,
            is_active=True
        )
        adh_sch_pm = MedicationSchedule.objects.create(
            prescription=adh_rx,
            scheduled_time=time(21, 0),
            start_date=past_date_base,
            end_date=yesterday,
            is_active=True
        )

        # Create 8 Taken across days 0..3 (4 days * 2 = 8 Taken)
        for i in range(4):
            d = past_date_base + timedelta(days=i)
            MedicationDoseLog.objects.create(schedule=adh_sch_am, scheduled_date=d, status='TAKEN', action_at=timezone.now(), marked_by=self.user_patient_a)
            MedicationDoseLog.objects.create(schedule=adh_sch_pm, scheduled_date=d, status='TAKEN', action_at=timezone.now(), marked_by=self.user_patient_a)

        # Day 4 (yesterday): AM is SKIPPED, PM is left unrecorded (MISSED)
        MedicationDoseLog.objects.create(schedule=adh_sch_am, scheduled_date=yesterday, status='SKIPPED', action_at=timezone.now(), marked_by=self.user_patient_a)

        # Disable original setup schedules from skewing the specific count
        self.sch_morning.is_active = False
        self.sch_morning.end_date = yesterday
        self.sch_morning.save()
        self.sch_evening.is_active = False
        self.sch_evening.end_date = yesterday
        self.sch_evening.save()

        self.client.force_authenticate(user=self.user_patient_a)
        res = self.client.get('/api/medications/adherence/?days=6')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data['taken_count'], 8)
        self.assertEqual(data['skipped_count'], 1)
        self.assertEqual(data['missed_count'], 1)
        self.assertEqual(data['eligible_doses'], 10)
        self.assertEqual(data['adherence_rate'], 80.0)


    def test_discontinued_prescription_behavior(self):
        self.client.force_authenticate(user=self.user_patient_a)
        # Mark morning dose taken
        self.client.post(f'/api/medications/doses/{self.sch_morning.id}/take/', format='json')
        self.assertEqual(MedicationDoseLog.objects.filter(schedule=self.sch_morning).count(), 1)

        # Doctor discontinues prescription
        self.client.force_authenticate(user=self.doctor)
        del_res = self.client.delete(f'/api/prescriptions/{self.rx.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.rx.refresh_from_db()
        self.assertEqual(self.rx.status, 'Discontinued')

        # Dose history remains intact
        self.assertEqual(MedicationDoseLog.objects.filter(schedule=self.sch_morning).count(), 1)

        # Future doses no longer appear in today's tracker
        self.client.force_authenticate(user=self.user_patient_a)
        today_res = self.client.get('/api/medications/today/')
        self.assertEqual(len(today_res.json()['doses']), 0)

    def test_schedule_update_preserves_historical_timing(self):
        # Patient marks dose under original 08:00 schedule
        self.client.force_authenticate(user=self.user_patient_a)
        self.client.post(f'/api/medications/doses/{self.sch_morning.id}/take/', format='json')

        # Doctor updates schedule times to 09:00 and 21:00
        self.client.force_authenticate(user=self.doctor)
        res = self.client.post(
            '/api/medications/schedule/',
            {'prescriptionId': self.rx.id, 'times': ['09:00', '21:00']},
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.sch_morning.refresh_from_db()
        self.assertFalse(self.sch_morning.is_active)
        # Historical dose log remains attached to old 08:00 schedule
        log = MedicationDoseLog.objects.filter(schedule=self.sch_morning).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.schedule.scheduled_time, time(8, 0))

    def test_legacy_prescription_without_schedule(self):
        # Create unconfigured legacy prescription
        legacy_rx = Prescription.objects.create(
            patient=self.patient_a,
            prescribing_doctor=self.doctor,
            medicines='Amlodipine 5mg',
            frequency='Once daily',
            status='Active'
        )
        self.client.force_authenticate(user=self.user_patient_a)
        res = self.client.get('/api/medications/today/')
        data = res.json()
        unconfigured = data.get('unconfigured_prescriptions', [])
        self.assertTrue(any(p['id'] == legacy_rx.id for p in unconfigured))

    def test_stage2_prescription_notifications_preserved(self):
        mail.outbox = []
        self.client.force_authenticate(user=self.doctor)
        # Create new prescription
        res = self.client.post(
            '/api/prescriptions/',
            {
                'patientId': 'P-101',
                'medicines': 'Lisinopril 10mg',
                'dosage': '1 tab',
                'frequency': 'Once daily'
            },
            format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Verify Stage 2 email dispatches to Patient, Caregiver, Family
        recipients = [m.to[0] for m in mail.outbox]
        self.assertIn('alice@nexus.test', recipients)
        self.assertIn('clara.caregiver@nexus.test', recipients)
        self.assertIn('fiona.family@nexus.test', recipients)

    def test_get_requests_send_zero_emails(self):
        mail.outbox = []
        self.client.force_authenticate(user=self.user_patient_a)
        self.client.get('/api/medications/today/')
        self.client.get('/api/medications/adherence/')
        self.client.get('/api/medications/history/')
        self.assertEqual(len(mail.outbox), 0)
