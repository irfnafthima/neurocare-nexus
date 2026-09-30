import os
import time
import json
import pytest
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import (
    login_as,
    save_evidence_screenshot,
    save_auth_screenshot
)

# Shared test helper to cleanly perform login in a test function
def perform_login(driver, role, email, password, extra_field=None, expect_success=True):
    driver.get(f"{config.FRONTEND_URL}/login")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # Clear previous sessionStorage to avoid state cross-contamination
    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")
    driver.refresh()

    if role == 'admin':
        admin_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'System Administrator gate')]")))
        driver.execute_script("arguments[0].click();", admin_btn)
        time.sleep(0.3)
    else:
        role_label = role.capitalize()
        try:
            role_tab = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{role_label}')]")))
            driver.execute_script("arguments[0].click();", role_tab)
            time.sleep(0.3)
        except Exception:
            pass

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    email_input.clear()
    if email:
        email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, 'password')
    password_input.clear()
    if password:
        password_input.send_keys(password)

    if role == 'doctor' and extra_field:
        try:
            npi_input = wait.until(EC.presence_of_element_located((By.NAME, 'npi')))
            npi_input.clear()
            npi_input.send_keys(extra_field)
        except Exception:
            pass
    elif role == 'patient' and extra_field:
        try:
            dev_input = wait.until(EC.presence_of_element_located((By.NAME, 'deviceId')))
            dev_input.clear()
            dev_input.send_keys(extra_field)
        except Exception:
            pass
    elif role == 'caregiver' and extra_field:
        try:
            agency_input = wait.until(EC.presence_of_element_located((By.NAME, 'agencyId')))
            agency_input.clear()
            agency_input.send_keys(extra_field)
        except Exception:
            pass
    elif role == 'family' and extra_field:
        try:
            pat_input = wait.until(EC.presence_of_element_located((By.NAME, 'patientId')))
            pat_input.clear()
            pat_input.send_keys(extra_field)
        except Exception:
            pass
    elif role == 'admin' and extra_field:
        try:
            key_input = wait.until(EC.presence_of_element_located((By.NAME, 'accessKey')))
            key_input.clear()
            key_input.send_keys(extra_field)
        except Exception:
            pass

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    if expect_success:
        wait.until(lambda d: '/dashboard' in d.current_url or '/doctor/verification-dashboard' in d.current_url)


# ==============================================================================
# 1. LOGIN — POSITIVE TESTING (TC_AUTH_001 - TC_AUTH_005)
# ==============================================================================

