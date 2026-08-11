"""
NeuroCare Nexus — Synthetic Reference Data Validator
=====================================================

PURPOSE:
    Validates the integrity of all generated reference CSV files.
    Fails loudly (non-zero exit code) if any check fails.

CHECKS:
    1.  Exact record counts
    2.  Duplicate primary identifiers
    3.  Duplicate synthetic registration numbers
    4.  Missing mandatory fields
    5.  Invalid date formats and date logic (end_date before start_date)
    6.  Invalid enum values
    7.  Foreign-key integrity (affiliations → doctors, affiliations → facilities)
    8.  Disciplinary records referencing nonexistent doctors
    9.  Affiliation counts within 8,000–10,000 range

USAGE:
    python validate_reference_data.py

Returns exit code 0 on full pass, 1 on any failure.

Author: NeuroCare Nexus Academic Team
"""

import csv
import os
import sys
from datetime import date, datetime
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'reference_data')

# ─────────────────────────────────────────────────────────────
# EXPECTED CONSTRAINTS
# ─────────────────────────────────────────────────────────────

EXPECTED_DOCTOR_COUNT = 5000
EXPECTED_FACILITY_COUNT = 500
EXPECTED_AFFILIATION_MIN = 8000
EXPECTED_AFFILIATION_MAX = 10000
EXPECTED_DISCIPLINARY_COUNT = 150
EXPECTED_TEST_CASE_COUNT = 130

VALID_REGISTRATION_STATUS = {'ACTIVE', 'INACTIVE', 'RETIRED'}
VALID_FACILITY_TYPES = {
    'PRIVATE_HOSPITAL', 'GOVERNMENT_HOSPITAL', 'MEDICAL_COLLEGE_HOSPITAL',
    'SPECIALTY_HOSPITAL', 'CLINIC', 'HEALTHCARE_CENTRE',
}
VALID_EMPLOYMENT_TYPES = {
    'FULL_TIME', 'PART_TIME', 'VISITING_CONSULTANT', 'CONSULTANT', 'RESIDENT',
}
VALID_AFF_STATUS = {'CURRENT', 'ENDED'}
VALID_DISC_ACTIONS = {'SUSPENSION', 'BLACKLIST', 'RESTORATION', 'REMOVAL'}
VALID_DISC_STATUS = {'ACTIVE', 'BLACKLISTED', 'REMOVED', 'RESTORED'}
VALID_TEST_CASE_TYPES = {
    'EXACT_MATCH', 'NAME_VARIATION', 'WRONG_NAME', 'REGISTRATION_NOT_FOUND',
    'WRONG_COUNCIL', 'MISSING_REGISTRATION', 'MISSING_COUNCIL',
    'DISCIPLINARY_STATUS', 'DUPLICATE_REFERENCE', 'QUALIFICATION_MISMATCH',
    'STANDARD_LOOKUP',
}
VALID_EXPECTED_RESULTS = {
    'EXACT_MATCH', 'LIKELY_MATCH', 'MISMATCH', 'NOT_FOUND',
    'STATUS_BLOCKED', 'INVALID', 'MANUAL_REVIEW', 'DATA_ERROR',
}

errors = []
warnings = []


def err(msg):
    errors.append(f"  ✗ ERROR: {msg}")


def warn(msg):
    warnings.append(f"  ⚠ WARNING: {msg}")


def ok(msg):
    print(f"  ✓ {msg}")


# ─────────────────────────────────────────────────────────────
# CSV LOADER
# ─────────────────────────────────────────────────────────────

def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        err(f"File not found: {path}")
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────────────────────
# DATE VALIDATOR
# ─────────────────────────────────────────────────────────────

def parse_date(val, field, row_id):
    if not val:
        return None
    try:
        return datetime.strptime(val, '%Y-%m-%d').date()
    except ValueError:
        err(f"Row {row_id}: Invalid date format in '{field}': {val!r}")
        return None


# ─────────────────────────────────────────────────────────────
# 1. VALIDATE REFERENCE DOCTORS
# ─────────────────────────────────────────────────────────────

