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

def test_adm26_admin_page_refresh(driver):
    """ADM26 - ADMIN PAGE REFRESH: Verify session persists across page reload."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    # Refresh page
    driver.refresh()
    time.sleep(2)

    wait.until(EC.url_contains('/dashboard'))
    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Administrator Operations Center') or contains(text(), 'Root System Administration') or contains(text(), 'Secure Admin')]"))
    )
    assert header is not None, "Admin session lost after page refresh"

    save_admin_screenshot(driver, 'ADM26_admin_page_refresh_pass')

def test_adm27_admin_logout(driver):
    """ADM27 - ADMIN LOGOUT: Verify clean logout and session clearance."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    # Open User Profile menu
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

    wait.until(EC.url_contains('/login'))
    assert 'login' in driver.current_url.lower(), "Admin was not redirected to /login upon sign out"

    save_admin_screenshot(driver, 'ADM27_admin_logout_pass')

def test_adm28_admin_route_after_logout(driver):
    """ADM28 - ADMIN ROUTE AFTER LOGOUT: Attempt protected route navigation following logout."""
    # Precondition: User logged out
    driver.get(f'{config.FRONTEND_URL}/dashboard')
    time.sleep(1.5)
    assert 'login' in driver.current_url.lower(), "ProtectedRoute allowed logged-out user to visit /dashboard"

    driver.get(f'{config.FRONTEND_URL}/audit-logs')
    time.sleep(1.5)
    assert 'login' in driver.current_url.lower(), "ProtectedRoute allowed logged-out user to visit /audit-logs"

    save_admin_screenshot(driver, 'ADM28_admin_route_after_logout_pass')

def test_adm29_browser_back_after_logout(driver):
    """ADM29 - BROWSER BACK AFTER LOGOUT: Verify browser back does not grant unauthorized session."""
    driver.get(f'{config.FRONTEND_URL}/login')
    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")
    time.sleep(1)

    # Attempt browser back
    driver.back()
    time.sleep(1.5)

    # Ensure application remains on login or root landing
    current_url = driver.current_url.lower()
    assert 'login' in current_url or current_url.endswith('/') or 'dashboard' not in current_url, "Browser back improperly accessed protected page"

    save_admin_screenshot(driver, 'ADM29_browser_back_after_logout_pass')