def test_tc_auth_001_valid_patient_login(driver):
    """TC_AUTH_001: Valid Patient Login."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    header = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Patient Health Dashboard') or contains(text(), 'Nexus Portal')]")
    ))
    assert header is not None, "Patient Health Dashboard header was not found."
    assert '/dashboard' in driver.current_url, "Patient was not redirected to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_001', 'valid_patient_login', 'PASS')


def test_tc_auth_002_valid_verified_doctor_login(driver):
    """TC_AUTH_002: Valid Verified Doctor Login."""
    perform_login(driver, 'doctor', config.DOCTOR_EMAIL, config.DOCTOR_PASSWORD, config.DOCTOR_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    header = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Clinician Oversight Workspace') or contains(text(), 'Nexus Portal')]")
    ))
    assert header is not None, "Doctor Clinician Workspace header was not found."
    assert 'verification-dashboard' not in driver.current_url, "Verified doctor should not be routed to verification dashboard."
    save_auth_screenshot(driver, 'TC_AUTH_002', 'valid_doctor_login', 'PASS')


def test_tc_auth_003_valid_caregiver_login(driver):
    """TC_AUTH_003: Valid Caregiver Login."""
    perform_login(driver, 'caregiver', config.CAREGIVER_EMAIL, config.CAREGIVER_PASSWORD, config.CAREGIVER_AGENCY_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    header = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Caregiver Operations Workspace') or contains(text(), 'Nexus Portal')]")
    ))
    assert header is not None, "Caregiver Operations Workspace header was not found."
    assert '/dashboard' in driver.current_url, "Caregiver was not redirected to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_003', 'valid_caregiver_login', 'PASS')


def test_tc_auth_004_valid_family_member_login(driver):
    """TC_AUTH_004: Valid Family Member Login."""
    perform_login(driver, 'family', config.FAMILY_EMAIL, config.FAMILY_PASSWORD, config.FAMILY_PATIENT_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    header = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Relative Care Monitor') or contains(text(), 'Nexus Portal')]")
    ))
    assert header is not None, "Family Relative Care Monitor header was not found."
    assert '/dashboard' in driver.current_url, "Family member was not redirected to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_004', 'valid_family_login', 'PASS')


def test_tc_auth_005_valid_administrator_login(driver):
    """TC_AUTH_005: Valid Administrator Login."""
    perform_login(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    header = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Root System Administration') or contains(text(), 'Secure Admin')]")
    ))
    assert header is not None, "Admin Root System Administration header was not found."
    assert '/dashboard' in driver.current_url, "Administrator was not redirected to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_005', 'valid_admin_login', 'PASS')


# ==============================================================================
# 2. LOGIN — NEGATIVE TESTING (TC_AUTH_006 - TC_AUTH_011)
# ==============================================================================

def test_tc_auth_006_invalid_password(driver):
    """TC_AUTH_006: Invalid Password."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, 'CompletelyWrongPass999!', expect_success=False)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    error_elem = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "p.text-red-500, .bg-red-50, div[role='alert']")
    ))
    assert error_elem is not None, "Expected error message element on invalid password."
    assert 'Incorrect password' in error_elem.text or 'failed' in error_elem.text.lower()
    assert '/dashboard' not in driver.current_url, "Protected dashboard must not open on invalid password."
    save_auth_screenshot(driver, 'TC_AUTH_006', 'invalid_password', 'PASS')


def test_tc_auth_007_unknown_unregistered_email(driver):
    """TC_AUTH_007: Unknown / Unregistered Email."""
    perform_login(driver, 'patient', 'unregistered_selenium_ghost@nexus.test', 'Password@123', expect_success=False)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    error_elem = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "p.text-red-500, .bg-red-50, div[role='alert']")
    ))
    assert error_elem is not None, "Expected error message on unknown email."
    assert 'No registered account found' in error_elem.text or 'not found' in error_elem.text.lower() or 'failed' in error_elem.text.lower()
    assert '/dashboard' not in driver.current_url, "Protected dashboard must not open for unknown email."
    save_auth_screenshot(driver, 'TC_AUTH_007', 'unknown_email', 'PASS')


def test_tc_auth_008_empty_login_form(driver):
    """TC_AUTH_008: Empty Login Form Submission."""
    driver.get(f"{config.FRONTEND_URL}/login")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    driver.execute_script("arguments[0].click();", submit_btn)

    error_elem = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "p.text-red-500, .bg-red-50, div[role='alert']")
    ))
    assert 'fill in email and password' in error_elem.text.lower(), f"Unexpected error message: {error_elem.text}"
    assert '/dashboard' not in driver.current_url
    save_auth_screenshot(driver, 'TC_AUTH_008', 'empty_login_form', 'PASS')


def test_tc_auth_009_email_entered_password_empty(driver):
    """TC_AUTH_009: Email Entered but Password Empty."""
    driver.get(f"{config.FRONTEND_URL}/login")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    email_input.clear()
    email_input.send_keys(config.PATIENT_EMAIL)

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    error_elem = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "p.text-red-500, .bg-red-50, div[role='alert']")
    ))
    assert 'fill in email and password' in error_elem.text.lower(), f"Unexpected error message: {error_elem.text}"
    assert '/dashboard' not in driver.current_url
    save_auth_screenshot(driver, 'TC_AUTH_009', 'email_only_empty_password', 'PASS')


