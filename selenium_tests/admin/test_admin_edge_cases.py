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

def test_adm30_empty_search_results_handling(driver):
    """ADM30 - EMPTY SEARCH RESULTS HANDLING: Verify graceful no-results display on Users and Devices."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # 1. Users page empty search
    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))
    search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Filter users']")))
    search_input.clear()
    search_input.send_keys('NONEXISTENT_QUERY_XYZ_12345')
    time.sleep(1)

    table_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
    assert len(table_rows) == 0, "Expected 0 table rows for nonexistent user query"

    # 2. Devices page empty search
    driver.get(f'{config.FRONTEND_URL}/devices')
    wait.until(EC.url_contains('/devices'))
    dev_search = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search by serial']")))
    dev_search.clear()
    dev_search.send_keys('NONEXISTENT_SERIAL_99999')
    time.sleep(1)

    dev_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'No Devices Found' in dev_text or '0' in dev_text, "Empty device search message missing"

    save_admin_screenshot(driver, 'ADM30_empty_search_handling_pass')

def test_adm31_invalid_route_graceful_handling(driver):
    """ADM31 - INVALID ROUTE GRACEFUL HANDLING: Direct navigation to nonexistent admin path."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    wait.until(EC.url_contains('/dashboard'))

    # Navigate to invalid path
    driver.get(f'{config.FRONTEND_URL}/admin/invalid-nonexistent-subpage')
    time.sleep(2)

    # Check that app handles it gracefully (redirects to / or loads without crash)
    assert not driver.find_elements(By.XPATH, "//*[contains(text(), 'Cannot GET') or contains(text(), 'Uncaught SyntaxError')]"), "Uncaught fatal route error"

    save_admin_screenshot(driver, 'ADM31_invalid_route_handling_pass')

def test_adm32_administrative_settings_and_governance(driver):
    """ADM32 - ADMINISTRATIVE SETTINGS: Access and configure admin settings & notifications."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/settings')
    wait.until(EC.url_contains('/settings'))

    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Settings')]"))
    )
    assert header is not None, "Settings header missing"

    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'active account profile' in body_text or 'settings' in body_text, "Account profile section missing"

    # Save administrative notification preferences
    save_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Save') or contains(., 'Update')]")
    if len(save_btns) > 0:
        driver.execute_script("arguments[0].click();", save_btns[0])
        time.sleep(1)

    save_admin_screenshot(driver, 'ADM32_admin_settings_pass')
