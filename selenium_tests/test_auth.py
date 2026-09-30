import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import login_as, save_evidence_screenshot

def test_st01_invalid_login(driver):
    """ST01 - INVALID LOGIN: Verify login rejection with invalid credentials."""
    driver.get(f'{config.FRONTEND_URL}/login')
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    email_input.clear()
    email_input.send_keys('invalid_test_user@nexus.com')

    password_input = driver.find_element(By.NAME, 'password')
    password_input.clear()
    password_input.send_keys('InvalidPassword999!')

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    # Verify error element appears
    error_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'p.text-red-500, .bg-red-50, div[role="alert"]'))
    )
    assert error_element is not None, 'Expected validation error message on invalid login'
    assert 'dashboard' not in driver.current_url.lower(), 'Should not navigate to dashboard on invalid login'

def test_st02_patient_login_and_dashboard(driver):
    """ST02 - PATIENT LOGIN AND DASHBOARD: End-to-end patient authentication."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    
    dashboard_header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Patient Health Dashboard') or contains(text(), 'Nexus Portal')]"))
    )
    assert dashboard_header is not None, 'Patient dashboard failed to render'
    save_evidence_screenshot(driver, 'ST02_Patient_Dashboard')

def test_st03_approved_doctor_login(driver):
    """ST03 - APPROVED DOCTOR LOGIN: Verify doctor authentication and approval gate."""
    login_as(driver, 'doctor', config.DOCTOR_EMAIL, config.DOCTOR_PASSWORD, config.DOCTOR_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    doc_header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Clinician Oversight Workspace') or contains(text(), 'Doctor') or contains(text(), 'Patients')]"))
    )
    assert doc_header is not None, 'Approved doctor dashboard failed to render'
    save_evidence_screenshot(driver, 'ST03_Doctor_Dashboard')

def test_st04_admin_login(driver):
    """ST04 - ADMIN LOGIN: Verify administrative role routing and operations."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    admin_header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Root System Administration') or contains(text(), 'Secure Admin')]"))
    )
    assert admin_header is not None, 'Admin dashboard failed to render'
    save_evidence_screenshot(driver, 'ST04_Admin_Dashboard')