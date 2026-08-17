# NeuroCare Nexus — Official Flutter Mobile Application

The **NeuroCare Nexus Mobile Application** is the official cross-platform Flutter client for the NeuroCare Nexus AI-IoT remote patient monitoring and clinical telemetry platform.

---

## 🏛️ System Architecture

```
Flutter Mobile App (mobile/)
        │  HTTP / Bearer JWT
        ▼
Django REST API (backend/ :8000)
        │
        ▼
PostgreSQL Database (neurocare_nexus)
        │
        ▼
AI / ML Services & Telemetry Ingestion
```

### Key Principles:
1. **Single Source of Truth**: Connects directly to the existing Django REST Framework API. No duplicate backends, mock databases, or standalone Firebase layers.
2. **Role-Based Experience**: Supports `PATIENT`, `DOCTOR`, `CAREGIVER`, `FAMILY`, and `ADMIN` with JWT authentication and authorization enforced server-side.
3. **Medical Security**: Local JWT tokens stored securely. Access control rules (e.g. `DoctorPatientLink`) enforced strictly by Django backend.

---

## 📱 Features

- **Patient Mobile Dashboard**: Clinical overview, risk score, connected physician, next consultation date, telemetry status.
- **Health Records**: Diagnosed conditions, known allergies, consultation logs.
- **Read-Only Prescriptions**: Medicine name, dosage, frequency, duration, instructions, prescribing clinician.
- **Protected Document Vault**: Metadata and secure streaming download links for lab reports, diagnostic scans, and medical files.
- **Approved Doctor Directory**: Search operational verified doctors and dispatch connection requests (`DoctorConnectionRequest`).
- **AI Clinical Assistant Chatbot**: Communicates with Django AI chatbot endpoint with medical advisory safety notices.
- **ESP32 Wearable Telemetry**: Wearable sensor hub status with clear empty states when hardware is offline.

---

## 🚀 Getting Started

### 1. Prerequisites
- [Flutter SDK](https://flutter.dev/docs/get-started/install) (v3.0.0 or higher)
- Running Django REST API backend (`http://localhost:8000`)
- Running PostgreSQL database (`neurocare_nexus`)

### 2. Configure API Host
The base API URL is centralized in `lib/core/config/api_config.dart`.
- **Android Emulator**: `http://10.0.2.2:8000` (Default)
- **iOS Simulator / Desktop**: `http://127.0.0.1:8000`
- **Physical Device**: Enter your machine's Wi-Fi IP address on the login screen or call `ApiConfig.setBaseUrl('http://<YOUR-IP>:8000')`.

### 3. Run Application
```bash
cd mobile
flutter pub get
flutter run
```

### 4. Run Test Suite
```bash
cd mobile
flutter test
```
