# NeuroCare Nexus — Reference Dataset Data Dictionary

> **DISCLAIMER:** All data described here is entirely synthetic. No fields contain real patient, doctor, or facility information.

---

## Table of Contents

1. [reference_doctors.csv](#1-reference_doctorscsv)
2. [reference_facilities.csv](#2-reference_facilitiescsv)
3. [doctor_facility_affiliations.csv](#3-doctor_facility_affiliationscsv)
4. [disciplinary_records.csv](#4-disciplinary_recordscsv)
5. [verification_test_cases.csv](#5-verification_test_casescsv)

---

## 1. reference_doctors.csv

**Purpose:** Core synthetic professional registration reference registry. Analogous to the NMC Indian Medical Register (IMR) structure — schema only, individual records are fictional.

| Field | Type | Nullable | Description | Example | Source/Meaning |
|---|---|---|---|---|---|
| `reference_id` | string | No | Unique synthetic reference identifier | `REF-KER-000001` | System-generated: `REF-{STATE_CODE}-{SEQ}` |
| `registration_number` | string | No | Unique synthetic medical registration number | `SYN-KER-MED-000001` | System-generated: `SYN-{STATE_CODE}-MED-{SEQ}`. Never a real MRN. |
| `doctor_name` | string | No | Synthetic full name of the doctor | `Ananya Menon` | Generated from synthetic Indian name pool |
| `normalized_name` | string | No | Title-stripped, whitespace-normalized, uppercase name | `ANANYA MENON` | Output of `normalize_name()` function |
| `state_medical_council` | string | No | Name of the state medical council under which registration is recorded | `Kerala Medical Council` | Controlled vocabulary; real council names used as structural reference |
| `registration_year` | integer | No | Year of initial registration | `2012` | Synthetic; range 1985–2023 |
| `registration_date` | date (YYYY-MM-DD) | No | Full date of registration | `2012-04-15` | Synthetic date within registration_year |
| `qualification` | string | No | Medical qualification(s) | `MBBS, MD` | Controlled vocabulary: MBBS, MBBS MD, MBBS MS, MBBS DNB, MBBS MD DM, MBBS MS MCh |
| `specialization` | string | No | Primary medical specialization | `Neurology` | Controlled vocabulary (23 specializations) |
| `registration_status` | string | No | Current registration status | `ACTIVE` | Enum: ACTIVE, INACTIVE, RETIRED |
| `source_type` | string | No | Identifies this as synthetic data | `SYNTHETIC_REFERENCE` | Always `SYNTHETIC_REFERENCE` for this dataset |
| `source_reference` | string | No | Structural schema reference | `NMC_IMR_STRUCTURE_REFERENCE` | Schema inspired by NMC IMR; records are fictional |
| `source_year` | integer | No | Year this synthetic record was generated | `2024` | Fixed at generation time |

**NOT included (by design):**
- `hospital`, `clinic`, `facility`, `consulting_hospital`, `workplace` — These belong in `doctor_facility_affiliations.csv`

---

## 2. reference_facilities.csv

**Purpose:** Synthetic healthcare facility directory. Analogous to ABDM Health Facility Registry (HFR) — schema only, individual facilities are fictional.

| Field | Type | Nullable | Description | Example | Source/Meaning |
|---|---|---|---|---|---|
| `facility_id` | string | No | Unique synthetic facility identifier | `FAC-KER-0001` | System-generated: `FAC-{STATE_CODE}-{SEQ}` |
| `facility_name` | string | No | Fictional name of the healthcare facility | `NeuroCare Reference Medical Centre 0001` | Must NOT use names of real hospitals |
| `facility_type` | string | No | Category of facility | `PRIVATE_HOSPITAL` | Enum: PRIVATE_HOSPITAL, GOVERNMENT_HOSPITAL, MEDICAL_COLLEGE_HOSPITAL, SPECIALTY_HOSPITAL, CLINIC, HEALTHCARE_CENTRE |
| `city` | string | No | City where facility is located | `Kochi` | Synthetic assignment from realistic Indian city list |
| `district` | string | No | District where facility is located | `Kochi` | Simplified: district = city for synthetic data |
| `state` | string | No | State where facility is located | `Kerala` | Indian state name |
| `facility_identifier` | string | No | Unique synthetic facility registration identifier | `SYN-FAC-KER-0001` | Clearly synthetic; not a real ABDM HFR ID |
| `verification_status` | string | No | Whether facility has been verified | `VERIFIED` | Enum: PENDING, VERIFIED |
| `source_type` | string | No | Identifies this as synthetic data | `SYNTHETIC_REFERENCE` | Always `SYNTHETIC_REFERENCE` |

---

## 3. doctor_facility_affiliations.csv

**Purpose:** Synthetic doctor-facility employment/affiliation relationships. Analogous to ABDM HPR self-reported affiliation declarations. A doctor may have 0–3 affiliations.

| Field | Type | Nullable | Description | Example | Source/Meaning |
|---|---|---|---|---|---|
| `affiliation_id` | string | No | Unique synthetic affiliation identifier | `AFF-000001` | System-generated sequential |
| `reference_doctor_id` | string | No | Foreign key to `reference_doctors.reference_id` | `REF-KER-000001` | References `reference_doctors.csv` |
| `facility_id` | string | No | Foreign key to `reference_facilities.facility_id` | `FAC-KER-0001` | References `reference_facilities.csv` |
| `department` | string | No | Clinical department within the facility | `Department of Neurology` | Controlled vocabulary (20 departments) |
| `designation` | string | No | Job title/role at the facility | `Senior Consultant` | Controlled vocabulary (10 designations) |
| `employment_type` | string | No | Nature of engagement | `FULL_TIME` | Enum: FULL_TIME, PART_TIME, VISITING_CONSULTANT, CONSULTANT, RESIDENT |
| `status` | string | No | Whether affiliation is current or ended | `CURRENT` | Enum: CURRENT, ENDED |
| `start_date` | date (YYYY-MM-DD) | No | Date affiliation commenced | `2015-06-01` | Synthetic; range 2000–2022 |
| `end_date` | date (YYYY-MM-DD) | Yes | Date affiliation ended (null if CURRENT) | `2020-12-31` | Synthetic; must be after start_date |
| `verification_status` | string | No | Admin verification state | `VERIFIED` | Enum: PENDING, VERIFIED |
| `source_type` | string | No | Identifies this as synthetic data | `SYNTHETIC_REFERENCE` | Always `SYNTHETIC_REFERENCE` |

**Important:** This table does NOT prove where a doctor currently practices. It is synthetic test data only.

---

## 4. disciplinary_records.csv

**Purpose:** Synthetic disciplinary action records. Analogous to NMC Blacklist structure — schema only. Individual records are entirely fictional and do not represent real disciplinary proceedings against any person.

| Field | Type | Nullable | Description | Example | Source/Meaning |
|---|---|---|---|---|---|
| `disciplinary_id` | string | No | Unique synthetic disciplinary record identifier | `DISC-0001` | System-generated sequential |
| `registration_number` | string | No | Foreign key to `reference_doctors.registration_number` | `SYN-KER-MED-000042` | Must reference an existing doctor in reference_doctors.csv |
| `doctor_name` | string | No | Synthetic name of doctor (denormalized for audit clarity) | `Ananya Menon` | Copied from reference_doctors for readability |
| `state_medical_council` | string | No | Council that issued the disciplinary action | `Kerala Medical Council` | Copied from reference_doctors |
| `action_type` | string | No | Type of disciplinary action | `SUSPENSION` | Enum: SUSPENSION, BLACKLIST, RESTORATION, REMOVAL |
| `status` | string | No | Current status of the disciplinary record | `ACTIVE` | Enum: ACTIVE, BLACKLISTED, REMOVED, RESTORED |
| `suspended_date` | date (YYYY-MM-DD) | No | Date disciplinary action was issued | `2018-03-15` | Synthetic date |
| `restored_date` | date (YYYY-MM-DD) | Yes | Date of restoration (only for RESTORATION records) | `2019-06-01` | Synthetic; must be after suspended_date |
| `source_type` | string | No | Identifies this as synthetic test data | `SYNTHETIC_TEST_REFERENCE` | Always `SYNTHETIC_TEST_REFERENCE` — distinct from SYNTHETIC_REFERENCE |
| `source_reference` | string | No | Structural schema reference | `NMC_BLACKLIST_STRUCTURE_REFERENCE` | Schema inspired by NMC Blacklist; records are fictional |
| `remarks` | string | No | Mandatory disclaimer text | `Synthetic test record; not a real disciplinary record.` | **Must always contain this disclaimer** |

**Action type distribution:**
| Action | Count |
|---|---|
| SUSPENSION | 100 |
| BLACKLIST | 20 |
| RESTORATION | 20 |
| REMOVAL | 10 |

---

## 5. verification_test_cases.csv

**Purpose:** Controlled test scenarios for automated testing of the NeuroCare Nexus verification engine. Each test case defines input values and the expected engine output.

| Field | Type | Nullable | Description | Example | Source/Meaning |
|---|---|---|---|---|---|
| `test_case_id` | string | No | Unique test case identifier | `TC-0001` | System-generated sequential |
| `case_type` | string | No | Classification of the test scenario | `EXACT_MATCH` | See case type table below |
| `registration_number` | string | Yes | Input registration number to submit | `SYN-KER-MED-000001` | May be empty for MISSING_REGISTRATION cases |
| `submitted_name` | string | No | Doctor name as submitted by the applicant | `Ananya Menon` | May include titles or case variations |
| `submitted_council` | string | Yes | Council name as submitted | `Kerala Medical Council` | May be empty for MISSING_COUNCIL cases |
| `expected_result` | string | No | Expected output of the verification engine | `EXACT_MATCH` | See expected result table below |
| `notes` | string | No | Human-readable description of the test scenario | `Exact registration number and name submitted.` | Test documentation |

**Case Types:**

| case_type | Count | Description |
|---|---|---|
| `EXACT_MATCH` | 30 | Correct reg number, name, and council |
| `NAME_VARIATION` | 20 | Correct reg number, name in uppercase without title |
| `WRONG_NAME` | 10 | Correct reg number, but wrong name |
| `REGISTRATION_NOT_FOUND` | 10 | Non-existent registration number |
| `WRONG_COUNCIL` | 10 | Correct reg number and name but wrong council |
| `MISSING_REGISTRATION` | 10 | Empty registration number |
| `MISSING_COUNCIL` | 10 | Empty council field |
| `DISCIPLINARY_STATUS` | 10 | Doctor has active disciplinary record |
| `DUPLICATE_REFERENCE` | 5 | Same reg number submitted twice |
| `QUALIFICATION_MISMATCH` | 5 | Correct identity but wrong qualification |
| `STANDARD_LOOKUP` | 10 | Normal full verification scenario |

**Expected Results:**

| expected_result | Meaning |
|---|---|
| `EXACT_MATCH` | Registration number, name, and council all match exactly |
| `LIKELY_MATCH` | Registration number matches, name is a close variation |
| `MISMATCH` | Registration found but name/council does not match |
| `NOT_FOUND` | Registration number does not exist in registry |
| `STATUS_BLOCKED` | Doctor has active disciplinary record — block access |
| `INVALID` | Required field is empty or malformed |
| `MANUAL_REVIEW` | Ambiguous result — requires admin human review |
| `DATA_ERROR` | Input data is internally inconsistent |

---

## Enum Value Reference

### registration_status
`ACTIVE` | `INACTIVE` | `RETIRED`

### facility_type
`PRIVATE_HOSPITAL` | `GOVERNMENT_HOSPITAL` | `MEDICAL_COLLEGE_HOSPITAL` | `SPECIALTY_HOSPITAL` | `CLINIC` | `HEALTHCARE_CENTRE`

### employment_type
`FULL_TIME` | `PART_TIME` | `VISITING_CONSULTANT` | `CONSULTANT` | `RESIDENT`

### affiliation status
`CURRENT` | `ENDED`

### disciplinary action_type
`SUSPENSION` | `BLACKLIST` | `RESTORATION` | `REMOVAL`

### disciplinary status
`ACTIVE` | `BLACKLISTED` | `REMOVED` | `RESTORED`

### source_type (core records)
`SYNTHETIC_REFERENCE`

### source_type (disciplinary records)
`SYNTHETIC_TEST_REFERENCE`

---

*NeuroCare Nexus Academic Team — Data Dictionary v1.0.0*
