import os
import django
import psycopg2

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from accounts.models import CustomUser
from patients.models import Patient
from doctors.models import SyntheticNPI, DoctorPatientLink, DoctorProfile, HealthFacility
from caregivers.models import CaregiverProfile
from django.contrib.auth.hashers import make_password

conn = psycopg2.connect(dbname='neurocare_nexus', user='postgres', password='irfu123', host='localhost', port='5432')
cur = conn.cursor()

print("--- SYNCING LEGACY PGADMIN DATA TO DJANGO ORM TABLES ---")

# 1. Sync Legacy Synthetic NPIs
cur.execute("SELECT npi, name, hospital, status FROM synthetic_npis;")
for npi, name, hospital, status_str in cur.fetchall():
    s_obj, created = SyntheticNPI.objects.get_or_create(
        npi=npi,
        defaults={'name': name, 'hospital': hospital or 'General Hospital', 'status': status_str or 'Active'}
    )
    if created:
        print(f"[NPI Synced] {npi} - {name}")

# 2. Sync Legacy Patients
cur.execute("SELECT id, name, age, gender, room, condition, risk, status, ehr_notes, doctor_npi FROM patients;")
for pid, name, age, gender, room, condition, risk, p_status, ehr_notes, doc_npi in cur.fetchall():
    p_obj, created = Patient.objects.get_or_create(
        id=pid,
        defaults={
            'name': name,
            'age': age or 50,
            'gender': gender or 'Male',
            'room': room or '101',
            'condition': condition or 'Stable',
            'risk': risk or 10,
            'status': p_status or 'Normal',
            'notes': ehr_notes or ''
        }
    )
    if not created:
        p_obj.name = name
        if doc_npi:
            npi_obj = SyntheticNPI.objects.filter(npi=doc_npi).first()
            if npi_obj:
                p_obj.doctor_npi = npi_obj
        p_obj.save()
    else:
        print(f"[Patient Synced] {pid} - {name}")

# 3. Sync Legacy Users
cur.execute("SELECT email, full_name, phone, role, npi, device_id, agency_id, patient_id, approved, specialization, experience, bio FROM users;")
for email, full_name, phone, role, npi, device_id, agency_id, patient_id, approved, spec, exp, bio in cur.fetchall():
    u_obj = CustomUser.objects.filter(email=email).first()
    if not u_obj:
        u_obj = CustomUser.objects.create_user(
            email=email,
            password='password123',
            full_name=full_name,
            role=role,
            npi=npi or '',
            device_id=device_id or '',
            agency_id=agency_id or '',
            patient_id=patient_id or '',
            approved=approved if approved is not None else True,
            status='ACTIVE'
        )
        print(f"[User Synced] {email} ({role})")

    # If doctor, ensure DoctorProfile exists
    if role == 'doctor':
        dp, _ = DoctorProfile.objects.get_or_create(
            user=u_obj,
            defaults={
                'medical_registration_number': npi or f"REG-{u_obj.id}",
                'state_medical_council': 'Tamil Nadu Medical Council',
                'specialization': spec or 'Cardiology',
                'qualification': 'MBBS, MD',
                'years_of_experience': exp or 10,
                'bio': bio or f"Attending {spec or 'Clinical'} clinician.",
                'verification_status': 'VERIFIED'
            }
        )
        # Check if linked to Sarah Johnson P-102 or Marcus Williams P-204
        for pid in ['P-102', 'P-204']:
            pat = Patient.objects.filter(id=pid).first()
            if pat:
                DoctorPatientLink.objects.get_or_create(doctor=u_obj, patient=pat)

conn.close()
print("--- SYNC COMPLETE ---")
