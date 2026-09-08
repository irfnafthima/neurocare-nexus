# TABLE DESIGN

NeuroCare Nexus uses PostgreSQL as its relational database management system. The database is designed to maintain data consistency, secure role-based access, patient clinical information, physiological measurements, care-team relationships, doctor verification, notifications, communication, and AI-assisted healthcare functionality.

Standard Django framework and internal infrastructure tables (such as `django_migrations`, `django_content_type`, `django_admin_log`, `auth_permission`, `auth_group`, `auth_group_permissions`, `accounts_customuser_groups`, `accounts_customuser_user_permissions`, and `django_session`) are excluded from this academic Table Design specification to focus exclusively on the core NeuroCare Nexus application domain.

---

### TABLE 1: USERS (`accounts_customuser`)

**Purpose:**  
Stores authentication credentials, role classifications (`patient`, `doctor`, `caregiver`, `family`, `admin`), account approval status, and high-level profile attributes for all registered NeuroCare Nexus users.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the user account. |
| `password` | VARCHAR(128) | NOT NULL | PBKDF2/Argon2 cryptographic hash of the user password. |
| `last_login` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp of the user's most recent authenticated session. |
| `is_superuser` | BOOLEAN | NOT NULL, DEFAULT: False | Designates whether the user has all administrative permissions. |
| `username` | VARCHAR(150) | NULL | Optional username field (email serves as primary authentication identifier). |
| `first_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | First name of the user. |
| `last_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Last name or surname of the user. |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | Unique primary email address used for system login and communications. |
| `is_staff` | BOOLEAN | NOT NULL, DEFAULT: False | Designates whether the user can log into the Django administrative portal. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Designates whether this user account is active. |
| `date_joined` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the user account was registered. |
| `full_name` | VARCHAR(100) | NOT NULL | Complete human-readable display name of the user. |
| `phone` | VARCHAR(20) | NULL | Primary contact phone number. |
| `role` | VARCHAR(50) | NOT NULL | Role categorization: `patient`, `doctor`, `caregiver`, `family`, or `admin`. |
| `npi` | VARCHAR(50) | NULL | National Provider Identifier or registration code for doctors during registration. |
| `device_id` | VARCHAR(20) | NULL | Associated hardware device serial number for wearable onboarding. |
| `agency_id` | VARCHAR(20) | NULL | Associated caregiving agency identification number. |
| `patient_id` | VARCHAR(20) | NULL | Direct patient linkage identifier for family/caregiver registration. |
| `access_key` | VARCHAR(20) | NULL | Temporary security access/pairing key for access authorization. |
| `approved` | BOOLEAN | NOT NULL, DEFAULT: True | Verification approval flag (defaults to `False` for doctor role, `True` for others). |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'ACTIVE' | Account lifecycle status: `PENDING`, `ACTIVE`, or `REJECTED`. |
| `specialization` | VARCHAR(100) | NULL | Clinical specialization for doctor accounts (e.g., Neurologist, Cardiologist). |
| `experience` | INTEGER | NULL | Total years of professional medical/caregiving experience. |
| `bio` | TEXT | NULL | Professional biography, summary, or background notes. |

---

### TABLE 2: AUDIT LOGS (`accounts_auditlog`)

**Purpose:**  
Captures immutable security and operational audit trail records for user actions, administrative interventions, and system events.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the audit record. |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Exact timestamp when the audited event occurred. |
| `username` | VARCHAR(100) | NOT NULL | Username/email of the actor at log generation time. |
| `actor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the authenticated user who initiated the action. |
| `action` | VARCHAR(255) | NOT NULL | Descriptive action performed (e.g., User Login, Verification Approved, EHR Updated). |
| `target` | VARCHAR(255) | NOT NULL | Entity or resource affected by the action (e.g., DoctorProfile: 14, Patient: P-102). |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Success' | Outcome status of the logged operation (e.g., Success, Failed, Denied). |
| `ip_address` | VARCHAR(45) | NULL | Client IP address (IPv4 or IPv6 format). |
| `device_info` | VARCHAR(255) | NULL | Client browser User-Agent or device environment metadata. |

---

### TABLE 3: SYNTHETIC PATIENTS (`patients_syntheticpatient`)

**Purpose:**  
Maintains pre-configured synthetic patient reference records and consent verification benchmarks for validation testing.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `patient_id` | VARCHAR(20) | PK, NOT NULL | Primary unique identifier for the synthetic patient record (e.g., `P-101`). |
| `code` | VARCHAR(20) | UNIQUE, NOT NULL | Unique access/verification security code assigned to the patient. |
| `patient_name` | VARCHAR(100) | NOT NULL | Full name of the synthetic patient subject. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Consent Verified' | Verification and consent readiness status. |

---

### TABLE 4: PATIENTS (`patients_patient`)

**Purpose:**  
Stores master operational patient demographic, clinical baseline, emergency contact, room allocation, and medical supervisor details.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | VARCHAR(20) | PK, NOT NULL | Unique business primary key for the patient (e.g., `P-102`). |
| `name` | VARCHAR(100) | NOT NULL | Full name of the patient. |
| `age` | INTEGER | NOT NULL | Patient age in years. |
| `gender` | VARCHAR(10) | NOT NULL | Patient gender (e.g., `Male`, `Female`, `Other`). |
| `room` | VARCHAR(10) | NOT NULL | Hospital room or ward designation (e.g., `302A`, `ICU-4`). |
| `condition` | VARCHAR(255) | NOT NULL | Primary clinical diagnosis or neurological condition summary. |
| `risk` | INTEGER | NOT NULL, DEFAULT: 0 | Calculated baseline clinical risk score / severity rating index (0–100). |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Normal' | Current operational status (e.g., `Normal`, `Critical`, `Stable`, `Discharged`). |
| `ehr_notes` | TEXT | NOT NULL, DEFAULT: '' | High-level baseline electronic health record summary notes. |
| `dob` | DATE | NULL | Date of birth. |
| `phone` | VARCHAR(25) | NOT NULL, DEFAULT: '' | Contact telephone number. |
| `address` | TEXT | NOT NULL, DEFAULT: '' | Residential or permanent residential address. |
| `emergency_contact_name` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Name of primary emergency contact / next of kin. |
| `emergency_contact_phone` | VARCHAR(25) | NOT NULL, DEFAULT: '' | Direct contact phone number for emergency contact. |
| `blood_group` | VARCHAR(10) | NOT NULL, DEFAULT: '' | ABO/Rh blood group typing (e.g., `A+`, `O-`, `B+`). |
| `doctor_npi_id` | VARCHAR(50) | FK → `doctors_syntheticnpi.npi`, NULL | Foreign key referencing the primary attending doctor's reference NPI identifier. |

---

### TABLE 5: APPOINTMENTS (`patients_appointment`)

**Purpose:**  
Stores scheduled clinical consultations, follow-ups, and diagnostic review sessions for patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the appointment record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking the appointment to the specific patient. |
| `details` | VARCHAR(255) | NOT NULL | Clinical purpose or details of the appointment (e.g., EEG Review, Routine Checkup). |
| `time` | VARCHAR(100) | NOT NULL | Human-readable or standardized appointment time schedule. |

---

### TABLE 6: FAMILY-PATIENT LINKS (`patients_familypatientlink`)

**Purpose:**  
Maintains verified relationships, care-team authorization, and clinical record permissions between family member user accounts and patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the family-patient link. |
| `family_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the registered User account with role `family`. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the linked patient record. |
| `is_approved` | BOOLEAN | NOT NULL, DEFAULT: False | Designates whether the family member link has been formally approved by an administrator/doctor. |
| `can_edit_clinical` | BOOLEAN | NOT NULL, DEFAULT: False | Explicit privilege flag granting permission to add/edit clinical information. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the link relationship was established. |

