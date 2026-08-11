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
