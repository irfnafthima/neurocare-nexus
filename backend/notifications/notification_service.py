import logging
from django.conf import settings
from django.utils import timezone
from accounts.models import CustomUser
from notifications.models import Notification, NotificationPreference, MedicationReminderEvent
from notifications.email_service import send_nexus_email, send_nexus_email_with_status

logger = logging.getLogger(__name__)

# Events that qualify for important email routing
IMPORTANT_EMAIL_EVENTS = {
    'CRITICAL_PATIENT_ALERT',
    'FALL_ALERT',
    'PRESCRIPTION_CREATED',
    'PRESCRIPTION_UPDATED',
    'PRESCRIPTION_DISCONTINUED',
    'DOCTOR_REGISTRATION_SUBMITTED',
    'DOCTOR_DOCUMENTS_REQUESTED',
    'DOCTOR_DOCUMENTS_SUBMITTED',
    'DOCTOR_DOCUMENT_ACCEPTED',
    'DOCTOR_DOCUMENT_RESUBMISSION_REQUIRED',
    'DOCTOR_APPROVED',
    'DOCTOR_REJECTED',
    'MEDICATION_UPCOMING_REMINDER',
    'MEDICATION_MISSED_DOSE',
    'MEDICATION_ADHERENCE_NOTICE',
}


def get_user_notification_preferences(user):
    """
    Retrieves the user's notification preferences or returns safe defaults
    without modifying database rows unless saved.
    """
    if not user:
        return NotificationPreference.get_defaults('patient')

    try:
        pref = getattr(user, 'notification_preferences', None)
        if pref:
            return {
                'critical_alerts_in_app': pref.critical_alerts_in_app,
                'critical_alerts_email': pref.critical_alerts_email,
                'prescription_updates_email': pref.prescription_updates_email,
                'medication_reminder_in_app': pref.medication_reminder_in_app,
                'medication_reminder_email': pref.medication_reminder_email,
                'missed_dose_in_app': pref.missed_dose_in_app,
                'missed_dose_email': pref.missed_dose_email,
                'adherence_escalation_in_app': pref.adherence_escalation_in_app,
                'adherence_escalation_email': pref.adherence_escalation_email,
            }
    except Exception:
        pass

    return NotificationPreference.get_defaults(getattr(user, 'role', 'patient'))


def should_send_email_for_event(event_type, user=None):
    """
    Determines if email should be dispatched based on event type and user preferences.
    """
    if event_type not in IMPORTANT_EMAIL_EVENTS:
        return False

    if user:
        prefs = get_user_notification_preferences(user)
        if event_type in ('CRITICAL_PATIENT_ALERT', 'FALL_ALERT'):
            return prefs.get('critical_alerts_email', True)
        elif event_type.startswith('PRESCRIPTION'):
            return prefs.get('prescription_updates_email', True)
        elif event_type == 'MEDICATION_UPCOMING_REMINDER':
            return prefs.get('medication_reminder_email', False)
        elif event_type == 'MEDICATION_MISSED_DOSE':
            return prefs.get('missed_dose_email', True)
        elif event_type == 'MEDICATION_ADHERENCE_NOTICE':
            return prefs.get('adherence_escalation_email', True)

    return True


def should_send_in_app_for_event(event_type, user=None):
    """
    Determines if in-app notification should be created based on safety policies and user preferences.
    """
    if not user:
        return True

    prefs = get_user_notification_preferences(user)
    # Critical physiological alerts are strictly mandatory in-app
    if event_type in ('CRITICAL_PATIENT_ALERT', 'FALL_ALERT'):
        return True

    if event_type == 'MEDICATION_UPCOMING_REMINDER':
        return prefs.get('medication_reminder_in_app', True)
    elif event_type == 'MEDICATION_MISSED_DOSE':
        return prefs.get('missed_dose_in_app', True)
    elif event_type == 'MEDICATION_ADHERENCE_NOTICE':
        return prefs.get('adherence_escalation_in_app', True)

    return True


def find_patient_instance(patient_or_id):
    from patients.models import Patient
    if isinstance(patient_or_id, Patient):
        return patient_or_id

    if not patient_or_id:
        return None

    from patients.views import find_patient_by_identifier
    return find_patient_by_identifier(str(patient_or_id))


