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

def test_adm01_valid_admin_login(driver):
    """ADM01 - VALID ADMIN LOGIN: Login with dedicated Admin test account and verify dashboard access."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    
    # Assert Admin-specific UI is rendered
    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Administrator Operations Center') or contains(text(), 'Root System Administration') or contains(text(), 'Secure Admin')]"))
    )
    assert header is not None, "Admin dashboard failed to render after valid login"
    
    page_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Secure Admin' in page_text or 'Administrator' in page_text, "Secure Admin banner missing"

    save_admin_screenshot(driver, 'ADM01_valid_admin_login_pass')

def test_adm02_admin_dashboard_direct_access_without_login(driver):
    """ADM02 - ADMIN DIRECT ACCESS WITHOUT LOGIN: Unauthenticated user attempting protected admin routes."""
    driver.get(f'{config.FRONTEND_URL}/login')
    time.sleep(1)
    
    # Purge any existing session
    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")
    
    protected_admin_routes = ['/dashboard', '/audit-logs', '/devices', '/doctor-verification', '/users']
    for route in protected_admin_routes:
        driver.get(f'{config.FRONTEND_URL}{route}')
        time.sleep(1)
        assert 'login' in driver.current_url.lower(), f"Unauthenticated access to {route} was not redirected to /login"

    save_admin_screenshot(driver, 'ADM02_unauthenticated_admin_access_pass')

def test_adm03_non_admin_access_to_admin_route(driver):
    """ADM03 - NON-ADMIN ACCESS TO ADMIN ROUTE: Patient/non-admin attempting Admin-only routes."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    # Attempt to directly open audit-logs or doctor verification
    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    time.sleep(2)

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    
    # Verify non-admin is not granted Root Admin capabilities
    assert 'Root System Administration' not in page_text, "Patient unexpectedly accessed Root Admin controls"
    assert 'Secure Admin' not in page_text, "Patient unexpectedly saw Secure Admin sidebar"

    save_admin_screenshot(driver, 'ADM03_non_admin_route_protection_pass')
