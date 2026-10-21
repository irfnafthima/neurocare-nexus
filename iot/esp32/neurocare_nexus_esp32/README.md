# NeuroCare Nexus — Physical ESP32 Hardware Integration Guide

This guide details the physical hardware assembly, wiring, firmware configuration, backend device registration, flashing, and end-to-end verification for the **NeuroCare Nexus ESP32 Wearable Telemetry Node**.

---

## 1. System Architecture

The physical ESP32 device integrates directly into the platform's unified clinical telemetry pipeline without modifying existing processing rules:

```
[ Physical ESP32 Node ]
   ├─ MAX30102 (PPG / HR / SpO2)
   ├─ MPU6050 (6-DOF Motion / Fall)
   ├─ DS18B20 (High-Precision Temp)
   └─ Emergency SOS Button
          │
          ▼ HTTP POST /api/monitoring/device-telemetry/
          ▼ Headers: X-Device-ID, X-Device-Key
[ Django DeviceTelemetryIngestView ]
          │ (Authenticates device key hash & verifies active patient assignment)
          ▼
   Canonical TelemetryPacket(source="REAL_DEVICE")
          │
          ▼
[ process_telemetry() Pipeline ]
          ├─ SensorReading persistence (SQLite / PostgreSQL)
          ├─ Clinical Anomaly Detection (HR, SpO2, Temp, Fall, SOS)
          ├─ Alert & Notification dispatch
          └─ Django Channels WebSocket broadcast
                 │
                 ▼
[ React Clinical Dashboards & RPMContext ]
```

---

## 2. Hardware Bill of Materials (BOM)

| Component | Specification | Purpose |
| :--- | :--- | :--- |
| **Microcontroller** | ESP32-WROOM-32 (38-pin DevKit V1) | Core processor with 2.4 GHz Wi-Fi & Dual Core 240 MHz |
| **Pulse Oximeter** | MAX30102 sensor breakout module | Photoplethysmography (PPG) Heart Rate & SpO2 estimation |
| **IMU Motion Sensor** | MPU-6050 6-Axis Accelerometer & Gyroscope | High-G impact detection, posture tilt, and fall analysis |
| **Body Temperature** | DS18B20 digital temperature probe / TO-92 | Accurate clinical body temperature measurement (±0.5°C) |
| **Pull-up Resistor** | 4.7 kΩ (Yellow-Purple-Red-Gold) | Required pull-up between DS18B20 Data line and 3.3V |
| **Emergency Button** | Tactile push button (Normally Open) | Manual SOS triggering by patient |
| **Status Feedback** | Onboard Blue LED (GPIO 2) + 5V/3.3V Active Buzzer (GPIO 18) | Audible & visual feedback for alerts and Wi-Fi status |
| **Power Supply** | Micro-USB cable connected to 5V 1A+ source / PC | Initial power source |

---

## 3. Wiring & Pinout Schematic

> [!IMPORTANT]
> The ESP32 operates at **3.3V logic**. Power all sensors from the ESP32 **3.3V pin** (do not connect 5V/VIN directly to sensor logic pins).
> The **I2C bus** is shared between the MAX30102 and MPU6050 because they use distinct I2C addresses (`0x57` and `0x68`).

### Connection Table

| Sensor / Peripheral | Sensor Pin | ESP32 Pin | Notes |
| :--- | :--- | :--- | :--- |
| **MAX30102** | VCC | `3V3` | 3.3V Power |
| | GND | `GND` | Common Ground |
| | SCL | `GPIO 22` | I2C Clock (Shared) |
| | SDA | `GPIO 21` | I2C Data (Shared) |
| | INT | *Unconnected* | Optional |
| **MPU-6050** | VCC | `3V3` | 3.3V Power |
| | GND | `GND` | Common Ground |
| | SCL | `GPIO 22` | I2C Clock (Shared) |
| | SDA | `GPIO 21` | I2C Data (Shared) |
| | AD0 | `GND` | Sets I2C Address to `0x68` |
| **DS18B20** | VDD (Red) | `3V3` | 3.3V Power |
| | GND (Black) | `GND` | Common Ground |
| | DQ / Data (Yellow) | `GPIO 4` | **Connect 4.7kΩ resistor between Data and 3V3** |
| **Emergency Button** | Terminal 1 | `GPIO 15` | Internal pull-up enabled (`INPUT_PULLUP`) |
| | Terminal 2 | `GND` | Pressing pulls pin LOW |
| **Active Buzzer** | Positive (+) | `GPIO 18` | Driven active HIGH |
| | Negative (-) | `GND` | Ground |
| **Status LED** | Built-in | `GPIO 2` | Onboard LED |

---

## 4. Arduino IDE Environment Setup

### Step 1: Install ESP32 Board Support
1. In Arduino IDE, navigate to **File → Preferences**.
2. In **Additional boards manager URLs**, add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Open **Tools → Board → Boards Manager**, search for `esp32` by Espressif Systems, and click **Install** (v2.0.x or v3.0.x).
4. Under **Tools → Board → ESP32 Arduino**, select:
   - **ESP32 Dev Module** (or `NodeMCU-32S` / `DOIT ESP32 DEVKIT V1`).
   - **Upload Speed**: `921600` (or `115200` if upload fails).
   - **Flash Frequency**: `80MHz`.
   - **Port**: Select your COM port (e.g., `COM3`).

### Step 2: Install Required Libraries
Open **Tools → Manage Libraries...** (Ctrl+Shift+I) and install the following:
1. `SparkFun MAX3010x Pulse and Proximity Sensor Library` (by SparkFun)
2. `Adafruit MPU6050` (by Adafruit) — choose *Install All* to install `Adafruit Unified Sensor` and `Adafruit BusIO`
3. `OneWire` (by Paul Stoffregen)
4. `DallasTemperature` (by Miles Burton)
5. `ArduinoJson` (by Benoit Blanchon, v6.x or v7.x)