def test_tc_auth_010_password_entered_email_empty(driver):
    """TC_AUTH_010: Password Entered but Email Empty."""
    driver.get(f"{config.FRONTEND_URL}/login")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    password_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
    password_input.clear()
    password_input.send_keys('ValidPassword123!')

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    error_elem = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "p.text-red-500, .bg-red-50, div[role='alert']")
    ))
    assert 'fill in email and password' in error_elem.text.lower(), f"Unexpected error message: {error_elem.text}"
    assert '/dashboard' not in driver.current_url
    save_auth_screenshot(driver, 'TC_AUTH_010', 'password_only_empty_email', 'PASS')


def test_tc_auth_011_invalid_email_format(driver):
    """TC_AUTH_011: Invalid Email Format in Login."""
    driver.get(f"{config.FRONTEND_URL}/login")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    email_input.clear()
    email_input.send_keys("invalid_email_format_without_at")

    password_input = driver.find_element(By.NAME, 'password')
    password_input.clear()
    password_input.send_keys("Password@123")

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    # HTML5 type="email" validation or backend error
    is_valid = driver.execute_script("return arguments[0].checkValidity();", email_input)
    assert not is_valid or '/dashboard' not in driver.current_url, "Malformed email should not be accepted for authentication."
    save_auth_screenshot(driver, 'TC_AUTH_011', 'invalid_email_format', 'PASS')


# ==============================================================================
# 3. DOCTOR VERIFICATION AUTHENTICATION (TC_AUTH_012 - TC_AUTH_016)
# ==============================================================================

def test_tc_auth_012_pending_doctor_login(driver):
    """TC_AUTH_012: Pending Doctor Login."""
    perform_login(driver, 'doctor', config.PENDING_DOCTOR_EMAIL, config.PENDING_DOCTOR_PASSWORD, config.PENDING_DOCTOR_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/doctor/verification-dashboard'))
    assert '/doctor/verification-dashboard' in driver.current_url, "Pending doctor was not routed to verification dashboard."

    page_text = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body'))).text
    assert 'Doctor Verification Portal' in page_text, "Verification Portal heading missing."
    assert 'Verification Pending' in page_text or 'Registration Verification In Progress' in page_text
    save_auth_screenshot(driver, 'TC_AUTH_012', 'pending_doctor_restricted', 'PASS')


def test_tc_auth_013_under_review_doctor_login(driver):
    """TC_AUTH_013: Under-Review Doctor Login."""
    perform_login(driver, 'doctor', config.REJECT_DOCTOR_EMAIL, config.REJECT_DOCTOR_PASSWORD, config.REJECT_DOCTOR_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/doctor/verification-dashboard'))
    assert '/doctor/verification-dashboard' in driver.current_url, "Under-review doctor was not routed to verification dashboard."

    # Explicitly wait for React state to fetch and render Under Review status badge
    review_elem = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Under Administrative Review') or contains(text(), 'UNDER ADMINISTRATIVE REVIEW') or contains(text(), 'Account Under Administrative Review')]")
    ))
    assert review_elem is not None
    save_auth_screenshot(driver, 'TC_AUTH_013', 'under_review_doctor_restricted', 'PASS')


def test_tc_auth_014_documents_requested_doctor_login(driver):
    """TC_AUTH_014: Documents-Requested Doctor Login."""
    perform_login(driver, 'doctor', config.DOC_REQUESTED_EMAIL, config.DOC_REQUESTED_PASSWORD, config.DOC_REQUESTED_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/doctor/verification-dashboard'))
    assert '/doctor/verification-dashboard' in driver.current_url

    # Explicitly wait for React state to fetch and render Documents Requested banner/badge
    req_elem = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Documents Requested') or contains(text(), 'DOCUMENTS REQUESTED') or contains(text(), 'Action Required')]")
    ))
    assert req_elem is not None
    save_auth_screenshot(driver, 'TC_AUTH_014', 'documents_requested_doctor', 'PASS')


