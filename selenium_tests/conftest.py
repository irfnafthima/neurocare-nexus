import pytest
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config

@pytest.fixture(scope='function')
def driver(request):
    chrome_options = Options()
    if os.getenv('SELENIUM_HEADLESS', 'true').lower() in ['true', '1', 'yes']:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--window-size=1400,900')

    driver = webdriver.Chrome(options=chrome_options)
    driver.implicitly_wait(3)

    yield driver

    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        test_name = request.node.name
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        is_admin_test = 'admin' in str(request.node.fspath).lower()
        is_auth_test = 'auth' in str(request.node.fspath).lower()
        if is_auth_test:
            target_dir = config.AUTH_SCREENSHOT_DIR
        elif is_admin_test:
            target_dir = config.ADMIN_SCREENSHOT_DIR
        else:
            target_dir = config.SCREENSHOT_DIR
        os.makedirs(target_dir, exist_ok=True)
        fail_path = target_dir / f'FAIL_{test_name}_{ts}.png'
        driver.save_screenshot(str(fail_path))

    driver.quit()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, 'rep_' + rep.when, rep)

def save_evidence_screenshot(driver, name):
    os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
    file_path = config.SCREENSHOT_DIR / f'{name}.png'
    driver.save_screenshot(str(file_path))
    return str(file_path)

def save_admin_screenshot(driver, name):
    os.makedirs(config.ADMIN_SCREENSHOT_DIR, exist_ok=True)
    file_path = config.ADMIN_SCREENSHOT_DIR / f'{name}.png'
    driver.save_screenshot(str(file_path))
    return str(file_path)

def save_auth_screenshot(driver, test_id, name, status="PASS"):
    os.makedirs(config.AUTH_SCREENSHOT_DIR, exist_ok=True)
    clean_name = name.replace(" ", "_").replace("/", "_")
    file_path = config.AUTH_SCREENSHOT_DIR / f'{test_id}_{clean_name}_{status}.png'
    driver.save_screenshot(str(file_path))
    return str(file_path)


def login_as(driver, role, email, password, extra_field=None):
    driver.get(f'{config.FRONTEND_URL}/login')
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    if role == 'admin':
        admin_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'System Administrator gate')]")))
        driver.execute_script("arguments[0].click();", admin_btn)
    else:
        role_label = role.capitalize()
        try:
            role_tab = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{role_label}')]")))
            driver.execute_script("arguments[0].click();", role_tab)
        except Exception:
            pass

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    email_input.clear()
    email_input.send_keys(email)

    password_input = driver.find_element(By.NAME, 'password')
    password_input.clear()
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
    elif role == 'admin' and extra_field:
        try:
            key_input = wait.until(EC.presence_of_element_located((By.NAME, 'accessKey')))
            key_input.clear()
            key_input.send_keys(extra_field)
        except Exception:
            pass

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", submit_btn)

    # Wait for React state to transition to /dashboard
    wait.until(EC.url_contains('/dashboard'))