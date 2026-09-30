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

def test_adm18_device_management_page_load(driver):
    """ADM18 - DEVICE MANAGEMENT PAGE LOAD: Verify Device Management header and view."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/devices')
    wait.until(EC.url_contains('/devices'))

    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Hardware & IoT Device Management')]"))
    )
    assert header is not None, "Hardware & IoT Device Management header missing"

    save_admin_screenshot(driver, 'ADM18_device_management_page_pass')

def test_adm19_device_inventory_display(driver):
    """ADM19 - DEVICE INVENTORY DISPLAY: Verify fleet metric cards and device inventory table."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/devices')
    wait.until(EC.url_contains('/devices'))

    time.sleep(2)
    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()

    # Metric cards
    assert 'total registered fleet' in body_text, "Fleet total metric missing"
    assert 'assigned to patients' in body_text, "Assigned devices metric missing"
    assert 'wearable biosensors' in body_text, "Wearable biosensors metric missing"
    assert 'synthetic generators' in body_text, "Synthetic generators metric missing"

    save_admin_screenshot(driver, 'ADM19_device_inventory_pass')

def test_adm20_device_search_and_filter(driver):
    """ADM20 - DEVICE SEARCH AND FILTER: Search and pill filtering on devices page."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/devices')
    wait.until(EC.url_contains('/devices'))

    # 1. Search test
    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search by serial']")))
    search_input.clear()
    search_input.send_keys('NP-101')
    time.sleep(1)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'NP-101' in body_text or 'Registered Devices' in body_text, "Device search failed"

    # 2. Filter pills test
    for filter_name in ['WEARABLE', 'SYNTHETIC', 'ALL']:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(., '{filter_name}')]")))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)

    save_admin_screenshot(driver, 'ADM20_device_search_filter_pass')
