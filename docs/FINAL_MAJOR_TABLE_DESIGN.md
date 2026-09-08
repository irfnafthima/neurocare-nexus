# TABLE DESIGN

NeuroCare Nexus uses PostgreSQL as its relational database management system. The database follows a relational design to support secure user management, patient clinical information, care-team authorization, physiological monitoring, doctor verification, alerts, communication, and AI-assisted healthcare functionality.

Standard Django internal framework tables (such as `django_migrations`, `django_content_type`, `django_admin_log`, `django_session`, and `auth_permission`) as well as synthetic testing registry models (`SyntheticPatient`, `SyntheticCaregiver`, `SyntheticDevice`, and `SyntheticNPI`) are excluded from this core Table Design specification to present the operational application schema required for the NeuroCare Nexus platform.

---

## A. CORE USER AND ACCESS TABLES

### TABLE 1: USERS (`accounts_customuser`)

**Purpose:**  
Stores authentication credentials, role-based access classifications (`patient`, `doctor`, `caregiver`, `family`, `admin`), account lifecycle states, and primary contact attributes for all registered users.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the user account. |
| `password` | VARCHAR(128) | NOT NULL | PBKDF2/Argon2 cryptographic hash of the user password. |
| `last_login` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp of the user's most recent authenticated session. |
| `is_superuser` | BOOLEAN | NOT NULL, DEFAULT: False | Designates whether the user possesses global administrative privileges. |
| `username` | VARCHAR(150) | NULL | Optional username field (email serves as primary authentication key). |
| `first_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | First name of the user. |
| `last_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Last name or surname of the user. |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | Unique primary email address used for system login and communication. |
| `is_staff` | BOOLEAN | NOT NULL, DEFAULT: False | Designates whether the user can access the administrative portal. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Designates whether this account is currently active. |
| `date_joined` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the user account was registered. |
| `full_name` | VARCHAR(100) | NOT NULL | Full legal display name of the user. |
| `phone` | VARCHAR(20) | NULL | Primary contact phone number. |
| `role` | VARCHAR(50) | NOT NULL | Role categorization: `patient`, `doctor`, `caregiver`, `family`, or `admin`. |
| `approved` | BOOLEAN | NOT NULL, DEFAULT: True | Approval status (defaults to `False` for doctor role pending vetting). |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'ACTIVE' | Account lifecycle status: `PENDING`, `ACTIVE`, or `REJECTED`. |
| `specialization` | VARCHAR(100) | NULL | Medical specialty for doctor accounts (e.g., Neurologist, Physiatrist). |
| `experience` | INTEGER | NULL | Total years of professional medical or caregiving experience. |
| `bio` | TEXT | NULL | Professional biography, summary, or clinical background notes. |

---

### TABLE 2: DOCTOR PROFILES (`doctors_doctorprofile`)

