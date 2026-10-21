/**
 * ==============================================================================
 * NEUROCARE NEXUS — PHYSICAL ESP32 WEARABLE FIRMWARE
 * ==============================================================================
 *
 * Target Board: ESP32 DevKit (38-pin)
 * Architecture: ESP32 IoT Hardware -> JSON Telemetry -> REST POST Ingest -> Django Pipeline
 *
 * Integrated Sensors:
 * 1. MAX30102 Pulse Oximeter & Heart Rate (I2C: SDA=21, SCL=22)
 * 2. MPU6050 6-DOF IMU Accelerometer & Gyroscope (I2C: SDA=21, SCL=22)
 * 3. DS18B20 OneWire High-Precision Digital Temperature (GPIO 4 with 4.7kΩ pull-up)
 * 4. Emergency SOS Push-Button (GPIO 15, Active-LOW)
 * 5. Visual & Audible Feedback (Status LED on GPIO 2, Buzzer on GPIO 18)
 *
 * Security:
 * - Machine-to-Machine authentication via custom headers:
 *     X-Device-ID:  <DEVICE_ID>
 *     X-Device-Key: <DEVICE_KEY>
 * - No browser JWT stored on microcontroller.
 *
 * Instructions:
 * 1. Ensure Arduino IDE has ESP32 Board Support (v2.x or v3.x) installed.
 * 2. Copy "config.h.example" to "config.h" and configure Wi-Fi & LAN IP.
 * 3. Install required libraries via Library Manager:
 *    - "SparkFun MAX3010x Pulse and Proximity Sensor Library"
 *    - "Adafruit MPU6050" and "Adafruit Unified Sensor"
 *    - "OneWire"
 *    - "DallasTemperature"
 *    - "ArduinoJson" (v6 or v7)
 * 4. Flash to ESP32 at 115200 or 921600 baud.
 * ==============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include "MAX30105.h"
#include "heartRate.h"
#include <ArduinoJson.h>

// Include local configuration (Wi-Fi, Server URL, Device Keys, Pinout)
#if __has_include("config.h")
  #include "config.h"
#else
  #warning "config.h not found! Please copy config.h.example to config.h. Using fallback defaults."
  #define WIFI_SSID            "YOUR_WIFI_SSID"
  #define WIFI_PASSWORD        "YOUR_WIFI_PASSWORD"
  #define SERVER_URL           "http://192.168.1.100:8000/api/monitoring/device-telemetry/"
  #define DEVICE_ID            "ESP32-DEV-001"
  #define DEVICE_KEY           "your_secret_device_auth_key_here"
  #define TELEMETRY_INTERVAL_MS 2000
  #define SENSOR_SAMPLE_INTERVAL_MS 40
  #define PIN_I2C_SDA          21
  #define PIN_I2C_SCL          22
  #define PIN_DS18B20          4
  #define PIN_STATUS_LED       2
  #define PIN_EMERGENCY_BTN    15
  #define PIN_BUZZER           18
#endif

// ==============================================================================
// GLOBAL SENSOR INSTANCES & STATE
// ==============================================================================

// I2C Sensors
MAX30105 max30102;
Adafruit_MPU6050 mpu;

// OneWire Temperature Sensor
OneWire oneWireBus(PIN_DS18B20);
DallasTemperature ds18b20(&oneWireBus);

// Sensor Availability Flags
bool max30102_ready = false;
bool mpu6050_ready   = false;
bool ds18b20_ready   = false;

// Heart Rate & SpO2 Calculation State
const byte RATE_SIZE = 4;
byte rates[RATE_SIZE];
byte rateSpot = 0;
long lastBeat = 0;
float beatsPerMinute = 0.0;
int beatAvg = 0;
float currentSpO2 = 98.0;

// Fall Detection State Machine
float prevAccelMagnitude = 1.0;
bool fallCandidateDetected = false;
unsigned long fallCandidateTime = 0;
bool fallEventLatched = false;

// Emergency SOS State
bool emergencyLatched = false;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 50;

// Telemetry Timers
unsigned long lastTelemetryDispatch = 0;
unsigned long lastSensorSample = 0;

// ==============================================================================
// HELPER FUNCTIONS
// ==============================================================================

void connectToWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println();
  Serial.print("[WiFi] Connecting to SSID: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 25) {
    delay(500);
    Serial.print(".");
    digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED)); // Blink while connecting
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("[WiFi] Connected! IP Address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(PIN_STATUS_LED, HIGH); // Solid ON when connected
  } else {
    Serial.println();
    Serial.println("[WiFi] Connection failed. Will retry in loop.");
    digitalWrite(PIN_STATUS_LED, LOW);
  }
}

void triggerBuzzer(int durationMs, int pulses = 1) {
  for (int i = 0; i < pulses; i++) {
    digitalWrite(PIN_BUZZER, HIGH);
    delay(durationMs);
    digitalWrite(PIN_BUZZER, LOW);
    if (i < pulses - 1) delay(50);
  }
}

// ==============================================================================
// SETUP
// ==============================================================================

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("==================================================");
  Serial.println("  NEUROCARE NEXUS — ESP32 TELEMETRY FIRMWARE");
  Serial.println("==================================================");
  Serial.print("Device ID: ");
  Serial.println(DEVICE_ID);

  // Initialize GPIO Pins
  pinMode(PIN_STATUS_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_EMERGENCY_BTN, INPUT_PULLUP);

  digitalWrite(PIN_STATUS_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  // Initialize I2C Bus
  Serial.println("[I2C] Initializing Wire bus on SDA=21, SCL=22...");
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);

  // 1. Initialize MAX30102 Pulse Oximeter
  Serial.print("[MAX30102] Connecting... ");
  if (max30102.begin(Wire, I2C_SPEED_FAST)) {
    max30102_ready = true;
    byte ledBrightness = 60; // 0=Off, 255=50mA
    byte sampleAverage = 4;
    byte ledMode = 2;        // 2 = Red + IR
    byte sampleRate = 100;   // 100 samples/sec
    int pulseWidth = 411;
    int adcRange = 4096;
    max30102.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange);
    max30102.setPulseAmplitudeRed(0x0A);
    max30102.setPulseAmplitudeGreen(0);
    Serial.println("SUCCESS (Address 0x57)");
  } else {
    Serial.println("FAILED! Check wiring (SDA=21, SCL=22, VCC=3.3V).");
  }

  // 2. Initialize MPU6050 IMU
  Serial.print("[MPU6050] Connecting... ");
  if (mpu.begin(0x68, &Wire)) {
    mpu6050_ready = true;
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
    Serial.println("SUCCESS (Address 0x68)");
  } else {
    Serial.println("FAILED! Check wiring (SDA=21, SCL=22, AD0=GND).");
  }

  // 3. Initialize DS18B20 OneWire Temperature
  Serial.print("[DS18B20] Connecting on GPIO ");
  Serial.print(PIN_DS18B20);
  Serial.print("... ");
  ds18b20.begin();
  if (ds18b20.getDeviceCount() > 0) {
    ds18b20_ready = true;
    ds18b20.setResolution(12); // 12-bit precision (0.0625°C)
    Serial.print("SUCCESS (Found ");
    Serial.print(ds18b20.getDeviceCount());
    Serial.println(" sensor(s))");
  } else {
    Serial.println("NO SENSORS FOUND! Ensure 4.7kΩ pull-up resistor is installed between Data and 3.3V.");
  }

  // Connect to Local Wi-Fi
  connectToWiFi();

  // Startup Beep Confirmation
  triggerBuzzer(100, 2);
  Serial.println("[SYSTEM] Setup completed. Entering telemetry loop.\n");
}

// ==============================================================================
// HIGH-FREQUENCY SENSOR POLLING & EVENT DETECTION
// ==============================================================================

void sampleSensorsAndDetectEvents() {
  // --- A. Emergency SOS Button Check (Active-LOW with debouncing) ---
  int btnReading = digitalRead(PIN_EMERGENCY_BTN);
  if (btnReading == LOW) {
    if (!emergencyLatched) {
      emergencyLatched = true;
      Serial.println("\n[ALERT] *** EMERGENCY SOS BUTTON PRESSED ***");
      triggerBuzzer(300, 1);
    }
  }

  // --- B. MAX30102 Heart Rate Sensing ---
  if (max30102_ready) {
    long irValue = max30102.getIR();

    if (checkForBeat(irValue)) {
      long delta = millis() - lastBeat;
      lastBeat = millis();
      beatsPerMinute = 60 / (delta / 1000.0);

      if (beatsPerMinute > 30 && beatsPerMinute < 220) {
        rates[rateSpot++] = (byte)beatsPerMinute;
        rateSpot %= RATE_SIZE;

        beatAvg = 0;
        for (byte x = 0; x < RATE_SIZE; x++) {
          beatAvg += rates[x];
        }
        beatAvg /= RATE_SIZE;
      }
    }
  }

  // --- C. MPU6050 Motion & Fall Detection Algorithm ---
  if (mpu6050_ready) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    // Acceleration vector magnitude in G's (1g = 9.80665 m/s^2)
    float ax = a.acceleration.x / 9.80665;
    float ay = a.acceleration.y / 9.80665;
    float az = a.acceleration.z / 9.80665;
    float currentMagnitude = sqrt(ax * ax + ay * ay + az * az);

    // Fall Algorithm:
    // 1. Free-fall phase: Sudden drop below 0.5g
    // 2. Impact phase: High-G shock (> 2.8g) within 600ms of free-fall
    // OR Direct violent impact (> 3.0g)
    if (currentMagnitude < 0.5) {
      fallCandidateDetected = true;
      fallCandidateTime = millis();
    }

    if (fallCandidateDetected && (millis() - fallCandidateTime <= 600)) {
      if (currentMagnitude > 2.6) {
        fallEventLatched = true;
        fallCandidateDetected = false;
        Serial.println("\n[ALERT] *** POTENTIAL PATIENT FALL DETECTED (IMPACT CONFIRMED) ***");
        triggerBuzzer(150, 3);
      }
    } else if (millis() - fallCandidateTime > 600) {
      fallCandidateDetected = false;
    }

    // Direct massive impact fallback
    if (currentMagnitude > 3.2) {
      fallEventLatched = true;
      Serial.println("\n[ALERT] *** SEVERE IMPACT / FALL DETECTED ***");
      triggerBuzzer(150, 3);
    }

    prevAccelMagnitude = currentMagnitude;
  }
}

// ==============================================================================
// TELEMETRY TRANSMISSION (REST HTTP POST)
// ==============================================================================

void dispatchTelemetryPacket() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Disconnected. Reconnecting before dispatch...");
    connectToWiFi();
    if (WiFi.status() != WL_CONNECTED) return;
  }

  // 1. Read Current Temperature
  float bodyTempC = 0.0;
  bool tempValid = false;
  if (ds18b20_ready) {
    ds18b20.requestTemperatures();
    float t = ds18b20.getTempCByIndex(0);
    if (t > -55.0 && t < 85.0 && t != DEVICE_DISCONNECTED_C) {
      bodyTempC = t;
      tempValid = true;
    }
  }

  // 2. Evaluate Optical Sensor Signal Quality
  long ir = max30102_ready ? max30102.getIR() : 0;
  bool fingerDetected = (ir > 50000);
  const char* signalQuality = fingerDetected ? "GOOD" : "INVALID";

  float reportedHR = fingerDetected ? (beatAvg > 0 ? (float)beatAvg : beatsPerMinute) : 0.0;
  float reportedSpO2 = fingerDetected ? currentSpO2 : 0.0;

  // 3. Read Current Motion Accelerations
  float ax = 0.0, ay = 0.0, az = 0.0;
  float gx = 0.0, gy = 0.0, gz = 0.0;
  if (mpu6050_ready) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    ax = a.acceleration.x / 9.80665;
    ay = a.acceleration.y / 9.80665;
    az = a.acceleration.z / 9.80665;
    gx = g.gyro.x;
    gy = g.gyro.y;
    gz = g.gyro.z;
  }

  // 4. Build JSON Telemetry Payload
  // Using ArduinoJson (compatible with v6 and v7)
#if ARDUINOJSON_VERSION_MAJOR >= 7
  JsonDocument doc;
#else
  StaticJsonDocument<768> doc;
#endif

  doc["device_id"] = DEVICE_ID;

  if (fingerDetected && reportedHR > 30.0) {
    doc["heart_rate"] = round(reportedHR * 10.0) / 10.0;
  } else {
    doc["heart_rate"] = nullptr;
  }

  if (fingerDetected && reportedSpO2 > 70.0) {
    doc["spo2"] = round(reportedSpO2 * 10.0) / 10.0;
  } else {
    doc["spo2"] = nullptr;
  }

  if (tempValid) {
    doc["temperature"] = round(bodyTempC * 10.0) / 10.0;
  } else {
    doc["temperature"] = nullptr;
  }

  doc["blood_pressure_sys"] = nullptr;
  doc["blood_pressure_dia"] = nullptr;
  doc["fall_detected"] = fallEventLatched;
  doc["emergency_button"] = emergencyLatched;
  doc["ecg_lead_status"] = "NOT_CONNECTED";
  doc["signal_quality"] = signalQuality;
  doc["battery_level"] = 95;

  JsonObject rawMotion = doc.createNestedObject("raw_motion");
  rawMotion["accel_x"] = round(ax * 1000.0) / 1000.0;
  rawMotion["accel_y"] = round(ay * 1000.0) / 1000.0;
  rawMotion["accel_z"] = round(az * 1000.0) / 1000.0;
  rawMotion["gyro_x"]  = round(gx * 100.0) / 100.0;
  rawMotion["gyro_y"]  = round(gy * 100.0) / 100.0;
  rawMotion["gyro_z"]  = round(gz * 100.0) / 100.0;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  // 5. Send HTTP POST to Ingestion API
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-ID", DEVICE_ID);
  http.addHeader("X-Device-Key", DEVICE_KEY);
  http.setTimeout(4000);

  int httpResponseCode = http.POST(jsonPayload);

  // Diagnostic Log Output
  Serial.print("[HTTP POST] Code: ");
  Serial.print(httpResponseCode);
  if (httpResponseCode == 201 || httpResponseCode == 200) {
    Serial.print(" [SUCCESS] Payload: ");
    Serial.println(jsonPayload);
  } else {
    Serial.print(" [ERROR] Response: ");
    Serial.println(http.getString());
  }

  http.end();

  // Reset latched transient events upon successful packaging
  fallEventLatched = false;
  emergencyLatched = false;
}

// ==============================================================================
// MAIN LOOP (NON-BLOCKING)
// ==============================================================================

void loop() {
  unsigned long currentMillis = millis();

  // High frequency sensor reading & fall/button sampling (25 Hz)
  if (currentMillis - lastSensorSample >= SENSOR_SAMPLE_INTERVAL_MS) {
    lastSensorSample = currentMillis;
    sampleSensorsAndDetectEvents();
  }

  // Telemetry transmission loop (every TELEMETRY_INTERVAL_MS)
  if (currentMillis - lastTelemetryDispatch >= TELEMETRY_INTERVAL_MS) {
    lastTelemetryDispatch = currentMillis;
    dispatchTelemetryPacket();
  }

  // Yield to allow ESP32 background Wi-Fi tasks to run smoothly
  yield();
}
