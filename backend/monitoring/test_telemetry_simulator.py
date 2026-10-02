from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import CustomUser, AuditLog
from patients.models import Patient
from alerts.models import Alert
from monitoring.models import SensorReading
from monitoring.telemetry_packet import TelemetryPacket
from monitoring.telemetry_service import process_telemetry, evaluate_telemetry_anomalies
from monitoring.telemetry_simulator import PatientSimulationState, RealTimeTelemetrySimulator


class TelemetryPacketAndServiceTest(TestCase):
    def setUp(self):
        self.patient = Patient.objects.create(
            id="P-TEST-501",
            name="Stage 5.2 Test Patient",
            age=45,
            gender="Female"
        )
        self.user = CustomUser.objects.create_user(
            email="sim_doctor@example.com",
            password="DocPassword@123",
            full_name="Dr. Sim Doctor",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )

    def test_packet_creation_and_dict_conversion(self):
        """TelemetryPacket instantiates with canonical defaults and serializes cleanly."""
        packet = TelemetryPacket(
            patient_id=self.patient.id,
            heart_rate=72,
            spo2=98,
            temperature=Decimal("36.75")
        )
        self.assertEqual(packet.patient_id, "P-TEST-501")
        self.assertEqual(packet.source, "SIMULATED")
        self.assertEqual(packet.signal_quality, "GOOD")
        self.assertEqual(packet.esp32_battery, 100)

        p_dict = packet.to_dict()
        self.assertEqual(p_dict['patient_id'], "P-TEST-501")
        self.assertEqual(p_dict['heart_rate'], 72)
        self.assertEqual(p_dict['spo2'], 98)
        self.assertEqual(p_dict['temperature'], 36.75)

    def test_normal_packet_process_telemetry_persists_and_no_alert(self):
        """Processing a normal telemetry packet persists SensorReading and produces 0 alerts."""
        alerts_before = Alert.objects.count()
        readings_before = SensorReading.objects.count()

        packet = TelemetryPacket(
            patient_id=self.patient.id,
            heart_rate=74,
            spo2=98,
            temperature=Decimal("36.80"),
            fall_detected=False,
            emergency_pressed=False
        )
        reading, alerts = process_telemetry(packet)

        self.assertIsNotNone(reading.id)
        self.assertEqual(reading.heart_rate, 74)
        self.assertEqual(reading.spo2, 98)
        self.assertEqual(reading.temperature, Decimal("36.80"))
        self.assertEqual(len(alerts), 0)
        self.assertEqual(Alert.objects.count(), alerts_before)
        self.assertEqual(SensorReading.objects.count(), readings_before + 1)

    def test_critical_anomaly_evaluation_generates_alert(self):
        """Anomaly thresholds correctly generate CRITICAL and WARNING alerts."""
        # 1. Critical High HR (135 bpm)
        crit_packet = TelemetryPacket(
            patient_id=self.patient.id,
            heart_rate=135,
            spo2=98,
            temperature=Decimal("36.80")
        )
        reading, alerts = process_telemetry(crit_packet)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, 'Heart Rate')
        self.assertEqual(alerts[0].severity, 'CRITICAL')

        # 2. Oxygen Saturation Dip (88% -> CRITICAL)
        low_spo2_packet = TelemetryPacket(
            patient_id=self.patient.id,
            heart_rate=75,
            spo2=88,
            temperature=Decimal("36.80")
        )
        reading, alerts = process_telemetry(low_spo2_packet)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, 'SpO2')
        self.assertEqual(alerts[0].severity, 'CRITICAL')

        # 3. Fall Detected -> CRITICAL
        fall_packet = TelemetryPacket(
            patient_id=self.patient.id,
            heart_rate=75,
            spo2=98,
            temperature=Decimal("36.80"),
            fall_detected=True
        )
        reading, alerts = process_telemetry(fall_packet)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].type, 'Fall')
        self.assertEqual(alerts[0].severity, 'CRITICAL')

    def test_invalid_patient_raises_value_error(self):
        """Non-existent patient ID raises ValueError cleanly in process_telemetry."""
        bad_packet = TelemetryPacket(patient_id="NON_EXISTENT_ID", heart_rate=72)
        with self.assertRaises(ValueError):
            process_telemetry(bad_packet)