**Purpose:**  
Stores verified professional profiles, statutory council registration credentials, qualifications, and verification states for registered doctor accounts.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the doctor profile. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, UNIQUE, NOT NULL | One-to-One foreign key linking to the registered User account (role: doctor). |
| `medical_registration_number` | VARCHAR(50) | NOT NULL | Official medical registration number issued by statutory council. |
| `state_medical_council` | VARCHAR(150) | NOT NULL | State medical council where the practitioner is officially registered. |
| `qualification` | VARCHAR(150) | NOT NULL | Primary recognized medical degrees (e.g., MBBS, MD, DM Neurology). |
| `specialization` | VARCHAR(100) | NOT NULL | Clinical specialization focus area. |
| `additional_qualifications` | VARCHAR(255) | NULL | Additional fellowships, diplomas, or postgraduate certifications. |
| `hpr_id` | VARCHAR(100) | NULL | National Healthcare Professional Registry (HPR / ABDM) digital ID. |
| `years_of_experience` | INTEGER | NOT NULL, DEFAULT: 0 | Total cumulative years in active clinical practice. |
| `verification_status` | VARCHAR(25) | NOT NULL, DEFAULT: 'PENDING' | Vetting state: `PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `SUSPENDED`. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the profile was officially approved and verified. |

---

### TABLE 3: CAREGIVER PROFILES (`caregivers_caregiverprofile`)

**Purpose:**  
Stores nursing credentials, agency affiliations, qualifications, and verification statuses for registered professional and family caregiver accounts.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the caregiver profile. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, UNIQUE, NOT NULL | One-to-One foreign key linking to the registered User account (role: caregiver). |
| `caregiver_type` | VARCHAR(20) | NOT NULL, DEFAULT: 'PROFESSIONAL' | Caregiver type: `PROFESSIONAL` (certified nurse/aide) or `FAMILY`. |
| `full_name` | VARCHAR(100) | NOT NULL | Complete legal name of the caregiver. |
| `contact` | VARCHAR(50) | NULL | Direct telephone contact number. |
| `qualification` | VARCHAR(150) | NULL | Nursing accreditation, nursing diploma, or clinical training certification. |
| `years_of_experience` | INTEGER | NOT NULL, DEFAULT: 0 | Total years in patient homecare, nursing, or clinical assistance. |
| `skills` | TEXT | NULL | Clinical competencies (e.g., Stroke Rehab, Vital Monitoring, Tracheostomy). |
| `previous_experience` | TEXT | NULL | Summary of past clinical nursing or caregiving engagements. |
| `current_agency` | VARCHAR(150) | NULL | Name of employing home healthcare or nursing agency. |
| `agency_contact` | VARCHAR(50) | NULL | Agency supervisory contact number. |
| `verification_status` | VARCHAR(20) | NOT NULL, DEFAULT: 'PENDING' | Vetting state: `PENDING`, `UNDER_REVIEW`, `VERIFIED`, `REJECTED`, `SUSPENDED`. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when the caregiver profile was verified. |

---

### TABLE 4: DOCTOR-PATIENT AUTHORIZATION LINKS (`doctors_doctorpatientlink`)

**Purpose:**  
Maintains active authorized clinical relationships between doctors and patients, establishing clinical data access boundaries.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the doctor-patient linkage. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the managed patient. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the assigned doctor User account (role: doctor). |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the doctor-patient authorization was established. |

*Unique Constraint:* Composite unique constraint on `(patient_id, doctor_id)`.

---

### TABLE 5: CAREGIVER-PATIENT AUTHORIZATION LINKS (`caregivers_caregiverpatientlink`)

**Purpose:**  
Maintains authorized bedside caregiving assignments, access permissions, and read-only privilege restrictions between caregivers and patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the caregiver assignment link. |
| `caregiver_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the caregiver User account (role: caregiver). |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the assigned patient. |
| `is_read_only` | BOOLEAN | NOT NULL, DEFAULT: True | Access restriction flag (defaults to True; prevents unauthorized clinical modifications). |
| `is_approved` | BOOLEAN | NOT NULL, DEFAULT: True | Administrative approval status of the caregiving assignment. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the caregiving assignment was created. |

*Unique Constraint:* Composite unique constraint on `(caregiver_id, patient_id)`.

---

### TABLE 6: FAMILY-PATIENT AUTHORIZATION LINKS (`patients_familypatientlink`)

