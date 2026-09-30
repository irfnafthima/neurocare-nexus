from django.db import models
from django.conf import settings

class Prescription(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    prescribing_doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'doctor'},
        related_name='issued_prescriptions',
        null=True,
        blank=True
    )
    prescribing_doctor_name = models.CharField(max_length=150, blank=True, default='')
    prescription_date = models.DateField(null=True, blank=True)
    medicines = models.TextField(blank=True, default='')
    dosage = models.CharField(max_length=100, blank=True, default='')
    frequency = models.CharField(max_length=100, blank=True, default='')
    duration = models.CharField(max_length=100, blank=True, default='7 days')
    instructions = models.TextField(blank=True, default='')
    document = models.FileField(upload_to='prescription_documents/', null=True, blank=True)
    status = models.CharField(max_length=50, default='Active')

    def __str__(self):
        return f"Prescription for {self.patient_id}"

class MedicationSchedule(models.Model):
    prescription = models.ForeignKey(
        'prescriptions.Prescription',
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    scheduled_time = models.TimeField(help_text="Time of day for dose administration in local time")
    time_label = models.CharField(max_length=50, blank=True, default='')
    start_date = models.DateField(null=True, blank=True, help_text="Schedule active start date")
    end_date = models.DateField(null=True, blank=True, help_text="Schedule active end date")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_time']
        constraints = [
            models.UniqueConstraint(
                fields=['prescription', 'scheduled_time'],
                condition=models.Q(is_active=True),
                name='unique_active_prescription_schedule_time'
            )
        ]
        indexes = [
            models.Index(fields=['prescription', 'is_active']),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("start_date must be before or equal to end_date.")

    def __str__(self):
        return f"Schedule for Rx #{self.prescription_id} at {self.scheduled_time} (Active: {self.is_active})"

class MedicationDoseLog(models.Model):
    STATUS_CHOICES = (
        ('TAKEN', 'Taken'),
        ('SKIPPED', 'Skipped'),
    )

    schedule = models.ForeignKey(
        'prescriptions.MedicationSchedule',
        on_delete=models.CASCADE,
        related_name='dose_logs'
    )
    scheduled_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    action_at = models.DateTimeField(null=True, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_doses'
    )
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', 'schedule__scheduled_time']
        constraints = [
            models.UniqueConstraint(
                fields=['schedule', 'scheduled_date'],
                name='unique_medication_dose_occurrence'
            )
        ]
        indexes = [
            models.Index(fields=['scheduled_date', 'status']),
        ]

    def __str__(self):
        return f"DoseLog: Schedule #{self.schedule_id} on {self.scheduled_date} -> {self.status} (by {self.marked_by_id})"

