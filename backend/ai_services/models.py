from django.db import models
from django.conf import settings
from patients.models import Patient

class MedicationKnowledgeBase(models.Model):
    CATEGORY_CHOICES = (
        ('GENERAL_INFORMATION', 'General Information'),
        ('OTC_INFORMATION', 'Over-The-Counter Information'),
        ('PRESCRIPTION_MEDICINE', 'Prescription Required Medicine'),
        ('RESTRICTED', 'Restricted Medicine'),
    )

    generic_name = models.CharField(max_length=150, db_index=True, unique=True)
    brand_names = models.CharField(max_length=255, blank=True, default='')
    medication_class = models.CharField(max_length=150, db_index=True)
    general_uses = models.TextField(blank=True, default='')
    common_precautions = models.TextField(blank=True, default='')
    common_contraindications = models.TextField(blank=True, default='')
    allergy_considerations = models.TextField(blank=True, default='')
    common_interactions = models.TextField(blank=True, default='')
    dosage_reference = models.TextField(blank=True, default='')
    age_precautions = models.TextField(blank=True, default='')
    pregnancy_precautions = models.TextField(blank=True, default='')
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='PRESCRIPTION_MEDICINE')
    source_reference = models.CharField(max_length=255, default='FDA Label Registry / National Formulary 2026')
    source_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.generic_name} ({self.medication_class}) - {self.source_reference}"

class DoctorMedicationReviewRequest(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Doctor Review'),
        ('REVIEWED', 'Reviewed by Clinician'),
        ('DECLINED', 'Declined'),
    )

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medication_review_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_medication_reviews')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_medication_reviews', null=True, blank=True)
    medication_name = models.CharField(max_length=150)
    question = models.TextField()
    safety_status = models.CharField(max_length=50, default='REVIEW_RECOMMENDED')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    doctor_response = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review Request for {self.medication_name} (Patient {self.patient_id}) - {self.status}"
