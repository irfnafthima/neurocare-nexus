# NeuroCare Nexus — Synthetic Reference Dataset

## Overview

This directory contains the synthetic professional healthcare reference dataset for the **NeuroCare Nexus** academic AI-IoT Remote Patient Monitoring prototype.

---

> [!IMPORTANT]
> **SYNTHETIC DATA DISCLAIMER**
>
> This dataset is **entirely fictional and synthetic**.  
> It does **not** represent real doctors, real medical registrations, real disciplinary actions, or real hospital affiliations.
>
> **"This dataset is synthetic and intended only for academic development, testing and demonstration. It does not establish the real-world registration, employment, practice status, disciplinary status or identity of any individual."**

---

## Purpose

The dataset provides a **reproducible, integrity-verified reference registry** used by the NeuroCare Nexus backend to:

1. **Validate doctor registrations** at sign-up using a name-normalization and fuzzy-matching engine
2. **Cross-reference facility affiliations** during admin-level clinician verification
3. **Detect disciplinary blocks** before approving doctor accounts
4. **Run automated verification engine tests** against known expected outcomes

---

## Dataset Files

| File | Records | Description |
|---|---|---|
| `reference_doctors.csv` | **5,000** | Core synthetic doctor registry |
| `reference_facilities.csv` | **500** | Synthetic healthcare facilities |
| `doctor_facility_affiliations.csv` | **8,000–10,000** | Synthetic doctor-facility relationships |
| `disciplinary_records.csv` | **150** | Synthetic disciplinary action records |
| `verification_test_cases.csv` | **130** | Controlled test scenarios for verification engine |
| `reference_data_summary.json` | — | Aggregated metadata and distribution statistics |

---

## Structural Reference

The **schema design** is inspired by publicly documented concepts from:

- **National Medical Commission (NMC) Indian Medical Register (IMR)**  
  https://www.nmc.org.in/information-desk/for-indian-medical-practitioner/mci-portal/
- **Ayushman Bharat Digital Mission (ABDM) Healthcare Professional Registry (HPR)**  
  https://hpr.abdm.gov.in/
- **Ayushman Bharat Digital Mission (ABDM) Health Facility Registry (HFR)**  
  https://facility.abdm.gov.in/

Individual records **do not come from these registries** and **must not be treated as authoritative data** from any official Indian medical body.

---

## Why Hospital Affiliations Are Separate

In the NMC/IMR model, the core doctor registry records **professional registration credentials only** — it does not list where a doctor currently practices.

Facility employment data is recorded separately in operational HR or ABDM HPR self-reported fields.

This architecture is reflected here:

- `reference_doctors.csv` — registration credentials only (no hospital fields)
- `reference_facilities.csv` — synthetic facility directory
- `doctor_facility_affiliations.csv` — synthetic linking table (analogous to ABDM HPR affiliation declarations)

This separation prevents the incorrect assumption that **registry presence = proof of current employment**.

---

## Why Disciplinary Data Is Separate

Disciplinary actions are published separately from registration records (analogous to the NMC Blacklist structure). They must be cross-referenced independently, not embedded into the registration status field.

The `disciplinary_records.csv` dataset simulates this separation for academic testing of:
- Suspension detection
- Blacklist lookup
- Restoration handling

Every disciplinary record carries `source_type = SYNTHETIC_TEST_REFERENCE` and a mandatory remarks field stating:

> "Synthetic test record; not a real disciplinary record."

---

## Synthetic Identifier Format

All registration numbers follow a clearly synthetic format:

```
SYN-{STATE_CODE}-MED-{SEQUENCE}

Examples:
  SYN-KER-MED-000001
  SYN-TN-MED-000042
  SYN-KA-MED-001250
```

All reference IDs follow:
```
REF-{STATE_CODE}-{SEQUENCE}

Examples:
  REF-KER-000001
  REF-TN-000042
```

These formats are deliberately different from any real NMC registration number formats.

---

## State Distribution (Synthetic)

| State | Synthetic Records |
|---|---|
| Tamil Nadu | 650 |
| Karnataka | 600 |
| Maharashtra | 600 |
| Kerala | 410 |
| Delhi | 350 |
| Telangana | 300 |
| Andhra Pradesh | 300 |
| West Bengal | 300 |
| Gujarat | 250 |
| Uttar Pradesh | 250 |
| Rajasthan | 200 |
| Punjab | 100 |
| Other states & Union Territories | 690 |
| **Total** | **5,000** |

> These distributions are **not statistics about real doctor populations**. They are synthetic values chosen for geographic diversity in testing.

---

## Limitations

1. **Not an authoritative registry** — cannot be used to verify real doctors
2. **No real identities** — all names are generated from synthetic name pools
3. **Simplified geographic data** — district fields use city names as proxies
4. **No real phone/email/address** — contact fields are not generated
5. **Registration years 1985–2023** — spans a reasonable synthetic career range
6. **Name normalization is approximate** — edge cases for multi-part names may need refinement

---

## Regeneration

To regenerate all datasets with a fixed reproducible seed:

```bash
cd backend/data_generation
python generate_reference_data.py
```

To validate after generation:

```bash
python validate_reference_data.py
```

To import into Django:

```bash
cd backend
python manage.py import_reference_data
```

---

## Django Integration

The reference data maps to these Django models:

| CSV File | Django Model | App |
|---|---|---|
| `reference_doctors.csv` | `ReferenceDoctorRegistry` | `doctors` |
| `reference_facilities.csv` | `HealthFacility` | `doctors` |
| `doctor_facility_affiliations.csv` | `DoctorFacilityAffiliation` *(reference variant)* | `doctors` |
| `disciplinary_records.csv` | *(new: `DoctorDisciplinaryRecord`)* | `doctors` |
| `verification_test_cases.csv` | *(used by test suite only)* | `doctors/tests` |

See the Django integration report (generated by `generate_reference_data.py`) for field-level mapping details.

---

## Author

NeuroCare Nexus Academic Team  
Generated: 2024 (reproducible, seed=42)
