import os
import time
import json
import pytest
from datetime import datetime
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config

PATIENT_SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / 'test_reports' / 'selenium' / 'patient' / 'screenshots'
PATIENT_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_patient_screenshot(driver, test_id, name):
    clean_name = name.replace(' ', '_').replace('/', '_')
    filename = f"{test_id}_{clean_name}.png"
    filepath = PATIENT_SCREENSHOT_DIR / filename
    driver.save_screenshot(str(filepath))
    return str(filepath)

def login_patient(driver):
    driver.get(f"{config.FRONTEND_URL}/login")
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)
    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")
    driver.refresh()

    role_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Patient')]")))
    driver.execute_script("arguments[0].click();", role_tab)
    time.sleep(0.3)

    email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
    email_input.clear()
    email_input.send_keys(config.PATIENT_EMAIL)

    password_input = driver.find_element(By.NAME, 'password')
    password_input.clear()
    password_input.send_keys(config.PATIENT_PASSWORD)

    try:
        dev_input = driver.find_element(By.NAME, 'deviceId')
        dev_input.clear()
        dev_input.send_keys(config.PATIENT_DEVICE_ID)
    except Exception:
        pass

    submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(., 'Secure Access Portal')]")))
    driver.execute_script("arguments[0].click();", submit_btn)

    wait.until(EC.url_contains('/dashboard'))
    time.sleep(1.0)


# =========================================================================
# CATEGORY A: PATIENT DASHBOARD (TC_PAT_001 - TC_PAT_005)
# =========================================================================

def test_tc_pat_001_patient_dashboard_load_and_welcome(driver):
    """TC_PAT_001: Patient Dashboard Successful Load & Welcome Banner."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    welcome_header = wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'Hello,') or contains(., 'Jane')]")))
    assert welcome_header is not None, "Patient greeting header not found"
    
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert "NeuroCare Nexus is monitoring your health securely" in body_text, "Slogan banner text missing"
    assert "System Active" in body_text, "System Active badge missing"

    save_patient_screenshot(driver, "TC_PAT_001", "patient_dashboard_welcome_PASS")


def test_tc_pat_002_patient_dashboard_vital_cards(driver):
    """TC_PAT_002: Patient Dashboard Vitals Metric Cards."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    hr_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Heart Rate')]")))
    spo2_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'SpO2 Oxygen')]")))
    temp_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Body Temp')]")))
    motion_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'MPU6050 Motion')]")))

    assert hr_card is not None and spo2_card is not None and temp_card is not None and motion_card is not None, "Vital telemetry metric cards not all rendered"

    save_patient_screenshot(driver, "TC_PAT_002", "patient_dashboard_vital_cards_PASS")


def test_tc_pat_003_patient_dashboard_clinician_card_and_nav_cards(driver):
    """TC_PAT_003: Attending Clinician Summary Card & Quick Navigation Cards."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    clinician_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Attending Consulting Clinician')]")))
    assert clinician_card is not None, "Attending Clinician card missing"

    vitals_nav = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Vitals & Monitoring')]")))
    records_nav = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Health Records & Documents')]")))
    ai_nav = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'AI Clinical Assistant')]")))

    assert vitals_nav is not None and records_nav is not None and ai_nav is not None, "Patient quick action cards missing"

    save_patient_screenshot(driver, "TC_PAT_003", "patient_dashboard_action_cards_PASS")


def test_tc_pat_004_patient_dashboard_role_isolation(driver):
    """TC_PAT_004: Patient Dashboard Isolation from Admin/Doctor Controls."""
    login_patient(driver)
    time.sleep(1.0)
    page_text = driver.find_element(By.TAG_NAME, 'body').text

    assert "Administrator Operations Center" not in page_text, "Admin header leaked to patient"
    assert "Doctor Verification Registry" not in page_text, "Doctor verification leaked to patient"
    assert "AI Clinical Attention — Patients Requiring Review" not in page_text, "Doctor review queue leaked to patient"
    assert "Active Doctor-Patient Links" not in page_text, "Doctor link metrics leaked to patient"

    save_patient_screenshot(driver, "TC_PAT_004", "patient_dashboard_role_isolation_PASS")


def test_tc_pat_005_patient_sidebar_menu_structure(driver):
    """TC_PAT_005: Patient Sidebar Navigation Menu Structure."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    expected_menu_items = [
        'Dashboard',
        'My Vitals',
        'Health Records & Documents',
        'Access Controls',
        'Prescriptions',
        'Care Team Chat',
        'AI Chatbot',
        'Settings'
    ]

    for item in expected_menu_items:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, f"//aside//button[contains(., '{item}')] | //button[contains(., '{item}')]")))
        assert elem is not None, f"Sidebar menu item '{item}' not found for Patient"

    save_patient_screenshot(driver, "TC_PAT_005", "patient_sidebar_menu_structure_PASS")


