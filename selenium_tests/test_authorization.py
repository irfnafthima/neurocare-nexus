import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import login_as, save_evidence_screenshot

def test_st11_unauthorized_protected_route(driver):
    """ST11 - UNAUTHORIZED / PROTECTED ROUTE: Verify non-admin cannot access admin operations."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))

    # Attempt to directly navigate to audit logs or admin doctor verification
    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    time.sleep(2)

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    
    # Verify patient cannot access Root Admin workspace
    assert 'Root System Administration' not in page_text, "Patient should not access Root Admin workspace"
    assert 'Secure Admin' not in page_text, "Patient should not have Root Admin interface"

    save_evidence_screenshot(driver, 'ST11_Protected_Route_Check')

def test_st12_logout_and_session_protection(driver):
    """ST12 - LOGOUT AND SESSION PROTECTION: Verify session clearance and protected route denial."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
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

    # Verify redirected to login
    wait.until(EC.url_contains('/login'))
    assert 'login' in driver.current_url.lower(), "Expected redirect to login upon logout"

    # Attempt to revisit protected dashboard URL directly
    driver.get(f'{config.FRONTEND_URL}/dashboard')
    time.sleep(2)

    # Verify ProtectedRoute forces user back to /login
    assert 'login' in driver.current_url.lower(), "Unauthenticated user was not redirected away from protected dashboard"
    save_evidence_screenshot(driver, 'ST12_Session_Cleared')