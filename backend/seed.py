import os
import django
from datetime import datetime

# Set up django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from doctors.models import SyntheticNPI, ReferenceDoctorRegistry, HealthFacility, DoctorProfile, DoctorFacilityAffiliation
from devices.models import SyntheticDevice
from caregivers.models import SyntheticCaregiver, CaregiverProfile
from patients.models import SyntheticPatient, Patient, Appointment, FamilyPatientLink
from accounts.models import CustomUser, AuditLog
from monitoring.models import SensorReading

def seed():
    print("Seeding synthetic data registries...")
    
    # 1. Seed Synthetic NPIs
    npis = [
        ('1982039485', 'Dr. Sarah Jenkins', 'City Care Medical Center', 'Active - Verified Registry'),
        ('1092837465', 'Dr. Michael Chang', 'Riverside General Hospital', 'Active - Verified Registry'),
        ('1827364509', 'Dr. Elizabeth Vance', 'Apex Valley Hospital', 'Active - Verified Registry'),
        ('1029384756', 'Dr. Rachel Kim', 'Pacific Horizon Medical Center', 'Active - Verified Registry'),
        ('1203948576', 'Dr. Samuel Torres', 'Riverside General Hospital', 'Active - Verified Registry'),
        ('1492039482', 'Dr. Lisa Wang', 'City Care Medical Center', 'Active - Verified Registry'),
        ('1738291049', 'Dr. David Foster', 'Apex Valley Hospital', 'Active - Verified Registry'),
        ('1102938475', 'Dr. James Carter', 'Pacific Horizon Medical Center', 'Active - Verified Registry'),
    ]
    for npi, name, hosp, stat in npis:
        SyntheticNPI.objects.get_or_create(npi=npi, defaults={'name': name, 'hospital': hosp, 'status': stat})

    # 1.1 Seed Health Facilities
    print("Seeding Health Facilities...")
    facilities = [
        ('Riverside General Hospital', 'Hospital', '12, MG Road', 'Bengaluru', 'Karnataka', 'HOSP-BLR-001', '+91 80 1234 5678', 'https://riverside.org'),
        ('City Care Medical Center', 'Hospital', '45, Gachibowli', 'Hyderabad', 'Telangana', 'HOSP-HYD-002', '+91 40 2345 6789', 'https://citycare.org'),
        ('Pacific Horizon Medical Center', 'Hospital', '89, Marine Drive', 'Mumbai', 'Maharashtra', 'HOSP-BOM-003', '+91 22 3456 7890', 'https://pacifichorizon.org'),
        ('Apex Valley Hospital', 'Hospital', '34, OMR Road', 'Chennai', 'Tamil Nadu', 'HOSP-MAA-004', '+91 44 4567 8901', 'https://apexvalley.org'),
    ]
    facility_map = {}
    for name, ftype, addr, city, state, reg_id, contact, web in facilities:
        fac, created = HealthFacility.objects.get_or_create(
            registration_identifier=reg_id,
            defaults={
                'name': name,
                'facility_type': ftype,
                'address': addr,
                'city': city,
                'state': state,
                'contact': contact,
                'website': web,
                'verification_status': 'VERIFIED',
                'verified_at': datetime.now()
            }
        )
        facility_map[name] = fac

    # 1.2 Seed Reference Doctor Registry
    print("Seeding Reference Doctor Registry...")
    ref_docs = [
        ('1029384756', 'Dr. Rachel Kim', 'Karnataka Medical Council', 'MBBS, MD (Cardiology)', 2015),
        ('1092837465', 'Dr. Michael Chang', 'Maharashtra Medical Council', 'MBBS, MS (Neurology)', 2012),
        ('1982039485', 'Dr. Sarah Jenkins', 'Karnataka Medical Council', 'MBBS, MD', 2018),
        ('1827364509', 'Dr. Elizabeth Vance', 'Tamil Nadu Medical Council', 'MBBS, MS', 2014),
        ('1203948576', 'Dr. Samuel Torres', 'Maharashtra Medical Council', 'MBBS, MD', 2016),
        ('9998887776', 'Dr. Rajesh Kumar', 'Delhi Medical Council', 'MBBS, MD', 2010),
    ]
    for reg_num, doc_name, council, qual, reg_yr in ref_docs:
        ReferenceDoctorRegistry.objects.get_or_create(
            registration_number=reg_num,
            defaults={
                'doctor_name': doc_name,
                'council': council,
                'qualification': qual,
                'registration_year': reg_yr
            }
        )
        
    # 2. Seed Synthetic Devices
    devices = [
        ('NP-101', '00:1B:44:11:3A:A1', 'Pre-registered / Unassigned'),
        ('NP-102', '00:1B:44:11:3A:B7', 'Pre-registered / Unassigned'),
        ('NP-103', '00:1B:44:11:3B:C5', 'Pre-registered / Unassigned'),
        ('NP-204', '00:1B:44:11:3C:A9', 'Pre-registered / Unassigned'),
        ('NP-108', '00:1B:44:11:3E:D2', 'Pre-registered / Unassigned'),
        ('NP-215', '00:1B:44:11:4A:11', 'Pre-registered / Unassigned'),
        ('NP-112', '00:1B:44:11:4B:22', 'Pre-registered / Unassigned'),
        ('NP-305', '00:1B:44:11:5C:33', 'Pre-registered / Unassigned'),
    ]
    for serial, mac, stat in devices:
        SyntheticDevice.objects.get_or_create(serial=serial, defaults={'mac': mac, 'status': stat})
        
    # 3. Seed Synthetic Caregivers
    caregivers = [
        ('CG-204', 'Maria Santos, RN', 'Beacon Home Health Services', 'Active License'),
        ('CG-105', 'David Miller, LPN', 'Metro Visiting Nurses', 'Active License'),
        ('CG-302', 'Jessica Taylor, CNA', 'Apex Care Network', 'Active License'),
        ('CG-118', 'Robert Chen, RN', 'Beacon Home Health Services', 'Active License'),
        ('CG-245', 'Emily Watson, LPN', 'Metro Visiting Nurses', 'Active License'),
    ]
    for cid, name, ag, stat in caregivers:
        SyntheticCaregiver.objects.get_or_create(agency_id=cid, defaults={'name': name, 'agency': ag, 'status': stat})
        
    # 4. Seed Synthetic Patients
    patients = [
        ('P-102', 'P-102', 'Sarah Johnson', 'Consent Verified'),
        ('P-204', 'P-204', 'Marcus Williams', 'Consent Verified'),
        ('P-108', 'P-108', 'Elena Rodriguez', 'Consent Verified'),
        ('P-215', 'P-215', 'James Smith', 'Consent Verified'),
        ('P-112', 'P-112', 'Linda Davis', 'Consent Verified'),
        ('P-305', 'P-305', 'William Miller', 'Consent Verified'),
    ]
    for pid, code, name, stat in patients:
        SyntheticPatient.objects.get_or_create(patient_id=pid, defaults={'code': code, 'patient_name': name, 'status': stat})

    print("Seeding admin account...")
    # System Admin Account
    admin_user, created = CustomUser.objects.get_or_create(
        email='admin@nexus.com',
        defaults={
            'full_name': 'System Administrator',
            'phone': '+1 (555) 001-2345',
            'role': 'admin',
            'access_key': 'ADM-90210',
            'approved': True,
            'status': 'ACTIVE',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('password123')
        admin_user.save()

    # Seeding clinical patient records
    # P-102
    doctor_obj = SyntheticNPI.objects.get(npi='1029384756')
    p102, created = Patient.objects.get_or_create(
        id='P-102',
        defaults={
            'name': 'Sarah Johnson',
            'age': 72,
            'gender': 'Female',
            'room': '102',
            'condition': 'Heart Failure Post-op',
            'risk': 12,
            'status': 'Normal',
            'ehr_notes': 'Patient stable. MAX30102 shows healthy BPM. No postural issues.',
            'doctor_npi': doctor_obj
        }
    )
    if created:
        # Telemetry
        SensorReading.objects.create(
            patient=p102,
            heart_rate=72,
            spo2=98,
            temperature=36.80,
            accel_x=0.05,
            accel_y=0.98,
            accel_z=0.04,
            gyro_x=0.50,
            gyro_y=-1.20,
            gyro_z=0.30,
            fall_detected=False,
            esp32_connected=True,
            esp32_battery=92,
            esp32_rssi=-65
        )
        # Appointments
        Appointment.objects.create(patient=p102, details='Dr. Rachel Kim — Cardiology consultation with Sarah Johnson', time='Today, 02:00 PM')
        Appointment.objects.create(patient=p102, details='Home Care Nurse — Patch replacement checkup', time='Tomorrow, 09:00 AM')

    # P-204
    p204, created = Patient.objects.get_or_create(
        id='P-204',
        defaults={
            'name': 'Marcus Williams',
            'age': 65,
            'gender': 'Male',
            'room': '204',
            'condition': 'Post-stroke Monitoring',
            'risk': 15,
            'status': 'Normal',
            'ehr_notes': 'Vitals within baseline bounds.',
            'doctor_npi': doctor_obj
        }
    )
    if created:
        # Telemetry
        SensorReading.objects.create(
            patient=p204,
            heart_rate=68,
            spo2=97,
            temperature=36.60,
            accel_x=-0.02,
            accel_y=0.99,
            accel_z=-0.05,
            gyro_x=-0.10,
            gyro_y=0.80,
            gyro_z=-0.20,
            fall_detected=False,
            esp32_connected=True,
            esp32_battery=85,
            esp32_rssi=-70
        )
        # Appointments
        Appointment.objects.create(patient=p204, details='Maria Santos, RN — Biometric review with Marcus Williams', time='Tomorrow, 10:30 AM')
        Appointment.objects.create(patient=p204, details='Dr. Samuel Torres — EEG interpretation checkup', time='Next Monday, 04:00 PM')

    print("Demo accounts and patients seeded successfully!")

if __name__ == '__main__':
    seed()
