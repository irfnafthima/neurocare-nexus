import time
import random
import threading
from decimal import Decimal
from typing import Dict, List, Optional, Callable, Any
from django.utils import timezone

from monitoring.telemetry_packet import TelemetryPacket
from monitoring.telemetry_service import process_telemetry
from patients.models import Patient


class PatientSimulationState:
    """
    Maintains in-memory simulation state for a single patient.
    Ensures temporal continuity via bounded random-walk variations around
    patient-specific baselines.
    """

    def __init__(self, patient_id: str, baseline_hr: Optional[int] = None,
                 baseline_spo2: Optional[int] = None,
                 baseline_temp: Optional[Decimal] = None):
        self.patient_id = patient_id

        # Deterministic seed offset based on patient identifier for reproducible baselines
        seed_hash = sum(ord(c) for c in str(patient_id))
        rng = random.Random(seed_hash)

        # 1. Patient-Specific Synthetic Baseline
        self.baseline_hr = baseline_hr or rng.randint(68, 78)
        self.baseline_spo2 = baseline_spo2 or rng.randint(97, 99)
        self.baseline_temp = baseline_temp or Decimal(str(round(rng.uniform(36.5, 37.0), 2)))

        # 2. Current dynamic physiological states
        self.current_hr = self.baseline_hr
        self.current_spo2 = self.baseline_spo2
        self.current_temp = self.baseline_temp

        # 3. Dynamic Motion / Postural States (Resting / Normal activity)
        self.current_accel_x = Decimal(str(round(rng.uniform(0.01, 0.08), 2)))
        self.current_accel_y = Decimal(str(round(rng.uniform(0.95, 1.02), 2)))
        self.current_accel_z = Decimal(str(round(rng.uniform(0.02, 0.09), 2)))
        self.current_gyro_x = Decimal(str(round(rng.uniform(-0.50, 0.50), 2)))
        self.current_gyro_y = Decimal(str(round(rng.uniform(-1.00, 1.00), 2)))
        self.current_gyro_z = Decimal(str(round(rng.uniform(-0.50, 0.50), 2)))

        # 4. Device / Signal Health
        self.device_id = f"SIM-NCN-{patient_id}"
        self.battery_pct = rng.randint(85, 100)
        self.rssi = rng.randint(-65, -45)
        self.device_connected = True
        self.fall_detected = False
        self.emergency_pressed = False
        self.signal_quality = "GOOD"

        # 5. Scenario & Lifecycle
        self.scenario = "NORMAL"
        self.simulation_started_at = timezone.now()
        self.last_packet_at = None
        self.packet_count = 0

    def next_packet(self) -> TelemetryPacket:
        """
        Advances the simulation state by one step and returns a TelemetryPacket.
        Enforces small bounded variation (Markovian walk) centered on baseline.
        """
        self.packet_count += 1
        now = timezone.now()
        self.last_packet_at = now

        if self.scenario == "NORMAL":
            # --- Heart Rate Transition: delta in {-1, 0, +1} with bounded pull to baseline ---
            hr_delta = random.choice([-1, 0, 1])
            # Gentle mean-reversion if drift exceeds 4 bpm from baseline
            if self.current_hr > self.baseline_hr + 3:
                hr_delta = -1
            elif self.current_hr < self.baseline_hr - 3:
                hr_delta = 1
            self.current_hr = max(55, min(95, self.current_hr + hr_delta))

            # --- SpO2 Transition: delta in {-1, 0, +1} bounded [96, 100] ---
            spo2_delta = random.choice([-1, 0, 0, 1])
            if self.current_spo2 > self.baseline_spo2:
                spo2_delta = -1
            elif self.current_spo2 < 96:
                spo2_delta = 1
            self.current_spo2 = max(96, min(100, self.current_spo2 + spo2_delta))

            # --- Temperature Transition: slow drift delta in {-0.02, 0.00, +0.02} ---
            temp_delta = Decimal(str(random.choice([-0.02, 0.00, 0.00, 0.02])))
            if self.current_temp > self.baseline_temp + Decimal("0.30"):
                temp_delta = Decimal("-0.02")
            elif self.current_temp < self.baseline_temp - Decimal("0.30"):
                temp_delta = Decimal("0.02")
            self.current_temp = (self.current_temp + temp_delta).quantize(Decimal("0.01"))

            # --- Motion: small resting tremors/adjustments ---
            self.current_accel_x = Decimal(str(round(random.uniform(0.01, 0.09), 2)))
            self.current_accel_y = Decimal(str(round(random.uniform(0.94, 1.03), 2)))
            self.current_accel_z = Decimal(str(round(random.uniform(0.02, 0.08), 2)))
            self.current_gyro_x = Decimal(str(round(random.uniform(-0.40, 0.40), 2)))
            self.current_gyro_y = Decimal(str(round(random.uniform(-0.80, 0.80), 2)))
            self.current_gyro_z = Decimal(str(round(random.uniform(-0.40, 0.40), 2)))

            # --- Wi-Fi & Battery Status ---
            if self.packet_count % 30 == 0 and self.battery_pct > 10:
                self.battery_pct -= 1
            self.rssi = max(-85, min(-40, self.rssi + random.choice([-2, -1, 0, 1, 2])))
            self.fall_detected = False
            self.emergency_pressed = False
            self.signal_quality = "GOOD"

        return TelemetryPacket(
            patient_id=self.patient_id,
            device_id=self.device_id,
            source="SIMULATED",
            timestamp=now,
            heart_rate=self.current_hr,
            spo2=self.current_spo2,
            temperature=self.current_temp,
            accel_x=self.current_accel_x,
            accel_y=self.current_accel_y,
            accel_z=self.current_accel_z,
            gyro_x=self.current_gyro_x,
            gyro_y=self.current_gyro_y,
            gyro_z=self.current_gyro_z,
            fall_detected=self.fall_detected,
            signal_quality=self.signal_quality,
            esp32_connected=self.device_connected,
            esp32_battery=self.battery_pct,
            esp32_rssi=self.rssi,
            emergency_pressed=self.emergency_pressed,
            risk_score=0,
            status_state="Normal",
            audit_action="Continuous Simulated Telemetry Stream",
            user_name="Continuous Telemetry Engine"
        )


