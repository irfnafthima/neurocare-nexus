from django.db import models
from django.conf import settings

class SyntheticNPI(models.Model):
    npi = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)
    hospital = models.CharField(max_length=150)
    status = models.CharField(max_length=50, default='Active')

    def __str__(self):
        return f"{self.name} - {self.hospital} ({self.npi})"

class ReferenceDoctorRegistry(models.Model):
    registration_number = models.CharField(max_length=50, primary_key=True, db_index=True)
    reference_id = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    doctor_name = models.CharField(max_length=100)
    normalized_name = models.CharField(max_length=150, db_index=True, blank=True, default='')
    council = models.CharField(max_length=150, db_index=True)
    qualification = models.CharField(max_length=150)
    registration_year = models.IntegerField()
    registration_date = models.DateField(null=True, blank=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    registration_status = models.CharField(max_length=20, default='ACTIVE', db_index=True)
    source_type = models.CharField(max_length=50, default='SYNTHETIC_REFERENCE')
    source_reference = models.CharField(max_length=150, blank=True, null=True)
    source_year = models.IntegerField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['normalized_name']),
            models.Index(fields=['council']),
            models.Index(fields=['registration_status']),
        ]

    def __str__(self):
        return f"{self.doctor_name} ({self.registration_number} - {self.council})"

class HealthFacility(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    )
    facility_id = models.CharField(max_length=50, unique=True, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=150)
    facility_type = models.CharField(max_length=50) # e.g. Hospital, Clinic
    address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100)
    registration_identifier = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=50, blank=True, default='')
    website = models.CharField(max_length=100, blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    source_type = models.CharField(max_length=50, default='SYNTHETIC_REFERENCE', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"

class DoctorDisciplinaryRecord(models.Model):
    disciplinary_id = models.CharField(max_length=50, unique=True)
    doctor = models.ForeignKey(ReferenceDoctorRegistry, on_delete=models.CASCADE, related_name='disciplinary_records')
    registration_number = models.CharField(max_length=50, db_index=True)
    doctor_name = models.CharField(max_length=100)
    state_medical_council = models.CharField(max_length=150)
    action_type = models.CharField(max_length=50) # SUSPENSION, BLACKLIST, RESTORATION, REMOVAL
    status = models.CharField(max_length=50, db_index=True) # ACTIVE, BLACKLISTED, REMOVED, RESTORED
    suspended_date = models.DateField(null=True, blank=True)
    restored_date = models.DateField(null=True, blank=True)
    source_type = models.CharField(max_length=50, default='SYNTHETIC_TEST_REFERENCE')
    source_reference = models.CharField(max_length=150, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.disciplinary_id} - {self.doctor_name} ({self.action_type}: {self.status})"

class ReferenceDoctorAffiliation(models.Model):
    affiliation_id = models.CharField(max_length=50, unique=True)
    reference_doctor = models.ForeignKey(ReferenceDoctorRegistry, on_delete=models.CASCADE, related_name='affiliations')
    facility = models.ForeignKey(HealthFacility, on_delete=models.CASCADE, related_name='reference_doctor_affiliations')
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=50) # FULL_TIME, PART_TIME, VISITING_CONSULTANT, CONSULTANT, RESIDENT
    status = models.CharField(max_length=50) # CURRENT, ENDED
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, default='PENDING')
    source_type = models.CharField(max_length=50, default='SYNTHETIC_REFERENCE')

    def __str__(self):
        return f"{self.reference_doctor} at {self.facility.name} ({self.affiliation_id})"


class DoctorProfile(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('UNDER_REVIEW', 'Under Review'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
        ('EXPIRED', 'Expired'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    medical_registration_number = models.CharField(max_length=50)
    state_medical_council = models.CharField(max_length=150)
    qualification = models.CharField(max_length=150)
    specialization = models.CharField(max_length=100)
    additional_qualifications = models.CharField(max_length=255, blank=True, null=True)
    hpr_id = models.CharField(max_length=100, blank=True, null=True)
    years_of_experience = models.IntegerField(default=0)
    verification_status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.full_name} - Reg: {self.medical_registration_number}"

class DoctorFacilityAffiliation(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='facility_affiliations')
    facility = models.ForeignKey(HealthFacility, on_delete=models.CASCADE, related_name='doctor_affiliations')
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    employment_status = models.CharField(max_length=50, default='Active') # e.g. Active, Inactive
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_source = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.doctor} at {self.facility.name}"

class VerificationRecord(models.Model):
    TYPE_CHOICES = (
        ('PROFESSIONAL_REGISTRATION', 'Professional Registration'),
        ('IDENTITY_MATCH', 'Identity Match'),
        ('QUALIFICATION', 'Qualification'),
        ('HOSPITAL_AFFILIATION', 'Hospital Affiliation'),
        ('ADMIN_REVIEW', 'Admin Review'),
    )
    RESULT_CHOICES = (
        ('EXACT_MATCH', 'Exact Match'),
        ('LIKELY_MATCH', 'Likely Match'),
        ('MISMATCH', 'Mismatch'),
        ('NOT_FOUND', 'Not Found'),
        ('MANUAL_REVIEW', 'Manual Review'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verification_records')
    verification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    source = models.CharField(max_length=150)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_verifications')
    verified_at = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.verification_type}: {self.result}"

class DoctorConnectionRequest(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Declined', 'Declined'),
    )
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='connection_requests')
    doctor_npi = models.ForeignKey(SyntheticNPI, on_delete=models.CASCADE, related_name='connection_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('patient', 'doctor_npi')

    def __str__(self):
        return f"Req: {self.patient_id} -> {self.doctor_npi_id} ({self.status})"

class DoctorPatientLink(models.Model):
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='doctor_links')
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'doctor'}, 
        related_name='patient_links'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'doctor')

    def __str__(self):
        return f"Link: {self.patient_id} <-> {self.doctor.email}"