def validate_doctors():
    print("\n[1] Validating reference_doctors.csv ...")
    rows = load_csv('reference_doctors.csv')
    if not rows:
        err("reference_doctors.csv is empty or missing.")
        return set(), set()

    # Count
    if len(rows) != EXPECTED_DOCTOR_COUNT:
        err(f"Expected {EXPECTED_DOCTOR_COUNT} doctors, got {len(rows)}.")
    else:
        ok(f"Record count: {len(rows)} (correct)")

    # Duplicate reference_ids
    ref_ids = [r['reference_id'] for r in rows]
    dup_ids = [v for v, c in Counter(ref_ids).items() if c > 1]
    if dup_ids:
        err(f"Duplicate reference_ids found: {dup_ids[:5]} ...")
    else:
        ok("No duplicate reference_ids.")

    # Duplicate registration_numbers
    reg_nums = [r['registration_number'] for r in rows]
    dup_regs = [v for v, c in Counter(reg_nums).items() if c > 1]
    if dup_regs:
        err(f"Duplicate registration_numbers: {dup_regs[:5]} ...")
    else:
        ok("No duplicate registration_numbers.")

    # Mandatory field checks
    mandatory = ['reference_id', 'registration_number', 'doctor_name',
                 'normalized_name', 'state_medical_council',
                 'registration_year', 'qualification', 'specialization']
    missing_count = 0
    for r in rows:
        for field in mandatory:
            if not r.get(field, '').strip():
                missing_count += 1
                err(f"Missing mandatory field '{field}' in row: {r.get('reference_id', '?')}")
                if missing_count > 10:
                    err("... (more missing field errors suppressed)")
                    break
        if missing_count > 10:
            break
    if missing_count == 0:
        ok("All mandatory fields present.")

    # Enum: registration_status
    invalid_status = [r['reference_id'] for r in rows
                      if r.get('registration_status') not in VALID_REGISTRATION_STATUS]
    if invalid_status:
        err(f"Invalid registration_status in rows: {invalid_status[:5]}")
    else:
        ok("All registration_status values valid.")

    # Synthetic ID format check
    invalid_format = [r['registration_number'] for r in rows
                      if not r['registration_number'].startswith('SYN-')]
    if invalid_format:
        err(f"Non-synthetic registration numbers found: {invalid_format[:5]}")
    else:
        ok("All registration numbers use SYN- prefix.")

    # Source type check
    wrong_source = [r['reference_id'] for r in rows
                    if r.get('source_type') != 'SYNTHETIC_REFERENCE']
    if wrong_source:
        err(f"Incorrect source_type in {len(wrong_source)} rows.")
    else:
        ok("All source_type values = SYNTHETIC_REFERENCE.")

    return set(ref_ids), set(reg_nums)


# ─────────────────────────────────────────────────────────────
# 2. VALIDATE REFERENCE FACILITIES
# ─────────────────────────────────────────────────────────────

def validate_facilities():
    print("\n[2] Validating reference_facilities.csv ...")
    rows = load_csv('reference_facilities.csv')
    if not rows:
        err("reference_facilities.csv is empty or missing.")
        return set()

    if len(rows) != EXPECTED_FACILITY_COUNT:
        err(f"Expected {EXPECTED_FACILITY_COUNT} facilities, got {len(rows)}.")
    else:
        ok(f"Record count: {len(rows)} (correct)")

    fac_ids = [r['facility_id'] for r in rows]
    dup_fac = [v for v, c in Counter(fac_ids).items() if c > 1]
    if dup_fac:
        err(f"Duplicate facility_ids: {dup_fac[:5]}")
    else:
        ok("No duplicate facility_ids.")

    invalid_type = [r['facility_id'] for r in rows
                    if r.get('facility_type') not in VALID_FACILITY_TYPES]
    if invalid_type:
        err(f"Invalid facility_type in rows: {invalid_type[:5]}")
    else:
        ok("All facility_type values valid.")

    # Ensure names are synthetic
    forbidden = ['AIIMS', 'Apollo', 'Fortis', 'Manipal', 'Narayana']
    for r in rows:
        for keyword in forbidden:
            if keyword.lower() in r.get('facility_name', '').lower():
                warn(f"Facility name may reference real institution: {r['facility_name']}")

    mandatory = ['facility_id', 'facility_name', 'facility_type', 'city', 'state']
    for r in rows:
        for f in mandatory:
            if not r.get(f, '').strip():
                err(f"Missing '{f}' in facility {r.get('facility_id', '?')}")

    ok("Facility mandatory fields check done.")
    return set(fac_ids)


# ─────────────────────────────────────────────────────────────
# 3. VALIDATE AFFILIATIONS
# ─────────────────────────────────────────────────────────────

