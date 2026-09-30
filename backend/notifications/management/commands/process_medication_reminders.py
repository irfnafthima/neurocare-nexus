import os
from datetime import datetime, date, time, timedelta
import zoneinfo
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models

from prescriptions.models import Prescription, MedicationSchedule, MedicationDoseLog
from notifications.models import Notification, NotificationPreference, MedicationReminderEvent
from notifications.notification_service import (
    resolve_patient_recipients,
    dispatch_medication_reminder_event,
    retry_failed_reminder_emails,
    get_user_notification_preferences,
)

logger = logging.getLogger(__name__)

APP_TIMEZONE = zoneinfo.ZoneInfo('Asia/Kolkata')

# Configurable prototype software thresholds (Not medical recommendations)
MEDICATION_REMINDER_LEAD_MINUTES = 30
MEDICATION_GRACE_PERIOD_MINUTES = 120
MEDICATION_ESCALATION_MISSED_COUNT = 3
MEDICATION_ESCALATION_WINDOW_DAYS = 7
MEDICATION_ESCALATION_COOLDOWN_DAYS = 3
MAX_EMAIL_RETRY_ATTEMPTS = 3


class Command(BaseCommand):
    help = "Processes upcoming medication reminders, missed-dose notices, adherence escalations, and bounded email retries."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate processing without creating notification or event records.',
        )
        parser.add_argument(
            '--force-date',
            type=str,
            help='Override current date for testing (format YYYY-MM-DD)',
        )
        parser.add_argument(
            '--force-time',
            type=str,
            help='Override current time for testing (format HH:MM)',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force_date_str = options.get('force_date')
        force_time_str = options.get('force_time')

        now_local = timezone.now().astimezone(APP_TIMEZONE)

        if force_date_str:
            forced_date = datetime.strptime(force_date_str.strip(), '%Y-%m-%d').date()
        else:
            forced_date = now_local.date()

        if force_time_str:
            forced_t = datetime.strptime(force_time_str.strip(), '%H:%M').time()
            current_eval_dt = datetime.combine(forced_date, forced_t, tzinfo=APP_TIMEZONE)
        else:
            current_eval_dt = datetime.combine(forced_date, now_local.time(), tzinfo=APP_TIMEZONE)

        self.stdout.write(self.style.NOTICE(
            f"--- Processing Medication Reminders & Escalations [{current_eval_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}] (Dry-Run: {dry_run}) ---"
        ))

        stats = {
            'upcoming_evaluated': 0,
            'upcoming_dispatched': 0,
            'missed_evaluated': 0,
            'missed_dispatched': 0,
            'escalations_evaluated': 0,
            'escalations_dispatched': 0,
            'email_retries_attempted': 0,
            'email_retries_succeeded': 0,
        }

        # 1. Fetch all active schedules on active prescriptions within date boundaries
        active_schedules = MedicationSchedule.objects.filter(
            prescription__status='Active',
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=forced_date)
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=forced_date)
        ).select_related('prescription', 'prescription__patient')

        # Cache existing dose logs for today to prevent repeated DB hits
        today_dose_logs = {
            (log.schedule_id, log.scheduled_date): log
            for log in MedicationDoseLog.objects.filter(
                schedule__in=active_schedules,
                scheduled_date=forced_date
            )
        }

        # ==============================================================================
        # STEP A: UPCOMING REMINDERS (Patient Only, 30m window before dose)
        # ==============================================================================
        for sch in active_schedules:
            stats['upcoming_evaluated'] += 1
            scheduled_dt = datetime.combine(forced_date, sch.scheduled_time, tzinfo=APP_TIMEZONE)
            diff_minutes = (scheduled_dt - current_eval_dt).total_seconds() / 60.0

            # Trigger condition: within lead time before scheduled time (e.g. 0 to 30 mins before)
            if 0 < diff_minutes <= MEDICATION_REMINDER_LEAD_MINUTES:
                # Check if dose was already recorded (TAKEN or SKIPPED)
                existing_log = today_dose_logs.get((sch.id, forced_date))
                if existing_log and existing_log.status in ('TAKEN', 'SKIPPED'):
                    continue

                # Recipient is PATIENT ONLY for upcoming routine reminders
                patient_users = resolve_patient_recipients(sch.prescription.patient_id, include_roles=['patient'])
                for pu in patient_users:
                    if dry_run:
                        self.stdout.write(f"[DRY-RUN] Would dispatch upcoming reminder for {sch} to {pu.email}")
                        stats['upcoming_dispatched'] += 1
                    else:
                        ev = dispatch_medication_reminder_event(
                            schedule=sch,
                            scheduled_date=forced_date,
                            event_type='MEDICATION_UPCOMING_REMINDER',
                            recipient=pu,
                            title="Medication Reminder",
                            message=f"Reminder: Dose of {sch.prescription.medicines} is scheduled at {sch.scheduled_time.strftime('%I:%M %p')}.",
                            context_data={
                                'scheduled_time': sch.scheduled_time.strftime('%I:%M %p'),
                                'medicine_name': sch.prescription.medicines
                            }
                        )
                        if ev:
                            stats['upcoming_dispatched'] += 1

        # ==============================================================================
        # STEP B: MISSED-DOSE NOTIFICATIONS (Grace period expired, Patient + Caregiver)
        # ==============================================================================
        for sch in active_schedules:
            stats['missed_evaluated'] += 1
            scheduled_dt = datetime.combine(forced_date, sch.scheduled_time, tzinfo=APP_TIMEZONE)
            grace_dt = scheduled_dt + timedelta(minutes=MEDICATION_GRACE_PERIOD_MINUTES)

            # Trigger condition: current time is past scheduled time + grace period
            if current_eval_dt > grace_dt:
                existing_log = today_dose_logs.get((sch.id, forced_date))
                # If dose was TAKEN or SKIPPED, it is NOT missed
                if existing_log and existing_log.status in ('TAKEN', 'SKIPPED'):
                    continue

                # Recipients: Patient and Approved Caregivers ONLY
                recipients = resolve_patient_recipients(
                    sch.prescription.patient_id,
                    include_roles=['patient', 'caregiver']
                )

                for r in recipients:
                    if dry_run:
                        self.stdout.write(f"[DRY-RUN] Would dispatch missed dose notice for {sch} to {r.email} ({r.role})")
                        stats['missed_dispatched'] += 1
                    else:
                        ev = dispatch_medication_reminder_event(
                            schedule=sch,
                            scheduled_date=forced_date,
                            event_type='MEDICATION_MISSED_DOSE',
                            recipient=r,
                            title="Missed Medication Notice",
                            message=f"A scheduled dose of {sch.prescription.medicines} at {sch.scheduled_time.strftime('%I:%M %p')} was not recorded.",
                            context_data={
                                'scheduled_time': sch.scheduled_time.strftime('%I:%M %p'),
                                'medicine_name': sch.prescription.medicines
                            }
                        )
                        if ev:
                            stats['missed_dispatched'] += 1

        # ==============================================================================
        # STEP C: REPEATED MISSED-DOSE ADHERENCE ESCALATION
        # ==============================================================================
        # Group active schedules by patient to evaluate adherence over rolling window
        patients_with_schedules = {}
        for sch in active_schedules:
            pid = sch.prescription.patient_id
            if pid not in patients_with_schedules:
                patients_with_schedules[pid] = {
                    'patient': sch.prescription.patient,
                    'schedules': []
                }
            patients_with_schedules[pid]['schedules'].append(sch)

        window_start_date = forced_date - timedelta(days=MEDICATION_ESCALATION_WINDOW_DAYS - 1)
        cooldown_cutoff_date = forced_date - timedelta(days=MEDICATION_ESCALATION_COOLDOWN_DAYS)

        for pid, pdata in patients_with_schedules.items():
            stats['escalations_evaluated'] += 1
            patient = pdata['patient']
            p_schedules = pdata['schedules']

            # Count missed doses in window
            # A slot is missed if for date in [window_start_date, forced_date]:
            # - date was within schedule start/end
            # - on date, current_eval_dt > scheduled_dt + grace
            # - no TAKEN or SKIPPED log exists for that day
            missed_count = 0
            for sch in p_schedules:
                cur_day = window_start_date
                while cur_day <= forced_date:
                    if (sch.start_date is None or sch.start_date <= cur_day) and (sch.end_date is None or sch.end_date >= cur_day):
                        slot_dt = datetime.combine(cur_day, sch.scheduled_time, tzinfo=APP_TIMEZONE)
                        if current_eval_dt > (slot_dt + timedelta(minutes=MEDICATION_GRACE_PERIOD_MINUTES)):
                            log_exists = MedicationDoseLog.objects.filter(
                                schedule=sch,
                                scheduled_date=cur_day,
                                status__in=['TAKEN', 'SKIPPED']
                            ).exists()
                            if not log_exists:
                                missed_count += 1
                    cur_day += timedelta(days=1)

            if missed_count >= MEDICATION_ESCALATION_MISSED_COUNT:
                # Check cooldown: has an escalation been sent in the last COOLDOWN days?
                recent_escalation = MedicationReminderEvent.objects.filter(
                    schedule__in=p_schedules,
                    event_type='MEDICATION_ADHERENCE_NOTICE',
                    scheduled_date__gte=cooldown_cutoff_date
                ).exists()

                if not recent_escalation:
                    rep_schedule = p_schedules[0]
                    # Escalation recipients: Patient, Approved Caregivers, Approved Treating Doctors
                    recipients = resolve_patient_recipients(
                        patient,
                        include_roles=['patient', 'caregiver', 'doctor']
                    )

                    for r in recipients:
                        if dry_run:
                            self.stdout.write(f"[DRY-RUN] Would dispatch adherence escalation for Patient {pid} ({missed_count} missed) to {r.email} ({r.role})")
                            stats['escalations_dispatched'] += 1
                        else:
                            ev = dispatch_medication_reminder_event(
                                schedule=rep_schedule,
                                scheduled_date=forced_date,
                                event_type='MEDICATION_ADHERENCE_NOTICE',
                                recipient=r,
                                title="Medication Adherence Notice",
                                message=f"Medication Adherence Notice: {missed_count} scheduled medication doses were missed over the past {MEDICATION_ESCALATION_WINDOW_DAYS} days.",
                                context_data={
                                    'missed_count': missed_count,
                                    'window_days': MEDICATION_ESCALATION_WINDOW_DAYS
                                }
                            )
                            if ev:
                                stats['escalations_dispatched'] += 1

        # ==============================================================================
        # STEP D: BOUNDED EMAIL RETRIES
        # ==============================================================================
        if not dry_run:
            retry_res = retry_failed_reminder_emails(max_attempts=MAX_EMAIL_RETRY_ATTEMPTS)
            stats['email_retries_attempted'] = retry_res.get('retried_count', 0)
            stats['email_retries_succeeded'] = retry_res.get('success_count', 0)

        self.stdout.write(self.style.SUCCESS(
            f"--- Completed: {stats['upcoming_dispatched']} upcoming reminders, "
            f"{stats['missed_dispatched']} missed notices, "
            f"{stats['escalations_dispatched']} adherence escalations, "
            f"{stats['email_retries_succeeded']}/{stats['email_retries_attempted']} email retries succeeded. ---"
        ))
