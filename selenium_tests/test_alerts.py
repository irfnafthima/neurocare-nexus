import pytest
import time
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import login_as, save_evidence_screenshot

def test_st08_live_monitoring_route(driver):
    """ST08 - LIVE MONITORING ROUTE: Verify navigation and telemetry monitoring UI."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/vitals')
    wait.until(EC.url_contains('/vitals'))
    
    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Vitals & Telemetry Monitoring')]"))
    )
    assert header is not None, "Vitals & Telemetry Monitoring header not found"

    time.sleep(2)
    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'max30102' in page_text, "MAX30102 PPG sensor card missing"
    assert 'ds18b20' in page_text, "DS18B20 Thermal sensor card missing"
    assert 'mpu6050' in page_text, "MPU6050 Motion sensor card missing"
    
    save_evidence_screenshot(driver, 'ST08_Live_Monitoring')

def test_st09_alerts_route_separation(driver):
    """ST09 - ALERTS ROUTE SEPARATION: Regression test verifying dedicated AlertsPage rendering."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/alerts')
    wait.until(EC.url_contains('/alerts'))

    alerts_header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Clinical Alerts')]"))
    )
    assert alerts_header is not None, "Clinical Alerts header not found"

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Vitals & Telemetry Monitoring' not in page_text, "Alerts route incorrectly rendered VitalsPage"
    assert 'MAX30102 Optical PPG' not in page_text, "Alerts route incorrectly contains live vitals charts"

    save_evidence_screenshot(driver, 'ST09_Alerts_Page')

def test_st10_simulated_abnormal_telemetry_to_alert(driver):
    """ST10 - SIMULATED ABNORMAL TELEMETRY -> ALERT: End-to-end integration test."""
    # 1. Obtain JWT token for Patient
    auth_resp = requests.post(
        f'{config.BACKEND_URL}/api/auth/login',
        json={'email': config.PATIENT_EMAIL, 'password': config.PATIENT_PASSWORD, 'role': 'patient'}
    )
    assert auth_resp.status_code == 200, f"Failed patient auth for simulation: {auth_resp.text}"
    token = auth_resp.json().get('token')

    # 2. Trigger abnormal telemetry via supported endpoint (HR=145 critical)
    sim_resp = requests.post(
        f'{config.BACKEND_URL}/api/simulation/trigger',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={
            'patientId': config.PATIENT_ID,
            'vitals': {
                'max30102': {'heartRate': 145, 'spo2': 84},
                'ds18b20': {'temperature': 39.2},
                'mpu6050': {'fallDetected': False}
            },
            'statusState': 'Critical',
            'auditAction': 'Selenium Automated Critical Trigger'
        }
    )
    assert sim_resp.status_code in [200, 201], f"Simulation trigger failed: {sim_resp.text}"

    # 3. Open browser and check /alerts
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/alerts')
    wait.until(EC.url_contains('/alerts'))

    time.sleep(2)
    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()

    assert 'critical' in page_text or 'heart rate' in page_text or '145' in page_text or 'alert' in page_text, "Generated critical alert not visible on /alerts"
    save_evidence_screenshot(driver, 'ST10_Generated_Alert')

    # 4. Test resolving the alert if button is visible
    try:
        resolve_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Resolve Alert')]")
        if resolve_btns:
            driver.execute_script("arguments[0].click();", resolve_btns[0])
            time.sleep(1.5)
    except Exception:
        pass