def test_tc_auth_015_rejected_doctor_login(driver):
    """TC_AUTH_015: Rejected Doctor Login."""
    perform_login(driver, 'doctor', config.DOC_REJECTED_EMAIL, config.DOC_REJECTED_PASSWORD)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/doctor/verification-dashboard'))
    assert '/doctor/verification-dashboard' in driver.current_url

    # Explicitly wait for React state to fetch and render Rejected status badge/banner
    rej_elem = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Application Not Approved') or contains(text(), 'APPLICATION NOT APPROVED') or contains(text(), 'Registration Application Rejected')]")
    ))
    assert rej_elem is not None
    save_auth_screenshot(driver, 'TC_AUTH_015', 'rejected_doctor_restricted', 'PASS')


def test_tc_auth_016_suspended_doctor_login(driver):
    """TC_AUTH_016: Suspended Doctor Login."""
    perform_login(driver, 'doctor', config.DOC_SUSPENDED_EMAIL, config.DOC_SUSPENDED_PASSWORD, config.DOC_SUSPENDED_NPI, expect_success=False)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    error_elem = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "p.text-red-500, .bg-red-50, div[role='alert']")
    ))
    assert 'suspended' in error_elem.text.lower(), f"Expected suspended message, got: {error_elem.text}"
    assert '/dashboard' not in driver.current_url
    assert '/doctor/verification-dashboard' not in driver.current_url
    save_auth_screenshot(driver, 'TC_AUTH_016', 'suspended_doctor_blocked', 'PASS')


# ==============================================================================
# 4. PROTECTED ROUTES & RBAC (TC_AUTH_017 - TC_AUTH_022)
# ==============================================================================

def test_tc_auth_017_unauthenticated_user_opens_protected_url(driver):
    """TC_AUTH_017: Unauthenticated User Opens Protected URL."""
    driver.get(f"{config.FRONTEND_URL}/dashboard")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # ProtectedRoute must redirect to /login
    wait.until(EC.url_contains('/login'))
    assert '/login' in driver.current_url, "Unauthenticated user was not redirected to /login."
    save_auth_screenshot(driver, 'TC_AUTH_017', 'unauthenticated_protected_route', 'PASS')


def test_tc_auth_018_patient_attempts_doctor_route(driver):
    """TC_AUTH_018: Patient Attempts Doctor Route."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # Attempt to open Doctor Verification Dashboard directly
    driver.get(f"{config.FRONTEND_URL}/doctor/verification-dashboard")
    time.sleep(1)

    # DoctorVerificationRoute must redirect non-doctors to /dashboard
    wait.until(lambda d: '/dashboard' in d.current_url or '/doctor/verification-dashboard' not in d.current_url)
    assert 'Doctor Verification Portal' not in driver.find_element(By.TAG_NAME, 'body').text
    save_auth_screenshot(driver, 'TC_AUTH_018', 'patient_doctor_route_denied', 'PASS')


def test_tc_auth_019_patient_attempts_admin_route(driver):
    """TC_AUTH_019: Patient Attempts Admin Route."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # Attempt to open Audit Logs
    driver.get(f"{config.FRONTEND_URL}/audit-logs")
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Root System Administration' not in body_text, "Patient should not access Root System Administration workspace."
    assert 'Secure Admin' not in body_text, "Patient should not see Secure Admin sidebar."
    save_auth_screenshot(driver, 'TC_AUTH_019', 'patient_admin_route_denied', 'PASS')