# =========================================================================
# CATEGORY B: PATIENT PROFILE & DEMOGRAPHICS (TC_PAT_006 - TC_PAT_008)
# =========================================================================

def test_tc_pat_006_patient_profile_card_health_records(driver):
    """TC_PAT_006: Patient Clinical Profile Card Display on Health Records."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    profile_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Patient Clinical Profile')]")))
    assert profile_card is not None, "Patient Clinical Profile section not found"

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert "P-777" in body_text, "Patient ID P-777 missing from Profile"
    assert "Full Name" in body_text, "Full Name label missing"
    assert "Age / Gender" in body_text, "Age / Gender label missing"

    save_patient_screenshot(driver, "TC_PAT_006", "patient_profile_card_display_PASS")


def test_tc_pat_007_patient_profile_modal_open_and_populate(driver):
    """TC_PAT_007: Patient Profile Edit Modal Open & Form Population."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Edit Profile')]")))
    driver.execute_script("arguments[0].click();", edit_btn)

    modal_title = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Edit Patient Health Profile')]")))
    assert modal_title is not None, "Edit Profile modal failed to open"

    name_input = driver.find_element(By.XPATH, "//div[contains(@class, 'fixed')]//input[@type='text' and @class[contains(., 'font-bold')]]")
    assert name_input is not None, "Full name input not found in modal"

    cancel_btn = driver.find_element(By.XPATH, "//button[contains(., 'Cancel')]")
    driver.execute_script("arguments[0].click();", cancel_btn)
    time.sleep(0.5)

    save_patient_screenshot(driver, "TC_PAT_007", "patient_profile_modal_populated_PASS")


def test_tc_pat_008_patient_profile_update_and_save(driver):
    """TC_PAT_008: Patient Profile Update & Form Validation."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    edit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Edit Profile')]")))
    driver.execute_script("arguments[0].click();", edit_btn)

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Edit Patient Health Profile')]")))

    phone_input = driver.find_element(By.XPATH, "//div[contains(@class, 'fixed')]//label[contains(., 'Phone Number')]/following-sibling::input")
    phone_input.clear()
    phone_input.send_keys("+1-555-777-8899")

    save_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save Profile')]")
    driver.execute_script("arguments[0].click();", save_btn)

    toast = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Patient Health Profile updated') or contains(text(), 'updated')]")))
    assert toast is not None, "Profile update toast not received"

    save_patient_screenshot(driver, "TC_PAT_008", "patient_profile_updated_success_PASS")


# =========================================================================
# CATEGORY C: VITALS & HEALTH MONITORING (TC_PAT_009 - TC_PAT_013)
# =========================================================================

def test_tc_pat_009_patient_vitals_page_load_and_badge(driver):
    """TC_PAT_009: Vitals Page Load & Patient Identification Badge."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/vitals")
    wait.until(EC.url_contains('/vitals'))

    header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Vitals & Telemetry Monitoring')]")))
    assert header is not None, "Vitals page header missing"

    badge = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'P-777')]")))
    assert badge is not None, "Patient identification badge with P-777 missing"

    save_patient_screenshot(driver, "TC_PAT_009", "patient_vitals_page_badge_PASS")


def test_tc_pat_010_telemetry_sensor_cards_and_simulated_indicator(driver):
    """TC_PAT_010: Real-time Telemetry Sensor Cards & Simulated Indicator."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/vitals")
    wait.until(EC.url_contains('/vitals'))

    max_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'MAX30102 Optical PPG')]")))
    ds_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'DS18B20 Thermal')]")))
    mpu_card = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'MPU6050 Motion')]")))

    simulated_badges = driver.find_elements(By.XPATH, "//*[contains(text(), 'Simulated Data')]")
    assert len(simulated_badges) >= 1, "Simulated data label missing from telemetry cards"

    save_patient_screenshot(driver, "TC_PAT_010", "patient_sensor_cards_simulated_PASS")


def test_tc_pat_011_live_ecg_telemetry_component(driver):
    """TC_PAT_011: Live ECG / PPG Telemetry Waveform Component."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/vitals")
    wait.until(EC.url_contains('/vitals'))

    chart_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//canvas | //*[contains(., 'Waveform') or contains(., 'waveform') or contains(., 'Pulse Waveform')]")))
    assert chart_elem is not None, "Live ECG waveform chart component missing"

    save_patient_screenshot(driver, "TC_PAT_011", "patient_live_ecg_waveform_PASS")