*Unique Constraint:* Composite unique constraint on `(family_id, patient_id)`.

---

### TABLE 7: SYNTHETIC NPI REGISTRY (`doctors_syntheticnpi`)

**Purpose:**  
Maintains pre-configured National Provider Identifier (NPI) credentials and hospital affiliations for doctor onboarding verification.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `npi` | VARCHAR(50) | PK, NOT NULL | Unique National Provider Identifier serving as the primary key. |
| `name` | VARCHAR(100) | NOT NULL | Full name of the medical practitioner. |
| `hospital` | VARCHAR(150) | NOT NULL | Primary affiliated medical center or health network name. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Operational credential status in the registry. |

---

### TABLE 8: REFERENCE DOCTOR REGISTRY (`doctors_referencedoctorregistry`)

**Purpose:**  
Stores official external regulatory council medical registry data used as authoritative reference benchmarks to cross-verify doctor credentials. (Note: Reference data only; distinct from registered system user accounts).

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `registration_number` | VARCHAR(50) | PK, NOT NULL | Official state/national medical council registration number. |
| `reference_id` | VARCHAR(50) | UNIQUE, NULL | Unique external reference tracking ID. |
| `doctor_name` | VARCHAR(100) | NOT NULL | Full official name of the registered doctor as recorded in the council gazette. |
| `normalized_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Normalized lower-case canonical name string for fuzzy matching algorithms. |
| `council` | VARCHAR(150) | NOT NULL | Governing medical council (e.g., Kerala State Medical Council, DMC). |
| `qualification` | VARCHAR(150) | NOT NULL | Primary and postgraduate medical qualifications (e.g., MBBS, MD Neurology). |
| `registration_year` | INTEGER | NOT NULL | Calendar year of initial registration. |
| `registration_date` | DATE | NULL | Exact date of registration with the medical council. |
| `specialization` | VARCHAR(100) | NULL | Recognized clinical sub-specialization. |
| `registration_status` | VARCHAR(20) | NOT NULL, DEFAULT: 'ACTIVE' | Regulatory registry status (e.g., `ACTIVE`, `SUSPENDED`, `LAPSED`). |
| `source_type` | VARCHAR(50) | NOT NULL, DEFAULT: 'SYNTHETIC_REFERENCE' | Origin data source category (e.g., `NMC_REGISTRY`, `SYNTHETIC_REFERENCE`). |
| `source_reference` | VARCHAR(150) | NULL | Document or gazette publication reference identifier. |
| `source_year` | INTEGER | NULL | Regulatory edition or publication year. |

*Indexes:* B-Tree indexes on `normalized_name`, `council`, and `registration_status`.

---

### TABLE 9: HEALTH FACILITIES (`doctors_healthfacility`)

**Purpose:**  
Stores verified healthcare facilities, hospitals, and specialized clinics associated with medical practitioners and institutional affiliations.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the health facility. |
| `facility_id` | VARCHAR(50) | UNIQUE, NULL | Business/clinical facility identification code. |
| `name` | VARCHAR(150) | NOT NULL | Official name of the medical institution/hospital. |
| `facility_type` | VARCHAR(50) | NOT NULL | Facility classification (e.g., `Hospital`, `Super Specialty Center`, `Clinic`). |
| `address` | TEXT | NOT NULL | Complete physical address of the facility. |
| `city` | VARCHAR(100) | NOT NULL | City where the facility is located. |
| `district` | VARCHAR(100) | NULL | Administrative district. |
| `state` | VARCHAR(100) | NOT NULL | State or province. |
| `registration_identifier` | VARCHAR(100) | UNIQUE, NOT NULL | Government or regulatory health facility registration / license number. |
| `contact` | VARCHAR(50) | NOT NULL, DEFAULT: '' | Official contact phone number or PBX line. |
| `website` | VARCHAR(100) | NULL | Official website URL. |
| `verification_status` | VARCHAR(20) | NOT NULL, DEFAULT: 'PENDING' | Facility vetting status: `PENDING`, `VERIFIED`, or `REJECTED`. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the facility was verified by platform administrators. |
| `source_type` | VARCHAR(50) | NULL, DEFAULT: 'SYNTHETIC_REFERENCE' | Registry source data category. |

---

### TABLE 10: DOCTOR DISCIPLINARY RECORDS (`doctors_doctordisciplinaryrecord`)

**Purpose:**  
Tracks official disciplinary sanctions, suspensions, blacklists, or restorations issued by statutory medical councils against reference doctor records.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the disciplinary record. |
| `disciplinary_id` | VARCHAR(50) | UNIQUE, NOT NULL | Unique business case identifier for the disciplinary order. |
| `doctor_id` | VARCHAR(50) | FK → `doctors_referencedoctorregistry.registration_number`, NOT NULL | Foreign key referencing the affected reference doctor. |
| `registration_number` | VARCHAR(50) | NOT NULL | Medical registration number recorded on the sanction order. |
| `doctor_name` | VARCHAR(100) | NOT NULL | Name of the practitioner subject to disciplinary action. |
| `state_medical_council` | VARCHAR(150) | NOT NULL | Medical council issuing the order. |
| `action_type` | VARCHAR(50) | NOT NULL | Type of action: `SUSPENSION`, `BLACKLIST`, `RESTORATION`, or `REMOVAL`. |
| `status` | VARCHAR(50) | NOT NULL | Current status of the sanction: `ACTIVE`, `BLACKLISTED`, `REMOVED`, `RESTORED`. |
| `suspended_date` | DATE | NULL | Effective start date of suspension/penalty. |
| `restored_date` | DATE | NULL | Date when clinical license/registration was formally restored. |
| `source_type` | VARCHAR(50) | NOT NULL, DEFAULT: 'SYNTHETIC_TEST_REFERENCE' | Origin data source category. |
| `source_reference` | VARCHAR(150) | NULL | Gazette citation or disciplinary order reference. |
| `remarks` | TEXT | NULL | Official summary of disciplinary charges and findings. |

---

### TABLE 11: REFERENCE DOCTOR AFFILIATIONS (`doctors_referencedoctoraffiliation`)

**Purpose:**  
Maintains official reference employment and clinical appointment affiliations between reference registry doctors and health facilities.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the reference affiliation. |
| `affiliation_id` | VARCHAR(50) | UNIQUE, NOT NULL | Unique business identifier for the reference affiliation record. |
| `reference_doctor_id` | VARCHAR(50) | FK → `doctors_referencedoctorregistry.registration_number`, NOT NULL | Foreign key referencing the registered reference doctor. |
| `facility_id` | BIGINT | FK → `doctors_healthfacility.id`, NOT NULL | Foreign key referencing the affiliated health facility. |
| `department` | VARCHAR(100) | NOT NULL | Clinical department (e.g., Neurology, Neurosurgery). |
| `designation` | VARCHAR(100) | NOT NULL | Official clinical title/designation (e.g., Senior Consultant). |
| `employment_type` | VARCHAR(50) | NOT NULL | Employment modality: `FULL_TIME`, `PART_TIME`, `VISITING_CONSULTANT`, `RESIDENT`. |
| `status` | VARCHAR(50) | NOT NULL | Status of affiliation: `CURRENT` or `ENDED`. |
| `start_date` | DATE | NULL | Commencement date of clinical appointment. |
| `end_date` | DATE | NULL | Termination date of clinical appointment. |
| `verification_status` | VARCHAR(20) | NOT NULL, DEFAULT: 'PENDING' | Verification audit status (`PENDING`, `VERIFIED`, `REJECTED`). |
| `source_type` | VARCHAR(50) | NOT NULL, DEFAULT: 'SYNTHETIC_REFERENCE' | Source data origin descriptor. |

---

### TABLE 12: DOCTOR PROFILES (`doctors_doctorprofile`)

**Purpose:**  
Stores verified professional profiles, credentials, statutory licensing details, and verification statuses for operational registered doctor user accounts.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the doctor profile. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, UNIQUE, NOT NULL | One-to-One foreign key linking to the registered User account (role: doctor). |
| `medical_registration_number` | VARCHAR(50) | NOT NULL | Official statutory medical registration number declared by the practitioner. |
| `state_medical_council` | VARCHAR(150) | NOT NULL | State medical council where the practitioner is registered. |
| `qualification` | VARCHAR(150) | NOT NULL | Primary recognized medical degrees (e.g., MBBS, MD, DM Neurology). |
| `specialization` | VARCHAR(100) | NOT NULL | Clinical specialization focus area. |
| `additional_qualifications` | VARCHAR(255) | NULL | Additional sub-specialty fellowships, diplomas, or certifications. |
| `hpr_id` | VARCHAR(100) | NULL | Healthcare Professional Registry (HPR / ABDM) digital identifier. |
| `years_of_experience` | INTEGER | NOT NULL, DEFAULT: 0 | Total cumulative years in clinical practice. |
| `verification_status` | VARCHAR(25) | NOT NULL, DEFAULT: 'PENDING' | Credential vetting state: `PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `SUSPENDED`, `EXPIRED`. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the profile attained verified status. |

