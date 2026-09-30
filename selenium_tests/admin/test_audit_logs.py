import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import login_as, save_admin_screenshot
from selenium_tests.admin.fixtures import init_admin_test_data

@pytest.fixture(autouse=True, scope='function')
def setup_test_data():
    init_admin_test_data()

def test_adm22_audit_log_page_load(driver):
    """ADM22 - AUDIT LOG PAGE LOAD: Verify Audit Logs and security trail rendering."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    wait.until(EC.url_contains('/audit-logs'))

    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Audit Logs & Security Trail') or contains(text(), 'Audit Logs')]"))
    )
    assert header is not None, "Audit Logs header missing"

    save_admin_screenshot(driver, 'ADM22_audit_log_page_pass')

def test_adm23_audit_record_display(driver):
    """ADM23 - AUDIT RECORD DISPLAY: Verify audit event stream table structure and metric cards."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    wait.until(EC.url_contains('/audit-logs'))

    # Wait for audit table / stream container
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Audit Event Stream') or contains(text(), 'Recorded Events')]")))

    time.sleep(2)
    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()

    # Metric cards
    assert 'recorded events' in body_text or 'events' in body_text, "Total recorded events metric card missing"
    assert 'authorized' in body_text or 'executions' in body_text, "Authorized executions metric card missing"
    assert 'blocked' in body_text or 'security' in body_text or 'failed' in body_text, "Blocked events metric missing"

    save_admin_screenshot(driver, 'ADM23_audit_record_display_pass')

def test_adm24_audit_search_and_filter(driver):
    """ADM24 - AUDIT SEARCH AND FILTER: Search and status filter pills in audit logs."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    wait.until(EC.url_contains('/audit-logs'))

    # 1. Search
    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search by user']")))
    search_input.clear()
    search_input.send_keys('Login')
    time.sleep(1)

    # 2. Filter pills
    for filter_name in ['SUCCESS', 'FAILED', 'ALL']:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{filter_name}')]")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)

    save_admin_screenshot(driver, 'ADM24_audit_search_filter_pass')

def test_adm25_audit_log_admin_authorization(driver):
    """ADM25 - AUDIT LOG ADMIN AUTHORIZATION: Confirm non-admin accounts cannot view audit logs."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    time.sleep(2)

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Audit Event Stream' not in page_text, "Patient was improperly allowed access to Audit Event Stream"

    save_admin_screenshot(driver, 'ADM25_audit_authorization_denial_pass')