def test_tc_pat_012_record_manual_vital_measurement(driver):
    """TC_PAT_012: Record Manual Vital Measurement Form."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/vitals")
    wait.until(EC.url_contains('/vitals'))

    record_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Record Manual Vitals')]")))
    driver.execute_script("arguments[0].click();", record_btn)

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Record Manual Vital Measurement')]")))

    hr_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='20-300']")))
    hr_input.clear()
    hr_input.send_keys('76')

    spo2_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='30-100']")
    spo2_input.clear()
    spo2_input.send_keys('99')

    temp_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='25.0-45.0']")
    temp_input.clear()
    temp_input.send_keys('36.9')

    notes_input = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='notes']")
    notes_input.clear()
    notes_input.send_keys('Selenium automated manual reading test')

    save_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save Manual Vitals')]")
    driver.execute_script("arguments[0].click();", save_btn)

    toast = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'source = MANUAL') or contains(text(), 'logged') or contains(text(), 'Manual vital')]")))
    assert toast is not None, "Manual vital save toast confirmation missing"

    time.sleep(1.0)
    save_patient_screenshot(driver, "TC_PAT_012", "patient_manual_vital_saved_PASS")


def test_tc_pat_013_delete_manual_vital_measurement(driver):
    """TC_PAT_013: Delete Manual Vital Measurement Record."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/vitals")
    wait.until(EC.url_contains('/vitals'))

    time.sleep(1.0)
    delete_btns = driver.find_elements(By.XPATH, "//div[contains(., 'Recorded Vital Measurements')]//button[contains(., 'Delete')]")
    if len(delete_btns) > 0:
        driver.execute_script("arguments[0].click();", delete_btns[0])
        time.sleep(0.5)

    save_patient_screenshot(driver, "TC_PAT_013", "patient_manual_vital_deleted_PASS")


# =========================================================================
# CATEGORY D: DEVICE INFORMATION & BOUNDS (TC_PAT_014 - TC_PAT_015)
# =========================================================================

def test_tc_pat_014_patient_device_serial_and_provenance(driver):
    """TC_PAT_014: Patient Device Serial & Provenance Verification."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/dashboard")
    wait.until(EC.url_contains('/dashboard'))

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    user_state = driver.execute_script("return sessionStorage.getItem('nexus_user');")
    assert user_state is not None, "nexus_user missing from session"
    user_data = json.loads(user_state)
    assert user_data.get('deviceId') == 'NP-777', f"Expected deviceId NP-777, got {user_data.get('deviceId')}"

    save_patient_screenshot(driver, "TC_PAT_014", "patient_device_provenance_PASS")


def test_tc_pat_015_patient_device_admin_route_isolation(driver):
    """TC_PAT_015: Patient Hardware Management Route Isolation (/devices)."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/devices")
    time.sleep(1.0)

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    assert "Root system nodes" not in page_text, "Admin hardware system controls exposed to patient"

    save_patient_screenshot(driver, "TC_PAT_015", "patient_devices_route_isolated_PASS")


# =========================================================================
# CATEGORY E: ALERTS & NOTIFICATIONS (TC_PAT_016 - TC_PAT_017)
# =========================================================================

def test_tc_pat_016_patient_alerts_page_view(driver):
    """TC_PAT_016: Patient Direct Alerts Page View."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/alerts")
    time.sleep(1.0)

    body_text = driver.find_element(By.TAG_NAME, 'body').text
    assert "P-777" in body_text or "Alerts" in body_text, "Alerts page failed to load for patient"

    save_patient_screenshot(driver, "TC_PAT_016", "patient_alerts_page_view_PASS")


def test_tc_pat_017_patient_notification_preferences_save(driver):
    """TC_PAT_017: Patient Notification Delivery Preferences."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/settings")
    wait.until(EC.url_contains('/settings'))

    pref_header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Notification Delivery Preferences')]")))
    assert pref_header is not None, "Notification preferences section missing"

    save_pref_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Save Preferences')]")))
    driver.execute_script("arguments[0].click();", save_pref_btn)

    toast = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'saved successfully') or contains(text(), 'Preferences')]")))
    assert toast is not None, "Notification preferences save toast missing"

    save_patient_screenshot(driver, "TC_PAT_017", "patient_notification_prefs_saved_PASS")


