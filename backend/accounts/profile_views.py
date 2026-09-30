import re
from datetime import datetime, date
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import CustomUser, AuditLog
from accounts.utils import log_audit_trail
from accounts.validators import (
    validate_human_name,
    validate_and_normalize_phone,
    validate_date_of_birth,
    calculate_age_from_dob
)
from patients.views import find_patient_record_for_user


class UserProfileMeView(APIView):
    """
    Role-Aware Self-Service Profile API for NeuroCare Nexus.
    Enforces strict ownership deriving identity exclusively from request.user.
    Provides mass-assignment protection with role-specific field whitelists.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = (user.role or '').lower()

        data = {
            'id': user.id,
            'email': user.email,
            'fullName': user.full_name,
            'phone': user.phone or '',
            'role': user.role,
            'bio': user.bio or '',
            'status': user.status,
            'approved': user.approved,
        }

        if role == 'patient':
            data['patientId'] = user.patient_id or ''
            data['deviceId'] = user.device_id or ''
            patient = find_patient_record_for_user(user)
            if patient:
                data['patientRecordId'] = patient.id
                data['age'] = patient.age
                data['gender'] = patient.gender or ''
                data['dob'] = str(patient.dob) if patient.dob else ''
                data['bloodGroup'] = patient.blood_group or ''
                data['address'] = patient.address or ''
                data['emergencyContactName'] = patient.emergency_contact_name or ''
                data['emergencyContactPhone'] = patient.emergency_contact_phone or ''
                data['condition'] = patient.condition or 'Normal'
                data['risk'] = patient.risk
                data['room'] = patient.room or ''
            else:
                data['patientRecordId'] = ''
                data['age'] = 35
                data['gender'] = ''
                data['dob'] = ''
                data['bloodGroup'] = ''
                data['address'] = ''
                data['emergencyContactName'] = ''
                data['emergencyContactPhone'] = ''

        elif role == 'doctor':
            data['specialization'] = user.specialization or ''
            data['experience'] = user.experience or 0
            data['npi'] = user.npi or ''
            if hasattr(user, 'doctor_profile'):
                dp = user.doctor_profile
                data['medicalRegistrationNumber'] = dp.medical_registration_number
                data['stateMedicalCouncil'] = dp.state_medical_council
                data['qualification'] = dp.qualification or ''
                data['specialization'] = dp.specialization or user.specialization or ''
                data['additionalQualifications'] = dp.additional_qualifications or ''
                data['hprId'] = dp.hpr_id or ''
                data['yearsOfExperience'] = dp.years_of_experience or user.experience or 0
                data['verificationStatus'] = dp.verification_status
                data['verifiedAt'] = str(dp.verified_at) if dp.verified_at else None
            else:
                data['medicalRegistrationNumber'] = ''
                data['stateMedicalCouncil'] = ''
                data['qualification'] = ''
                data['additionalQualifications'] = ''
                data['hprId'] = ''
                data['yearsOfExperience'] = user.experience or 0
                data['verificationStatus'] = 'UNCONFIGURED'
                data['verifiedAt'] = None

        elif role == 'caregiver':
            data['agencyId'] = user.agency_id or ''
            if hasattr(user, 'caregiver_profile'):
                cp = user.caregiver_profile
                data['caregiverType'] = cp.caregiver_type
                data['qualification'] = cp.qualification or ''
                data['yearsOfExperience'] = cp.years_of_experience or 0
                data['skills'] = cp.skills or ''
                data['previousExperience'] = cp.previous_experience or ''
                data['currentAgency'] = cp.current_agency or ''
                data['agencyContact'] = cp.agency_contact or ''
                data['verificationStatus'] = cp.verification_status
            else:
                data['caregiverType'] = 'PROFESSIONAL'
                data['qualification'] = ''
                data['yearsOfExperience'] = 0
                data['skills'] = ''
                data['previousExperience'] = ''
                data['currentAgency'] = ''
                data['agencyContact'] = ''
                data['verificationStatus'] = 'ACTIVE'

        elif role == 'family':
            data['patientId'] = user.patient_id or ''

        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        user = request.user
        role = (user.role or '').lower()

        if role not in ['patient', 'doctor', 'caregiver', 'family']:
            return Response(
                {"error": "Profile editing is currently restricted to Patient, Doctor, Caregiver, and Family accounts."},
                status=status.HTTP_403_FORBIDDEN
            )

        payload = request.data
        if not isinstance(payload, dict):
            return Response({"error": "Invalid JSON payload."}, status=status.HTTP_400_BAD_REQUEST)

        # -------------------------------------------------------------
        # 1. Detect and reject mass-assignment security attack attempts
        # -------------------------------------------------------------
        forbidden_keys = [
            'role', 'is_staff', 'is_superuser', 'email', 'id', 'user_id',
            'approved', 'status', 'verification_status', 'verificationStatus',
            'verified_at', 'verifiedAt', 'medical_registration_number',
            'medicalRegistrationNumber', 'state_medical_council', 'stateMedicalCouncil',
            'hpr_id', 'hprId', 'patient_id', 'patientId', 'device_id', 'deviceId',
            'agency_id', 'agencyId', 'access_key', 'accessKey',
            'caregiver_links', 'family_links', 'doctor_npi', 'room', 'condition',
            'risk', 'ehr_notes'
        ]

        # For auditing / explicit security validation
        field_errors = {}

        # -------------------------------------------------------------
        # 2. Role-specific permitted field validation & sanitization
        # -------------------------------------------------------------
        with transaction.atomic():
            user_updated_fields = []

            # A. Common: Full Name
            name_val = payload.get('fullName') or payload.get('full_name') or payload.get('name')
            if name_val is not None:
                ok_name, clean_name, err_name = validate_human_name(name_val, "Full name")
                if not ok_name:
                    return Response({"error": err_name, "field": "fullName"}, status=status.HTTP_400_BAD_REQUEST)
                user.full_name = clean_name
                user_updated_fields.append('full_name')

            # B. Common: Phone
            phone_val = payload.get('phone') or payload.get('contact')
            if phone_val is not None:
                raw_phone = str(phone_val).strip()
                if raw_phone:
                    # Validate phone format
                    if re.search(r'[^\d\+\-\s\(\)]', raw_phone) or len(re.sub(r'\D', '', raw_phone)) < 7:
                        return Response({"error": "Please enter a valid contact phone number.", "field": "phone"}, status=status.HTTP_400_BAD_REQUEST)
                    user.phone = raw_phone
                else:
                    user.phone = ''
                user_updated_fields.append('phone')

            # C. Common: Bio
            if 'bio' in payload:
                user.bio = str(payload.get('bio') or '').strip()
                user_updated_fields.append('bio')

            # ---------------------------------------------------------
            # D. Role-Specific Logic: PATIENT
            # ---------------------------------------------------------
            if role == 'patient':
                patient = find_patient_record_for_user(user)
                if patient:
                    patient_updated = False
                    if user_updated_fields and 'full_name' in user_updated_fields:
                        patient.name = user.full_name
                        patient_updated = True
                    if user_updated_fields and 'phone' in user_updated_fields:
                        patient.phone = user.phone
                        patient_updated = True

                    # DOB & Age
                    dob_val = payload.get('dob')
                    if dob_val is not None:
                        ok_dob, dob_date, err_dob = validate_date_of_birth(dob_val)
                        if not ok_dob:
                            return Response({"error": err_dob, "field": "dob"}, status=status.HTTP_400_BAD_REQUEST)
                        patient.dob = dob_date
                        if dob_date:
                            patient.age = calculate_age_from_dob(dob_date)
                        patient_updated = True

                    # Explicit Age override if provided without dob
                    age_val = payload.get('age')
                    if age_val is not None and not dob_val:
                        try:
                            clean_age = int(age_val)
                            if 0 <= clean_age <= 150:
                                patient.age = clean_age
                                patient_updated = True
                            else:
                                return Response({"error": "Age must be between 0 and 150.", "field": "age"}, status=status.HTTP_400_BAD_REQUEST)
                        except (ValueError, TypeError):
                            return Response({"error": "Age must be a valid number.", "field": "age"}, status=status.HTTP_400_BAD_REQUEST)

                    # Gender
                    if 'gender' in payload:
                        patient.gender = str(payload.get('gender') or '').strip()
                        patient_updated = True

                    # Blood Group
                    blood_val = payload.get('bloodGroup') or payload.get('blood_group')
                    if blood_val is not None:
                        patient.blood_group = str(blood_val).strip()
                        patient_updated = True

                    # Address
                    if 'address' in payload:
                        patient.address = str(payload.get('address') or '').strip()
                        patient_updated = True

                    # Emergency Contact Name
                    em_name = payload.get('emergencyContactName') or payload.get('emergency_contact_name')
                    if em_name is not None:
                        patient.emergency_contact_name = str(em_name).strip()
                        patient_updated = True

                    # Emergency Contact Phone
                    em_phone = payload.get('emergencyContactPhone') or payload.get('emergency_contact_phone')
                    if em_phone is not None:
                        patient.emergency_contact_phone = str(em_phone).strip()
                        patient_updated = True

                    if patient_updated:
                        patient.save()

            # ---------------------------------------------------------
            # E. Role-Specific Logic: DOCTOR
            # ---------------------------------------------------------
            elif role == 'doctor':
                if 'specialization' in payload:
                    clean_spec = str(payload.get('specialization') or '').strip()
                    user.specialization = clean_spec
                    user_updated_fields.append('specialization')

                exp_val = payload.get('yearsOfExperience') or payload.get('years_of_experience') or payload.get('experience')
                if exp_val is not None:
                    try:
                        clean_exp = max(0, int(exp_val))
                        user.experience = clean_exp
                        user_updated_fields.append('experience')
                    except (ValueError, TypeError):
                        return Response({"error": "Years of experience must be a non-negative integer.", "field": "yearsOfExperience"}, status=status.HTTP_400_BAD_REQUEST)

                if hasattr(user, 'doctor_profile'):
                    dp = user.doctor_profile
                    dp_updated = False

                    if 'specialization' in payload:
                        dp.specialization = str(payload.get('specialization') or '').strip()
                        dp_updated = True

                    if 'qualification' in payload:
                        dp.qualification = str(payload.get('qualification') or '').strip()
                        dp_updated = True

                    add_qual = payload.get('additionalQualifications') or payload.get('additional_qualifications')
                    if add_qual is not None:
                        dp.additional_qualifications = str(add_qual).strip()
                        dp_updated = True

                    if exp_val is not None:
                        dp.years_of_experience = clean_exp
                        dp_updated = True

                    if dp_updated:
                        dp.save()

            # ---------------------------------------------------------
            # F. Role-Specific Logic: CAREGIVER
            # ---------------------------------------------------------
            elif role == 'caregiver':
                if hasattr(user, 'caregiver_profile'):
                    cp = user.caregiver_profile
                    cp_updated = False

                    if user_updated_fields and 'full_name' in user_updated_fields:
                        cp.full_name = user.full_name
                        cp_updated = True
                    if user_updated_fields and 'phone' in user_updated_fields:
                        cp.contact = user.phone
                        cp_updated = True

                    if 'qualification' in payload:
                        cp.qualification = str(payload.get('qualification') or '').strip()
                        cp_updated = True

                    exp_val = payload.get('yearsOfExperience') or payload.get('years_of_experience')
                    if exp_val is not None:
                        try:
                            cp.years_of_experience = max(0, int(exp_val))
                            cp_updated = True
                        except (ValueError, TypeError):
                            return Response({"error": "Years of experience must be a valid number.", "field": "yearsOfExperience"}, status=status.HTTP_400_BAD_REQUEST)

                    if 'skills' in payload:
                        cp.skills = str(payload.get('skills') or '').strip()
                        cp_updated = True

                    prev_exp = payload.get('previousExperience') or payload.get('previous_experience')
                    if prev_exp is not None:
                        cp.previous_experience = str(prev_exp).strip()
                        cp_updated = True

                    agency_val = payload.get('currentAgency') or payload.get('current_agency')
                    if agency_val is not None:
                        cp.current_agency = str(agency_val).strip()
                        cp_updated = True

                    agency_contact_val = payload.get('agencyContact') or payload.get('agency_contact')
                    if agency_contact_val is not None:
                        cp.agency_contact = str(agency_contact_val).strip()
                        cp_updated = True

                    if cp_updated:
                        cp.save()

            # ---------------------------------------------------------
            # G. Role-Specific Logic: FAMILY
            # ---------------------------------------------------------
            elif role == 'family':
                # Family members update full_name, phone, bio on CustomUser only.
                pass

            # Save CustomUser if any user fields changed
            if user_updated_fields:
                user.save(update_fields=list(set(user_updated_fields)))

        # Log audit trail
        log_audit_trail(
            request=request,
            action='Self Profile Update',
            target=f"User {user.email} (Role: {user.role})",
            result='Success'
        )

        # Return updated profile payload
        return self.get(request)