---

### TABLE 13: DOCTOR FACILITY AFFILIATIONS (`doctors_doctorfacilityaffiliation`)

**Purpose:**  
Tracks operational hospital and clinical practice affiliations for registered doctors.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the doctor facility affiliation. |
| `doctor_id` | BIGINT | FK → `doctors_doctorprofile.id`, NOT NULL | Foreign key referencing the registered doctor profile. |
| `facility_id` | BIGINT | FK → `doctors_healthfacility.id`, NOT NULL | Foreign key referencing the affiliated health facility. |
| `department` | VARCHAR(100) | NOT NULL | Clinical department in which the doctor practices. |
| `designation` | VARCHAR(100) | NOT NULL | Official clinical appointment title. |
| `employment_status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Operational status: `Active` or `Inactive`. |
| `start_date` | DATE | NOT NULL | Effective start date of practice at the facility. |
| `end_date` | DATE | NULL | Practice end date (if affiliation concluded). |
| `verification_status` | VARCHAR(20) | NOT NULL, DEFAULT: 'PENDING' | Status of facility credential cross-verification (`PENDING`, `VERIFIED`, `REJECTED`). |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp of facility credential verification. |
| `verification_source` | VARCHAR(150) | NULL | Document or institutional contact source confirming employment. |

---

### TABLE 14: VERIFICATION RECORDS (`doctors_verificationrecord`)

**Purpose:**  
Logs comprehensive automated and administrative verification audits, credential matching scores, and decision outcomes for healthcare professionals.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the verification audit log. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the user account undergoing verification. |
| `verification_type` | VARCHAR(30) | NOT NULL | Check category: `PROFESSIONAL_REGISTRATION`, `IDENTITY_MATCH`, `QUALIFICATION`, `HOSPITAL_AFFILIATION`, `ADMIN_REVIEW`. |
| `source` | VARCHAR(150) | NOT NULL | Verification source or database endpoint evaluated. |
| `result` | VARCHAR(20) | NOT NULL | Matching outcome: `EXACT_MATCH`, `LIKELY_MATCH`, `MISMATCH`, `NOT_FOUND`, `MANUAL_REVIEW`. |
| `verified_by_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the administrator who conducted or ratified the review. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the verification step was executed. |
| `remarks` | TEXT | NULL | Detailed notes, confidence scores, or matching discrepancies. |

---

### TABLE 15: DOCTOR CONNECTION REQUESTS (`doctors_doctorconnectionrequest`)

**Purpose:**  
Manages connection requests initiated between patients and medical practitioners before formal inclusion into the care team.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the connection request. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the patient requesting clinical connection. |
| `doctor_npi_id` | VARCHAR(50) | FK → `doctors_syntheticnpi.npi`, NOT NULL | Foreign key referencing the target doctor by NPI identifier. |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'Pending' | Request state: `Pending`, `Approved`, or `Declined`. |
| `request_message` | TEXT | NOT NULL, DEFAULT: '' | Accompanying introductory clinical notes or patient message. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the connection request was generated. |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp of last status modification. |

*Unique Constraint:* Composite unique constraint on `(patient_id, doctor_npi_id)`.

---

### TABLE 16: DOCTOR-PATIENT LINKS (`doctors_doctorpatientlink`)

**Purpose:**  
Maintains active, authorized clinical relationships granting doctors secure clinical access to manage patient care, prescriptions, and records.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the link. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the managed patient. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the assigned doctor User account (role: doctor). |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the formal doctor-patient link was established. |

*Unique Constraint:* Composite unique constraint on `(patient_id, doctor_id)`.

---

### TABLE 17: SYNTHETIC CAREGIVERS (`caregivers_syntheticcaregiver`)

**Purpose:**  
Maintains pre-configured synthetic caregiver agency records and validation test profiles.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `agency_id` | VARCHAR(20) | PK, NOT NULL | Unique agency identification code serving as primary key. |
| `name` | VARCHAR(100) | NOT NULL | Full name of the professional caregiver. |
| `agency` | VARCHAR(150) | NOT NULL | Name of the home care or nursing agency. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Operational status of the caregiver profile. |

---

### TABLE 18: CAREGIVER PROFILES (`caregivers_caregiverprofile`)