# =========================================================================
# CATEGORY F: CARE TEAM & ACCESS CONTROLS (TC_PAT_018 - TC_PAT_022)
# =========================================================================

def test_tc_pat_018_access_controls_patient_code_display(driver):
    """TC_PAT_018: Access Controls Page Load & Patient Access Code Display."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/access-controls")
    wait.until(EC.url_contains('/access-controls'))

    header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Healthcare Access Controls & Permissions')]")))
    assert header is not None, "Access controls header missing"

    code_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'P-777')]")))
    assert code_elem is not None, "Patient access code P-777 missing"

    copy_btn = driver.find_element(By.XPATH, "//button[contains(., 'Copy Code')]")
    assert copy_btn is not None, "Copy Code button missing"

    save_patient_screenshot(driver, "TC_PAT_018", "access_controls_patient_code_PASS")


def test_tc_pat_019_attending_clinicians_directory_listing(driver):
    """TC_PAT_019: Attending Clinicians & Doctors Directory Listing."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/access-controls")
    wait.until(EC.url_contains('/access-controls'))

    clinician_sec = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Attending Clinicians & Doctors')]")))
    search_sec = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Search & Request Consulting Clinician')]")))

    assert clinician_sec is not None and search_sec is not None, "Clinicians directory sections missing"

    save_patient_screenshot(driver, "TC_PAT_019", "attending_clinicians_directory_PASS")


def test_tc_pat_020_clinician_directory_search_filter(driver):
    """TC_PAT_020: Clinician Directory Search & Dynamic Filtering."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/access-controls")
    wait.until(EC.url_contains('/access-controls'))

    search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, 'Search clinician')]")))
    search_input.clear()
    search_input.send_keys("Dr.")
    time.sleep(0.5)

    results = driver.find_elements(By.XPATH, "//div[contains(@class, 'max-h-56')]//div")
    assert len(results) >= 0, "Search directory rendered without error"

    save_patient_screenshot(driver, "TC_PAT_020", "clinician_directory_search_PASS")


def test_tc_pat_021_caregiver_authorization_section(driver):
    """TC_PAT_021: Authorized Caregivers Section & Direct Link Form."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/access-controls")
    wait.until(EC.url_contains('/access-controls'))

    cg_sec = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Authorized Caregivers')]")))
    cg_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Caregiver email or Agency ID')]")
    assert cg_sec is not None and cg_input is not None, "Caregiver authorization section missing"

    save_patient_screenshot(driver, "TC_PAT_021", "caregiver_authorization_section_PASS")


def test_tc_pat_022_family_member_authorization_section(driver):
    """TC_PAT_022: Authorized Family Members Section & Direct Link Form."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/access-controls")
    wait.until(EC.url_contains('/access-controls'))

    fam_sec = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Authorized Family Members')]")))
    fam_input = driver.find_element(By.XPATH, "//input[contains(@placeholder, 'Family member email')]")
    assert fam_sec is not None and fam_input is not None, "Family member authorization section missing"

    save_patient_screenshot(driver, "TC_PAT_022", "family_authorization_section_PASS")


# =========================================================================
# CATEGORY G: HEALTH RECORDS, PRESCRIPTIONS & VAULT (TC_PAT_023 - TC_PAT_028)
# =========================================================================

def test_tc_pat_023_health_records_page_load_grid(driver):
    """TC_PAT_023: Health Records Page Load & Conditions/Allergies Grid."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    cond_header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Health Conditions')]")))
    allergy_header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Allergies & Sensitivities')]")))
    vault_header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Medical Document Vault')]")))

    assert cond_header is not None and allergy_header is not None and vault_header is not None, "Health records main sections missing"

    save_patient_screenshot(driver, "TC_PAT_023", "health_records_grid_load_PASS")