**Purpose:**  
Maintains verified family relationships, portal visibility authorization, and optional clinical record editing permissions between family users and patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the family-patient link. |
| `family_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the family User account (role: family). |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the linked patient. |
| `is_approved` | BOOLEAN | NOT NULL, DEFAULT: False | Designates whether the family link has been approved by admin/doctor. |
| `can_edit_clinical` | BOOLEAN | NOT NULL, DEFAULT: False | Privilege flag granting permission to add or update clinical notes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the family relationship link was established. |

*Unique Constraint:* Composite unique constraint on `(family_id, patient_id)`.

---

### TABLE 7: DOCTOR CREDENTIAL VERIFICATION RECORDS (`doctors_verificationrecord`)

**Purpose:**  
Logs automated and administrative credential verification audits, regulatory matching scores, and vetting decisions for medical practitioners.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the verification audit log. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the user account undergoing verification. |
| `verification_type` | VARCHAR(30) | NOT NULL | Vetting type: `PROFESSIONAL_REGISTRATION`, `IDENTITY_MATCH`, `QUALIFICATION`, `HOSPITAL_AFFILIATION`, `ADMIN_REVIEW`. |
| `source` | VARCHAR(150) | NOT NULL | Verification source or regulatory registry endpoint checked. |
| `result` | VARCHAR(20) | NOT NULL | Outcome: `EXACT_MATCH`, `LIKELY_MATCH`, `MISMATCH`, `NOT_FOUND`, `MANUAL_REVIEW`. |
| `verified_by_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the administrator who conducted or ratified review. |
| `verified_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the verification step was executed. |
| `remarks` | TEXT | NULL | Verification notes, confidence score, or discrepancy details. |

---

## B. CLINICAL AND PATIENT RECORD TABLES

### TABLE 8: PATIENTS (`patients_patient`)

**Purpose:**  
Stores core demographic, clinical baseline, neurological condition summary, risk score, and emergency contact details for enrolled patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | VARCHAR(20) | PK, NOT NULL | Unique business primary key identifying the patient (e.g., `P-102`). |
| `name` | VARCHAR(100) | NOT NULL | Full name of the patient. |
| `age` | INTEGER | NOT NULL | Patient age in years. |
| `gender` | VARCHAR(10) | NOT NULL | Patient gender (e.g., `Male`, `Female`, `Other`). |
| `room` | VARCHAR(10) | NOT NULL | Hospital room or ward designation (e.g., `302A`, `ICU-4`). |
| `condition` | VARCHAR(255) | NOT NULL | Primary neurological condition or clinical diagnosis summary. |
| `risk` | INTEGER | NOT NULL, DEFAULT: 0 | Baseline clinical risk score / severity rating index (0–100). |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Normal' | Operational status (e.g., `Normal`, `Critical`, `Stable`, `Discharged`). |
| `ehr_notes` | TEXT | NOT NULL, DEFAULT: '' | Baseline electronic health record summary notes. |
| `dob` | DATE | NULL | Date of birth. |
| `phone` | VARCHAR(25) | NOT NULL, DEFAULT: '' | Primary contact telephone number. |
| `address` | TEXT | NOT NULL, DEFAULT: '' | Residential address. |
| `emergency_contact_name` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Full name of primary emergency contact / next of kin. |
| `emergency_contact_phone` | VARCHAR(25) | NOT NULL, DEFAULT: '' | Emergency contact telephone number. |
| `blood_group` | VARCHAR(10) | NOT NULL, DEFAULT: '' | ABO/Rh blood group typing (e.g., `A+`, `O-`, `B+`). |
| `doctor_npi_id` | VARCHAR(50) | NULL | Optional reference identifier to primary attending physician. |

---

### TABLE 9: PATIENT CONDITIONS (`medical_records_patientcondition`)

**Purpose:**  
Maintains structured tracking of a patient's chronic diagnoses, acute neurological conditions, comorbidities, and resolution timelines.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the condition entry. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the diagnosed patient. |
| `condition_name` | VARCHAR(150) | NOT NULL | Standardized disease or clinical condition name (e.g., `Ischemic Stroke`). |
| `description` | TEXT | NOT NULL, DEFAULT: '' | Clinical details, etiology, and presentation symptoms. |
| `diagnosis_date` | DATE | NULL | Date when the condition was formally diagnosed. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Disease status: `Active`, `Managed`, or `Resolved`. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | Clinical management and prognosis notes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the condition was recorded. |

---

### TABLE 10: PATIENT ALLERGIES (`medical_records_patientallergy`)

**Purpose:**  
Tracks verified allergic sensitivities (drug, food, environmental) to prevent adverse medication interactions and trigger clinical alerts.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the allergy record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the allergic patient. |
| `allergen` | VARCHAR(150) | NOT NULL | Specific substance or agent causing hypersensitivity (e.g., `Penicillin`). |
| `reaction` | VARCHAR(200) | NOT NULL, DEFAULT: '' | Observed clinical reaction (e.g., `Anaphylaxis`, `Urticaria`, `Bronchospasm`). |
| `severity` | VARCHAR(50) | NOT NULL, DEFAULT: 'Moderate' | Clinical severity grade: `Mild`, `Moderate`, or `Severe`. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | History of prior reactions and diagnostic details. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Indicates if the allergy remains clinically active. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the allergy entry was created. |

---

### TABLE 11: PATIENT ACTIVE MEDICATIONS (`medical_records_patientmedication`)

**Purpose:**  
Maintains detailed active medication regimens, therapeutic routes, dosage units, prescribing doctors, and treatment durations.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the active medication entry. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the medicated patient. |
| `medicine_name` | VARCHAR(150) | NOT NULL | Generic or brand name of the pharmaceutical drug. |
| `dosage` | VARCHAR(100) | NOT NULL | Numerical or quantitative dosage value (e.g., `500`, `25`). |
| `dosage_unit` | VARCHAR(50) | NOT NULL, DEFAULT: 'mg' | Measurement unit for dosage (e.g., `mg`, `mcg`, `ml`, `IU`). |
| `frequency` | VARCHAR(100) | NOT NULL | Administration schedule (e.g., `Once daily`, `Twice daily after meals`). |
| `route` | VARCHAR(50) | NOT NULL, DEFAULT: 'Oral' | Route of administration (e.g., `Oral`, `Intravenous`, `Subcutaneous`). |
| `start_date` | DATE | NULL | Start date of pharmacological therapy. |
| `end_date` | DATE | NULL | Scheduled conclusion or review date. |
| `prescribing_doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the prescribing doctor User account. |
| `prescribing_doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Prescribing doctor name stored for quick access. |
| `instructions` | TEXT | NOT NULL, DEFAULT: '' | Patient administration instructions and dietary requirements. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Flag indicating whether medication is currently active in regimen. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the medication entry was recorded. |

---

### TABLE 12: PRESCRIPTIONS (`prescriptions_prescription`)

**Purpose:**  
Stores formal prescription orders issued by doctors, including medication details, dosage schedules, duration, instructions, and uploaded digital documents.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the prescription record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the prescribed patient. |
| `prescribing_doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the prescribing doctor User account. |
| `prescribing_doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Stored full name of the prescribing physician. |
| `prescription_date` | DATE | NULL | Date when the prescription was formally issued. |
| `medicines` | TEXT | NOT NULL, DEFAULT: '' | Summary or comma-separated list of prescribed medications. |
| `dosage` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Prescribed dosage quantity (e.g., `500 mg`, `10 ml`). |
| `frequency` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Prescribed frequency (e.g., `BD`, `TDS`, `Once daily`). |
| `duration` | VARCHAR(100) | NOT NULL, DEFAULT: '7 days' | Prescribed duration of therapy (e.g., `7 days`, `1 month`, `Ongoing`). |
| `instructions` | TEXT | NOT NULL, DEFAULT: '' | Special clinical instructions or precautions. |
| `document` | VARCHAR(100) | NULL | File storage path for scanned or digital PDF prescription copy. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Status of prescription (`Active`, `Completed`, `Discontinued`). |

---

### TABLE 13: MEDICAL CLINICAL RECORDS (`medical_records_medicalrecord`)

**Purpose:**  
Stores longitudinal electronic health record progress notes and clinical observations authored by attending clinicians.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the clinical record note. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking the note to the patient. |
| `clinician_name` | VARCHAR(100) | NOT NULL | Full name of the clinician authoring the record entry. |
| `notes` | TEXT | NOT NULL | Clinical evaluation, progress observations, and diagnostic notes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the clinical record entry was logged. |

---

### TABLE 14: PATIENT CONSULTATIONS (`medical_records_patientconsultation`)

**Purpose:**  
Records formal clinical encounter sessions between physicians and patients, including presenting complaints, physical exam findings, follow-up plans, and next consultation dates.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the consultation. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the examined patient. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the consulting doctor User account. |
| `doctor_name` | VARCHAR(150) | NOT NULL, DEFAULT: '' | Stored full name of the consulting physician. |
| `consultation_date` | DATE | NOT NULL | Date when the clinical encounter occurred. |
| `reason` | VARCHAR(255) | NOT NULL | Chief clinical complaint or consultation reason. |
| `clinical_notes` | TEXT | NOT NULL, DEFAULT: '' | Detailed clinical examination observations and assessment. |
| `follow_up_notes` | TEXT | NOT NULL, DEFAULT: '' | Follow-up directions, care modifications, and patient counsel. |
| `next_consultation_date` | DATE | NULL | Recommended date for subsequent clinical review. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the consultation record was created. |

---

### TABLE 15: MEDICAL DOCUMENTS (`medical_records_medicaldocument`)

**Purpose:**  
Stores categorized medical documents (`Blood Test`, `Scan`, `Consultation`, `Prescription`, `Discharge Summary`, `Other`), uploaded file links, and optional consultation linkages.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the document record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the patient to whom document belongs. |
| `uploaded_by_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the user account that uploaded the document. |
| `document_type` | VARCHAR(50) | NOT NULL, DEFAULT: 'Other' | Category: `Blood Test`, `Scan`, `Consultation`, `Prescription`, `Discharge Summary`, `Other`. |
| `title` | VARCHAR(150) | NOT NULL | Descriptive title of document (e.g., Brain MRI Axial T2). |
| `upload_date` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the file was uploaded. |
| `description` | TEXT | NOT NULL, DEFAULT: '' | Clinical notes or contextual summary of document content. |
| `file` | VARCHAR(100) | NOT NULL | Server file storage path (`medical_documents/`). |
| `consultation_id` | BIGINT | FK → `medical_records_patientconsultation.id`, NULL | Optional foreign key linking document directly to a clinical consultation. |

