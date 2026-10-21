import json
from django.test import TestCase
from rest_framework.test import APIClient
from alerts.models import Alert
from patients.models import Patient


class PublicAlertStatusApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = Patient.objects.create(
            id="P-TEST-901",
            name="Confidential Patient Name",
            age=52,
            gender="Male",
            room="ICU-4"
        )

    def test_public_alert_status_when_active_critical_alert_exists(self):
        """Active CRITICAL alert returns status CRITICAL, correct count, and leaks NO PHI."""
        alert = Alert.objects.create(
            patient=self.patient,
            type='Heart Rate',
            severity='CRITICAL',
            message='Clinical emergency: Patient Confidential Patient Name HR reached 182 BPM AFib arrhythmia',
            status='Active',
            source='Wearable'
        )

        response = self.client.get('/api/public/alert-status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data.get('hasCriticalAlert'))
        self.assertEqual(data.get('activeCriticalAlerts'), 1)
        self.assertEqual(data.get('status'), 'CRITICAL')
        self.assertIsNotNone(data.get('timestamp'))

        # Absolute PHI / identity protection audit
        raw_text = response.content.decode('utf-8')
        self.assertNotIn("Confidential Patient Name", raw_text)
        self.assertNotIn("P-TEST-901", raw_text)
        self.assertNotIn("ICU-4", raw_text)
        self.assertNotIn("182", raw_text)
        self.assertNotIn("AFib", raw_text)
        self.assertNotIn("arrhythmia", raw_text)
        self.assertNotIn("patient", data)
        self.assertNotIn("patient_id", data)
        self.assertNotIn("patient_name", data)
        self.assertNotIn("message", data)
        self.assertNotIn("notes", data)

    def test_public_alert_status_when_no_active_critical_alerts(self):
        """When no active CRITICAL alerts exist, returns ALL SYSTEMS STABLE."""
        response = self.client.get('/api/public/alert-status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertFalse(data.get('hasCriticalAlert'))
        self.assertEqual(data.get('activeCriticalAlerts'), 0)
        self.assertEqual(data.get('status'), 'STABLE')
        self.assertIsNone(data.get('timestamp'))

    def test_resolved_critical_alert_not_counted_as_active(self):
        """Resolved CRITICAL alerts must not be reported as active on public landing page."""
        Alert.objects.create(
            patient=self.patient,
            type='SpO2',
            severity='CRITICAL',
            message='Desaturation recovered and cleared',
            status='Resolved',
            source='System'
        )

        response = self.client.get('/api/public/alert-status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertFalse(data.get('hasCriticalAlert'))
        self.assertEqual(data.get('activeCriticalAlerts'), 0)
        self.assertEqual(data.get('status'), 'STABLE')

    def test_multiple_active_critical_alerts_correct_count(self):
        """Multiple active CRITICAL alerts report exact aggregate count."""
        Alert.objects.create(patient=self.patient, type='Heart Rate', severity='CRITICAL', status='Active')
        Alert.objects.create(patient=self.patient, type='Fall', severity='CRITICAL', status='Active')
        Alert.objects.create(patient=self.patient, type='SpO2', severity='CRITICAL', status='Active')
        # Non-critical alerts should not inflate count
        Alert.objects.create(patient=self.patient, type='Temperature', severity='WARNING', status='Active')
        Alert.objects.create(patient=self.patient, type='Battery', severity='INFO', status='Active')

        response = self.client.get('/api/public/alert-status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data.get('hasCriticalAlert'))
        self.assertEqual(data.get('activeCriticalAlerts'), 3)
        self.assertEqual(data.get('status'), 'CRITICAL')

    def test_warning_and_info_alerts_do_not_trigger_critical(self):
        """Active WARNING or INFO alerts alone must not trigger CRITICAL status on landing page."""
        Alert.objects.create(patient=self.patient, type='Temperature', severity='WARNING', status='Active')
        Alert.objects.create(patient=self.patient, type='Battery', severity='INFO', status='Active')

        response = self.client.get('/api/public/alert-status')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertFalse(data.get('hasCriticalAlert'))
        self.assertEqual(data.get('activeCriticalAlerts'), 0)
        self.assertEqual(data.get('status'), 'STABLE')

    def test_unauthenticated_public_access_and_isolation(self):
        """Public endpoint is accessible unauthenticated; clinical alert API remains protected."""
        # Public status endpoint must succeed without authentication
        public_resp = self.client.get('/api/public/alert-status')
        self.assertEqual(public_resp.status_code, 200)

        # Authenticated clinical list endpoint must reject unauthenticated requests
        clinical_resp = self.client.get('/api/alerts')
        self.assertIn(clinical_resp.status_code, [401, 403])

    def test_read_only_method_enforcement(self):
        """Public status endpoint accepts only GET requests."""
        post_resp = self.client.post('/api/public/alert-status', {'fake': 'data'})
        self.assertEqual(post_resp.status_code, 405)

        delete_resp = self.client.delete('/api/public/alert-status')
        self.assertEqual(delete_resp.status_code, 405)

        put_resp = self.client.put('/api/public/alert-status', {'fake': 'data'})
        self.assertEqual(put_resp.status_code, 405)

    def test_trailing_slash_support(self):
        """Endpoint responds cleanly with or without trailing slash."""
        resp_no_slash = self.client.get('/api/public/alert-status')
        self.assertEqual(resp_no_slash.status_code, 200)

        resp_slash = self.client.get('/api/public/alert-status/')
        self.assertEqual(resp_slash.status_code, 200)
        self.assertEqual(resp_no_slash.json(), resp_slash.json())