def test_tc_auth_020_caregiver_attempts_admin_route(driver):
    """TC_AUTH_020: Caregiver Attempts Admin Route."""
    perform_login(driver, 'caregiver', config.CAREGIVER_EMAIL, config.CAREGIVER_PASSWORD, config.CAREGIVER_AGENCY_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/audit-logs")
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Root System Administration' not in body_text, "Caregiver should not access Root System Administration."
    assert 'Secure Admin' not in body_text
    save_auth_screenshot(driver, 'TC_AUTH_020', 'caregiver_admin_route_denied', 'PASS')


def test_tc_auth_021_family_member_attempts_admin_route(driver):
    """TC_AUTH_021: Family Member Attempts Admin Route."""
    perform_login(driver, 'family', config.FAMILY_EMAIL, config.FAMILY_PASSWORD, config.FAMILY_PATIENT_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/audit-logs")
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Root System Administration' not in body_text, "Family member should not access Root System Administration."
    assert 'Secure Admin' not in body_text
    save_auth_screenshot(driver, 'TC_AUTH_021', 'family_admin_route_denied', 'PASS')


def test_tc_auth_022_restricted_doctor_attempts_clinical_doctor_route(driver):
    """TC_AUTH_022: Restricted Doctor Attempts Clinical Doctor Route."""
    perform_login(driver, 'doctor', config.PENDING_DOCTOR_EMAIL, config.PENDING_DOCTOR_PASSWORD, config.PENDING_DOCTOR_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/doctor/verification-dashboard'))

    # Attempt to bypass by directly opening /dashboard
    driver.get(f"{config.FRONTEND_URL}/dashboard")
    time.sleep(1)

    # ProtectedRoute must redirect restricted doctor back to /doctor/verification-dashboard
    wait.until(EC.url_contains('/doctor/verification-dashboard'))
    assert '/doctor/verification-dashboard' in driver.current_url, "Restricted doctor must be redirected back to verification dashboard."
    assert 'Clinician Oversight Workspace' not in driver.find_element(By.TAG_NAME, 'body').text
    save_auth_screenshot(driver, 'TC_AUTH_022', 'restricted_doctor_bypass_blocked', 'PASS')


# ==============================================================================
# 5. SESSION & AUTH STATE (TC_AUTH_023 - TC_AUTH_027)
# ==============================================================================

def test_tc_auth_023_authentication_state_after_login(driver):
    """TC_AUTH_023: Authentication State After Login."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))

    # Check sessionStorage has nexus_user with expected sanitized fields
    user_json = driver.execute_script("return sessionStorage.getItem('nexus_user');")
    assert user_json is not None, "sessionStorage 'nexus_user' missing after login."
    user_data = json.loads(user_json)
    assert user_data.get('email') == config.PATIENT_EMAIL
    assert user_data.get('role') == 'patient'
    assert 'token' in user_data and len(user_data['token']) > 20
    save_auth_screenshot(driver, 'TC_AUTH_023', 'auth_state_stored', 'PASS')


def test_tc_auth_024_page_refresh_after_login(driver):
    """TC_AUTH_024: Page Refresh After Login."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))

    # Perform browser refresh
    driver.refresh()
    time.sleep(1)

    # Verify session persisted on /dashboard
    wait.until(EC.url_contains('/dashboard'))
    assert '/dashboard' in driver.current_url, "Session did not persist after browser refresh."
    header = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(text(), 'Patient Health Dashboard') or contains(text(), 'Nexus Portal')]")
    ))
    assert header is not None
    save_auth_screenshot(driver, 'TC_AUTH_024', 'page_refresh_session_persisted', 'PASS')