---

## C. IoT AND PHYSIOLOGICAL MONITORING TABLES

### TABLE 16: WEARABLE DEVICES (`devices_wearabledevice`)

**Purpose:**  
Maintains physical ESP32-based patient monitoring bands, hardware serial identifiers, MAC addresses, and operational statuses.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `serial` | VARCHAR(20) | PK, NOT NULL | Unique hardware serial number of the wearable device. |
| `mac` | VARCHAR(30) | UNIQUE, NOT NULL | Physical Wi-Fi / Bluetooth MAC address of microcontroller. |
| `status` | VARCHAR(50) | NOT NULL, DEFAULT: 'Active' | Operational status: `Active`, `Charging`, `Maintenance`, `Decommissioned`. |

---

### TABLE 17: WEARABLE DEVICE ASSIGNMENTS (`devices_deviceassignment`)

**Purpose:**  
Maintains strict 1-to-1 operational pairing between an active wearable device and an enrolled patient.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the device assignment. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, UNIQUE, NOT NULL | One-to-One foreign key linking assignment to the patient. |
| `device_id` | VARCHAR(20) | FK → `devices_wearabledevice.serial`, UNIQUE, NOT NULL | One-to-One foreign key linking assignment to the wearable unit. |
| `assigned_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the hardware unit was paired to the patient. |

---

### TABLE 18: IoT SENSOR TELEMETRY READINGS (`monitoring_sensorreading`)

**Purpose:**  
Stores high-frequency automated IoT sensor telemetry transmitted continuously by ESP32 wearable devices (MAX30102 pulse oximeter, DS18B20 temperature sensor, MPU6050 6-axis IMU).

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the telemetry reading. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the monitored patient. |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Exact timestamp when telemetry was captured and ingested. |
| `heart_rate` | INTEGER | NULL | Real-time heart rate from MAX30102 sensor (BPM). |
| `spo2` | INTEGER | NULL | Peripheral blood oxygen saturation percentage from MAX30102 sensor (SpO2 %). |
| `temperature` | NUMERIC(4, 2) | NULL | Skin/body temperature in degrees Celsius (°C) from DS18B20 sensor. |
| `accel_x` | NUMERIC(5, 2) | NULL | Linear acceleration along X-axis from MPU6050 accelerometer ($m/s^2$ or g). |
| `accel_y` | NUMERIC(5, 2) | NULL | Linear acceleration along Y-axis from MPU6050 accelerometer ($m/s^2$ or g). |
| `accel_z` | NUMERIC(5, 2) | NULL | Linear acceleration along Z-axis from MPU6050 accelerometer ($m/s^2$ or g). |
| `gyro_x` | NUMERIC(5, 2) | NULL | Angular velocity around X-axis from MPU6050 gyroscope (deg/sec). |
| `gyro_y` | NUMERIC(5, 2) | NULL | Angular velocity around Y-axis from MPU6050 gyroscope (deg/sec). |
| `gyro_z` | NUMERIC(5, 2) | NULL | Angular velocity around Z-axis from MPU6050 gyroscope (deg/sec). |
| `fall_detected` | BOOLEAN | NOT NULL, DEFAULT: False | Kinematic threshold trigger indicating a patient fall event. |
| `esp32_connected` | BOOLEAN | NOT NULL, DEFAULT: True | Microcontroller heartbeat link connectivity status. |
| `esp32_battery` | INTEGER | NULL | Remaining battery charge percentage of wearable unit (0–100%). |
| `esp32_rssi` | INTEGER | NULL | Received Signal Strength Indication (RSSI) of Wi-Fi in dBm. |

---

### TABLE 19: CLINICAL VITAL MEASUREMENTS (`medical_records_vitalmeasurement`)

**Purpose:**  
Stores episodic and clinical vital sign measurements, distinguishing explicitly between manual bedside data entry and automated device readings with full provenance tracking.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the vital measurement record. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the measured patient. |
| `measurement_time` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT: `now()` | Exact date and time when measurement was taken. |
| `source` | VARCHAR(20) | NOT NULL, DEFAULT: 'MANUAL' | Provenance classification: `MANUAL` (bedside entry) or `DEVICE` (device/ESP32). |
| `entered_by_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the user who entered data (for manual entries). |
| `entered_by_name` | VARCHAR(100) | NOT NULL, DEFAULT: '' | Cached display name of the user who recorded the observation. |
| `heart_rate` | DOUBLE PRECISION | NULL | Heart rate in beats per minute (BPM). |
| `spo2` | DOUBLE PRECISION | NULL | Peripheral capillary oxygen saturation percentage (SpO2 %). |
| `temperature` | DOUBLE PRECISION | NULL | Body temperature in degrees Celsius (°C). |
| `respiratory_rate` | INTEGER | NULL | Respiratory rate in breaths per minute. |
| `systolic_bp` | INTEGER | NULL | Systolic arterial blood pressure in mmHg. |
| `diastolic_bp` | INTEGER | NULL | Diastolic arterial blood pressure in mmHg. |
| `weight` | DOUBLE PRECISION | NULL | Patient body weight in kilograms (kg). |
| `blood_glucose` | DOUBLE PRECISION | NULL | Blood glucose concentration in mg/dL. |
| `notes` | TEXT | NOT NULL, DEFAULT: '' | Clinical notes or measurement circumstances. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the measurement was saved. |

