from django.db import models
from django.conf import settings

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    category = models.CharField(max_length=50, blank=True, null=True)
    target_id = models.CharField(max_length=100, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Notification for {self.user.email} - {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    # Critical physiological alerts (In-app is mandatory and locked)
    critical_alerts_in_app = models.BooleanField(default=True, help_text="Mandatory in-app alert delivery")
    critical_alerts_email = models.BooleanField(default=True)

    # Prescription lifecycle notices
    prescription_updates_email = models.BooleanField(default=True)

    # Medication Reminders (Upcoming dose)
    medication_reminder_in_app = models.BooleanField(default=True)
    medication_reminder_email = models.BooleanField(default=False, help_text="Default OFF to prevent inbox fatigue")

    # Missed-Dose Alerts
    missed_dose_in_app = models.BooleanField(default=True)
    missed_dose_email = models.BooleanField(default=True)

    # Adherence Escalation Notices
    adherence_escalation_in_app = models.BooleanField(default=True)
    adherence_escalation_email = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_defaults(cls, role='patient'):
        is_patient = (role == 'patient')
        return {
            'critical_alerts_in_app': True,
            'critical_alerts_email': True,
            'prescription_updates_email': True,
            'medication_reminder_in_app': is_patient,
            'medication_reminder_email': False,
            'missed_dose_in_app': True,
            'missed_dose_email': True,
            'adherence_escalation_in_app': True,
            'adherence_escalation_email': True,
        }

    def __str__(self):
        return f"NotificationPreferences for {self.user.email} ({self.user.role})"


class MedicationReminderEvent(models.Model):
    EVENT_TYPE_CHOICES = (
        ('MEDICATION_UPCOMING_REMINDER', 'Upcoming Dose Reminder'),
        ('MEDICATION_MISSED_DOSE', 'Missed Dose Alert'),
        ('MEDICATION_ADHERENCE_NOTICE', 'Adherence Notice'),
    )

    DELIVERY_STATUS_CHOICES = (
        ('NOT_REQUIRED', 'Not Required'),
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    )

    schedule = models.ForeignKey(
        'prescriptions.MedicationSchedule',
        on_delete=models.CASCADE,
        related_name='reminder_events'
    )
    scheduled_date = models.DateField(db_index=True)
    event_type = models.CharField(max_length=40, choices=EVENT_TYPE_CHOICES, db_index=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_reminder_events'
    )
    recipient_role_snapshot = models.CharField(max_length=30, blank=True, default='')

    in_app_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='PENDING')
    email_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='PENDING')

    in_app_dispatched_at = models.DateTimeField(null=True, blank=True)
    email_attempted_at = models.DateTimeField(null=True, blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_attempt_count = models.PositiveSmallIntegerField(default=0)

    last_error = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'scheduled_date', 'event_type', 'recipient'],
                name='unique_schedule_event_recipient_dispatch'
            )
        ]
        indexes = [
            models.Index(fields=['scheduled_date', 'event_type']),
            models.Index(fields=['email_status', 'email_attempt_count']),
        ]

    def __str__(self):
        recip_str = self.recipient.email if self.recipient else f"DeletedUser({self.recipient_role_snapshot})"
        return f"{self.event_type} on {self.scheduled_date} for {recip_str} (InApp:{self.in_app_status}, Email:{self.email_status})"