class StatefulSimulationAndTemporalContinuityTest(TestCase):
    def setUp(self):
        self.p1 = Patient.objects.create(id="P-SIM-001", name="Sim Alpha", age=30, gender="Female")
        self.p2 = Patient.objects.create(id="P-SIM-002", name="Sim Beta", age=65, gender="Male")

    def test_patient_specific_baseline_initialization(self):
        """Different patients initialize with independent, realistic synthetic baselines."""
        state1 = PatientSimulationState(patient_id=self.p1.id)
        state2 = PatientSimulationState(patient_id=self.p2.id)

        self.assertGreaterEqual(state1.baseline_hr, 60)
        self.assertLessEqual(state1.baseline_hr, 85)
        self.assertGreaterEqual(state1.baseline_spo2, 95)
        self.assertLessEqual(state1.baseline_spo2, 100)

        self.assertGreaterEqual(state2.baseline_hr, 60)
        self.assertLessEqual(state2.baseline_hr, 85)

    def test_temporal_continuity_in_normal_stream(self):
        """Consecutive packets exhibit bounded, Markovian transitions (no erratic jumps)."""
        state = PatientSimulationState(patient_id=self.p1.id, baseline_hr=72, baseline_spo2=98, baseline_temp=Decimal("36.70"))

        previous_hr = state.current_hr
        previous_spo2 = state.current_spo2
        previous_temp = state.current_temp

        for _ in range(20):
            packet = state.next_packet()
            # HR step variation must be bounded <= 2 bpm per step
            hr_diff = abs(packet.heart_rate - previous_hr)
            self.assertLessEqual(hr_diff, 2, f"Erratic HR step jump detected: {previous_hr} -> {packet.heart_rate}")

            # SpO2 step variation must be bounded <= 1% per step
            spo2_diff = abs(packet.spo2 - previous_spo2)
            self.assertLessEqual(spo2_diff, 1, f"Erratic SpO2 jump detected: {previous_spo2} -> {packet.spo2}")

            # Temperature step variation must be bounded <= 0.05°C per step
            temp_diff = abs(packet.temperature - previous_temp)
            self.assertLessEqual(temp_diff, Decimal("0.05"), f"Erratic Temp jump: {previous_temp} -> {packet.temperature}")

            previous_hr = packet.heart_rate
            previous_spo2 = packet.spo2
            previous_temp = packet.temperature

    def test_multi_patient_state_isolation(self):
        """Simulation states between multiple patients are strictly isolated."""
        state1 = PatientSimulationState(patient_id="P-1", baseline_hr=70)
        state2 = PatientSimulationState(patient_id="P-2", baseline_hr=80)

        pkt1 = state1.next_packet()
        pkt2 = state2.next_packet()

        self.assertEqual(pkt1.patient_id, "P-1")
        self.assertEqual(pkt2.patient_id, "P-2")
        self.assertNotEqual(pkt1.device_id, pkt2.device_id)


class SimulatorLifecycleAndDurationTest(TestCase):
    def setUp(self):
        self.p1 = Patient.objects.create(id="P-RUN-1", name="Runner One", age=50, gender="Male")
        self.p2 = Patient.objects.create(id="P-RUN-2", name="Runner Two", age=55, gender="Female")

    def test_duration_limited_simulation_execution(self):
        """Simulator runs for exact configured duration and terminates cleanly."""
        received_packets = []

        def callback(packet, reading, alerts):
            received_packets.append(packet)

        # Run 2 patients with 0.1s interval for 0.5s duration
        sim = RealTimeTelemetrySimulator(
            patient_ids=[self.p1.id, self.p2.id],
            interval_seconds=0.1,
            duration_seconds=1,
            persist=True,
            on_packet_callback=callback
        )
        sim.start(async_mode=False)

        self.assertEqual(sim.state, "STOPPED")
        self.assertGreaterEqual(len(received_packets), 4)
        self.assertGreaterEqual(SensorReading.objects.filter(patient_id__in=[self.p1.id, self.p2.id]).count(), 4)

    def test_manual_start_and_stop_lifecycle(self):
        """Simulator starts in async thread and stops cleanly on stop()."""
        sim = RealTimeTelemetrySimulator(
            patient_ids=[self.p1.id],
            interval_seconds=0.05,
            persist=False
        )
        self.assertEqual(sim.state, "STOPPED")
        sim.start(async_mode=True)
        self.assertEqual(sim.state, "RUNNING")

        sim.stop(wait=True)
        self.assertEqual(sim.state, "STOPPED")


class ExistingSimulationTriggerEndpointRegressionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = Patient.objects.create(id="P-ENDPOINT-1", name="Endpoint Test", age=40, gender="Male")
        self.doctor = CustomUser.objects.create_user(
            email="endpoint_doc@example.com",
            password="DocPassword@123",
            full_name="Dr. Endpoint",
            role="doctor",
            approved=True,
            status="ACTIVE"
        )
        self.client.force_authenticate(user=self.doctor)

    def test_existing_simulation_trigger_endpoint_still_works(self):
        """POST /api/simulation/trigger continues to work identically after service refactoring."""
        payload = {
            'patientId': self.patient.id,
            'vitals': {
                'max30102': {'heartRate': 76, 'spo2': 98},
                'ds18b20': {'temperature': 36.7},
                'mpu6050': {'accelX': 0.05, 'accelY': 0.98, 'accelZ': 0.04, 'fallDetected': False},
                'esp32': {'connected': True, 'battery': 95, 'rssi': -60}
            },
            'riskScore': 15,
            'statusState': 'Normal'
        }
        res = self.client.post('/api/simulation/trigger', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        reading = SensorReading.objects.filter(patient=self.patient).last()
        self.assertIsNotNone(reading)
        self.assertEqual(reading.heart_rate, 76)
        self.assertEqual(reading.spo2, 98)

        self.patient.refresh_from_db()
        self.assertEqual(self.patient.risk, 15)