class RealTimeTelemetrySimulator:
    """
    Multi-patient telemetry simulation coordinator.
    Manages continuous generation lifecycle (START, RUNNING, STOP, STOPPED).
    """

    def __init__(self, patient_ids: Optional[List[str]] = None,
                 interval_seconds: float = 2.0,
                 duration_seconds: Optional[int] = None,
                 persist: bool = True,
                 on_packet_callback: Optional[Callable[[TelemetryPacket, Any, list], None]] = None):
        self.patient_ids = patient_ids or []
        self.interval_seconds = interval_seconds
        self.duration_seconds = duration_seconds
        self.persist = persist
        self.on_packet_callback = on_packet_callback

        self.patient_states: Dict[str, PatientSimulationState] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.state: str = "STOPPED"  # STOPPED | RUNNING | STOPPING

        self.total_packets_emitted = 0
        self.total_alerts_emitted = 0

        # Initialize patient states
        for pid in self.patient_ids:
            self.patient_states[pid] = PatientSimulationState(patient_id=pid)

    def add_patient(self, patient_id: str) -> PatientSimulationState:
        if patient_id not in self.patient_states:
            self.patient_states[patient_id] = PatientSimulationState(patient_id=patient_id)
            if patient_id not in self.patient_ids:
                self.patient_ids.append(patient_id)
        return self.patient_states[patient_id]

    def start(self, async_mode: bool = True):
        """Starts continuous simulation."""
        if self.state == "RUNNING":
            return

        if not self.patient_states and not self.patient_ids:
            # Resolve active patients from database if none specified
            db_patients = list(Patient.objects.all().values_list('id', flat=True)[:5])
            for pid in db_patients:
                self.add_patient(str(pid))

        self._stop_event.clear()
        self.state = "RUNNING"

        if async_mode:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        else:
            self._run_loop()

    def stop(self, wait: bool = True):
        """Gracefully stops continuous simulation."""
        self.state = "STOPPING"
        self._stop_event.set()
        if wait and self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval_seconds * 2 + 1.0)
        self.state = "STOPPED"

    def _run_loop(self):
        start_time = time.time()

        try:
            while not self._stop_event.is_set():
                loop_start = time.time()

                # Check duration limit
                if self.duration_seconds and (loop_start - start_time) >= self.duration_seconds:
                    break

                for pid, pstate in list(self.patient_states.items()):
                    if self._stop_event.is_set():
                        break

                    packet = pstate.next_packet()
                    reading = None
                    alerts = []

                    if self.persist:
                        try:
                            reading, alerts = process_telemetry(packet)
                            self.total_alerts_emitted += len(alerts)
                        except Exception as e:
                            # Log exception without crashing the simulation loop
                            print(f"[Simulator Error] Patient {pid}: {e}")

                    self.total_packets_emitted += 1

                    if self.on_packet_callback:
                        try:
                            self.on_packet_callback(packet, reading, alerts)
                        except Exception as e:
                            print(f"[Simulator Callback Error]: {e}")

                # Sleep remainder of interval
                elapsed = time.time() - loop_start
                sleep_time = max(0.05, self.interval_seconds - elapsed)
                self._stop_event.wait(timeout=sleep_time)

        finally:
            self.state = "STOPPED"