def validate_affiliations(valid_doctor_ref_ids, valid_facility_ids):
    print("\n[3] Validating doctor_facility_affiliations.csv ...")
    rows = load_csv('doctor_facility_affiliations.csv')
    if not rows:
        err("doctor_facility_affiliations.csv is empty or missing.")
        return

    count = len(rows)
    if not (EXPECTED_AFFILIATION_MIN <= count <= EXPECTED_AFFILIATION_MAX):
        err(f"Affiliation count {count} outside range [{EXPECTED_AFFILIATION_MIN}, {EXPECTED_AFFILIATION_MAX}].")
    else:
        ok(f"Record count: {count} (within required range {EXPECTED_AFFILIATION_MIN}–{EXPECTED_AFFILIATION_MAX})")

    aff_ids = [r['affiliation_id'] for r in rows]
    dup_aff = [v for v, c in Counter(aff_ids).items() if c > 1]
    if dup_aff:
        err(f"Duplicate affiliation_ids: {dup_aff[:5]}")
    else:
        ok("No duplicate affiliation_ids.")

    bad_doc_fk = [r['affiliation_id'] for r in rows
                  if r.get('reference_doctor_id') not in valid_doctor_ref_ids]
    if bad_doc_fk:
        err(f"Invalid reference_doctor_id FK in {len(bad_doc_fk)} affiliations (first 5: {bad_doc_fk[:5]})")
    else:
        ok("All reference_doctor_id foreign keys valid.")

    bad_fac_fk = [r['affiliation_id'] for r in rows
                  if r.get('facility_id') not in valid_facility_ids]
    if bad_fac_fk:
        err(f"Invalid facility_id FK in {len(bad_fac_fk)} affiliations (first 5: {bad_fac_fk[:5]})")
    else:
        ok("All facility_id foreign keys valid.")

    # Date logic
    date_errors = 0
    for r in rows:
        start = parse_date(r.get('start_date'), 'start_date', r['affiliation_id'])
        end_val = r.get('end_date', '').strip()
        if end_val:
            end = parse_date(end_val, 'end_date', r['affiliation_id'])
            if start and end and end < start:
                err(f"end_date before start_date in affiliation {r['affiliation_id']}")
                date_errors += 1
                if date_errors > 10:
                    break
    if date_errors == 0:
        ok("All affiliation date ranges valid.")

    invalid_emp = [r['affiliation_id'] for r in rows
                   if r.get('employment_type') not in VALID_EMPLOYMENT_TYPES]
    if invalid_emp:
        err(f"Invalid employment_type in {len(invalid_emp)} rows.")
    else:
        ok("All employment_type values valid.")

    invalid_status = [r['affiliation_id'] for r in rows
                      if r.get('status') not in VALID_AFF_STATUS]
    if invalid_status:
        err(f"Invalid affiliation status in {len(invalid_status)} rows.")
    else:
        ok("All affiliation status values valid.")


# ─────────────────────────────────────────────────────────────
# 4. VALIDATE DISCIPLINARY RECORDS
# ─────────────────────────────────────────────────────────────

def validate_disciplinary(valid_reg_numbers):
    print("\n[4] Validating disciplinary_records.csv ...")
    rows = load_csv('disciplinary_records.csv')
    if not rows:
        err("disciplinary_records.csv is empty or missing.")
        return

    if len(rows) != EXPECTED_DISCIPLINARY_COUNT:
        err(f"Expected {EXPECTED_DISCIPLINARY_COUNT} disciplinary records, got {len(rows)}.")
    else:
        ok(f"Record count: {len(rows)} (correct)")

    disc_ids = [r['disciplinary_id'] for r in rows]
    dup_disc = [v for v, c in Counter(disc_ids).items() if c > 1]
    if dup_disc:
        err(f"Duplicate disciplinary_ids: {dup_disc[:5]}")
    else:
        ok("No duplicate disciplinary_ids.")

    # Foreign key: registration_number must exist
    bad_fk = [r['disciplinary_id'] for r in rows
              if r.get('registration_number') not in valid_reg_numbers]
    if bad_fk:
        err(f"Disciplinary records referencing nonexistent doctors: {bad_fk[:5]}")
    else:
        ok("All disciplinary registration_number FKs valid.")

    invalid_action = [r['disciplinary_id'] for r in rows
                      if r.get('action_type') not in VALID_DISC_ACTIONS]
    if invalid_action:
        err(f"Invalid action_type: {invalid_action[:5]}")
    else:
        ok("All action_type values valid.")

    invalid_status = [r['disciplinary_id'] for r in rows
                      if r.get('status') not in VALID_DISC_STATUS]
    if invalid_status:
        err(f"Invalid disciplinary status: {invalid_status[:5]}")
    else:
        ok("All disciplinary status values valid.")

    # Mandatory synthetic disclaimer in remarks
    missing_remarks = [r['disciplinary_id'] for r in rows
                       if 'Synthetic test record' not in r.get('remarks', '')]
    if missing_remarks:
        err(f"Remarks field missing synthetic disclaimer in {len(missing_remarks)} records.")
    else:
        ok("All disciplinary remarks contain synthetic disclaimer.")

    wrong_source = [r['disciplinary_id'] for r in rows
                    if r.get('source_type') != 'SYNTHETIC_TEST_REFERENCE']
    if wrong_source:
        err(f"Incorrect source_type in {len(wrong_source)} disciplinary rows.")
    else:
        ok("All source_type = SYNTHETIC_TEST_REFERENCE.")

    # Action type distribution
    action_counts = Counter(r['action_type'] for r in rows)
    ok(f"Disciplinary action distribution: {dict(action_counts)}")