def test_tc_auth_025_logout(driver):
    """TC_AUTH_025: Logout."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))

    # Open User Profile popover
    profile_btn = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='User Profile']"))
    )
    driver.execute_script("arguments[0].click();", profile_btn)
    time.sleep(1)

    # Click Sign Out
    logout_btn = wait.until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Sign Out')]"))
    )
    driver.execute_script("arguments[0].click();", logout_btn)

    # Verify redirected to login & session cleared
    wait.until(EC.url_contains('/login'))
    assert '/login' in driver.current_url, "Expected redirect to /login upon logout."

    stored_user = driver.execute_script("return sessionStorage.getItem('nexus_user');")
    assert stored_user is None, "sessionStorage 'nexus_user' was not cleared upon logout."
    save_auth_screenshot(driver, 'TC_AUTH_025', 'logout_session_cleared', 'PASS')


def test_tc_auth_026_protected_url_after_logout(driver):
    """TC_AUTH_026: Protected URL After Logout."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))

    # Logout
    profile_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='User Profile']")))
    driver.execute_script("arguments[0].click();", profile_btn)
    time.sleep(1)
    logout_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Sign Out')]")))
    driver.execute_script("arguments[0].click();", logout_btn)
    wait.until(EC.url_contains('/login'))

    # Attempt to revisit protected /dashboard
    driver.get(f"{config.FRONTEND_URL}/dashboard")
    time.sleep(1)

    wait.until(EC.url_contains('/login'))
    assert '/login' in driver.current_url, "Protected URL accessible after logout."
    save_auth_screenshot(driver, 'TC_AUTH_026', 'protected_url_after_logout_denied', 'PASS')


def test_tc_auth_027_browser_back_navigation_after_logout(driver):
    """TC_AUTH_027: Browser Back Navigation After Logout."""
    perform_login(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))

    # Logout
    profile_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label='User Profile']")))
    driver.execute_script("arguments[0].click();", profile_btn)
    time.sleep(1)
    logout_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Sign Out')]")))
    driver.execute_script("arguments[0].click();", logout_btn)
    wait.until(EC.url_contains('/login'))

    # Hit Browser Back Button
    driver.back()
    time.sleep(1)

    # ProtectedRoute must keep user on /login or force redirect back to /login
    wait.until(lambda d: '/login' in d.current_url or '/dashboard' not in d.current_url)
    stored_user = driver.execute_script("return sessionStorage.getItem('nexus_user');")
    assert stored_user is None, "Session reconstructed upon back navigation."
    save_auth_screenshot(driver, 'TC_AUTH_027', 'back_navigation_after_logout_safe', 'PASS')


# ==============================================================================
# 6. REGISTRATION (TC_AUTH_028 - TC_AUTH_031)
# ==============================================================================

def test_tc_auth_028_valid_patient_registration(driver):
    """TC_AUTH_028: Valid Patient Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # Clear storage
    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")

    ts = int(time.time() * 1000)
    test_email = f"selenium_reg_pat_{ts}@nexus.test"

    # Select Patient tab
    patient_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Patient')]")))
    driver.execute_script("arguments[0].click();", patient_tab)

    driver.find_element(By.NAME, 'firstName').send_keys("SeleniumPat")
    driver.find_element(By.NAME, 'lastName').send_keys("TestUser")
    driver.find_element(By.NAME, 'workEmail').send_keys(test_email)
    driver.find_element(By.NAME, 'phone').send_keys("+91 9876543210")
    driver.find_element(By.NAME, 'password').send_keys("SeleniumPatPass123!")
    driver.find_element(By.NAME, 'confirmPassword').send_keys("SeleniumPatPass123!")

    # Submit
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    wait.until(EC.url_contains('/dashboard'))
    assert '/dashboard' in driver.current_url, "Patient registration did not navigate to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_028', 'patient_registration_success', 'PASS')


def test_tc_auth_029_valid_caregiver_registration(driver):
    """TC_AUTH_029: Valid Caregiver Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")

    ts = int(time.time() * 1000)
    test_email = f"selenium_reg_cg_{ts}@nexus.test"

    # Select Caregiver tab
    cg_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Caregiver')]")))
    driver.execute_script("arguments[0].click();", cg_tab)

    driver.find_element(By.NAME, 'firstName').send_keys("SeleniumCg")
    driver.find_element(By.NAME, 'lastName').send_keys("TestUser")
    driver.find_element(By.NAME, 'workEmail').send_keys(test_email)
    driver.find_element(By.NAME, 'agencyId').send_keys("CG-999")
    driver.find_element(By.NAME, 'phone').send_keys("+91 9876543211")
    driver.find_element(By.NAME, 'password').send_keys("SeleniumCgPass123!")
    driver.find_element(By.NAME, 'confirmPassword').send_keys("SeleniumCgPass123!")

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    wait.until(EC.url_contains('/dashboard'))
    assert '/dashboard' in driver.current_url, "Caregiver registration did not navigate to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_029', 'caregiver_registration_success', 'PASS')


