from django.db import models
from django.conf import settings
from django.utils import timezone

class MedicalRecord(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='records')
    clinician_name = models.CharField(max_length=100)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for {self.patient_id} by {self.clinician_name} at {self.created_at}"

class PatientCondition(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Managed', 'Managed'),
        ('Resolved', 'Resolved'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='conditions')
    condition_name = models.CharField(max_length=150)
    description = models.TextField(blank=True, default='')
    diagnosis_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.condition_name} ({self.patient_id})"

class PatientAllergy(models.Model):
    SEVERITY_CHOICES = (
        ('Mild', 'Mild'),
        ('Moderate', 'Moderate'),
        ('Severe', 'Severe'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=150)
    reaction = models.CharField(max_length=200, blank=True, default='')
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, default='Moderate')
    notes = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Allergy: {self.allergen} for {self.patient_id}"

class PatientMedication(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='medications')
    medicine_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100)
    dosage_unit = models.CharField(max_length=50, blank=True, default='mg')
    frequency = models.CharField(max_length=100)
    route = models.CharField(max_length=50, blank=True, default='Oral')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    prescribing_doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescribed_medications')
    prescribing_doctor_name = models.CharField(max_length=150, blank=True, default='')
    instructions = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.medicine_name} {self.dosage} for {self.patient_id}"

class PatientConsultation(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_consultations')
    doctor_name = models.CharField(max_length=150, blank=True, default='')
    consultation_date = models.DateField()
    reason = models.CharField(max_length=255)
    clinical_notes = models.TextField(blank=True, default='')
    follow_up_notes = models.TextField(blank=True, default='')
    next_consultation_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation: {self.patient_id} with {self.doctor_name or self.doctor_id} on {self.consultation_date}"

class NextConsultation(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='next_consultations')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='scheduled_consultations')
    doctor_name = models.CharField(max_length=150, blank=True, default='')
    consultation_date = models.DateField()
    time = models.CharField(max_length=50, blank=True, default='10:00 AM')
    facility = models.CharField(max_length=150, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Next Consultation: {self.patient_id} on {self.consultation_date} {self.time}"

class MedicalDocument(models.Model):
    TYPE_CHOICES = (
        ('Blood Test', 'Blood Test'),
        ('Scan', 'Scan Report'),
        ('Consultation', 'Consultation Report'),
        ('Prescription', 'Prescription Document'),
        ('Discharge Summary', 'Discharge Summary'),
        ('Other', 'Other Medical Document'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='documents')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='uploaded_documents')
    document_type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='Other')
    title = models.CharField(max_length=150)
    upload_date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, default='')
    file = models.FileField(upload_to='medical_documents/')
    consultation = models.ForeignKey(PatientConsultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')

    def __str__(self):
        return f"{self.title} ({self.document_type}) for {self.patient_id}"

class VitalMeasurement(models.Model):
    SOURCE_CHOICES = (
        ('MANUAL', 'Manual entry'),
        ('DEVICE', 'Device / ESP32'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='vitals')
    measurement_time = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='MANUAL')
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='entered_vitals')
    entered_by_name = models.CharField(max_length=100, blank=True, default='')
    heart_rate = models.FloatField(null=True, blank=True)
    spo2 = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    systolic_bp = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    blood_glucose = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        valid_sources = [choice[0] for choice in self.SOURCE_CHOICES]
        if self.source not in valid_sources:
            raise ValidationError(f"Invalid source '{self.source}'. Must be one of {valid_sources}.")

        # At least 1 clinical measurement field must be non-null
        vitals_provided = [
            self.heart_rate, self.spo2, self.temperature,
            self.respiratory_rate, self.systolic_bp, self.diastolic_bp,
            self.weight, self.blood_glucose
        ]
        if not any(v is not None for v in vitals_provided):
            raise ValidationError("At least one clinical vital measurement value must be provided.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def source_label(self):
        return 'Manual entry' if self.source == 'MANUAL' else 'Device / ESP32'

    def __str__(self):
        return f"Vital ({self.source}): Patient {self.patient_id} at {self.measurement_time}"