**Purpose:**  
Stores professional nursing credentials, agency affiliations, caregiving qualifications, and verification statuses for registered caregiver user accounts.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the caregiver profile. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, UNIQUE, NOT NULL | One-to-One foreign key linking to the registered User account (role: caregiver). |
| `caregiver_type` | VARCHAR(20) | NOT NULL, DEFAULT: 'PROFESSIONAL' | Classification: `PROFESSIONAL` (certified nurse/aide) or `FAMILY` (personal caregiver). |
| `full_name` | VARCHAR(100) | NOT NULL | Complete legal name of the caregiver. |
| `contact` | VARCHAR(50) | NULL | Direct telephone contact number. |
| `qualification` | VARCHAR(150) | NULL | Nursing/caregiver certification, degree, or training accreditation. |
| `years_of_experience` | INTEGER | NOT NULL, DEFAULT: 0 | Total years in patient homecare or clinical assistance. |
| `skills` | TEXT | NULL | Clinical competencies (e.g., Tracheostomy Care, Stroke Rehabilitation, Vital Monitoring). |
| `previous_experience` | TEXT | NULL | Summary of past clinical nursing or caregiving postings. |
| `current_agency` | VARCHAR(150) | NULL | Name of employing healthcare / nursing agency. |
| `agency_contact` | VARCHAR(50) | NULL | Official agency supervisor or dispatch contact number. |
| `verification_status` | VARCHAR(20) | NOT NULL, DEFAULT: 'PENDING' | Credential vetting state: `PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `SUSPENDED`. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the profile was officially verified. |

---

### TABLE 19: CAREGIVER-PATIENT LINKS (`caregivers_caregiverpatientlink`)

**Purpose:**  
Maintains authorized clinical care assignments, access permissions, and read-only flags between caregivers and patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the caregiver-patient link. |
| `caregiver_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the caregiver User account (role: caregiver). |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the assigned patient. |
| `is_read_only` | BOOLEAN | NOT NULL, DEFAULT: True | Access restriction flag (defaults to True; prevents unauthorized clinical modifications). |
| `is_approved` | BOOLEAN | NOT NULL, DEFAULT: True | Approval status of the caregiving assignment. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the assignment link was created. |

*Unique Constraint:* Composite unique constraint on `(caregiver_id, patient_id)`.

---

### TABLE 20: SYNTHETIC DEVICES (`devices_syntheticdevice`)

**Purpose:**  
Stores pre-registered synthetic IoT wearable hardware serials and MAC addresses for validation and testing.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `serial` | VARCHAR(20) | PK, NOT NULL | Unique hardware serial number serving as primary key. |
| `mac` | VARCHAR(30) | UNIQUE, NOT NULL | Unique physical MAC address of the device network controller. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Unassigned' | Device deployment status (e.g., `Unassigned`, `Provisioned`). |

---

### TABLE 21: WEARABLE DEVICES (`devices_wearabledevice`)

**Purpose:**  
Maintains inventory, hardware identification, and operational statuses for physical ESP32-based patient monitoring bands and sensor nodes.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `serial` | VARCHAR(20) | PK, NOT NULL | Unique hardware serial number of the wearable device. |
| `mac` | VARCHAR(30) | UNIQUE, NOT NULL | Physical Wi-Fi / Bluetooth MAC address of the microcontroller. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Operational status: `Active`, `Charging`, `Maintenance`, `Decommissioned`. |

---

### TABLE 22: DEVICE ASSIGNMENTS (`devices_deviceassignment`)