---

## D. ALERT AND NOTIFICATION TABLES

### TABLE 20: CLINICAL AND SENSOR ALERTS (`alerts_alert`)

**Purpose:**  
Captures real-time clinical threshold breaches, physiological emergencies, hardware failover warnings, and AI-generated hazard notifications.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the alert. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking alert to the affected patient. |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when trigger condition occurred. |
| `type` | VARCHAR(50) | NOT NULL | Alert classification: `Heart Rate`, `SpO2`, `Fall`, `Emergency`, `Temperature`. |
| `severity` | VARCHAR(20) | NOT NULL | Severity classification: `INFO`, `WARNING`, or `CRITICAL`. |
| `message` | TEXT | NOT NULL | Detailed clinical or diagnostic description of alert trigger. |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'Active' | Resolution status: `Active`, `Acknowledged`, or `Resolved`. |
| `source` | VARCHAR(50) | NOT NULL, DEFAULT: 'System' | Origin subsystem that generated alert (e.g., `System`, `AI`, `Wearable`). |

---

### TABLE 21: USER NOTIFICATIONS (`notifications_notification`)

**Purpose:**  
Stores user-specific in-app notifications, system announcements, care-team alerts, and read/unread delivery statuses.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the notification. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the recipient User account. |
| `title` | VARCHAR(255) | NOT NULL | Brief headline or summary of the notification. |
| `message` | TEXT | NOT NULL | Full body text content of the notification. |
| `category` | VARCHAR(50) | NULL | Notification category (e.g., `ALERT`, `MESSAGE`, `SYSTEM`, `PRESCRIPTION`). |
| `target_id` | VARCHAR(100) | NULL | Identifier of the related entity (e.g., Conversation ID, Alert ID) for deep linking. |
| `is_read` | BOOLEAN | NOT NULL, DEFAULT: False | Read status flag (False = unread, True = read). |
| `timestamp` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when notification was generated. |