def resolve_patient_recipients(patient_or_id, exclude_user=None, include_roles=None):
    from doctors.models import DoctorPatientLink, DoctorProfile
    from caregivers.models import CaregiverPatientLink
    from patients.models import FamilyPatientLink

    patient = find_patient_instance(patient_or_id)
    if not patient:
        logger.warning(f"[NotificationService] Cannot resolve recipients: Patient '{patient_or_id}' not found.")
        return []

    if include_roles is None:
        include_roles = {'patient', 'doctor', 'caregiver', 'family'}
    else:
        include_roles = {r.lower() for r in include_roles}

    exclude_id = exclude_user.id if hasattr(exclude_user, 'id') else exclude_user

    resolved_users = []
    seen_user_ids = set()

    def add_user(user):
        if not user or not user.is_active:
            return
        if user.id == exclude_id:
            return
        if user.id in seen_user_ids:
            return
        seen_user_ids.add(user.id)
        resolved_users.append(user)

    # 1. Patient User Account
    if 'patient' in include_roles:
        patient_users = CustomUser.objects.filter(role='patient', is_active=True)
        for pu in patient_users:
            is_match = False
            if pu.patient_id and pu.patient_id.strip() == patient.id:
                is_match = True
            elif pu.device_id and pu.device_id.upper().replace('NP-', 'P-') == patient.id:
                is_match = True
            elif pu.full_name and pu.full_name.strip().lower() == patient.name.strip().lower():
                is_match = True

            if is_match:
                add_user(pu)

    # 2. Treating Doctors (Active & Approved only)
    if 'doctor' in include_roles:
        doc_links = DoctorPatientLink.objects.filter(patient=patient).select_related('doctor')
        for dl in doc_links:
            doc = dl.doctor
            if doc and doc.approved and doc.status == 'ACTIVE':
                prof = DoctorProfile.objects.filter(user=doc).first()
                if prof and prof.verification_status in ['REJECTED', 'SUSPENDED', 'BLOCKED']:
                    continue
                add_user(doc)

        if patient.doctor_npi:
            doc_users = CustomUser.objects.filter(
                role='doctor', 
                npi=patient.doctor_npi.npi,
                approved=True,
                status='ACTIVE'
            )
            for du in doc_users:
                prof = DoctorProfile.objects.filter(user=du).first()
                if prof and prof.verification_status in ['REJECTED', 'SUSPENDED', 'BLOCKED']:
                    continue
                add_user(du)

    # 3. Assigned Caregivers (Active & Approved links only)
    if 'caregiver' in include_roles:
        cg_links = CaregiverPatientLink.objects.filter(
            patient=patient, 
            is_approved=True
        ).select_related('caregiver')
        for cl in cg_links:
            if cl.caregiver and cl.caregiver.is_active:
                add_user(cl.caregiver)

    # 4. Authorized Family Members (Active & Approved links only)
    if 'family' in include_roles:
        fam_links = FamilyPatientLink.objects.filter(
            patient=patient, 
            is_approved=True
        ).select_related('family')
        for fl in fam_links:
            if fl.family and fl.family.is_active:
                add_user(fl.family)

    return resolved_users


def dispatch_event_notification(
    event_type,
    patient_or_id,
    title,
    message,
    category=None,
    target_id=None,
    actor=None,
    context_data=None,
    include_roles=None
):
    """
    Central dispatch coordinator for NeuroCare Nexus notifications.
    """
    patient = find_patient_instance(patient_or_id)
    if not patient:
        logger.warning(f"[NotificationService] Cannot dispatch '{event_type}': Patient '{patient_or_id}' not found.")
        return {'in_app_count': 0, 'email_count': 0, 'recipients': []}

    exclude_actor = actor if (event_type and event_type.startswith('PRESCRIPTION')) else None

    recipients = resolve_patient_recipients(
        patient_or_id=patient,
        exclude_user=exclude_actor,
        include_roles=include_roles
    )

    in_app_count = 0
    email_count = 0
    recipient_ids = []

    # 1. Create In-App Notifications
    for user in recipients:
        if should_send_in_app_for_event(event_type, user):
            try:
                Notification.objects.create(
                    user=user,
                    title=title,
                    message=message,
                    category=category or 'system',
                    target_id=str(target_id) if target_id else None
                )
                in_app_count += 1
                recipient_ids.append(user.id)
            except Exception as e:
                logger.error(f"[NotificationService] Failed to create in-app notification for user {user.id}: {e}")

    # 2. Check Email Policy & Dispatch per recipient preferences
    if context_data is None:
        context_data = {}

    email_ctx = {
        'patient_id': patient.id,
        'patient_name': patient.name,
        'alert_type': title,
        'alert_message': message,
        'prescription_date': str(timezone.now().date()),
        **context_data
    }

    sent_emails = set()
    for user in recipients:
        if not should_send_email_for_event(event_type, user):
            continue

        email = (user.email or '').strip().lower()
        if not email or email in sent_emails:
            continue

        sent_emails.add(email)
        try:
            success = send_nexus_email(event_type, email, email_ctx)
            if success:
                email_count += 1
        except Exception as e:
            logger.error(f"[NotificationService] Error sending '{event_type}' email to {email}: {e}")

    logger.info(
        f"[NotificationService] Dispatched '{event_type}' for Patient {patient.id}: "
        f"{in_app_count} in-app, {email_count} emails."
    )

    return {
        'in_app_count': in_app_count,
        'email_count': email_count,
        'recipients': recipient_ids
    }