---

## 5. Backend Device Registration

Before powering the ESP32, create a registered `WearableDevice` record and assign it to a patient in Django:

```bash
cd backend
venv\Scripts\python.exe manage.py shell
```

Inside the Python interactive shell:

```python
from accounts.models import User
from devices.models import WearableDevice, DeviceAssignment

# 1. Fetch the patient user
patient = User.objects.filter(role="Patient").first()
print("Assigning to Patient:", patient.email, "(ID:", patient.id, ")")

# 2. Create or update the WearableDevice record
device, created = WearableDevice.objects.get_or_create(
    device_id="ESP32-DEV-001",
    defaults={
        "device_type": "SMARTWATCH",
        "name": "Clinical Wearable Band ESP32",
        "status": "Active"
    }
)

# 3. Set the secure hardware authentication key (e.g. "my_secure_physical_key_987")
# This stores a SHA-256 hash in device_key_hash
RAW_SECRET_KEY = "my_secure_physical_key_987"
device.set_device_key(RAW_SECRET_KEY)
device.status = "Active"
device.save()

# 4. Assign the device to the patient
assignment, _ = DeviceAssignment.objects.get_or_create(
    device=device,
    patient=patient,
    defaults={"status": "Active"}
)
assignment.status = "Active"
assignment.save()

print(f"Device {device.device_id} successfully bound to Patient {patient.id} with secret key configured.")
```

---

## 6. Configuring and Flashing Firmware

1. Navigate to the firmware directory:
   `iot/esp32/neurocare_nexus_esp32/`
2. Duplicate `config.h.example` and name it `config.h`.
3. Open `config.h` and configure:
   ```c
   #define WIFI_SSID       "YourWiFiNetworkName"
   #define WIFI_PASSWORD   "YourWiFiPassword"

   // Replace with your development PC's LAN IP:
   #define SERVER_URL      "http://192.168.1.100:8000/api/monitoring/device-telemetry/"

   #define DEVICE_ID       "ESP32-DEV-001"
   #define DEVICE_KEY      "my_secure_physical_key_987"
   ```
4. Start your Django backend bound to all local network interfaces:
   ```bash
   cd backend
   venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
   ```
5. In Arduino IDE, open `neurocare_nexus_esp32.ino`.
6. Select your COM port, and click **Upload** (Ctrl+U).
   *(If the upload hangs on `Connecting........_____.....`, press and hold the **BOOT** button on the ESP32 until the upload begins).*

---

## 7. Verification & Live Pipeline Testing

### 1. Serial Monitor (115200 Baud)
Open **Tools → Serial Monitor** at `115200` baud. Successful boot and transmission output looks like:

```text
==================================================
  NEUROCARE NEXUS — ESP32 TELEMETRY FIRMWARE
==================================================
Device ID: ESP32-DEV-001
[I2C] Initializing Wire bus on SDA=21, SCL=22...
[MAX30102] Connecting... SUCCESS (Address 0x57)
[MPU6050] Connecting... SUCCESS (Address 0x68)
[DS18B20] Connecting on GPIO 4... SUCCESS (Found 1 sensor(s))
[WiFi] Connecting to SSID: HomeNet-2.4G
....
[WiFi] Connected! IP Address: 192.168.1.145
[SYSTEM] Setup completed. Entering telemetry loop.

[HTTP POST] Code: 201 [SUCCESS] Payload: {"device_id":"ESP32-DEV-001","heart_rate":74.2,"spo2":98.0,"temperature":36.7,"fall_detected":false,"emergency_button":false,"signal_quality":"GOOD",...}
```

### 2. Live Frontend Dashboard Observation
1. Login to the NeuroCare Nexus portal as the assigned patient or their attending clinician.
2. Navigate to **Vitals & RPM Live Monitoring**.
3. Place a finger on the MAX30102 optical lens:
   - Observe Heart Rate and SpO2 updating live via WebSocket.
   - When the finger is removed, `signal_quality: "INVALID"` is communicated and values clear smoothly.
4. Shake or simulate an impact on the MPU6050:
   - Notice the high-priority Fall Alert banner appearing instantaneously on the dashboard.
5. Press the Emergency Push Button:
   - Notice the Critical SOS Notification triggering in real time with high-priority audio alert.

---

## 8. Troubleshooting

| Symptom | Probable Cause | Resolution |
| :--- | :--- | :--- |
| `[HTTP POST] Code: -1` | Cannot reach server / Network timeout | Ensure Django is running on `0.0.0.0:8000` (not `127.0.0.1`), check that PC and ESP32 are on the same Wi-Fi subnet, and verify Windows Firewall permits inbound connections on port 8000. |
| `[HTTP POST] Code: 401` | Authentication failure | Verify `X-Device-ID` and `DEVICE_KEY` in `config.h` exactly match the credentials passed to `device.set_device_key(RAW_KEY)` in Django. |
| `[HTTP POST] Code: 403` | Inactive or unassigned device | Confirm in Django Admin that `WearableDevice.status` is `"Active"` and that an active `DeviceAssignment` exists linking the device to a patient. |
| `[MAX30102] FAILED!` | I2C wiring issue | Check SDA=GPIO 21 and SCL=GPIO 22 connections. Ensure the module is receiving 3.3V power. |
| `[DS18B20] NO SENSORS FOUND!` | Missing pull-up resistor | The OneWire bus requires a **4.7 kΩ pull-up resistor** between the Data pin (GPIO 4) and 3.3V. |
| Optical reading values `null` | Finger detection threshold | The firmware protects against fake data by requiring `irValue > 50000` before calculating vitals. Apply gentle, flat pressure with your fingertip. |