# ─────────────────────────────────────────────────────────────
# 5. VALIDATE VERIFICATION TEST CASES
# ─────────────────────────────────────────────────────────────

def validate_test_cases():
    print("\n[5] Validating verification_test_cases.csv ...")
    rows = load_csv('verification_test_cases.csv')
    if not rows:
        err("verification_test_cases.csv is empty or missing.")
        return

    if len(rows) != EXPECTED_TEST_CASE_COUNT:
        err(f"Expected {EXPECTED_TEST_CASE_COUNT} test cases, got {len(rows)}.")
    else:
        ok(f"Record count: {len(rows)} (correct)")

    tc_ids = [r['test_case_id'] for r in rows]
    dup_tc = [v for v, c in Counter(tc_ids).items() if c > 1]
    if dup_tc:
        err(f"Duplicate test_case_ids: {dup_tc[:5]}")
    else:
        ok("No duplicate test_case_ids.")

    invalid_types = [r['test_case_id'] for r in rows
                     if r.get('case_type') not in VALID_TEST_CASE_TYPES]
    if invalid_types:
        err(f"Invalid case_type in: {invalid_types[:5]}")
    else:
        ok("All case_type values valid.")

    invalid_results = [r['test_case_id'] for r in rows
                       if r.get('expected_result') not in VALID_EXPECTED_RESULTS]
    if invalid_results:
        err(f"Invalid expected_result in: {invalid_results[:5]}")
    else:
        ok("All expected_result values valid.")

    type_dist = Counter(r['case_type'] for r in rows)
    ok(f"Test case type distribution: {dict(type_dist)}")


# ─────────────────────────────────────────────────────────────
# SUMMARY JSON CHECK
# ─────────────────────────────────────────────────────────────

def validate_summary_json():
    print("\n[6] Validating reference_data_summary.json ...")
    path = os.path.join(DATA_DIR, 'reference_data_summary.json')
    if not os.path.exists(path):
        err("reference_data_summary.json not found.")
        return
    import json
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    counts = data.get('record_counts', {})
    if counts.get('reference_doctors') != EXPECTED_DOCTOR_COUNT:
        err(f"Summary JSON doctor count mismatch: {counts.get('reference_doctors')}")
    else:
        ok("Summary JSON doctor count matches.")
    if counts.get('reference_facilities') != EXPECTED_FACILITY_COUNT:
        err(f"Summary JSON facility count mismatch: {counts.get('reference_facilities')}")
    else:
        ok("Summary JSON facility count matches.")
    ok("Summary JSON loaded and checked.")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("NeuroCare Nexus — Reference Data Validator")
    print("=" * 60)

    valid_doctor_ref_ids, valid_reg_numbers = validate_doctors()
    valid_facility_ids = validate_facilities()
    validate_affiliations(valid_doctor_ref_ids, valid_facility_ids)
    validate_disciplinary(valid_reg_numbers)
    validate_test_cases()
    validate_summary_json()

    print("\n" + "=" * 60)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(w)

    if errors:
        print("\nVALIDATION FAILED:")
        for e in errors:
            print(e)
        print(f"\n{len(errors)} error(s) found. Fix them before importing into Django.")
        sys.exit(1)
    else:
        print("ALL VALIDATION CHECKS PASSED ✓")
        print("=" * 60)
        sys.exit(0)


if __name__ == '__main__':
    main()
