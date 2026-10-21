from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from patients.models import Patient
from accounts.models import CustomUser
from devices.models import WearableDevice, DeviceAssignment
from monitoring.models import SensorReading
from alerts.models import Alert


class PhysicalDeviceTelemetryIngestionTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Test Patient
        self.patient = Patient.objects.create(
            id="P-ESP-101",
            name="Physical Test Patient",
            age=48,
            gender="Male",
            room="ICU-101",
            risk=15,
            status="Normal"
        )

        # 2. Patient B for anti-spoofing tests
        self.patient_b = Patient.objects.create(
            id="P-ESP-102",
            name="Second Test Patient",
            age=62,
            gender="Female",
            room="ICU-102",
            risk=20,
            status="Normal"
        )

        # 3. Registered Wearable Device
        self.device = WearableDevice.objects.create(
            serial="NCN-ESP32-001",
            mac="24:6F:28:AB:CD:EF",
            name="NeuroCare Physical Node 1",
            device_type="ESP32_WEARABLE",
            status="Active"
        )
        self.raw_key = "secret_esp32_device_key_2026"
        self.device.set_device_key(self.raw_key)
        self.device.save()

        # 4. Device Assignment to Patient
        self.assignment = DeviceAssignment.objects.create(
            patient=self.patient,
            device=self.device
        )

        # 5. Inactive Device for security testing
        self.inactive_device = WearableDevice.objects.create(
            serial="NCN-ESP32-INACTIVE",
            mac="24:6F:28:00:11:22",
            name="Decommissioned Node",
            device_type="ESP32_WEARABLE",
            status="Decommissioned"
        )
        self.inactive_device.set_device_key(self.raw_key)
        self.inactive_device.save()
        DeviceAssignment.objects.create(
            patient=self.patient_b,
            device=self.inactive_device
        )

        # 6. Unassigned Device for testing
        self.unassigned_device = WearableDevice.objects.create(
            serial="NCN-ESP32-UNASSIGNED",
            mac="24:6F:28:99:88:77",
            name="Unassigned Node",
            device_type="ESP32_WEARABLE",
            status="Active"
        )
        self.unassigned_device.set_device_key(self.raw_key)
        self.unassigned_device.save()

    def test_valid_physical_telemetry_ingestion(self):
        """Valid packet from registered ESP32 creates SensorReading and updates device last_seen_at."""
        payload = {
            "patient_id": "P-ESP-101",
            "heart_rate": 74,
            "spo2": 98,
            "temperature": 36.75,
            "accel_x": 0.05,
            "accel_y": 0.98,
            "accel_z": 0.04,
            "gyro_x": 0.50,
            "gyro_y": -1.20,
            "gyro_z": 0.30,
            "fall_detected": False,
            "signal_quality": "GOOD",
            "esp32_connected": True,
            "esp32_battery": 95,
            "esp32_rssi": -58
        }

        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'success')
        self.assertEqual(res_data['device_id'], self.device.serial)
        self.assertEqual(res_data['patient_id'], self.patient.id)

        # Verify SensorReading persistence
        reading = SensorReading.objects.get(id=res_data['reading_id'])
        self.assertEqual(reading.patient, self.patient)
        self.assertEqual(reading.heart_rate, 74)
        self.assertEqual(reading.spo2, 98)
        self.assertEqual(reading.temperature, Decimal("36.75"))
        self.assertEqual(reading.esp32_connected, True)
        self.assertEqual(reading.esp32_battery, 95)
        self.assertEqual(reading.esp32_rssi, -58)

        # Verify device last_seen_at updated
        self.device.refresh_from_db()
        self.assertIsNotNone(self.device.last_seen_at)

    def test_missing_device_headers_rejected(self):
        """Request without X-Device-ID or X-Device-Key is rejected with 401 Unauthorized."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={"heart_rate": 72},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Missing X-Device-ID", response.json()['error'])

    def test_invalid_device_key_rejected(self):
        """Request with incorrect device key is rejected with 401 Unauthorized."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={"heart_rate": 72},
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY="wrong_password_key"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Invalid device credentials", response.json()['error'])

    def test_unregistered_device_rejected(self):
        """Unknown device serial is rejected with 401 Unauthorized."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={"heart_rate": 72},
            format='json',
            HTTP_X_DEVICE_ID="NCN-UNKNOWN-999",
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_device_rejected(self):
        """Decommissioned / inactive device is rejected with 403 Forbidden."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={"heart_rate": 72},
            format='json',
            HTTP_X_DEVICE_ID=self.inactive_device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("inactive or decommissioned", response.json()['error'])

    def test_unassigned_device_rejected(self):
        """Device not linked to any patient is rejected with 403 Forbidden."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={"heart_rate": 72},
            format='json',
            HTTP_X_DEVICE_ID=self.unassigned_device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not assigned to an active patient", response.json()['error'])

    def test_anti_spoofing_patient_mismatch(self):
        """Device attempting to transmit for a patient other than its assigned patient is blocked."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={
                "patient_id": "P-ESP-102",  # Attempting to spoof patient B
                "heart_rate": 80
            },
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not authorized for patient", response.json()['error'])

    def test_invalid_numeric_values_rejected(self):
        """Malformed non-numeric vitals return 400 Bad Request."""
        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data={
                "heart_rate": "NOT_A_NUMBER",
                "spo2": 98
            },
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid numeric value", response.json()['error'])

    def test_critical_anomaly_triggers_alert(self):
        """Severe SpO2 dip in physical packet triggers existing Alert and notification generation."""
        alerts_before = Alert.objects.count()

        payload = {
            "heart_rate": 75,
            "spo2": 86,  # Critical Hypoxemia (< 90%)
            "temperature": 36.80
        }

        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(Alert.objects.count(), alerts_before)

        latest_alert = Alert.objects.filter(patient=self.patient).order_by('-timestamp').first()
        self.assertEqual(latest_alert.type, 'SpO2')
        self.assertEqual(latest_alert.severity, 'CRITICAL')

    def test_fall_detected_anomaly(self):
        """Postural fall in physical packet triggers Fall Alert."""
        payload = {
            "heart_rate": 72,
            "spo2": 98,
            "fall_detected": True
        }

        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fall_alert = Alert.objects.filter(patient=self.patient, type='Fall').first()
        self.assertIsNotNone(fall_alert)
        self.assertEqual(fall_alert.severity, 'CRITICAL')

    def test_emergency_distress_button(self):
        """Emergency button in physical packet triggers Emergency Alert."""
        payload = {
            "heart_rate": 72,
            "spo2": 98,
            "emergency_pressed": True
        }

        response = self.client.post(
            '/api/monitoring/device-telemetry/',
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        em_alert = Alert.objects.filter(patient=self.patient, type='Emergency').first()
        self.assertIsNotNone(em_alert)
        self.assertEqual(em_alert.severity, 'CRITICAL')

    def test_trailing_and_non_trailing_slash_support(self):
        """Endpoint works with or without trailing slash."""
        payload = {"heart_rate": 70, "spo2": 99}

        res1 = self.client.post(
            '/api/monitoring/device-telemetry',
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        res2 = self.client.post(
            '/api/monitoring/device-telemetry/',
            data=payload,
            format='json',
            HTTP_X_DEVICE_ID=self.device.serial,
            HTTP_X_DEVICE_KEY=self.raw_key
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
