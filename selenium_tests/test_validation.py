import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import save_evidence_screenshot

def test_st05_registration_live_validation(driver):
    """ST05 - REGISTRATION LIVE VALIDATION: Verify form validation and negative submission block."""
    driver.get(f'{config.FRONTEND_URL}/register')
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    # 1. Fill First and Last Name
    first_name = wait.until(EC.presence_of_element_located((By.NAME, 'firstName')))
    first_name.clear()
    first_name.send_keys('Test')

    last_name = driver.find_element(By.NAME, 'lastName')
    last_name.clear()
    last_name.send_keys('User')

    # 2. Enter Invalid Email: 'abc'
    email_input = driver.find_element(By.NAME, 'workEmail')
    email_input.clear()
    email_input.send_keys('abc')
    email_input.send_keys(Keys.TAB)

    # 3. Enter Invalid Phone: 'hdjdj267'
    phone_input = driver.find_element(By.NAME, 'phone')
    phone_input.clear()
    phone_input.send_keys('hdjdj267')
    phone_input.send_keys(Keys.TAB)

    # 4. Enter Mismatched Passwords
    pass_input = driver.find_element(By.NAME, 'password')
    pass_input.clear()
    pass_input.send_keys('ValidPassword123!')

    confirm_input = driver.find_element(By.NAME, 'confirmPassword')
    confirm_input.clear()
    confirm_input.send_keys('MismatchPassword999!')
    confirm_input.send_keys(Keys.TAB)

    time.sleep(1)

    # 5. Verify validation error messages are displayed
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    
    has_email_err = 'valid email' in body_text.lower() or 'email address is required' in body_text.lower()
    has_phone_err = 'digit' in body_text.lower() or 'mobile number' in body_text.lower()
    has_pass_err = 'match' in body_text.lower()

    assert has_email_err, f"Expected email validation error in page. Current body text snippet: {body_text[:200]}"
    assert has_phone_err, "Expected phone validation error in page"
    assert has_pass_err, "Expected password mismatch error in page"

    # 6. Click submit and verify page does NOT register/navigate away
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()
    time.sleep(1)

    assert 'register' in driver.current_url.lower(), 'Registration form should not navigate away on invalid data'
    save_evidence_screenshot(driver, 'ST05_Registration_Validation')