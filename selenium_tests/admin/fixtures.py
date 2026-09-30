import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.utils import timezone
from accounts.models import CustomUser, AuditLog
from doctors.models import DoctorProfile, ReferenceDoctorRegistry, HealthFacility, DoctorFacilityAffiliation
from patients.models import Patient
from devices.models import SyntheticDevice, WearableDevice
from selenium_tests import config

def init_admin_test_data():
    """Seed / Reset dedicated Selenium Admin test accounts without touching real doctors."""
    
    # 1. Admin account
    admin_user, created = CustomUser.objects.get_or_create(
        email=config.ADMIN_EMAIL,
        defaults={
            'full_name': 'Selenium Test Admin',
            'phone': '+1 (555) 902-1000',
            'role': 'admin',
            'access_key': config.ADMIN_ACCESS_KEY,
            'approved': True,
            'status': 'ACTIVE',
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin_user.set_password(config.ADMIN_PASSWORD)
    admin_user.approved = True
    admin_user.status = 'ACTIVE'
    admin_user.access_key = config.ADMIN_ACCESS_KEY
    admin_user.save()

    # 2. Patient account
    patient_user, _ = CustomUser.objects.get_or_create(
        email=config.PATIENT_EMAIL,
        defaults={
            'full_name': 'Selenium Patient',
            'phone': '+1 (555) 777-1111',
            'role': 'patient',
            'device_id': config.PATIENT_DEVICE_ID,
            'patient_id': config.PATIENT_ID,
            'approved': True,
            'status': 'ACTIVE'
        }
    )
    patient_user.set_password(config.PATIENT_PASSWORD)
    patient_user.save()

    # 3. Pending Doctor account for ADM08, ADM09, ADM10, ADM11
    pending_doc, _ = CustomUser.objects.get_or_create(
        email=config.PENDING_DOCTOR_EMAIL,
        defaults={
            'full_name': 'Dr. Selenium Pending Candidate',
            'phone': '+91 98765 43210',
            'role': 'doctor',
            'approved': False,
            'status': 'PENDING'
        }
    )
    pending_doc.set_password(config.PENDING_DOCTOR_PASSWORD)
    pending_doc.approved = False
    pending_doc.status = 'PENDING'
    pending_doc.npi = config.PENDING_DOCTOR_NPI
    pending_doc.save()

    # Reference registry entry for pending doctor
    ReferenceDoctorRegistry.objects.get_or_create(
        registration_number=config.PENDING_DOCTOR_NPI,
        defaults={
            'doctor_name': 'Dr. Selenium Pending Candidate',
            'council': 'Karnataka Medical Council',
            'qualification': 'MBBS, MD (Neurology)',
            'registration_year': 2018
        }
    )

    doc_profile, _ = DoctorProfile.objects.get_or_create(
        user=pending_doc,
        defaults={
            'medical_registration_number': config.PENDING_DOCTOR_NPI,
            'state_medical_council': 'Karnataka Medical Council',
            'qualification': 'MBBS, MD (Neurology)',
            'specialization': 'Neurology',
            'years_of_experience': 6,
            'verification_status': 'PENDING'
        }
    )
    doc_profile.medical_registration_number = config.PENDING_DOCTOR_NPI
    doc_profile.state_medical_council = 'Karnataka Medical Council'
    doc_profile.qualification = 'MBBS, MD (Neurology)'
    doc_profile.specialization = 'Neurology'
    doc_profile.years_of_experience = 6
    doc_profile.verification_status = 'PENDING'
    doc_profile.save()

    # 4. Reject Doctor account for ADM12
    reject_doc, _ = CustomUser.objects.get_or_create(
        email=config.REJECT_DOCTOR_EMAIL,
        defaults={
            'full_name': 'Dr. Selenium Reject Candidate',
            'phone': '+91 98765 43211',
            'role': 'doctor',
            'approved': False,
            'status': 'PENDING'
        }
    )
    reject_doc.set_password(config.REJECT_DOCTOR_PASSWORD)
    reject_doc.approved = False
    reject_doc.status = 'PENDING'
    reject_doc.npi = config.REJECT_DOCTOR_NPI
    reject_doc.save()

    rej_profile, _ = DoctorProfile.objects.get_or_create(
        user=reject_doc,
        defaults={
            'medical_registration_number': config.REJECT_DOCTOR_NPI,
            'state_medical_council': 'Maharashtra Medical Council',
            'qualification': 'MBBS',
            'specialization': 'General Medicine',
            'years_of_experience': 2,
            'verification_status': 'UNDER_REVIEW'
        }
    )
    rej_profile.medical_registration_number = config.REJECT_DOCTOR_NPI
    rej_profile.state_medical_council = 'Maharashtra Medical Council'
    rej_profile.verification_status = 'UNDER_REVIEW'
    rej_profile.save()

    # Ensure some audit logs exist
    if AuditLog.objects.count() == 0:
        AuditLog.objects.create(
            username='System Admin',
            action='System Initialization',
            target='EHR Node Alpha',
            status='Success'
        )

if __name__ == '__main__':
    init_admin_test_data()
    print("Admin test data initialized successfully.")