def test_tc_auth_030_valid_family_registration(driver):
    """TC_AUTH_030: Valid Family Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")

    ts = int(time.time() * 1000)
    test_email = f"selenium_reg_fam_{ts}@nexus.test"

    # Select Family tab
    fam_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Family')]")))
    driver.execute_script("arguments[0].click();", fam_tab)

    driver.find_element(By.NAME, 'firstName').send_keys("SeleniumFam")
    driver.find_element(By.NAME, 'lastName').send_keys("TestUser")
    driver.find_element(By.NAME, 'workEmail').send_keys(test_email)
    driver.find_element(By.NAME, 'patientId').send_keys(config.PATIENT_ID)
    driver.find_element(By.NAME, 'phone').send_keys("+91 9876543212")
    driver.find_element(By.NAME, 'password').send_keys("SeleniumFamPass123!")
    driver.find_element(By.NAME, 'confirmPassword').send_keys("SeleniumFamPass123!")

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    wait.until(EC.url_contains('/dashboard'))
    assert '/dashboard' in driver.current_url, "Family registration did not navigate to /dashboard"
    save_auth_screenshot(driver, 'TC_AUTH_030', 'family_registration_success', 'PASS')


def test_tc_auth_031_valid_doctor_registration(driver):
    """TC_AUTH_031: Valid Doctor Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")

    ts = int(time.time() * 1000)
    test_email = f"selenium_reg_doc_{ts}@nexus.test"

    # Select Doctor tab
    doc_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Doctor')]")))
    driver.execute_script("arguments[0].click();", doc_tab)

    driver.find_element(By.NAME, 'firstName').send_keys("SeleniumDoc")
    driver.find_element(By.NAME, 'lastName').send_keys("Applicant")
    driver.find_element(By.NAME, 'workEmail').send_keys(test_email)
    driver.find_element(By.NAME, 'medicalRegistrationNumber').send_keys(f"REG-{ts % 1000000:06d}")

    # Select State Medical Council
    council_select = Select(driver.find_element(By.NAME, 'stateMedicalCouncil'))
    council_select.select_by_value("Karnataka Medical Council")

    driver.find_element(By.NAME, 'registrationYear').send_keys("2018")
    driver.find_element(By.NAME, 'qualification').send_keys("MBBS, MD")

    # Select Specialization
    spec_select = Select(driver.find_element(By.NAME, 'specialization'))
    spec_select.select_by_value("Neurology")

    driver.find_element(By.NAME, 'experience').send_keys("6")
    driver.find_element(By.NAME, 'phone').send_keys("+91 9876543213")
    driver.find_element(By.NAME, 'password').send_keys("SeleniumDocPass123!")
    driver.find_element(By.NAME, 'confirmPassword').send_keys("SeleniumDocPass123!")

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    # Verify Doctor Verification Status Modal appears (Doctor account created in pending/restricted state)
    status_modal = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//*[contains(., 'Verification Required') or contains(., 'Verification Result') or contains(., 'Administrator Review') or contains(., 'Registration Record') or contains(., 'Continue to Login')]")
    ))
    assert status_modal is not None, "Doctor verification status modal did not appear."
    assert '/dashboard' not in driver.current_url, "Doctor must not receive immediate clinical dashboard access."
    save_auth_screenshot(driver, 'TC_AUTH_031', 'doctor_registration_pending_modal', 'PASS')


# ==============================================================================
# 7. REGISTRATION VALIDATION (TC_AUTH_032 - TC_AUTH_037)
# ==============================================================================

