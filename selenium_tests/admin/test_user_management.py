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

def test_adm13_user_management_page_load(driver):
    """ADM13 - USER MANAGEMENT PAGE LOAD: Verify user directory rendering."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))

    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Registered Portal Users') or contains(text(), 'System User Directory')]"))
    )
    assert header is not None, "Registered Portal Users header missing"

    save_admin_screenshot(driver, 'ADM13_user_management_load_pass')

def test_adm14_user_data_display(driver):
    """ADM14 - USER DATA DISPLAY: Verify user directory table structure and role badges."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))

    time.sleep(2)
    table = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
    assert table is not None, "User directory table not found"

    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'user profile' in body_text, "User Profile column missing"
    assert 'role' in body_text, "Role column missing"
    assert 'phone & email' in body_text or 'email' in body_text, "Phone & Email column missing"
    assert 'status' in body_text, "Status column missing"

    save_admin_screenshot(driver, 'ADM14_user_data_display_pass')

def test_adm15_user_search(driver):
    """ADM15 - USER SEARCH: Search filtering by known user and nonexistent string."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))

    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Filter users']")))
    search_input.clear()
    search_input.send_keys('selenium_patient')
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'selenium_patient' in body_text or 'selenium patient' in body_text, "Search failed to match known user"

    # Search nonexistent
    search_input.clear()
    search_input.send_keys('xyz_nonexistent_user_999')
    time.sleep(1)
    
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'selenium_patient@nexus.test' not in body_text, "Search filter did not exclude non-matching users"

    save_admin_screenshot(driver, 'ADM15_user_search_pass')

def test_adm16_user_tab_switching(driver):
    """ADM16 - USER TAB SWITCHING: Switch between Doctor Verification Queue and User Directory tabs."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))

    # Click Verification Queue tab
    queue_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Doctor Verification Queue')]"))
    )
    driver.execute_script("arguments[0].click();", queue_btn)
    time.sleep(1)

    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'doctor credential verification' in page_text or 'verification queue' in page_text, "Failed to switch to verification queue tab"

    # Switch back to User Directory
    users_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'System User Directory')]"))
    )
    driver.execute_script("arguments[0].click();", users_btn)
    time.sleep(1)

    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'registered portal users' in page_text or 'user directory' in page_text, "Failed to switch back to users directory tab"

    save_admin_screenshot(driver, 'ADM16_tab_switching_pass')

def test_adm17_user_self_protection(driver):
    """ADM17 - USER DETAILS & SELF-PROTECTION: Ensure active Admin has self-protection badge."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))

    time.sleep(2)
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert '(You)' in body_text, "Active logged-in Admin self badge '(You)' missing"

    save_admin_screenshot(driver, 'ADM17_user_self_protection_pass')
