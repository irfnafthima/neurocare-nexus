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

def test_adm04_admin_dashboard_load(driver):
    """ADM04 - ADMIN DASHBOARD LOAD: Verify Admin Operations Center rendering."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    # Verify Header Banner
    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Administrator Operations Center')]"))
    )
    assert header is not None, "Administrator Operations Center header missing"

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Root system nodes' in body_text, "Admin subtitle missing"
    assert 'System Active' in body_text, "System Active badge missing"

    save_admin_screenshot(driver, 'ADM04_admin_dashboard_load_pass')

def test_adm05_admin_statistics(driver):
    """ADM05 - ADMIN STATISTICS: Verify real-time metric cards on Admin dashboard."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    time.sleep(2)
    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()

    # Verify stat cards present
    assert 'registered users' in body_text, "Registered Users metric card missing"
    assert 'registered doctors' in body_text, "Registered Doctors metric card missing"
    assert 'pending verifications' in body_text, "Pending Verifications metric card missing"
    assert 'devices' in body_text, "Devices metric card missing"
    assert 'reference medical registry' in body_text or 'audit events' in body_text, "Registry strip missing"

    save_admin_screenshot(driver, 'ADM05_admin_statistics_pass')

def test_adm06_admin_navigation(driver):
    """ADM06 - ADMIN NAVIGATION: Verify sidebar navigation across all Admin modules."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    # Test route mappings
    routes_to_test = [
        ('/doctor-verification', ['Doctor', 'Verification']),
        ('/users', ['Registered Portal Users', 'User Directory', 'Users']),
        ('/devices', ['Hardware & IoT Device Management', 'Devices']),
        ('/audit-logs', ['Audit Logs & Security Trail', 'Audit Event Stream']),
        ('/settings', ['System & Administrative Settings', 'Settings']),
        ('/dashboard', ['Administrator Operations Center', 'Admin'])
    ]

    for route, expected_keywords in routes_to_test:
        driver.get(f'{config.FRONTEND_URL}{route}')
        wait.until(EC.url_contains(route))
        time.sleep(1.5)
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        matched = any(kw in page_text for kw in expected_keywords)
        assert matched, f"Route {route} did not contain any expected keywords: {expected_keywords}"

    save_admin_screenshot(driver, 'ADM06_admin_navigation_pass')

