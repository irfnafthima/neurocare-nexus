import re
from datetime import datetime
from doctors.models import ReferenceDoctorRegistry, DoctorDisciplinaryRecord

def clean_name(name):
    """
    Normalizes doctor names by converting to lowercase, removing common titles/prefixes,
    and stripping extra whitespace.
    """
    if not name:
        return ""
    n = name.lower()
    n = re.sub(r'^(dr\.\s*|dr\s*|doctor\s*|md\s*|mbbs\s*)', '', n)
    n = re.sub(r'(\s*,\s*(md|mbbs|ms|dnb|phd|mch))', '', n)
    n = re.sub(r'[^a-z\s]', '', n)
    return " ".join(n.split())

def clean_qualification(qual):
    if not qual:
        return ""
    q = qual.lower()
    q = re.sub(r'[^a-z\s]', ' ', q)
    return " ".join(q.split())

def verify_doctor_credentials(registration_number, name, council, qualification=None, registration_year=None):
    """
    Executes the Indian Medical Verification Engine algorithm.
    Compares registration criteria against academic reference registries and disciplinary records.
    """
    remarks = []
    checks = {
        'registration_check': 'FAILED',
        'name_check': 'MISMATCH',
        'council_check': 'MISMATCH',
        'qualification_check': 'PENDING',
        'disciplinary_check': 'CLEAR'
    }

    if not registration_number or not str(registration_number).strip():
        return {
            'result': 'NOT_FOUND',
            'reference_record': None,
            'remarks': 'Registration number is missing or empty.',
            'checks': checks
        }

    try:
        ref = ReferenceDoctorRegistry.objects.get(registration_number=registration_number.strip())
        checks['registration_check'] = 'VERIFIED'
    except ReferenceDoctorRegistry.DoesNotExist:
        return {
            'result': 'NOT_FOUND',
            'reference_record': None,
            'remarks': 'Registration number not found in reference registries.',
            'checks': checks
        }

    # Disciplinary Check
    disc_records = DoctorDisciplinaryRecord.objects.filter(doctor=ref)
    active_disc = disc_records.filter(status__in=['ACTIVE', 'BLACKLISTED', 'REMOVED']).exclude(status='RESTORED').first()
    
    if active_disc:
        checks['disciplinary_check'] = 'BLOCKED'
        remarks.append(f"Disciplinary block active: Action '{active_disc.action_type}' ({active_disc.status}) recorded on {active_disc.suspended_date}.")
        return {
            'result': 'STATUS_BLOCKED',
            'reference_record': ref,
            'remarks': " | ".join(remarks),
            'checks': checks
        }
    elif disc_records.filter(status='RESTORED').exists():
        checks['disciplinary_check'] = 'RESTORED'
        remarks.append("Prior disciplinary record found but status is RESTORED.")

    # Compare Name
    sub_name_clean = clean_name(name)
    ref_name_clean = clean_name(ref.doctor_name)
    
    if sub_name_clean == ref_name_clean:
        name_match = 'EXACT'
        checks['name_check'] = 'VERIFIED'
    else:
        sub_tokens = set(sub_name_clean.split())
        ref_tokens = set(ref_name_clean.split())
        intersection = sub_tokens.intersection(ref_tokens)
        
        if len(intersection) >= min(len(sub_tokens), len(ref_tokens)) - 1 and len(intersection) > 0:
            name_match = 'LIKELY'
            checks['name_check'] = 'LIKELY'
            remarks.append(f"Name match likely: Matched partial tokens '{list(intersection)}' (Sub: '{name}', Ref: '{ref.doctor_name}').")
        else:
            name_match = 'MISMATCH'
            checks['name_check'] = 'MISMATCH'
            remarks.append(f"Name mismatch: Submitted '{name}', Registered '{ref.doctor_name}'.")

    # Compare Council
    sub_council_clean = council.strip().lower() if council else ""
    ref_council_clean = ref.council.strip().lower() if ref.council else ""
    if sub_council_clean and ref_council_clean and (sub_council_clean == ref_council_clean or ref_council_clean in sub_council_clean or sub_council_clean in ref_council_clean):
        checks['council_check'] = 'VERIFIED'
    else:
        checks['council_check'] = 'MISMATCH'
        remarks.append(f"Council mismatch: Submitted '{council}', Registered '{ref.council}'.")

    # Compare Qualification
    if qualification:
        sub_qual_clean = clean_qualification(qualification)
        ref_qual_clean = clean_qualification(ref.qualification)
        sub_tokens = set(sub_qual_clean.split())
        ref_tokens = set(ref_qual_clean.split())
        if sub_tokens and ref_tokens and len(sub_tokens.intersection(ref_tokens)) > 0:
            checks['qualification_check'] = 'VERIFIED'
        else:
            checks['qualification_check'] = 'MISMATCH'
            remarks.append(f"Qualification mismatch: Submitted '{qualification}', Registered '{ref.qualification}'.")
    else:
        checks['qualification_check'] = 'PENDING'

    # Determine Overall Result
    if checks['name_check'] == 'VERIFIED' and checks['council_check'] == 'VERIFIED':
        result = 'EXACT_MATCH'
        remarks.append("Exact match confirmed on name and medical registration credentials.")
    elif checks['name_check'] == 'LIKELY' and checks['council_check'] == 'VERIFIED':
        result = 'LIKELY_MATCH'
        remarks.append("Likely match confirmed with minor name variations.")
    elif checks['name_check'] == 'MISMATCH':
        result = 'MISMATCH'
        remarks.append("Verification rejected: Name mismatch against medical registration number.")
    else:
        result = 'MANUAL_REVIEW'
        remarks.append("Credential discrepancies detected. Scheduled for manual administrative review.")

    return {
        'result': result,
        'reference_record': ref,
        'remarks': " | ".join(remarks),
        'checks': checks
    }
