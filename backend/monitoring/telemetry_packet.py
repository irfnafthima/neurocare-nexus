import dataclasses
from decimal import Decimal
from typing import Optional, Dict, Any
from django.utils import timezone


@dataclasses.dataclass
class TelemetryPacket:
    patient_id: str
    device_id: str = "SIM-DEVICE"
    source: str = "SIMULATED"  # SIMULATED | REAL_DEVICE | REPLAY
    timestamp: Any = dataclasses.field(default_factory=timezone.now)

    # MAX30102
    heart_rate: Optional[int] = None
    spo2: Optional[int] = None

    # DS18B20
    temperature: Optional[Decimal] = None

    # MPU6050
    accel_x: Optional[Decimal] = Decimal("0.05")
    accel_y: Optional[Decimal] = Decimal("0.98")
    accel_z: Optional[Decimal] = Decimal("0.04")
    gyro_x: Optional[Decimal] = Decimal("0.50")
    gyro_y: Optional[Decimal] = Decimal("-1.20")
    gyro_z: Optional[Decimal] = Decimal("0.30")
    fall_detected: bool = False

    # Signal & Hardware Health
    signal_quality: str = "GOOD"  # GOOD | POOR | INVALID
    esp32_connected: bool = True
    esp32_battery: Optional[int] = 100
    esp32_rssi: Optional[int] = -55
    emergency_pressed: bool = False

    # Optional clinical scoring
    risk_score: int = 0
    status_state: str = "Normal"
    audit_action: str = "Simulated Telemetry Update"
    user_name: str = "Telemetry Simulator"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'patient_id': self.patient_id,
            'device_id': self.device_id,
            'source': self.source,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'heart_rate': self.heart_rate,
            'spo2': self.spo2,
            'temperature': float(self.temperature) if self.temperature is not None else None,
            'accel_x': float(self.accel_x) if self.accel_x is not None else None,
            'accel_y': float(self.accel_y) if self.accel_y is not None else None,
            'accel_z': float(self.accel_z) if self.accel_z is not None else None,
            'gyro_x': float(self.gyro_x) if self.gyro_x is not None else None,
            'gyro_y': float(self.gyro_y) if self.gyro_y is not None else None,
            'gyro_z': float(self.gyro_z) if self.gyro_z is not None else None,
            'fall_detected': self.fall_detected,
            'signal_quality': self.signal_quality,
            'esp32_connected': self.esp32_connected,
            'esp32_battery': self.esp32_battery,
            'esp32_rssi': self.esp32_rssi,
            'emergency_pressed': self.emergency_pressed,
            'risk_score': self.risk_score,
            'status_state': self.status_state,
        }