---

## E. CARE-TEAM COMMUNICATION TABLES

### TABLE 22: CARE-TEAM CHAT CONVERSATIONS (`chat_conversation`)

**Purpose:**  
Maintains dedicated care-team communication channels scoped to individual patients, supporting real-time messaging between doctors, caregivers, family members, and patients.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the conversation channel. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key linking conversation thread to the central patient. |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT: 'ACTIVE' | Status of conversation thread: `ACTIVE` or `ARCHIVED`. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the conversation channel was initiated. |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when conversation was last active (ordered newest first). |

---

### TABLE 23: CONVERSATION PARTICIPANTS (`chat_conversationparticipant`)

**Purpose:**  
Represents multi-party membership and role participation in a patient's care-team conversation channel.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the membership record. |
| `conversation_id` | BIGINT | FK → `chat_conversation.id`, NOT NULL | Foreign key referencing the conversation channel. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the participant User account. |
| `role` | VARCHAR(20) | NOT NULL | Participant role in chat: `patient`, `doctor`, `caregiver`, `family`, or `admin`. |
| `joined_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the user joined the conversation. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT: True | Membership active status flag. |

*Unique Constraint:* Composite unique constraint on `(conversation_id, user_id)`.

---

### TABLE 24: CARE-TEAM CHAT MESSAGES (`chat_message`)

**Purpose:**  
Stores individual messages, media attachments, delivery states, read receipts, and clinical emergency priorities within a care-team chat conversation.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the chat message. |
| `conversation_id` | BIGINT | FK → `chat_conversation.id`, NOT NULL | Foreign key referencing the parent conversation thread. |
| `sender_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the User account who authored message. |
| `message_type` | VARCHAR(20) | NOT NULL, DEFAULT: 'TEXT' | Message payload format: `TEXT`, `IMAGE`, `DOCUMENT`, or `VIDEO`. |
| `content` | TEXT | NOT NULL, DEFAULT: '' | Text content or caption of the message. |
| `attachment` | VARCHAR(100) | NULL | Server storage path for uploaded media (`private_chat_attachments/<uuid>.<ext>`). |
| `attachment_original_name` | VARCHAR(255) | NOT NULL, DEFAULT: '' | Original filename of the uploaded attachment at time of upload. |
| `attachment_mime_type` | VARCHAR(100) | NOT NULL, DEFAULT: '' | MIME type of the uploaded file (e.g., `image/jpeg`, `application/pdf`). |
| `attachment_size` | INTEGER | NULL | File size of attachment in bytes. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the message was sent (ordered chronologically). |
| `delivered_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when message was delivered to recipient devices. |
| `read_at` | TIMESTAMP WITH TIME ZONE | NULL | Timestamp when message was marked as read by participants. |
| `priority` | VARCHAR(20) | NOT NULL, DEFAULT: 'NORMAL' | Priority level: `NORMAL`, `URGENT`, or `EMERGENCY`. |
| `is_emergency` | BOOLEAN | NOT NULL, DEFAULT: False | Emergency flag triggering elevated audio/visual notifications across the care team. |

---

## F. AI / CLINICAL SUPPORT TABLES

### TABLE 25: MEDICATION KNOWLEDGE BASE (`ai_services_medicationknowledgebase`)

**Purpose:**  
Maintains persistent pharmacological reference records, drug classes, contraindications, precautions, allergy warnings, and regulatory formulary references for AI-driven safety validation and clinical query answering.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the medication knowledge entry. |
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

### TABLE 26: DOCTOR MEDICATION REVIEW REQUESTS (`ai_services_doctormedicationreviewrequest`)

**Purpose:**  
Stores AI-assisted medication safety inquiries initiated by patients/caregivers that require formal clinical review and human-in-the-loop sign-off by a qualified physician.

| Field Name | Data Type | Constraints | Description |
|------------|-----------|-------------|-------------|
| `id` | BIGINT | PK, Auto-generated | Unique primary key identifying the medication review request. |
| `patient_id` | VARCHAR(20) | FK → `patients_patient.id`, NOT NULL | Foreign key referencing the patient associated with inquiry. |
| `user_id` | BIGINT | FK → `accounts_customuser.id`, NOT NULL | Foreign key referencing the user who submitted question. |
| `doctor_id` | BIGINT | FK → `accounts_customuser.id`, NULL | Foreign key referencing the doctor assigned to review inquiry. |
| `medication_name` | VARCHAR(150) | NOT NULL | Name of the pharmaceutical product under query. |
| `question` | TEXT | NOT NULL | Patient or caregiver question regarding dosage, interactions, or adverse effects. |
| `safety_status` | VARCHAR(50) | NOT NULL, DEFAULT: 'REVIEW_RECOMMENDED' | Initial AI-determined safety assessment score/label. |
| `status` | VARCHAR(30) | NOT NULL, DEFAULT: 'PENDING' | Workflow review status: `PENDING`, `REVIEWED`, or `DECLINED`. |
| `doctor_response` | TEXT | NOT NULL, DEFAULT: '' | Formal clinical advice and response provided by the reviewing physician. |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, Auto-generated | Timestamp when the review request was created. |

---

## G. SUPPORTING DOCTOR VERIFICATION REFERENCE DATA

*Note: The following tables represent external regulatory registry datasets and hospital affiliation benchmarks used strictly for credential cross-verification and institutional vetting. They are distinct from operational user accounts.*

- **`doctors_referencedoctorregistry` (Reference Doctor Registry):** Official medical council gazette dataset containing regulatory registration numbers, council names, qualifications, and registration dates used as external benchmarks during doctor onboarding verification.
- **`doctors_healthfacility` (Health Facilities):** Registered hospitals, clinics, and academic medical institutions with regulatory license identifiers and location metadata.
- **`doctors_doctordisciplinaryrecord` (Doctor Disciplinary Records):** Statutory disciplinary orders, suspensions, and sanctions published by state medical councils to identify flagged practitioners.
- **`doctors_referencedoctoraffiliation` (Reference Doctor Affiliations):** External institutional clinical appointment records linking reference registry doctors to verified health facilities.
- **`doctors_doctorfacilityaffiliation` (Doctor Facility Affiliations):** Operational hospital practice postings logged by registered doctors on the platform.

---

## DATABASE RELATIONSHIP SUMMARY

The core entity relationships governing the NeuroCare Nexus database schema are summarized below:

```
[User & Authentication]
CustomUser (1) ─────────── (0..1) DoctorProfile
CustomUser (1) ─────────── (0..1) CaregiverProfile
CustomUser (1) ─────────── (0..*) VerificationRecord
CustomUser (1) ─────────── (0..*) Notification

