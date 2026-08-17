from django.db import models
from django.conf import settings

class SyntheticPatient(models.Model):
    patient_id = models.CharField(max_length=20, primary_key=True)
    code = models.CharField(max_length=20, unique=True)
    patient_name = models.CharField(max_length=100)
    status = models.CharField(max_length=50, default='Consent Verified')

    def __str__(self):
        return f"{self.patient_name} ({self.patient_id})"

class Patient(models.Model):
    id = models.CharField(max_length=20, primary_key=True) # e.g. 'P-102'
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    room = models.CharField(max_length=10)
    condition = models.CharField(max_length=255)
    risk = models.IntegerField(default=0)
    status = models.CharField(max_length=50, default='Normal')
    ehr_notes = models.TextField(blank=True, default='')
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=25, blank=True, default='')
    address = models.TextField(blank=True, default='')
    emergency_contact_name = models.CharField(max_length=100, blank=True, default='')
    emergency_contact_phone = models.CharField(max_length=25, blank=True, default='')
    blood_group = models.CharField(max_length=10, blank=True, default='')
    doctor_npi = models.ForeignKey(
        'doctors.SyntheticNPI', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='patients'
    )

    def __str__(self):
        return f"{self.name} ({self.id})"

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    details = models.CharField(max_length=255)
    time = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.patient_id} - {self.details} at {self.time}"

class FamilyPatientLink(models.Model):
    family = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'family'}, 
        related_name='family_links'
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='family_links')
    is_approved = models.BooleanField(default=False)
    can_edit_clinical = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('family', 'patient')

    def __str__(self):
        return f"Family Link: {self.family.email} <-> {self.patient.id} (Approved: {self.is_approved}, Edit: {self.can_edit_clinical})"