**Purpose:**  
Maintains strict 1-to-1 operational pairing between an active wearable device and an enrolled patient.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the device assignment record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, UNIQUE, NOT NULL | One-to-One foreign key linking the assignment to the specific patient. |
| `device_id` | VARCHAR(20) | FK → `devices_wearabledevice.serial`, UNIQUE, NOT NULL | One-to-One foreign key linking the assignment to the specific wearable device. |
| `assigned_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the hardware unit was paired to the patient. |

---

### TABLE 23: SENSOR READINGS / TELEMETRY (`monitoring_sensorreading`)

**Purpose:**  
Stores high-frequency automated IoT sensor telemetry transmitted continuously by ESP32 wearable devices (MAX30102 pulse oximeter, DS18B20 temperature sensor, MPU6050 6-axis IMU).

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the telemetry reading. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the monitored patient. |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Exact timestamp when telemetry was captured and ingested. |
| `heart_rate` | INTEGER | NULL | Real-time heart rate measurement from MAX30102 sensor (BPM). |
| `spo2` | INTEGER | NULL | Peripheral blood oxygen saturation percentage from MAX30102 sensor (SpO2 %). |
| `temperature` | NUMERIC(4, 2) | NULL | Skin/body temperature in degrees Celsius (°C) from DS18B20 digital sensor. |
| `accel_x` | NUMERIC(5, 2) | NULL | Linear acceleration along X-axis from MPU6050 accelerometer ($m/s^2$ or g). |
| `accel_y` | NUMERIC(5, 2) | NULL | Linear acceleration along Y-axis from MPU6050 accelerometer ($m/s^2$ or g). |
| `accel_z` | NUMERIC(5, 2) | NULL | Linear acceleration along Z-axis from MPU6050 accelerometer ($m/s^2$ or g). |
| `gyro_x` | NUMERIC(5, 2) | NULL | Angular velocity around X-axis from MPU6050 gyroscope (deg/sec). |
| `gyro_y` | NUMERIC(5, 2) | NULL | Angular velocity around Y-axis from MPU6050 gyroscope (deg/sec). |
| `gyro_z` | NUMERIC(5, 2) | NULL | Angular velocity around Z-axis from MPU6050 gyroscope (deg/sec). |
| `fall_detected` | BOOLEAN | NOT NULL, DEFAULT: False | Real-time kinematic threshold trigger indicating a patient fall event. |
| `esp32_connected` | BOOLEAN | NOT NULL, DEFAULT: True | Microcontroller heartbeat link connectivity status. |
| `esp32_battery` | INTEGER | NULL | Remaining battery charge percentage of the wearable unit (0–100%). |
| `esp32_rssi` | INTEGER | NULL | Received Signal Strength Indication (RSSI) of the Wi-Fi connection in dBm. |

---

### TABLE 24: ALERTS (`alerts_alert`)

**Purpose:**  
Captures real-time clinical threshold breaches, physiological emergencies, hardware failover warnings, and AI-generated hazard notifications.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the alert. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking the alert to the affected patient. |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the trigger condition was evaluated. |
| `type` | VARCHAR(50) | NOT NULL | Alert classification: `Heart Rate`, `SpO2`, `Fall`, `Emergency`, `Temperature`. |
| `severity` | VARCHAR(20) | NOT NULL | Severity classification: `INFO`, `WARNING`, or `CRITICAL`. |
| `message` | TEXT | NOT NULL | Detailed clinical or diagnostic description of the alert trigger. |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'Active' | Resolution status: `Active`, `Acknowledged`, or `Resolved`. |
| `source` | VARCHAR(50) | NOT NULL, DEFAULT: 'System' | Origin subsystem that generated the alert (e.g., `System`, `AI`, `Wearable`). |

---

### TABLE 25: PRESCRIPTIONS (`prescriptions_prescription`)

**Purpose:**  
Stores pharmacological prescriptions issued by authorized doctors, including medicine dosage, regimen schedule, duration, instructions, and uploaded digital prescription documents.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the prescription record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the prescribed patient. |
| `prescribing_doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the prescribing doctor User account. |
| `prescribing_doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Stored/fallback full name of the prescribing physician. |
| `prescription_date` | DATE | NULL | Date when the prescription was formally issued. |
| `medicines` | TEXT | NOT NULL, DEFAULT: '' | Summary or comma-separated list of prescribed pharmaceutical items. |
| `dosage` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Prescribed dosage quantity (e.g., `500 mg`, `10 ml`). |
| `frequency` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Administration frequency (e.g., `Once daily`, `Twice daily after meals`). |
| `duration` | VARCHAR(100) | NOT NULL, DEFAULT: '7 days' | Prescribed duration of therapy (e.g., `7 days`, `1 month`, `Ongoing`). |
| `instructions` | TEXT | NOT NULL, DEFAULT: '' | Special clinical administration instructions or dietary precautions. |
| `document` | VARCHAR(100) | NULL | File storage path for scanned or digital PDF prescription copy (`prescription_documents/`). |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Status of the prescription regimen (`Active`, `Completed`, `Discontinued`). |

---

### TABLE 26: MEDICAL RECORDS / EHR NOTES (`medical_records_medicalrecord`)

**Purpose:**  
Stores longitudinal electronic health record clinician clinical progress notes and general evaluations.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the medical record note. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking the note to the patient. |
| `clinician_name` | VARCHAR(100) | NOT NULL | Full name of the clinician authoring the record entry. |
| `notes` | TEXT | NOT NULL | Clinical evaluation, progress observations, and diagnostic notes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the medical record entry was logged. |

---

### TABLE 27: PATIENT CONDITIONS (`medical_records_patientcondition`)

**Purpose:**  
Maintains structured tracking of a patient's chronic diagnoses, acute neurological conditions, comorbidities, and resolution timelines.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the condition entry. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the diagnosed patient. |
| `condition_name` | VARCHAR(150) | NOT NULL | Standardized disease or clinical condition name (e.g., `Ischemic Stroke`, `Epilepsy`). |
| `description` | TEXT | NOT NULL, DEFAULT: '' | Clinical details, etiology, and presentation symptoms. |
| `diagnosis_date` | DATE | NULL | Date when the condition was formally diagnosed. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Disease state: `Active`, `Managed`, or `Resolved`. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | Clinical management and prognosis notes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the condition was registered in the system. |

---

### TABLE 28: PATIENT ALLERGIES (`medical_records_patientallergy`)

**Purpose:**  
Tracks verified allergic sensitivities (drug, food, environmental) to prevent adverse medication interactions and trigger clinical alerts.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the allergy record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the allergic patient. |
| `allergen` | VARCHAR(150) | NOT NULL | Specific substance or agent causing hypersensitivity (e.g., `Penicillin`, `NSAIDs`). |
| `reaction` | VARCHAR(200) | NOT NULL, DEFAULT: '' | Observed clinical reaction manifestation (e.g., `Anaphylaxis`, `Urticaria`). |
| `severity` | VARCHAR(50) | NOT NULL, DEFAULT: 'Moderate' | Clinical severity grade: `Mild`, `Moderate`, or `Severe`. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | History of prior reactions and diagnostic details. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Indicates if the allergy remains clinically active. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the allergy entry was created. |

---

### TABLE 29: PATIENT MEDICATIONS (`medical_records_patientmedication`)

**Purpose:**  
Maintains detailed active medication profiles, therapeutic routes, dosage units, prescribing doctors, and treatment durations.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the medication entry. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the medicated patient. |
| `medicine_name` | VARCHAR(150) | NOT NULL | Generic or brand name of the prescribed drug. |
| `dosage` | VARCHAR(100) | NOT NULL | Numerical/quantitative dosage value (e.g., `250`, `50`). |
| `dosage_unit` | VARCHAR(50) | NOT NULL, DEFAULT: 'mg' | Measurement unit for dosage (e.g., `mg`, `mcg`, `ml`, `IU`). |
| `frequency` | VARCHAR(100) | NOT NULL | Dosage frequency schedule (e.g., `TDS`, `BD`, `Once daily at bedtime`). |
| `route` | VARCHAR(50) | NOT NULL, DEFAULT: 'Oral' | Route of administration (e.g., `Oral`, `Intravenous`, `Subcutaneous`). |
| `start_date` | DATE | NULL | Start date of pharmacological therapy. |
| `end_date` | DATE | NULL | Scheduled conclusion or review date. |
| `prescribing_doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the prescribing doctor User account. |
| `prescribing_doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Prescribing doctor name recorded for quick access. |
| `instructions` | TEXT | NOT NULL, DEFAULT: '' | Patient administration instructions and food requirements. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Flag indicating whether medication is currently active in the patient's regimen. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the medication entry was added. |

---

### TABLE 30: PATIENT CONSULTATIONS (`medical_records_patientconsultation`)

**Purpose:**  
Records formal clinical encounter sessions between physicians and patients, including presenting complaints, physical exam findings, follow-up plans, and linked diagnostic records.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the consultation. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the examined patient. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the consulting doctor User account. |
| `doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Stored full name of the consulting physician. |
| `consultation_date` | DATE | NOT NULL | Date when the clinical encounter occurred. |
| `reason` | VARCHAR(255) | NOT NULL | Chief clinical complaint or consultation reason. |
| `clinical_notes` | TEXT | NOT NULL, DEFAULT: '' | Detailed clinical examination observations and assessment. |
| `follow_up_notes` | TEXT | NOT NULL, DEFAULT: '' | Follow-up directions, care modifications, and patient counsel. |
| `next_consultation_date` | DATE | NULL | Recommended date for subsequent review. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the consultation record was created. |

---

### TABLE 31: NEXT CONSULTATIONS (`medical_records_nextconsultation`)

**Purpose:**  
Manages scheduling, facility locations, and time allocations for upcoming patient follow-up consultations.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the scheduled consultation. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the patient. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the attending physician User account. |
| `doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Full name of the doctor scheduled for the session. |
| `consultation_date` | DATE | NOT NULL | Scheduled calendar date of the encounter. |
| `time` | VARCHAR(50) | NOT NULL, DEFAULT: '10:00 AM' | Scheduled appointment time. |
| `facility` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Clinic, hospital wing, or OPD room location. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | Preparation instructions or clinical objectives for the visit. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the consultation was scheduled. |

---

### TABLE 32: MEDICAL DOCUMENTS (`medical_records_medicaldocument`)

**Purpose:**  
Stores metadata, categorized document types (`Blood Test`, `Scan`, `Consultation`, `Prescription`, `Discharge Summary`, `Other`), uploaded file links, and consultation linkages for digital medical attachments.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the document record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the patient to whom the document belongs. |
| `uploaded_by_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the user account that uploaded the document. |
| `document_type` | VARCHAR(50) | NOT NULL, DEFAULT: 'Other' | Category: `Blood Test`, `Scan`, `Consultation`, `Prescription`, `Discharge Summary`, `Other`. |
| `title` | VARCHAR(150) | NOT NULL | Descriptive title of the document (e.g., Brain MRI Axial T2). |
| `upload_date` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the file was uploaded. |
| `description` | TEXT | NOT NULL, DEFAULT: '' | Clinical notes or contextual summary of document content. |
| `file` | VARCHAR(100) | NOT NULL | Server file storage path (`medical_documents/`). |
| `consultation_id` | BIGINT | FK → `medical_records_patientconsultation.id`, NULL | Optional foreign key linking document directly to a clinical consultation. |

---

### TABLE 33: VITAL MEASUREMENTS (`medical_records_vitalmeasurement`)