def test_tc_auth_032_required_fields_missing(driver):
    """TC_AUTH_032: Required Fields Missing in Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    driver.execute_script("arguments[0].click();", submit_btn)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'First name is required' in body_text or 'required' in body_text.lower()
    assert 'register' in driver.current_url.lower(), "Registration form should not submit with empty fields."
    save_auth_screenshot(driver, 'TC_AUTH_032', 'required_fields_missing', 'PASS')


def test_tc_auth_033_password_confirm_password_mismatch(driver):
    """TC_AUTH_033: Password / Confirm Password Mismatch."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.find_element(By.NAME, 'firstName').send_keys("Test")
    driver.find_element(By.NAME, 'lastName').send_keys("User")
    driver.find_element(By.NAME, 'workEmail').send_keys("mismatch_test@nexus.test")
    driver.find_element(By.NAME, 'phone').send_keys("+91 9876543210")
    driver.find_element(By.NAME, 'password').send_keys("ValidPassword123!")

    confirm_input = driver.find_element(By.NAME, 'confirmPassword')
    confirm_input.send_keys("DifferentPassword999!")
    confirm_input.send_keys(Keys.TAB)
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'match' in body_text.lower() or 'passwords do not match' in body_text.lower()

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)
    assert 'register' in driver.current_url.lower()
    save_auth_screenshot(driver, 'TC_AUTH_033', 'password_mismatch', 'PASS')


def test_tc_auth_034_duplicate_email_registration(driver):
    """TC_AUTH_034: Duplicate Email Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # Enter already registered email
    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'workEmail')))
    email_input.clear()
    email_input.send_keys(config.PATIENT_EMAIL)
    email_input.send_keys(Keys.TAB)

    # Wait for debounced live check
    time.sleep(2)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'already registered' in body_text.lower() or 'already exists' in body_text.lower()
    save_auth_screenshot(driver, 'TC_AUTH_034', 'duplicate_email_blocked', 'PASS')


def test_tc_auth_035_invalid_email_format(driver):
    """TC_AUTH_035: Invalid Email Format in Registration."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'workEmail')))
    email_input.clear()
    email_input.send_keys("invalid-format-no-domain")
    email_input.send_keys(Keys.TAB)
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'valid email' in body_text.lower()
    save_auth_screenshot(driver, 'TC_AUTH_035', 'invalid_email_format', 'PASS')


def test_tc_auth_036_password_validation_rules(driver):
    """TC_AUTH_036: Password Validation Rules Checklist."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    pass_input = wait.until(EC.presence_of_element_located((By.NAME, 'password')))
    pass_input.clear()
    pass_input.send_keys("short")
    pass_input.send_keys(Keys.TAB)
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert '8 characters' in body_text.lower() or 'password must be at least 8' in body_text.lower()
    save_auth_screenshot(driver, 'TC_AUTH_036', 'password_rules_validation', 'PASS')


def test_tc_auth_037_role_validation_and_form_adaptation(driver):
    """TC_AUTH_037: Dynamic Role Form Adaptation."""
    driver.get(f"{config.FRONTEND_URL}/register")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # 1. Check Doctor fields
    doc_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Doctor')]")))
    driver.execute_script("arguments[0].click();", doc_tab)
    time.sleep(0.5)
    assert driver.find_element(By.NAME, 'medicalRegistrationNumber') is not None
    assert driver.find_element(By.NAME, 'stateMedicalCouncil') is not None

    # 2. Check Caregiver fields
    cg_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Caregiver')]")))
    driver.execute_script("arguments[0].click();", cg_tab)
    time.sleep(0.5)
    assert driver.find_element(By.NAME, 'agencyId') is not None

    # 3. Check Family fields
    fam_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Family')]")))
    driver.execute_script("arguments[0].click();", fam_tab)
    time.sleep(0.5)
    assert driver.find_element(By.NAME, 'patientId') is not None

    save_auth_screenshot(driver, 'TC_AUTH_037', 'role_form_adaptation', 'PASS')
