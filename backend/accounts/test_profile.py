from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from patients.models import Patient
from doctors.models import DoctorProfile
from caregivers.models import CaregiverProfile

User = get_user_model()


class UserProfileMeTests(TestCase):
    """
    Comprehensive Security & Authorization Tests for Role-Based Self-Service Edit Profile API.
    Covers Patient, Doctor, Caregiver, and Family Member roles.
    Verifies mass-assignment defenses, identity immutability, and database persistence.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Patient User & Record
        self.patient_user = User.objects.create_user(
            email='test_patient_edit@nexus.test',
            password='TestPatientPass123!',
            full_name='Original Patient Name',
            role='patient',
            device_id='NP-901',
            patient_id='P-901',
            phone='+91 9876543210'
        )
        self.patient_record = Patient.objects.create(
            id='P-901',
            name='Original Patient Name',
            age=30,
            gender='Female',
            room='101-A',
            condition='Hypertension',
            risk=2,
            dob=date(1994, 5, 15),
            phone='+91 9876543210',
            blood_group='O+',
            address='123 Initial Street, Bangalore',
            emergency_contact_name='Original Contact',
            emergency_contact_phone='+91 9123456780'
        )

        # 2. Doctor User & Profile
        self.doctor_user = User.objects.create_user(
            email='test_doctor_edit@nexus.test',
            password='TestDoctorPass123!',
            full_name='Dr. Original Doctor',
            role='doctor',
            phone='+91 9876543211',
            specialization='Cardiology',
            experience=10
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            medical_registration_number='KMC-TEST-998877',
            state_medical_council='Karnataka Medical Council',
            qualification='MBBS, MD',
            specialization='Cardiology',
            additional_qualifications='FACC',
            hpr_id='HPR-TEST-12345',
            years_of_experience=10,
            verification_status='VERIFIED'
        )

        # 3. Caregiver User & Profile
        self.caregiver_user = User.objects.create_user(
            email='test_caregiver_edit@nexus.test',
            password='TestCaregiverPass123!',
            full_name='Original Caregiver Name',
            role='caregiver',
            phone='+91 9876543212',
            agency_id='CG-TEST-456'
        )
        self.caregiver_profile = CaregiverProfile.objects.create(
            user=self.caregiver_user,
            caregiver_type='PROFESSIONAL',
            full_name='Original Caregiver Name',
            contact='+91 9876543212',
            qualification='B.Sc Nursing',
            years_of_experience=5,
            skills='Elderly Care, ICU Monitoring',
            previous_experience='3 years at Apollo',
            current_agency='Apex Healthcare',
            agency_contact='+91 8012345678',
            verification_status='VERIFIED'
        )

        # 4. Family Member User
        self.family_user = User.objects.create_user(
            email='test_family_edit@nexus.test',
            password='TestFamilyPass123!',
            full_name='Original Family Name',
            role='family',
            phone='+91 9876543213',
            patient_id='P-901'
        )

    # =========================================================================
    # 1. UNAUTHENTICATED ACCESS SECURITY
    # =========================================================================

    def test_unauthenticated_get_rejected(self):
        """Unauthenticated GET /api/profile/me must return HTTP 401."""
        response = self.client.get('/api/profile/me')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_patch_rejected(self):
        """Unauthenticated PATCH /api/profile/me must return HTTP 401."""
        response = self.client.patch('/api/profile/me', {'fullName': 'Hacker Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # =========================================================================
    # 2. PATIENT PROFILE TESTS
    # =========================================================================

    def test_patient_get_profile(self):
        """Patient can retrieve their own consolidated profile."""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.get('/api/profile/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['email'], 'test_patient_edit@nexus.test')
        self.assertEqual(data['fullName'], 'Original Patient Name')
        self.assertEqual(data['patientId'], 'P-901')
        self.assertEqual(data['bloodGroup'], 'O+')
        self.assertEqual(data['address'], '123 Initial Street, Bangalore')

    def test_patient_update_permitted_fields_persisted(self):
        """Patient can update permitted demographic and contact fields with database persistence."""
        self.client.force_authenticate(user=self.patient_user)
        payload = {
            'fullName': 'Updated Patient Jane',
            'phone': '+91 9998887776',
            'dob': '1992-08-20',
            'gender': 'Female',
            'bloodGroup': 'AB+',
            'address': '456 New Colony, MG Road, Bangalore',
            'emergencyContactName': 'Updated Emergency Contact',
            'emergencyContactPhone': '+91 9887766554',
            'bio': 'Patient with managed hypertension.'
        }
        response = self.client.patch('/api/profile/me', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify CustomUser database persistence
        self.patient_user.refresh_from_db()
        self.assertEqual(self.patient_user.full_name, 'Updated Patient Jane')
        self.assertEqual(self.patient_user.phone, '+91 9998887776')
        self.assertEqual(self.patient_user.bio, 'Patient with managed hypertension.')

        # Verify Patient record database persistence
        self.patient_record.refresh_from_db()
        self.assertEqual(self.patient_record.name, 'Updated Patient Jane')
        self.assertEqual(self.patient_record.phone, '+91 9998887776')
        self.assertEqual(self.patient_record.dob, date(1992, 8, 20))
        self.assertEqual(self.patient_record.blood_group, 'AB+')
        self.assertEqual(self.patient_record.address, '456 New Colony, MG Road, Bangalore')
        self.assertEqual(self.patient_record.emergency_contact_name, 'Updated Emergency Contact')
        self.assertEqual(self.patient_record.emergency_contact_phone, '+91 9887766554')

    def test_patient_mass_assignment_attack_fails_to_change_protected_fields(self):
        """Patient attempting to escalate privileges or modify protected clinical/identity fields is blocked."""
        self.client.force_authenticate(user=self.patient_user)
        malicious_payload = {
            'fullName': 'Jane Patient Valid Name',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True,
            'email': 'hacked_patient@evil.test',
            'id': 99999,
            'user_id': 99999,
            'approved': True,
            'status': 'HACKED',
            'patient_id': 'P-HACKED-999',
            'device_id': 'NP-HACKED-999',
            'room': 'VIP-SUITE',
            'condition': 'Cured',
            'risk': 0,
            'ehr_notes': 'Fake cleared doctor notes'
        }
        response = self.client.patch('/api/profile/me', malicious_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify CustomUser protected fields remained strictly untouched
        self.patient_user.refresh_from_db()
        self.assertEqual(self.patient_user.role, 'patient')
        self.assertFalse(self.patient_user.is_staff)
        self.assertFalse(self.patient_user.is_superuser)
        self.assertEqual(self.patient_user.email, 'test_patient_edit@nexus.test')
        self.assertEqual(self.patient_user.patient_id, 'P-901')
        self.assertEqual(self.patient_user.device_id, 'NP-901')

        # Verify Patient record protected clinical fields remained untouched
        self.patient_record.refresh_from_db()
        self.assertEqual(self.patient_record.id, 'P-901')
        self.assertEqual(self.patient_record.room, '101-A')
        self.assertEqual(self.patient_record.condition, 'Hypertension')
        self.assertEqual(self.patient_record.risk, 2)
        self.assertEqual(self.patient_record.ehr_notes, '')

    # =========================================================================
    # 3. DOCTOR PROFILE TESTS
    # =========================================================================

    def test_doctor_get_profile(self):
        """Doctor can retrieve their own consolidated profile."""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.get('/api/profile/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['email'], 'test_doctor_edit@nexus.test')
        self.assertEqual(data['fullName'], 'Dr. Original Doctor')
        self.assertEqual(data['medicalRegistrationNumber'], 'KMC-TEST-998877')
        self.assertEqual(data['verificationStatus'], 'VERIFIED')
        self.assertEqual(data['specialization'], 'Cardiology')

    def test_doctor_update_permitted_fields_persisted(self):
        """Doctor can update permitted contact, qualification, and specialization info."""
        self.client.force_authenticate(user=self.doctor_user)
        payload = {
            'fullName': 'Dr. Updated Cardiologist',
            'phone': '+91 9876500001',
            'specialization': 'Interventional Cardiology',
            'qualification': 'MBBS, MD, DM (Cardiology)',
            'additionalQualifications': 'FACC, FSCAI',
            'yearsOfExperience': 14,
            'bio': 'Senior Consultant Interventional Cardiologist with 14 years clinical experience.'
        }
        response = self.client.patch('/api/profile/me', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify CustomUser database persistence
        self.doctor_user.refresh_from_db()
        self.assertEqual(self.doctor_user.full_name, 'Dr. Updated Cardiologist')
        self.assertEqual(self.doctor_user.phone, '+91 9876500001')
        self.assertEqual(self.doctor_user.specialization, 'Interventional Cardiology')
        self.assertEqual(self.doctor_user.experience, 14)

        # Verify DoctorProfile database persistence
        self.doctor_profile.refresh_from_db()
        self.assertEqual(self.doctor_profile.specialization, 'Interventional Cardiology')
        self.assertEqual(self.doctor_profile.qualification, 'MBBS, MD, DM (Cardiology)')
        self.assertEqual(self.doctor_profile.additional_qualifications, 'FACC, FSCAI')
        self.assertEqual(self.doctor_profile.years_of_experience, 14)

    def test_doctor_professional_identity_fields_remain_strictly_immutable(self):
        """Doctor attempting to modify registration number, council, verification status, or HPR ID is blocked."""
        self.client.force_authenticate(user=self.doctor_user)
        attack_payload = {
            'fullName': 'Dr. Valid Doctor Name',
            'medicalRegistrationNumber': 'ATTACK-REG-666',
            'medical_registration_number': 'ATTACK-REG-666',
            'stateMedicalCouncil': 'Tamil Nadu Medical Council',
            'state_medical_council': 'Tamil Nadu Medical Council',
            'verificationStatus': 'DOCUMENTS_REQUESTED',
            'verification_status': 'DOCUMENTS_REQUESTED',
            'hprId': 'ATTACK-HPR-999',
            'hpr_id': 'ATTACK-HPR-999',
            'verifiedAt': '2030-01-01T00:00:00Z',
            'role': 'admin'
        }
        response = self.client.patch('/api/profile/me', attack_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify DoctorProfile professional identity remained 100% immutable
        self.doctor_profile.refresh_from_db()
        self.assertEqual(self.doctor_profile.medical_registration_number, 'KMC-TEST-998877')
        self.assertEqual(self.doctor_profile.state_medical_council, 'Karnataka Medical Council')
        self.assertEqual(self.doctor_profile.verification_status, 'VERIFIED')
        self.assertEqual(self.doctor_profile.hpr_id, 'HPR-TEST-12345')

        # Verify CustomUser role unchanged
        self.doctor_user.refresh_from_db()
        self.assertEqual(self.doctor_user.role, 'doctor')

    # =========================================================================
    # 4. CAREGIVER PROFILE TESTS
    # =========================================================================

    def test_caregiver_get_profile(self):
        """Caregiver can retrieve their own consolidated profile."""
        self.client.force_authenticate(user=self.caregiver_user)
        response = self.client.get('/api/profile/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['email'], 'test_caregiver_edit@nexus.test')
        self.assertEqual(data['agencyId'], 'CG-TEST-456')
        self.assertEqual(data['caregiverType'], 'PROFESSIONAL')
        self.assertEqual(data['qualification'], 'B.Sc Nursing')

    def test_caregiver_update_permitted_fields_persisted(self):
        """Caregiver can update permitted qualifications, skills, and agency contact details."""
        self.client.force_authenticate(user=self.caregiver_user)
        payload = {
            'fullName': 'Updated Caregiver Sarah',
            'phone': '+91 9876500002',
            'qualification': 'M.Sc Critical Care Nursing',
            'yearsOfExperience': 8,
            'skills': 'Critical Care, Stroke Rehabilitation, Ventilator Support',
            'previousExperience': '5 years Manipal Hospital ICU',
            'currentAgency': 'CareFirst Home Health',
            'agencyContact': '+91 8087654321',
            'bio': 'Certified critical care specialist for neurological recovery.'
        }
        response = self.client.patch('/api/profile/me', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify CustomUser database persistence
        self.caregiver_user.refresh_from_db()
        self.assertEqual(self.caregiver_user.full_name, 'Updated Caregiver Sarah')
        self.assertEqual(self.caregiver_user.phone, '+91 9876500002')

        # Verify CaregiverProfile database persistence
        self.caregiver_profile.refresh_from_db()
        self.assertEqual(self.caregiver_profile.full_name, 'Updated Caregiver Sarah')
        self.assertEqual(self.caregiver_profile.qualification, 'M.Sc Critical Care Nursing')
        self.assertEqual(self.caregiver_profile.years_of_experience, 8)
        self.assertEqual(self.caregiver_profile.skills, 'Critical Care, Stroke Rehabilitation, Ventilator Support')
        self.assertEqual(self.caregiver_profile.current_agency, 'CareFirst Home Health')
        self.assertEqual(self.caregiver_profile.agency_contact, '+91 8087654321')

    def test_caregiver_protected_fields_remain_immutable(self):
        """Caregiver attempting to modify agency ID, caregiver type, or verification status is blocked."""
        self.client.force_authenticate(user=self.caregiver_user)
        attack_payload = {
            'fullName': 'Sarah Caregiver Valid',
            'agencyId': 'ATTACK-AGENCY-999',
            'agency_id': 'ATTACK-AGENCY-999',
            'caregiverType': 'FAMILY',
            'caregiver_type': 'FAMILY',
            'verificationStatus': 'REJECTED',
            'verification_status': 'REJECTED',
            'role': 'doctor'
        }
        response = self.client.patch('/api/profile/me', attack_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify CaregiverProfile protected fields remained unchanged
        self.caregiver_profile.refresh_from_db()
        self.assertEqual(self.caregiver_profile.caregiver_type, 'PROFESSIONAL')
        self.assertEqual(self.caregiver_profile.verification_status, 'VERIFIED')

        # Verify CustomUser protected fields remained unchanged
        self.caregiver_user.refresh_from_db()
        self.assertEqual(self.caregiver_user.agency_id, 'CG-TEST-456')
        self.assertEqual(self.caregiver_user.role, 'caregiver')

    # =========================================================================
    # 5. FAMILY MEMBER PROFILE TESTS
    # =========================================================================

    def test_family_get_profile(self):
        """Family member can retrieve their profile."""
        self.client.force_authenticate(user=self.family_user)
        response = self.client.get('/api/profile/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['email'], 'test_family_edit@nexus.test')
        self.assertEqual(data['fullName'], 'Original Family Name')
        self.assertEqual(data['patientId'], 'P-901')

    def test_family_update_permitted_fields_persisted(self):
        """Family member can update their contact info with database persistence."""
        self.client.force_authenticate(user=self.family_user)
        payload = {
            'fullName': 'Updated Family Brother',
            'phone': '+91 9876500003',
            'bio': 'Primary family contact for Jane.'
        }
        response = self.client.patch('/api/profile/me', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.family_user.refresh_from_db()
        self.assertEqual(self.family_user.full_name, 'Updated Family Brother')
        self.assertEqual(self.family_user.phone, '+91 9876500003')
        self.assertEqual(self.family_user.bio, 'Primary family contact for Jane.')

    def test_family_patient_linkage_remains_strictly_protected(self):
        """Family member cannot modify patientId or attach to another patient via profile edit."""
        self.client.force_authenticate(user=self.family_user)
        attack_payload = {
            'fullName': 'Family Member Name',
            'patientId': 'P-ATTACK-ANOTHER-PATIENT-999',
            'patient_id': 'P-ATTACK-ANOTHER-PATIENT-999',
            'role': 'admin'
        }
        response = self.client.patch('/api/profile/me', attack_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.family_user.refresh_from_db()
        self.assertEqual(self.family_user.patient_id, 'P-901')
        self.assertEqual(self.family_user.role, 'family')

    # =========================================================================
    # 6. CROSS-USER ISOLATION & VALIDATION CHECKS
    # =========================================================================

    def test_cross_user_isolation_cannot_update_other_user(self):
        """Passing another user's ID in payload does not modify the target user."""
        self.client.force_authenticate(user=self.family_user)
        attack_payload = {
            'id': self.doctor_user.id,
            'user_id': self.doctor_user.id,
            'fullName': 'Hacked Doctor Name'
        }
        response = self.client.patch('/api/profile/me', attack_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Doctor user must NOT be changed
        self.doctor_user.refresh_from_db()
        self.assertEqual(self.doctor_user.full_name, 'Dr. Original Doctor')

        # Only the authenticated family user is updated
        self.family_user.refresh_from_db()
        self.assertEqual(self.family_user.full_name, 'Hacked Doctor Name')

    def test_invalid_name_validation_rejected(self):
        """Submitting invalid full name (digits only or too short) returns HTTP 400."""
        self.client.force_authenticate(user=self.patient_user)
        response = self.client.patch('/api/profile/me', {'fullName': '12345'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())

    def test_future_dob_validation_rejected(self):
        """Submitting future date of birth returns HTTP 400."""
        self.client.force_authenticate(user=self.patient_user)
        future_date = (date.today() + timedelta(days=365)).strftime('%Y-%m-%d')
        response = self.client.patch('/api/profile/me', {'dob': future_date}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