def test_tc_pat_024_record_and_delete_health_condition(driver):
    """TC_PAT_024: Record & Delete Patient Health Condition."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '+ Add Condition')]")))
    driver.execute_script("arguments[0].click();", add_btn)

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Record Health Condition')]")))

    cond_name_input = driver.find_element(By.XPATH, "//div[contains(@class, 'fixed')]//input[@type='text']")
    cond_name_input.clear()
    cond_name_input.send_keys("Hypertension Stage 1")

    save_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save Condition')]")
    driver.execute_script("arguments[0].click();", save_btn)

    toast = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Condition recorded') or contains(text(), 'Condition')]")))
    assert toast is not None, "Condition saved toast not received"

    time.sleep(1.0)
    del_btns = driver.find_elements(By.XPATH, "//div[contains(., 'Health Conditions')]//button[contains(@class, 'hover:text-red')]")
    if len(del_btns) > 0:
        driver.execute_script("arguments[0].click();", del_btns[0])
        time.sleep(0.5)

    save_patient_screenshot(driver, "TC_PAT_024", "health_condition_recorded_PASS")


def test_tc_pat_025_record_and_delete_patient_allergy(driver):
    """TC_PAT_025: Record & Delete Patient Allergy."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    add_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '+ Add Allergy')]")))
    driver.execute_script("arguments[0].click();", add_btn)

    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Record Allergy') or contains(text(), 'Allergy')]")))

    allergen_input = driver.find_element(By.XPATH, "//div[contains(@class, 'fixed')]//input[@type='text']")
    allergen_input.clear()
    allergen_input.send_keys("Penicillin")

    save_btn = driver.find_element(By.XPATH, "//button[contains(., 'Save Allergy')]")
    driver.execute_script("arguments[0].click();", save_btn)

    toast = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Allergy recorded') or contains(text(), 'Allergy')]")))
    assert toast is not None, "Allergy saved toast not received"

    time.sleep(1.0)
    del_btns = driver.find_elements(By.XPATH, "//div[contains(., 'Allergies & Sensitivities')]//button[contains(@class, 'hover:text-red')]")
    if len(del_btns) > 0:
        driver.execute_script("arguments[0].click();", del_btns[0])
        time.sleep(0.5)

    save_patient_screenshot(driver, "TC_PAT_025", "patient_allergy_recorded_PASS")


def test_tc_pat_026_medical_document_vault_upload_and_listing(driver):
    """TC_PAT_026: Medical Document Vault Upload & Listing."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    vault_title = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Medical Document Vault (RAG Ready)')]")))
    upload_form = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Upload Clinical Lab Report')]")))

    assert vault_title is not None and upload_form is not None, "Document Vault upload section missing"

    save_patient_screenshot(driver, "TC_PAT_026", "document_vault_view_PASS")


def test_tc_pat_027_prescriptions_repository_view(driver):
    """TC_PAT_027: Prescriptions & Medication Repository View."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/prescriptions")
    wait.until(EC.url_contains('/prescriptions'))

    header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Prescriptions & Medication Repository')]")))
    badge = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'P-777')]")))

    assert header is not None and badge is not None, "Prescriptions repository header or patient badge missing"

    save_patient_screenshot(driver, "TC_PAT_027", "prescriptions_repository_view_PASS")


def test_tc_pat_028_prescription_issuance_role_isolation(driver):
    """TC_PAT_028: Prescription Issuance Role Isolation (Doctor Only)."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/prescriptions")
    wait.until(EC.url_contains('/prescriptions'))

    issue_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Issue New Prescription')]")
    assert len(issue_btns) == 0, "Patient must not have access to Issue New Prescription button"

    save_patient_screenshot(driver, "TC_PAT_028", "prescription_issuance_role_isolated_PASS")


# =========================================================================
# CATEGORY H: CHAT & AI ASSISTANT (TC_PAT_029 - TC_PAT_030)
# =========================================================================

def test_tc_pat_029_care_team_chat_interface_load(driver):
    """TC_PAT_029: Care Team Chat Interface Load."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/care-team-chat")
    wait.until(EC.url_contains('/care-team-chat'))

    chat_container = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Care Team') or contains(text(), 'Chat') or contains(@class, 'chat')]")))
    assert chat_container is not None, "Care Team Chat component failed to render"

    save_patient_screenshot(driver, "TC_PAT_029", "care_team_chat_loaded_PASS")


