import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
env_file = ROOT_DIR / '.env.selenium'
if env_file.exists():
    load_dotenv(env_file)

FRONTEND_URL = os.getenv('BASE_FRONTEND_URL', 'http://localhost:5173')
BACKEND_URL = os.getenv('BASE_BACKEND_URL', 'http://127.0.0.1:8000')

def get_required_env(var_name: str) -> str:
    val = os.getenv(var_name)
    if not val:
        raise RuntimeError(f"Missing required environment variable '{var_name}'. Please ensure it is set in .env.selenium or system environment.")
    return val

PATIENT_EMAIL = get_required_env('TEST_PATIENT_EMAIL')
PATIENT_PASSWORD = get_required_env('TEST_PATIENT_PASSWORD')
PATIENT_DEVICE_ID = os.getenv('TEST_PATIENT_DEVICE_ID', 'NP-777')
PATIENT_ID = os.getenv('TEST_PATIENT_ID', 'P-777')

DOCTOR_EMAIL = get_required_env('TEST_DOCTOR_EMAIL')
DOCTOR_PASSWORD = get_required_env('TEST_DOCTOR_PASSWORD')
DOCTOR_NPI = os.getenv('TEST_DOCTOR_NPI', 'SYN-KER-MED-000001')

PENDING_DOCTOR_EMAIL = os.getenv('TEST_PENDING_DOCTOR_EMAIL', 'selenium_pending_doctor@nexus.test')
PENDING_DOCTOR_PASSWORD = os.getenv('TEST_PENDING_DOCTOR_PASSWORD', 'SeleniumPendingDocPass123!')
PENDING_DOCTOR_NPI = os.getenv('TEST_PENDING_DOCTOR_NPI', 'SYN-PEND-DOC-001')

REJECT_DOCTOR_EMAIL = os.getenv('TEST_REJECT_DOCTOR_EMAIL', 'selenium_reject_doctor@nexus.test')
REJECT_DOCTOR_PASSWORD = os.getenv('TEST_REJECT_DOCTOR_PASSWORD', 'SeleniumRejectDocPass123!')
REJECT_DOCTOR_NPI = os.getenv('TEST_REJECT_DOCTOR_NPI', 'SYN-REJ-DOC-002')

ADMIN_EMAIL = get_required_env('TEST_ADMIN_EMAIL')
ADMIN_PASSWORD = get_required_env('TEST_ADMIN_PASSWORD')
ADMIN_ACCESS_KEY = os.getenv('TEST_ADMIN_ACCESS_KEY', 'ADM-90210')

CAREGIVER_EMAIL = os.getenv('TEST_CAREGIVER_EMAIL', 'selenium_caregiver@nexus.test')
CAREGIVER_PASSWORD = os.getenv('TEST_CAREGIVER_PASSWORD', 'SeleniumCgPass123!')
CAREGIVER_AGENCY_ID = os.getenv('TEST_CAREGIVER_AGENCY_ID', 'CG-777')

FAMILY_EMAIL = os.getenv('TEST_FAMILY_EMAIL', 'selenium_family@nexus.test')
FAMILY_PASSWORD = os.getenv('TEST_FAMILY_PASSWORD', 'SeleniumFamPass123!')
FAMILY_PATIENT_ID = os.getenv('TEST_FAMILY_PATIENT_ID', 'P-777')

DOC_REQUESTED_EMAIL = os.getenv('TEST_DOC_REQUESTED_EMAIL', 'selenium_doc_requested@nexus.test')
DOC_REQUESTED_PASSWORD = os.getenv('TEST_DOC_REQUESTED_PASSWORD', 'SeleniumReqDocPass123!')
DOC_REQUESTED_NPI = os.getenv('TEST_DOC_REQUESTED_NPI', 'SYN-REQ-DOC-003')

DOC_SUSPENDED_EMAIL = os.getenv('TEST_DOC_SUSPENDED_EMAIL', 'selenium_doc_suspended@nexus.test')
DOC_SUSPENDED_PASSWORD = os.getenv('TEST_DOC_SUSPENDED_PASSWORD', 'SeleniumSuspDocPass123!')
DOC_SUSPENDED_NPI = os.getenv('TEST_DOC_SUSPENDED_NPI', 'SYN-SUSP-DOC-004')

DOC_REJECTED_EMAIL = os.getenv('TEST_DOC_REJECTED_EMAIL', 'jayan.naik.fresh@nexus.com')
DOC_REJECTED_PASSWORD = os.getenv('TEST_DOC_REJECTED_PASSWORD', 'password123')

DEFAULT_TIMEOUT = int(os.getenv('SELENIUM_DEFAULT_TIMEOUT', '10'))
EXPLICIT_WAIT = int(os.getenv('SELENIUM_EXPLICIT_WAIT', '12'))
SCREENSHOT_DIR = ROOT_DIR / 'test_reports' / 'screenshots'
ADMIN_SCREENSHOT_DIR = ROOT_DIR / 'test_reports' / 'admin' / 'screenshots'
AUTH_SCREENSHOT_DIR = ROOT_DIR / 'test_reports' / 'selenium' / 'authentication' / 'screenshots'
