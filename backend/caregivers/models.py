from django.db import models
from django.conf import settings

class SyntheticCaregiver(models.Model):
    agency_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100)
    agency = models.CharField(max_length=150)
    status = models.CharField(max_length=50, default='Active')

    def __str__(self):
        return f"{self.name} - {self.agency} ({self.agency_id})"

class CaregiverProfile(models.Model):
    TYPE_CHOICES = (
        ('PROFESSIONAL', 'Professional Caregiver'),
        ('FAMILY', 'Family/Personal Caregiver'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='caregiver_profile')
    caregiver_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='PROFESSIONAL')
    full_name = models.CharField(max_length=100)
    contact = models.CharField(max_length=50, blank=True, null=True)
    qualification = models.CharField(max_length=150, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0)
    skills = models.TextField(blank=True, null=True)
    previous_experience = models.TextField(blank=True, null=True)
    current_agency = models.CharField(max_length=150, blank=True, null=True)
    agency_contact = models.CharField(max_length=50, blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.caregiver_type})"

class CaregiverPatientLink(models.Model):
    caregiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'caregiver'}, 
        related_name='caregiver_links'
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='caregiver_links')
    is_read_only = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('caregiver', 'patient')

    def __str__(self):
        return f"Caregiver Link: {self.caregiver.email} <-> {self.patient.id}"
