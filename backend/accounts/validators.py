import re
from datetime import datetime, date
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_and_normalize_phone(phone_str, required=True):
    """
    Validates and normalizes Indian mobile phone numbers.
    Accepts 10-digit mobile numbers starting with 6, 7, 8, 9.
    Allows prefixes like +91, 91, 0, spaces, hyphens, parentheses.
    Rejects strings with arbitrary letters, symbols, invalid lengths, or invalid starting digits.
    Returns: (is_valid: bool, normalized_phone: str or None, error_message: str or None)
    """
    if phone_str is None or not str(phone_str).strip():
        if required:
            return False, None, "Phone number is required."
        return True, "", None

    raw = str(phone_str).strip()

    # Reject any letters or arbitrary symbols (only digits, +, -, spaces, parentheses allowed)
    if re.search(r'[^\d\+\-\s\(\)]', raw):
        return False, None, "Phone number can only contain digits and country code (+91)."

    # Extract all digits
    digits = re.sub(r'\D', '', raw)

    if raw.startswith('+91'):
        if len(digits) == 12 and digits.startswith('91'):
            local_num = digits[2:]
        else:
            return False, None, "Enter a valid 10-digit Indian mobile number."
    elif digits.startswith('91') and len(digits) == 12:
        local_num = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        local_num = digits[1:]
    elif len(digits) == 10:
        local_num = digits
    else:
        return False, None, "Enter a valid 10-digit Indian mobile number."

    # Indian mobile numbers must start with 6, 7, 8, or 9
    if not re.match(r'^[6-9]\d{9}$', local_num):
        return False, None, "Indian mobile numbers must start with 6, 7, 8, or 9 (e.g. +91 9876543210)."

    normalized = f"+91{local_num}"
    return True, normalized, None


def validate_and_normalize_email(email_str):
    """
    Validates and trims email address using standard Django email validation.
    Returns: (is_valid: bool, normalized_email: str or None, error_message: str or None)
    """
    if not email_str or not str(email_str).strip():
        return False, None, "Email address is required."

    cleaned = str(email_str).strip().lower()

    # Basic RFC structure checks to reject obvious malformed strings before validator
    if '@' not in cleaned or cleaned.startswith('@') or cleaned.endswith('@'):
        return False, None, "Enter a valid email address."

    parts = cleaned.split('@')
    if len(parts) != 2 or not parts[0] or not parts[1] or '.' not in parts[1] or parts[1].endswith('.'):
        return False, None, "Enter a valid email address."

    try:
        django_validate_email(cleaned)
    except ValidationError:
        return False, None, "Enter a valid email address."

    return True, cleaned, None


def validate_human_name(name_str, field_name="Full name"):
    """
    Validates that a human name contains legitimate characters, not only digits or symbols.
    Allows spaces, hyphens, apostrophes, periods, and initials.
    Returns: (is_valid: bool, cleaned_name: str or None, error_message: str or None)
    """
    if not name_str or not str(name_str).strip():
        return False, None, f"{field_name} is required."

    cleaned = " ".join(str(name_str).strip().split())

    # Must be between 2 and 100 characters
    if len(cleaned) < 2 or len(cleaned) > 100:
        return False, None, f"{field_name} must be between 2 and 100 characters."

    # Must contain at least 2 letters
    if len(re.findall(r'[a-zA-Z]', cleaned)) < 2:
        return False, None, f"Enter a valid {field_name.lower()}."

    # Must not contain invalid characters (only letters, spaces, hyphens, apostrophes, dots)
    if not re.match(r"^[a-zA-Z\s\.\'\-]+$", cleaned):
        return False, None, f"Enter a valid {field_name.lower()}."

    return True, cleaned, None


def validate_password_strength(password, password_confirm=None):
    """
    Validates password length and match.
    Returns: (is_valid: bool, error_message: str or None)
    """
    if not password or not str(password).strip():
        return False, "Password is required."

    p_str = str(password)
    if len(p_str) < 8:
        return False, "Password must be at least 8 characters long."

    if password_confirm is not None and p_str != str(password_confirm):
        return False, "Passwords do not match."

    return True, None


def validate_date_of_birth(dob_val):
    """
    Validates date of birth is not in the future and is properly formatted.
    Returns: (is_valid: bool, date_obj: date or None, error_message: str or None)
    """
    if not dob_val:
        return True, None, None

    if isinstance(dob_val, (datetime, date)):
        d = dob_val.date() if isinstance(dob_val, datetime) else dob_val
    else:
        try:
            d = datetime.strptime(str(dob_val).strip()[:10], '%Y-%m-%d').date()
        except ValueError:
            return False, None, "Invalid date format. Use YYYY-MM-DD."

    today = timezone.now().date()
    if d > today:
        return False, None, "Date of birth cannot be in the future."

    return True, d, None


def calculate_age_from_dob(dob_date):
    """Calculates age in whole years from date of birth."""
    if not dob_date:
        return 35
    today = timezone.now().date()
    return today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