[Multi-Party Care Team Links]
CustomUser (Doctor) (1..*) ── (0..*) Patient   [through DoctorPatientLink]
CustomUser (Caregiver) (1..*) (0..*) Patient   [through CaregiverPatientLink]
CustomUser (Family) (1..*) ── (0..*) Patient   [through FamilyPatientLink]

[Patient & Clinical Records]
Patient (1) ────────────── (0..*) PatientCondition
Patient (1) ────────────── (0..*) PatientAllergy
Patient (1) ────────────── (0..*) PatientMedication
Patient (1) ────────────── (0..*) Prescription
Patient (1) ────────────── (0..*) MedicalRecord
Patient (1) ────────────── (0..*) PatientConsultation
Patient (1) ────────────── (0..*) MedicalDocument
PatientConsultation (1) ── (0..*) MedicalDocument

[IoT & Physiological Monitoring]
Patient (1) ────────────── (0..1) WearableDevice  [through DeviceAssignment]
Patient (1) ────────────── (0..*) SensorReading   [High-frequency ESP32 Telemetry]
Patient (1) ────────────── (0..*) VitalMeasurement [Episodic Clinical/Manual Vitals]
Patient (1) ────────────── (0..*) Alert

[Care-Team Chat & AI Services]
Patient (1) ────────────── (0..*) Conversation
Conversation (1) ───────── (1..*) ConversationParticipant
CustomUser (1) ─────────── (0..*) ConversationParticipant
Conversation (1) ───────── (0..*) Message
CustomUser (1) ─────────── (0..*) Message
Patient (1) ────────────── (0..*) DoctorMedicationReviewRequest
CustomUser (1) ─────────── (0..*) DoctorMedicationReviewRequest
```

---

## CONCEPTUAL SEPARATION SUMMARY

1. **`DoctorProfile` vs `ReferenceDoctorRegistry`:**  
   `DoctorProfile` represents an active, authenticated doctor registered on NeuroCare Nexus. `ReferenceDoctorRegistry` is a read-only regulatory council reference dataset used solely to cross-verify professional licenses.

2. **`VitalMeasurement` vs `SensorReading`:**  
   `SensorReading` captures high-frequency automated IoT sensor telemetry from the ESP32 wearable (heart rate, SpO2, skin temperature, 6-axis IMU acceleration/gyroscope). `VitalMeasurement` captures episodic, clinical bedside measurements (blood pressure, blood glucose, weight, respiratory rate) with explicit `source` provenance tracking (`MANUAL` entry with `entered_by` vs `DEVICE`).

3. **`Alert` vs `Notification`:**  
   `Alert` represents patient-specific clinical emergencies, threshold violations, or fall detections displayed on monitoring consoles. `Notification` represents individual user-targeted in-app inbox messages (e.g., chat notifications, document uploads, connection approvals).
