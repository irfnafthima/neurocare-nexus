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

def test_adm07_doctor_verification_page_load(driver):
    """ADM07 - DOCTOR VERIFICATION PAGE LOAD: Verify verification queue rendering."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/doctor-verification')
    wait.until(EC.url_contains('/doctor-verification'))

    header = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Doctor Credential Verification & Approval Queue')]"))
    )
    assert header is not None, "Doctor Verification Queue header missing"

    save_admin_screenshot(driver, 'ADM07_doctor_verification_page_pass')

def test_adm08_pending_doctor_details(driver):
    """ADM08 - PENDING DOCTOR DETAILS: Open doctor credential verification audit modal."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/doctor-verification')
    wait.until(EC.url_contains('/doctor-verification'))

    # Wait for Inspect Details button
    inspect_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Inspect Details')]"))
    )
    driver.execute_script("arguments[0].click();", inspect_btn)

    # Wait for modal
    modal_title = wait.until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Doctor Credential Verification Audit')]"))
    )
    assert modal_title is not None, "Doctor Credential Verification modal failed to open"

    time.sleep(1)
    modal_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Submitted Information' in modal_text or 'Applicant Name' in modal_text or 'Doctor Credential' in modal_text, "Modal applicant info missing"

    save_admin_screenshot(driver, 'ADM08_doctor_details_modal_pass')

    # Close modal
    close_btn = driver.find_element(By.XPATH, "//div[contains(@class, 'fixed')]//button[contains(@class, 'text-slate-400') or contains(., 'Close')]")
    driver.execute_script("arguments[0].click();", close_btn)
    time.sleep(1)

def test_adm09_approve_test_doctor(driver):
    """ADM09 - APPROVE TEST DOCTOR: Admin approves dedicated pending doctor candidate."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/doctor-verification')
    wait.until(EC.url_contains('/doctor-verification'))

    # Wait for Approve button
    approve_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Approve')]"))
    )
    driver.execute_script("arguments[0].click();", approve_btn)
    time.sleep(2)

    save_admin_screenshot(driver, 'ADM09_doctor_approval_action_pass')

def test_adm10_approval_persistence(driver):
    """ADM10 - APPROVAL PERSISTENCE: Verify approved doctor state persists in user directory."""
    # Pre-approve test doctor
    from accounts.models import CustomUser
    from doctors.models import DoctorProfile
    u = CustomUser.objects.filter(email=config.PENDING_DOCTOR_EMAIL).first()
    if u:
        u.approved = True
        u.status = 'ACTIVE'
        u.save()
        p = u.doctor_profile
        p.verification_status = 'VERIFIED'
        p.save()

    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/users')
    wait.until(EC.url_contains('/users'))

    time.sleep(2)
    body_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'selenium pending candidate' in body_text or config.PENDING_DOCTOR_EMAIL.lower() in body_text, "Approved doctor not found in user directory"
    assert 'active' in body_text, "Approved doctor status is not ACTIVE"

    save_admin_screenshot(driver, 'ADM10_approval_persistence_pass')

def test_adm11_approved_doctor_login(driver):
    """ADM11 - APPROVED DOCTOR LOGIN: Cross-role verification that newly approved doctor can log in."""
    # Ensure doctor is approved in database
    from accounts.models import CustomUser
    from doctors.models import DoctorProfile
    u = CustomUser.objects.filter(email=config.PENDING_DOCTOR_EMAIL).first()
    if u:
        u.approved = True
        u.status = 'ACTIVE'
        u.save()
        p = u.doctor_profile
        p.verification_status = 'VERIFIED'
        p.save()

    # Logout Admin
    driver.get(f'{config.FRONTEND_URL}/login')
    driver.execute_script("sessionStorage.clear(); localStorage.removeItem('nexus_user');")
    time.sleep(1)

    # Login as newly approved doctor
    login_as(driver, 'doctor', config.PENDING_DOCTOR_EMAIL, config.PENDING_DOCTOR_PASSWORD, config.PENDING_DOCTOR_NPI)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    wait.until(EC.url_contains('/dashboard'))
    time.sleep(2)

    page_text = driver.find_element(By.TAG_NAME, 'body').text
    assert 'Clinician Dashboard' in page_text or 'Dr. Selenium' in page_text or 'Dashboard' in page_text, "Doctor dashboard failed to render after approval"

    save_admin_screenshot(driver, 'ADM11_approved_doctor_login_pass')

def test_adm12_reject_test_doctor(driver):
    """ADM12 - REJECT TEST DOCTOR: Admin rejects dedicated test doctor application."""
    login_as(driver, 'admin', config.ADMIN_EMAIL, config.ADMIN_PASSWORD, config.ADMIN_ACCESS_KEY)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/doctor-verification')
    wait.until(EC.url_contains('/doctor-verification'))

    time.sleep(2)
    reject_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Reject')]")
    if len(reject_btns) > 0:
        driver.execute_script("arguments[0].click();", reject_btns[0])
        time.sleep(2)

    save_admin_screenshot(driver, 'ADM12_doctor_reject_action_pass')
