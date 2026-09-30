# Builder script for Patient Selenium Suite
import os
from pathlib import Path

ROOT_DIR = Path(r'E:\PROJECT NEUROCARE NEXUS')
TEST_FILE = ROOT_DIR / 'selenium_tests' / 'test_patient.py'
RUNNER_FILE = ROOT_DIR / 'selenium_tests' / 'run_patient_suite.py'
REPORT_DIR = ROOT_DIR / 'test_reports' / 'selenium' / 'patient'
SCREENSHOT_DIR = REPORT_DIR / 'screenshots'

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
print('Directories created successfully.')