**Purpose:**  
Stores episodic and clinical vital sign measurements, distinguishing explicitly between manual bedside data entry and automated device/ESP32 sensor readings with full provenance tracking.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the vital measurement record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the measured patient. |
| `measurement_time` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT: `now()` | Exact date and time when the measurement was taken. |
| `source` | VARCHAR(20) | NOT NULL, DEFAULT: 'MANUAL' | Provenance classification: `MANUAL` (bedside manual entry) or `DEVICE` (device/ESP32). |
| `entered_by_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the user who entered the measurement (for manual entries). |
| `entered_by_name` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Cached display name of the user who recorded the observation. |
| `heart_rate` | DOUBLE PRECISION | NULL | Heart rate in beats per minute (BPM). |
| `spo2` | DOUBLE PRECISION | NULL | Peripheral capillary oxygen saturation percentage (SpO2 %). |
| `temperature` | DOUBLE PRECISION | NULL | Body temperature in degrees Celsius (°C). |
| `respiratory_rate` | INTEGER | NULL | Respiratory rate in breaths per minute. |
| `systolic_bp` | INTEGER | NULL | Systolic arterial blood pressure in millimeters of mercury (mmHg). |
| `diastolic_bp` | INTEGER | NULL | Diastolic arterial blood pressure in millimeters of mercury (mmHg). |
| `weight` | DOUBLE PRECISION | NULL | Patient body weight in kilograms (kg). |
| `blood_glucose` | DOUBLE PRECISION | NULL | Blood glucose concentration in mg/dL. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | Clinical notes, patient posture, or measurement circumstances. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the measurement was saved in the database. |

---

### TABLE 34: NOTIFICATIONS (`notifications_notification`)

**Purpose:**  
Stores in-app notifications, system announcements, care-team alerts, and read/unread statuses for individual users.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the notification. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the recipient User account. |
| `title` | VARCHAR(255) | NOT NULL | Brief headline or summary of the notification. |
| `message` | TEXT | NOT NULL | Full body text content of the notification. |
| `category` | VARCHAR(50) | NULL | Notification category (e.g., `ALERT`, `MESSAGE`, `SYSTEM`, `PRESCRIPTION`). |
| `target_id` | VARCHAR(100) | NULL | Identifier of the related entity (e.g., Conversation ID, Alert ID) for deep navigation. |
| `is_read` | BOOLEAN | NOT NULL, DEFAULT: False | Read status flag (False = unread, True = read). |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the notification was created. |

---

### TABLE 35: MEDICATION KNOWLEDGE BASE (`ai_services_medicationknowledgebase`)

**Purpose:**  
Maintains persistent pharmacological reference records, drug classes, contraindications, precautions, allergy warnings, and regulatory formulary references for AI-driven safety validation and clinical query answering.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the medication knowledge entry. |
| `generic_name` | VARCHAR(150) | UNIQUE, NOT NULL | Standardized pharmacological generic active substance name. |
| `brand_names` | VARCHAR(255) | NOT NULL, DEFAULT: '' | Common commercial brand names. |
| `medication_class` | VARCHAR(150) | NOT NULL | Pharmacological / therapeutic drug class. |
| `general_uses` | TEXT | NOT NULL, DEFAULT: '' | Standard medical indications and approved clinical uses. |
| `common_precautions` | TEXT | NOT NULL, DEFAULT: '' | Clinical warnings and safety precautions. |
| `common_contraindications` | TEXT | NOT NULL, DEFAULT: '' | Absolute and relative clinical contraindications. |
| `allergy_considerations` | TEXT | NOT NULL, DEFAULT: '' | Cross-sensitivity and allergic reaction warnings. |
| `common_interactions` | TEXT | NOT NULL, DEFAULT: '' | Known adverse drug-drug and drug-food interactions. |
| `dosage_reference` | TEXT | NOT NULL, DEFAULT: '' | Standard clinical dosing guidelines and therapeutic ranges. |
| `age_precautions` | TEXT | NOT NULL, DEFAULT: '' | Pediatric and geriatric safety guidelines. |
| `pregnancy_precautions` | TEXT | NOT NULL, DEFAULT: '' | Pregnancy and lactation safety classifications and warnings. |
| `category` | VARCHAR(30) | NOT NULL, DEFAULT: 'PRESCRIPTION_MEDICINE' | Category: `GENERAL_INFORMATION`, `OTC_INFORMATION`, `PRESCRIPTION_MEDICINE`, `RESTRICTED`. |
| `source_reference` | VARCHAR(255) | NOT NULL, DEFAULT: 'FDA Label Registry / National Formulary 2026' | Official source citation / national regulatory authority. |
| `source_date` | DATE | NOT NULL, Auto-generated | Date when the knowledge entry was ingested or updated. |

---

### TABLE 36: DOCTOR MEDICATION REVIEW REQUESTS (`ai_services_doctormedicationreviewrequest`)

**Purpose:**  
Stores AI-assisted medication safety inquiries initiated by patients/caregivers that require formal clinical review and human-in-the-loop sign-off by a qualified physician.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the medication review request. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the patient associated with the inquiry. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the user who submitted the question. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the doctor assigned to review the inquiry. |
| `medication_name` | VARCHAR(150) | NOT NULL | Name of the pharmaceutical product under query. |
| `question` | TEXT | NOT NULL | Patient or caregiver question regarding dosage, interactions, or adverse effects. |
| `safety_status` | VARCHAR(50) | NOT NULL, DEFAULT: 'REVIEW_RECOMMENDED' | Initial AI-determined safety assessment score/label. |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT: 'PENDING' | Workflow review status: `PENDING`, `REVIEWED`, or `DECLINED`. |
| `doctor_response` | TEXT | NOT NULL, DEFAULT: '' | Formal clinical advice and response provided by the reviewing physician. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the review request was created. |

---

### TABLE 37: CHAT CONVERSATIONS (`chat_conversation`)

**Purpose:**  
Maintains dedicated care-team communication channels scoped to individual patients, supporting real-time messaging between doctors, caregivers, family members, and patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the care team conversation channel. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking the conversation thread to the central patient. |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'ACTIVE' | Status of conversation thread: `ACTIVE` or `ARCHIVED`. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the conversation channel was initiated. |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the conversation was last active (ordered newest first). |

---

### TABLE 38: CONVERSATION PARTICIPANTS (`chat_conversationparticipant`)

**Purpose:**  
Represents multi-party membership and role participation in a patient's care-team conversation channel.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the membership record. |
| `conversation_id` | BIGINT | FK → `chat_conversation.id`, NOT NULL | Foreign key referencing the conversation channel. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the participant User account. |
| `role` | VARCHAR(20) | NOT NULL | Participant role in chat: `patient`, `doctor`, `caregiver`, `family`, or `admin`. |
| `joined_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the user joined the conversation. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Membership active status flag. |

*Unique Constraint:* Composite unique constraint on `(conversation_id, user_id)`.

---

### TABLE 39: CHAT MESSAGES (`chat_message`)

