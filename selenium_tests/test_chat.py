import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_tests import config
from selenium_tests.conftest import login_as, save_evidence_screenshot

def test_st13_care_team_chat(driver):
    """ST13 (OPTIONAL) - CARE TEAM CHAT: Verify communication interface loading."""
    login_as(driver, 'patient', config.PATIENT_EMAIL, config.PATIENT_PASSWORD, config.PATIENT_DEVICE_ID)
    wait = WebDriverWait(driver, config.EXPLICIT_WAIT)

    driver.get(f'{config.FRONTEND_URL}/care-team-chat')
    wait.until(EC.url_contains('/care-team-chat'))

    time.sleep(2)
    page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
    assert 'clinical notice' in page_text or 'channels' in page_text or 'chat' in page_text or 'care team' in page_text or 'care-team' in page_text, "Chat interface failed to render"

    save_evidence_screenshot(driver, 'ST13_Care_Team_Chat')