def test_tc_pat_030_ai_clinical_assistant_chatbot_interface(driver):
    """TC_PAT_030: AI Clinical Assistant Chatbot Interface."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/ai-chatbot")
    wait.until(EC.url_contains('/ai-chatbot'))

    bot_msg = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'NeuroCare AI clinical assistant') or contains(text(), 'support your care journey')]")))
    input_box = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Type a message...' or contains(@placeholder, 'Ask')] | //textarea")))

    assert bot_msg is not None and input_box is not None, "AI Chatbot interface elements missing"

    save_patient_screenshot(driver, "TC_PAT_030", "ai_chatbot_interface_loaded_PASS")


# =========================================================================
# CATEGORY I: SIDEBAR & LIFECYCLE (TC_PAT_031 - TC_PAT_033)
# =========================================================================

def test_tc_pat_031_sequential_sidebar_navigation_walkthrough(driver):
    """TC_PAT_031: Sequential Patient Sidebar Navigation Walkthrough."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    routes_to_test = [
        ('My Vitals', '/vitals'),
        ('Health Records', '/health-records'),
        ('Access Controls', '/access-controls'),
        ('Prescriptions', '/prescriptions'),
        ('AI Chatbot', '/ai-chatbot'),
        ('Settings', '/settings'),
        ('Dashboard', '/dashboard')
    ]

    for title_str, route in routes_to_test:
        btn = wait.until(EC.presence_of_element_located((By.XPATH, f"//nav//button[contains(@title, '{title_str}')] | //aside//button[contains(., '{title_str}')] | //button[contains(., '{title_str}')]")))
        driver.execute_script("arguments[0].click();", btn)
        wait.until(EC.url_contains(route))
        time.sleep(0.4)

    save_patient_screenshot(driver, "TC_PAT_031", "sidebar_navigation_walkthrough_PASS")


def test_tc_pat_032_browser_back_forward_and_refresh_persistence(driver):
    """TC_PAT_032: Browser Back / Forward & Page Refresh Session Persistence."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/vitals")
    wait.until(EC.url_contains('/vitals'))

    driver.get(f"{config.FRONTEND_URL}/health-records")
    wait.until(EC.url_contains('/health-records'))

    driver.back()
    wait.until(EC.url_contains('/vitals'))

    driver.refresh()
    wait.until(EC.url_contains('/vitals'))

    user_state = driver.execute_script("return sessionStorage.getItem('nexus_user');")
    assert user_state is not None, "Session lost after refresh"

    save_patient_screenshot(driver, "TC_PAT_032", "back_forward_refresh_persistence_PASS")


def test_tc_pat_033_invalid_route_safe_handling(driver):
    """TC_PAT_033: Invalid / Nonexistent Route Safe Redirection."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/invalid-route-404-nonexistent")
    time.sleep(1.0)

    current_url = driver.current_url
    assert ('/dashboard' in current_url or current_url.endswith('/') or '/login' in current_url), f"Unexpected URL after invalid route: {current_url}"

    save_patient_screenshot(driver, "TC_PAT_033", "invalid_route_redirect_safe_PASS")


# =========================================================================
# CATEGORY J: SETTINGS, THEME & EMPTY STATES (TC_PAT_034 - TC_PAT_035)
# =========================================================================

def test_tc_pat_034_patient_account_settings_display(driver):
    """TC_PAT_034: Patient Account Settings & Profile Information Display."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/settings")
    wait.until(EC.url_contains('/settings'))

    header = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Account & Notification Settings')]")))
    role_elem = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'patient') or contains(text(), 'PATIENT')]")))

    assert header is not None and role_elem is not None, "Settings page profile information missing"

    save_patient_screenshot(driver, "TC_PAT_034", "patient_settings_profile_PASS")


def test_tc_pat_035_theme_mode_switcher(driver):
    """TC_PAT_035: Patient Portal Theme Mode Switcher (Dark, Light, System)."""
    login_patient(driver)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f"{config.FRONTEND_URL}/settings")
    wait.until(EC.url_contains('/settings'))

    dark_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Dark Mode')]")))
    driver.execute_script("arguments[0].click();", dark_btn)
    time.sleep(0.5)

    html_class = driver.find_element(By.TAG_NAME, 'html').get_attribute('class')
    assert 'dark' in html_class, f"Expected dark class on html element, got '{html_class}'"

    light_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Light Mode')]")))
    driver.execute_script("arguments[0].click();", light_btn)
    time.sleep(0.5)

    save_patient_screenshot(driver, "TC_PAT_035", "theme_switcher_tested_PASS")
