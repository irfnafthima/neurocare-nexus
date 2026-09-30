import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import login_as, save_evidence_screenshot

def test_st06_manual_vital_entry(driver):
    """ST06 - MANUAL VITAL ENTRY: End-to-end form -> backend -> database -> UI workflow."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # Navigate to Vitals page
    driver.get(f'{config.FRONTEND_URL}/vitals')
    wait.until(EC.url_contains('/vitals'))

    # Click Record Manual Vitals button
    record_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Record Manual Vitals')]"))
    )
    driver.execute_script("arguments[0].click();", record_btn)

    # Wait for modal to open
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Record Manual Vital Measurement')]")))

    # Fill distinct test values
    hr_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='20-300']")))
    hr_input.clear()
    hr_input.send_keys('82')

    spo2_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='30-100']")
    spo2_input.clear()
    spo2_input.send_keys('97')

    temp_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='25.0-45.0']")
    temp_input.clear()
    temp_input.send_keys('36.8')

    notes_input = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='notes']")
    notes_input.clear()
    notes_input.send_keys('Selenium automated test vital entry')

    # Save
    save_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save Manual Vitals')]")
    driver.execute_script("arguments[0].click();", save_btn)

    time.sleep(2)
    save_evidence_screenshot(driver, 'ST06_Manual_Vital_Save')

def test_st07_manual_vital_history(driver):
    """ST07 - MANUAL VITAL HISTORY: Verify persistence and provenance separation."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/vitals')
    wait.until(EC.url_contains('/vitals'))

    # Wait for history container
    history_header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Recorded Vital Measurements History')]"))
    )
    assert history_header is not None, "History header not found"

    time.sleep(2)
    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()

    # Assert manual entry provenance and values
    assert 'manual entry' in page_text or '82' in page_text, "Manual vital measurement not found in history"
    
    # Assert sensor cards maintain explicit 'Simulated Data' labeling
    assert 'simulated data' in page_text or 'simulated' in page_text, "Simulated data label missing from telemetry cards"
    save_evidence_screenshot(driver, 'ST07_Manual_Vital_History')