def dispatch_medication_reminder_event(
    schedule,
    scheduled_date,
    event_type,
    recipient,
    title,
    message,
    category='medication',
    context_data=None,
    max_email_retries=3
):
    """
    Durable, idempotent medication reminder dispatcher.
    
    Guarantees:
    - Exactly one MedicationReminderEvent record per (schedule, scheduled_date, event_type, recipient).
    - In-app and Email delivery status tracked independently.
    - In-app notification created at most once.
    - Bounded email retries on failure.
    - Safe error sanitization.
    """
    if not schedule or not recipient:
        return None

    now = timezone.now()
    role_snapshot = getattr(recipient, 'role', '')

    # 1. Get or create the unique MedicationReminderEvent record atomically
    event, created = MedicationReminderEvent.objects.get_or_create(
        schedule=schedule,
        scheduled_date=scheduled_date,
        event_type=event_type,
        recipient=recipient,
        defaults={
            'recipient_role_snapshot': role_snapshot,
            'in_app_status': 'PENDING',
            'email_status': 'PENDING',
        }
    )

    # 2. In-App Notification Delivery
    if event.in_app_status in ('PENDING', 'FAILED'):
        if should_send_in_app_for_event(event_type, recipient):
            try:
                Notification.objects.create(
                    user=recipient,
                    title=title,
                    message=message,
                    category=category,
                    target_id=str(schedule.prescription_id)
                )
                event.in_app_status = 'SENT'
                event.in_app_dispatched_at = now
            except Exception as e:
                event.in_app_status = 'FAILED'
                event.last_error = str(e)[:250]
                logger.error(f"[ReminderService] Failed creating in-app reminder for user {recipient.id}: {e}")
        else:
            event.in_app_status = 'NOT_REQUIRED'

    # 3. Email Notification Delivery
    if event.email_status in ('PENDING', 'FAILED'):
        if event.email_attempt_count >= max_email_retries:
            logger.info(f"[ReminderService] Max email retries reached for event #{event.id}. Skipping email.")
        elif should_send_email_for_event(event_type, recipient):
            email = (recipient.email or '').strip().lower()
            if email:
                if context_data is None:
                    context_data = {}

                ctx = {
                    'patient_id': schedule.prescription.patient_id,
                    'patient_name': schedule.prescription.patient.name if hasattr(schedule.prescription, 'patient') else 'Patient',
                    'medicine_name': schedule.prescription.medicines,
                    'scheduled_time': schedule.scheduled_time.strftime('%I:%M %p'),
                    'alert_type': title,
                    'alert_message': message,
                    **context_data
                }

                event.email_attempt_count += 1
                event.email_attempted_at = now
                success, err_msg = send_nexus_email_with_status(event_type, email, ctx)

                if success:
                    event.email_status = 'SENT'
                    event.email_sent_at = now
                    event.last_error = ''
                else:
                    event.email_status = 'FAILED'
                    event.last_error = (err_msg or 'Email delivery failed')[:250]
            else:
                event.email_status = 'NOT_REQUIRED'
        else:
            event.email_status = 'NOT_REQUIRED'

    event.save()
    return event


def retry_failed_reminder_emails(max_attempts=3):
    """
    Retries failed email deliveries for medication reminder events without
    re-creating in-app notifications.
    """
    failed_events = MedicationReminderEvent.objects.filter(
        email_status='FAILED',
        email_attempt_count__lt=max_attempts,
        recipient__isnull=False
    ).select_related('schedule', 'schedule__prescription', 'schedule__prescription__patient', 'recipient')

    retried_count = 0
    success_count = 0

    now = timezone.now()
    for ev in failed_events:
        user = ev.recipient
        if not user or not user.email:
            ev.email_status = 'NOT_REQUIRED'
            ev.save(update_fields=['email_status'])
            continue

        if not should_send_email_for_event(ev.event_type, user):
            ev.email_status = 'NOT_REQUIRED'
            ev.save(update_fields=['email_status'])
            continue

        rx = ev.schedule.prescription
        ctx = {
            'patient_id': rx.patient_id,
            'patient_name': rx.patient.name if hasattr(rx, 'patient') else 'Patient',
            'medicine_name': rx.medicines,
            'scheduled_time': ev.schedule.scheduled_time.strftime('%I:%M %p'),
        }

        ev.email_attempt_count += 1
        ev.email_attempted_at = now
        retried_count += 1

        success, err_msg = send_nexus_email_with_status(ev.event_type, user.email, ctx)
        if success:
            ev.email_status = 'SENT'
            ev.email_sent_at = now
            ev.last_error = ''
            success_count += 1
        else:
            ev.email_status = 'FAILED'
            ev.last_error = (err_msg or 'Retry failed')[:250]

        ev.save(update_fields=['email_status', 'email_attempt_count', 'email_attempted_at', 'email_sent_at', 'last_error'])

    return {'retried_count': retried_count, 'success_count': success_count}