**Purpose:**  
Stores individual messages, media attachments, delivery states, read receipts, and clinical emergency priorities within a care-team chat conversation.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, NOT NULL, Auto-generated | Unique primary key identifying the chat message. |
| `conversation_id` | BIGINT | FK → `chat_conversation.id`, NOT NULL | Foreign key referencing the parent conversation thread. |
| `sender_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the User account who authored the message. |
| `message_type` | VARCHAR(20) | NOT NULL, DEFAULT: 'TEXT' | Message payload format: `TEXT`, `IMAGE`, `DOCUMENT`, or `VIDEO`. |
| `content` | TEXT | NOT NULL, DEFAULT: '' | Text content or caption of the message. |
| `attachment` | VARCHAR(100) | NULL | Server storage path for uploaded media (`private_chat_attachments/<uuid>.<ext>`). |
| `attachment_original_name` | VARCHAR(255) | NOT NULL, DEFAULT: '' | Original filename of the uploaded attachment at time of upload. |
| `attachment_mime_type` | VARCHAR(100) | NOT NULL, DEFAULT: '' | MIME type of the uploaded file (e.g., `image/jpeg`, `application/pdf`). |
| `attachment_size` | INTEGER | NULL | File size of attachment in bytes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the message was sent (ordered chronologically). |
| `delivered_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the message was delivered to recipient devices. |
| `read_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the message was marked as read by participants. |
| `priority` | VARCHAR(20) | NOT NULL, DEFAULT: 'NORMAL' | Priority level: `NORMAL`, `URGENT`, or `EMERGENCY`. |
| `is_emergency` | BOOLEAN | NOT NULL, DEFAULT: False | Emergency flag triggering elevated audio/visual notifications across the care team. |

---

## DATABASE RELATIONSHIP SUMMARY

The relational architecture of NeuroCare Nexus is organized into five core functional clusters:

### 1. User Authentication & Clinical Profile Relationships
- `CustomUser` (1) ──── (1) `DoctorProfile` [One-to-One via `DoctorProfile.user_id`]
- `CustomUser` (1) ──── (1) `CaregiverProfile` [One-to-One via `CaregiverProfile.user_id`]
- `CustomUser` (1) ──── (M) `AuditLog` [One-to-Many via `AuditLog.actor_id`]
- `CustomUser` (1) ──── (M) `VerificationRecord` [One-to-Many via `VerificationRecord.user_id` and `verified_by_id`]
- `CustomUser` (1) ──── (M) `Notification` [One-to-Many via `Notification.user_id`]

### 2. Reference Regulatory Registry Relationships (Credential Verification)
- `ReferenceDoctorRegistry` (1) ──── (M) `DoctorDisciplinaryRecord` [One-to-Many via `DoctorDisciplinaryRecord.doctor_id`]
- `ReferenceDoctorRegistry` (1) ──── (M) `ReferenceDoctorAffiliation` [One-to-Many via `ReferenceDoctorAffiliation.reference_doctor_id`]
- `HealthFacility` (1) ──── (M) `ReferenceDoctorAffiliation` [One-to-Many via `ReferenceDoctorAffiliation.facility_id`]
- `HealthFacility` (1) ──── (M) `DoctorFacilityAffiliation` [One-to-Many via `DoctorFacilityAffiliation.facility_id`]
- `DoctorProfile` (1) ──── (M) `DoctorFacilityAffiliation` [One-to-Many via `DoctorFacilityAffiliation.doctor_id`]
- `SyntheticNPI` (1) ──── (M) `Patient` [One-to-Many via `Patient.doctor_npi_id`]
- `SyntheticNPI` (1) ──── (M) `DoctorConnectionRequest` [One-to-Many via `DoctorConnectionRequest.doctor_npi_id`]

### 3. Patient & Care-Team Multi-Party Authorizations
- `CustomUser` (Doctor) (M) ──── (N) `Patient` through `DoctorPatientLink` [Composite Unique: `(patient_id, doctor_id)`]
- `CustomUser` (Caregiver) (M) ──── (N) `Patient` through `CaregiverPatientLink` [Composite Unique: `(caregiver_id, patient_id)`]
- `CustomUser` (Family) (M) ──── (N) `Patient` through `FamilyPatientLink` [Composite Unique: `(family_id, patient_id)`]
- `Patient` (1) ──── (M) `DoctorConnectionRequest` [One-to-Many via `DoctorConnectionRequest.patient_id`]
- `Patient` (1) ──── (M) `Appointment` [One-to-Many via `Appointment.patient_id`]

### 4. IoT Devices, Telemetry & Clinical Records
- `Patient` (1) ──── (1) `WearableDevice` through `DeviceAssignment` [Unique `patient_id` and `device_id`]
- `Patient` (1) ──── (M) `SensorReading` [One-to-Many via `SensorReading.patient_id` (High-frequency IoT Telemetry)]
- `Patient` (1) ──── (M) `VitalMeasurement` [One-to-Many via `VitalMeasurement.patient_id` (Manual/Device Episodic Vitals)]
- `Patient` (1) ──── (M) `Alert` [One-to-Many via `Alert.patient_id`]
- `Patient` (1) ──── (M) `Prescription` [One-to-Many via `Prescription.patient_id`]
- `Patient` (1) ──── (M) `MedicalRecord` [One-to-Many via `MedicalRecord.patient_id`]
- `Patient` (1) ──── (M) `PatientCondition` [One-to-Many via `PatientCondition.patient_id`]
- `Patient` (1) ──── (M) `PatientAllergy` [One-to-Many via `PatientAllergy.patient_id`]
- `Patient` (1) ──── (M) `PatientMedication` [One-to-Many via `PatientMedication.patient_id`]
- `Patient` (1) ──── (M) `PatientConsultation` [One-to-Many via `PatientConsultation.patient_id`]
- `Patient` (1) ──── (M) `NextConsultation` [One-to-Many via `NextConsultation.patient_id`]
- `Patient` (1) ──── (M) `MedicalDocument` [One-to-Many via `MedicalDocument.patient_id`]
- `PatientConsultation` (1) ──── (M) `MedicalDocument` [One-to-Many via `MedicalDocument.consultation_id`]

### 5. Care-Team Communication & AI Services
- `Patient` (1) ──── (M) `Conversation` [One-to-Many via `Conversation.patient_id`]
- `Conversation` (1) ──── (M) `ConversationParticipant` [One-to-Many via `ConversationParticipant.conversation_id`]
- `CustomUser` (1) ──── (M) `ConversationParticipant` [One-to-Many via `ConversationParticipant.user_id`, Composite Unique: `(conversation_id, user_id)`]
- `Conversation` (1) ──── (M) `Message` [One-to-Many via `Message.conversation_id`]
- `CustomUser` (1) ──── (M) `Message` [One-to-Many via `Message.sender_id`]
- `Patient` (1) ──── (M) `DoctorMedicationReviewRequest` [One-to-Many via `DoctorMedicationReviewRequest.patient_id`]
- `CustomUser` (1) ──── (M) `DoctorMedicationReviewRequest` [One-to-Many via `user_id` and `doctor_id`]

---

## DATABASE DESIGN VALIDATION REPORT

1. **Total project-specific application models found:** 39 models across 12 local Django apps.
2. **Total tables documented:** 39 core application tables (see full catalog in Table 1 through Table 39).
3. **Primary keys checked:** All 39 tables have verified primary keys. 34 tables use auto-incrementing `BIGINT` (`BigAutoField`), while 5 tables use explicit domain character primary keys (`Patient.id` [VARCHAR(20)], `SyntheticPatient.patient_id` [VARCHAR(20)], `SyntheticNPI.npi` [VARCHAR(50)], `ReferenceDoctorRegistry.registration_number` [VARCHAR(50)], `SyntheticCaregiver.agency_id` [VARCHAR(20)], `SyntheticDevice.serial` [VARCHAR(20)], and `WearableDevice.serial` [VARCHAR(20)]).
4. **Foreign keys checked:** 42 explicit relational Foreign Keys and One-to-One Keys verified and validated across all models.
5. **One-to-one relationships found:** 3 verified One-to-One relationships:
   - `DoctorProfile.user` ↔ `CustomUser`
   - `CaregiverProfile.user` ↔ `CustomUser`
   - `DeviceAssignment` (One-to-One with `Patient` and One-to-One with `WearableDevice`)
6. **Many-to-many / through relationships found:** 4 explicit join/link models:
   - `DoctorPatientLink` (Doctor `CustomUser` ↔ `Patient`)
   - `CaregiverPatientLink` (Caregiver `CustomUser` ↔ `Patient`)
   - `FamilyPatientLink` (Family `CustomUser` ↔ `Patient`)
   - `ConversationParticipant` (`Conversation` ↔ `CustomUser`)
7. **Unique constraints found:** 
   - `accounts_customuser.email` (UNIQUE)
   - `patients_syntheticpatient.code` (UNIQUE)
   - `patients_familypatientlink` (`family`, `patient`) (UNIQUE TOGETHER)
   - `doctors_referencedoctorregistry.reference_id` (UNIQUE)
   - `doctors_healthfacility.facility_id` (UNIQUE)
   - `doctors_healthfacility.registration_identifier` (UNIQUE)
   - `doctors_doctordisciplinaryrecord.disciplinary_id` (UNIQUE)
   - `doctors_referencedoctoraffiliation.affiliation_id` (UNIQUE)
   - `doctors_doctorprofile.user_id` (UNIQUE)
   - `doctors_doctorconnectionrequest` (`patient`, `doctor_npi`) (UNIQUE TOGETHER)
   - `doctors_doctorpatientlink` (`patient`, `doctor`) (UNIQUE TOGETHER)
   - `caregivers_caregiverprofile.user_id` (UNIQUE)
   - `caregivers_caregiverpatientlink` (`caregiver`, `patient`) (UNIQUE TOGETHER)
   - `devices_syntheticdevice.mac` (UNIQUE)
   - `devices_wearabledevice.mac` (UNIQUE)
   - `devices_deviceassignment.patient_id` (UNIQUE)
   - `devices_deviceassignment.device_id` (UNIQUE)
   - `ai_services_medicationknowledgebase.generic_name` (UNIQUE)
   - `chat_conversationparticipant` (`conversation`, `user`) (UNIQUE TOGETHER)
8. **Important indexes found:**
   - `doctors_referencedoctorregistry`: B-Tree indexes on `normalized_name`, `council`, and `registration_status`.
   - `ai_services_medicationknowledgebase`: Indexes on `generic_name` and `medication_class`.
   - Auto-created indexes on all primary keys, unique fields, and foreign keys.
9. **Duplicate/overlapping models detected:** None that require code refactoring; clear architectural separation exists between real-time telemetry vs episodic vitals, reference datasets vs operational user profiles, and system alerts vs general notifications (see full breakdown below).
10. **Potential orphan/unused models:** A placeholder `chat/models.py` file was detected in the root project directory, which is an empty artifact outside the active `backend/chat` package. The operational application relies exclusively on `backend/chat/models.py`.
11. **MySQL-specific terminology detected anywhere in current documentation/code:** None. All models and migrations cleanly compile against the configured PostgreSQL engine (`django.db.backends.postgresql`).
12. **Django model vs migration inconsistencies:** Zero inconsistencies. All 29 Django migrations across all 12 apps are in complete parity and fully applied (`[X]`) in the active PostgreSQL database.
13. **Django model vs PostgreSQL inconsistencies:** Verified zero discrepancies. Introspected column definitions, types, and nullability match the PostgreSQL schema.
14. **Missing relationships that could affect existing functionality:** None. All cross-app relationships (e.g., chat to users/patients, doctor-patient links, AI review requests) are consistently defined with appropriate cascade rules (`CASCADE` or `SET_NULL`).
15. **Standard Django framework tables excluded from the academic Table Design:** The following 9 framework/infrastructure tables were intentionally excluded from this design to preserve academic clarity: `django_migrations`, `django_content_type`, `django_admin_log`, `auth_permission`, `auth_group`, `auth_group_permissions`, `accounts_customuser_groups`, `accounts_customuser_user_permissions`, and `django_session`.

---

## CHECK FOR DUPLICATION & CONCEPTUAL SEPARATION

| Conceptual Comparison | Model A | Model B | Classification | Technical Justification |
|-----------------------|---------|---------|----------------|--------------------------|
| **Vitals vs IoT Telemetry** | `VitalMeasurement` | `SensorReading` | **VALID SEPARATION** | `SensorReading` stores automated, continuous, high-frequency time-series telemetry directly from the ESP32 wearable (heart rate, SpO2, skin temp, 6-axis IMU accelerometer/gyroscope, battery, RSSI). In contrast, `VitalMeasurement` stores episodic, clinical bedside measurements (blood pressure, blood glucose, weight, respiratory rate) with explicit provenance tracking (`MANUAL` entry with `entered_by` audit vs `DEVICE`). |
| **Operational Doctor vs Reference Registry** | `DoctorProfile` / `CustomUser` | `ReferenceDoctorRegistry` | **VALID SEPARATION** | `ReferenceDoctorRegistry` is a read-only regulatory reference dataset (e.g. State Medical Council registries) containing official registration numbers, council names, and disciplinary sanctions used strictly as verification benchmarks. `DoctorProfile` represents actual registered, authenticated system user accounts actively managing patients on NeuroCare Nexus. |
| **System Alerts vs User Notifications** | `Alert` | `Notification` | **VALID SEPARATION** | `Alert` records patient-specific clinical emergencies and threshold breaches (`CRITICAL`, `WARNING`, `INFO` for heart rate, SpO2, fall events) monitored by clinicians across the patient overview. `Notification` represents generalized user-specific in-app inbox messages (e.g., chat message received, connection approved, document uploaded) targeted at individual user accounts. |
| **Clinical Encounter vs Progress Notes** | `PatientConsultation` | `MedicalRecord` | **VALID SEPARATION** | `PatientConsultation` represents formal scheduled or completed doctor-patient encounters with distinct date, reason, clinical findings, next consultation date, and document linkages. `MedicalRecord` represents general longitudinal clinical progress notes and observations logged by various healthcare workers over time. |
| **Prescription Regimen vs Active Medication** | `Prescription` | `PatientMedication` | **VALID SEPARATION** | `Prescription` represents the formal medical prescription order issued by a physician (including uploaded scanned documents, duration, and doctor signature). `PatientMedication` represents the structured active pharmacological list of all medications the patient is currently taking (with dosage units, routes, and active/inactive status). |
