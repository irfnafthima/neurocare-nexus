# NeuroCare Nexus

> **Hybrid AI-IoT Remote Patient Monitoring (RPM) Platform for Academic & Research Purposes.**  
> Designed for remote monitoring, healthcare professional verification, patient-authorized access, physiological telemetry, health-record management, and AI-assisted patient support.

---

##  Table of Contents

- [Overview](#-overview)
- [Current Technology Stack](#-current-technology-stack)
- [Project Architecture](#-project-architecture)
- [System Roles](#-system-roles)
- [Doctor Verification Workflow](#-doctor-verification-workflow)
- [Synthetic Reference Dataset](#-synthetic-reference-dataset)
- [Patient → Doctor Connection Workflow](#-patient--doctor-connection-workflow)
- [Caregiver & Family Access Control](#-caregiver--family-access-control)
- [Health Records Management](#-health-records-management)
- [Prescriptions & Medications](#-prescriptions--medications)
- [Medical Document Management](#-medical-document-management)
- [AI Healthcare Support Assistant](#-ai-healthcare-support-assistant)
- [Audit Logging & Access Control](#-audit-logging--access-control)
- [Environment Setup & Installation](#-environment-setup--installation)
- [Environment Variables](#-environment-variables)
- [Verified Test Results](#-verified-test-results)
- [Project Status & Disclaimers](#-project-status--disclaimers)
- [Security & Privacy Guidelines](#-security--privacy-guidelines)

---

##  Overview

**NeuroCare Nexus** is a full-stack academic Remote Patient Monitoring (RPM) platform. It integrates real-time IoT sensor telemetry with a clinical monitoring dashboard, database-backed AI assistant support, automated healthcare professional verification, and granular permission-controlled access for patients, doctors, caregivers, family members, and system administrators.

---

##  Current Technology Stack

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite 8
- **Routing**: React Router v7 (with protected & role-gated route guards)
- **Data Visualization**: Recharts (physiological vital charts)
- **Iconography**: Lucide React
- **Form Management**: React Hook Form
- **Styling**: Tailwind CSS v4

### Backend
- **Language**: Python 3.13
- **Framework**: Django 6.1
- **API Engine**: Django REST Framework (DRF)
- **Authentication**: SimpleJWT (JWT Bearer Token Authentication)
- **CORS Management**: `django-cors-headers`

### Database
- **Database**: PostgreSQL 14+ (Relational schema for accounts, patients, telemetry, audit logs, medical records, prescriptions, and verification registries)

### IoT Architecture
- **Hardware Controller**: ESP32-based wearable node architecture
- **Sensors**:
  - **MAX30102**: Heart Rate & SpO₂ (Oxygen Saturation)
  - **DS18B20**: Precision Body Temperature Sensor
  - **MPU6050**: 3-axis Accelerometer & 3-axis Gyroscope (Fall Detection)
- **Protocol**: MQTT telemetry ingestion architecture & emergency event handling

### AI Integration
- **Context Engine**: Database-backed healthcare chatbot context (`ai_services` app) powered by Google Gemini API.
- **Clinical Disclaimer**: The chatbot is an **AI assistant/support feature** for health guidance and context retrieval. It is **NOT** a replacement for a qualified doctor, clinical diagnosis, or emergency medical service.

---

##  Project Architecture

```text
PROJECT NEUROCARE NEXUS/
├── src/                          # React Frontend Application
│   ├── components/               # UI Components (Common & Dashboard)
│   ├── pages/                    # Landing, Login, Register, Dashboard, Chatbot
│   ├── routes/                   # AppRouter with Protected & Role-Based Wrappers
│   ├── hooks/                    # Auth Hook (useAuth)
│   └── services/                 # API Service Layer
├── backend/                      # Django Python Backend
│   ├── accounts/                 # Auth, CustomUser, AuditLog, Admin Endpoints
│   ├── doctors/                  # DoctorProfile, Verification Engine, Reference Registries
│   ├── patients/                 # Patient Model, Family & Doctor Linkages
│   ├── caregivers/               # CaregiverProfile & Patient Linkages
│   ├── devices/                  # Synthetic Device Registries
│   ├── monitoring/               # Telemetry Sensor Readings Ingestion & Storage
│   ├── alerts/                   # Critical Alarm Notifications
│   ├── medical_records/          # EHR Care Notes & Consultation Records
│   ├── medical_documents/        # Protected Document Uploads & Metadata
│   ├── prescriptions/            # Medication Prescriptions & Dosage Tracking
│   ├── ai_services/              # Healthcare Chatbot Context & Integration
│   ├── core/                     # Django Settings, URLs, WSGI/ASGI
│   ├── reference_data/           # Synthetic Reference CSV Datasets
│   ├── data_generation/          # Dataset Generator & Validation Scripts
│   └── seed.py                   # Reference Dataset Ingestion Script
├── public/                       # Static Assets & Public Images
├── index.html                    # Single Page Application HTML Entry
├── vite.config.js                # Vite Configuration
└── package.json                  # Frontend Dependencies & Scripts
```

---

##  System Roles

The platform enforces 5 distinct roles with server-side permission checks:

1. **Patient**:
   - Access personal physiological vitals & telemetry history.
   - View active prescriptions, medical records, and uploaded medical documents.
   - Search eligible registered doctors and send connection requests.
   - Approve or decline caregiver and family member linkage requests.
   - Interact with the AI Healthcare Support Assistant.

2. **Doctor**:
   - Search active, verified registered doctors on the platform.
   - Manage incoming patient connection requests (Accept / Decline).
   - View real-time telemetry and EHR records for linked/authorized patients.
   - Write clinical care notes and issue digital prescriptions.
   - View administrative verification profile details.

3. **Caregiver**:
   - Submit linkage requests to patients using agency verification credentials.
   - View real-time vitals and critical fall/fever alerts for authorized patients upon patient approval.

4. **Family Member**:
   - Submit linkage requests to a patient using patient identification keys.
   - Monitor real-time physiological vitals for authorized family members upon patient approval.

5. **Administrator**:
   - Monitor system-wide operational statistics (patients, clinicians, devices, alarms).
   - Administrate the User Accounts Directory (revoke accounts, suspend doctors).
   - Open detailed **Doctor Verification Details** profiles (personal info, credentials, dataset verification matrix, reference registry comparisons, disciplinary status, facility affiliations).
   - Execute manual Admin decisions (Approve / Reject / Suspend).

---

##  Doctor Verification Workflow

To ensure healthcare professional verification, doctor signups undergo an automated multi-step verification process against the reference database:

```text
Doctor Registration
        ↓
Professional credentials submitted (MRN, Council, Qualification, Year)
        ↓
ReferenceDoctorRegistry Lookup
        ↓
Name / Registration / Council / Qualification Checks
        ↓
Disciplinary Status Check (DoctorDisciplinaryRecord)
        ↓
Verification Result Engine Execution
        ↓
Admin Review where required
        ↓
Approval / Rejection / Blocked State
```

### Supported Verification Outcomes
- `EXACT_MATCH`: Credentials, name, council, and qualification match exact reference record; disciplinary check clear. Auto-approved.
- `LIKELY_MATCH`: Partial match on name variations or year formatting; flagged for Admin manual review.
- `MISMATCH`: Explicit mismatch detected between submitted data and reference registry.
- `NOT_FOUND`: No matching reference record found. Admin manual verification required.
- `MANUAL_REVIEW`: Credentials require administrator review prior to account approval.
- `STATUS_BLOCKED`: Reference record indicates an active disciplinary suspension or blacklist. **Approval is strictly disabled**.

>  **Synthetic Reference Disclaimer**: The reference dataset is a **SYNTHETIC REFERENCE DATASET** generated strictly for academic and testing purposes. It is **NOT** an official government registry or state medical council database.

---

##  Synthetic Reference Dataset

The project includes a comprehensive synthetic dataset for professional credential verification:

- **5,000** Synthetic Doctor Records ([`ReferenceDoctorRegistry`](file:///e:/PROJECT%20NEUROCARE%20NEXUS/backend/doctors/models.py))
- **500** Synthetic Health Facilities ([`HealthFacility`](file:///e:/PROJECT%20NEUROCARE%20NEXUS/backend/doctors/models.py))
- **8,263** Synthetic Doctor-Facility Affiliations ([`ReferenceDoctorAffiliation`](file:///e:/PROJECT%20NEUROCARE%20NEXUS/backend/doctors/models.py))
- **150** Synthetic Disciplinary Records ([`DoctorDisciplinaryRecord`](file:///e:/PROJECT%20NEUROCARE%20NEXUS/backend/doctors/models.py))
- **130** Verification Engine Test Cases

### Validation Status
The reference dataset has been validated using the project's automated validation tool (`python backend/data_generation/validate_reference_data.py`):
- **42 / 42 Validation Checks Passed** (Zero duplicate identifiers, 100% foreign key integrity, valid date ranges, and correct status distributions).

>  **Notice**: These records are entirely synthetic for academic simulation. The system is **NOT** connected to the National Medical Commission (NMC), State Medical Councils, Ayushman Bharat Digital Mission (ABDM), or any live government portal.

---

##  Patient → Doctor Connection Workflow

Clinical patient access operates on an explicit authorization model:

```text
Patient searches eligible registered doctors
        ↓
Patient sends connection request
        ↓
Doctor sees pending request in clinical portal
        ↓
Doctor accepts or declines request
        ↓
DoctorPatientLink created in PostgreSQL only after approval
        ↓
Doctor gains authorized patient access
```

### Reference Dataset vs. Live Application Users
- **Reference Dataset**: Used solely for background professional verification during doctor registration.
- **Registered Application Users**: Live `DoctorProfile` accounts created by actual application users. Patient connections can only be established with live registered doctor accounts.

---

##  Caregiver & Family Access Control

- **Caregiver Access**: Professional caregivers submit linkage requests via Agency Certificate ID. Patient must explicitly accept the request.
- **Family Access**: Family members submit linkage requests via Patient ID keys. Patient must explicitly grant permission.
- **Permission-Gated Access**: Telemetry, alerts, and care notes are blocked server-side until the link is approved (`is_approved = True`).
- **Revocation**: Patients can revoke caregiver or family authorization at any time, instantly severing clinical data access.

---

##  Health Records Management

The implemented Electronic Health Record (EHR) module includes:

- **Current Conditions**: Diagnosis and active clinical condition tracking.
- **Allergies & Reactions**: Severity-coded allergy logging.
- **Medications**: Active pharmaceutical regimens.
- **Consultations**: Clinical consultation history and notes.
- **Next Consultation Date**: Scheduled clinical follow-up tracking.
- **EHR Care Notes**: Clinician note synchronization with audit trails.

Access to health records is strictly governed by server-side role permissions.

---

##  Prescriptions & Medications

- **Doctor Prescriptions**: Clinicians generate digital prescriptions linked to authorized patients.
- **Medication Details**: Drug name, dosage, administration frequency, and duration instructions.
- **Patient Viewing**: Patients view active prescriptions directly within their dashboard portal.
- **Schedule & Reminders**: Visual medication tracking and regimen schedules.

---

##  Medical Document Management

- **Protected Upload**: Patients upload medical reports and lab documents with associated metadata.
- **Authorization Enforcement**: Documents are accessible only to the patient and authorized clinicians/caregivers linked via database records.
- **Audit Logging**: Document uploads and downloads generate HIPAA audit log entries.
- **Private Storage**: Documents are retrieved through authenticated API endpoints and are **NOT** exposed via public static URLs.

---

##  AI Healthcare Support Assistant

The integrated **AI Chatbot** ([`ChatbotPage.jsx`](file:///e:/PROJECT%20NEUROCARE%20NEXUS/src/pages/DashboardPage.jsx)) acts as an intelligent healthcare support assistant:

- **Database-Backed Context**: Dynamically pulls authorized patient data (active conditions, allergies, current medications, past consultations, upcoming appointments, recent sensor vitals, active alarms, and document metadata) to provide personalized responses.
- **Important Limitations**:
  - The AI assistant does **NOT** replace professional medical judgment.
  - The AI assistant does **NOT** make definitive medical diagnoses.
  - Emergency situations must use emergency medical services immediately.

---

##  Audit Logging & Access Control

NeuroCare Nexus uses server-side authorization checks (`IsAuthenticated`, `IsAdminRole`, link checks) to guard all sensitive API routes.

### Monitored Audit Events
- Doctor verification execution & Admin approval/rejection
- Patient-doctor connection request dispatch & approval
- Caregiver & family linkage authorizations / revocations
- Medical document upload & access
- Prescription creation
- Account suspension & revocation

All audit actions are saved to PostgreSQL in the `AuditLog` model and accessible to administrators.

---

##  Environment Setup & Installation

### Prerequisites
- **Python**: v3.11+
- **Node.js**: v18+
- **PostgreSQL**: v14+
- **npm**: v9+

---

### 1. Clone Repository
```bash
git clone https://github.com/irfnafthima/neurocare-nexus.git
cd neurocare-nexus
```

### 2. Configure Database
```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE neurocare_nexus;"
```

### 3. Backend Setup (Django)
```bash
# Navigate to backend directory
cd backend

# Create & activate Python virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux/macOS:
# source venv/bin/activate

# Install backend dependencies
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers psycopg2-binary google-genai

# Configure backend environment variables (create backend/.env)
# See Environment Variables section below

# Run Django migrations
python manage.py migrate

# Seed synthetic reference dataset into PostgreSQL
python seed.py

# Start Django backend server (Port 5000)
python manage.py runserver 5000
```

### 4. Frontend Setup (React + Vite)
```bash
# From project root directory
npm install

# Start Vite development server (Port 5173)
npm run dev
```

---

##  Environment Variables

Secrets must remain in local `.env` files and must **NOT** be committed to version control. Create `backend/.env`:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=neurocare_nexus
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOWED_ORIGINS=http://localhost:5173
PORT=5000
JWT_SECRET=your_jwt_secret_key
GEMINI_API_KEY=your_google_gemini_api_key
```

---

##  Verified Test Results

The platform implementation has been verified using Django test tools and Vite build validation:

```text
----------------------------------------------------------------------
Django Backend Test Suite:
Command: python manage.py test
Result:  Ran 34 tests in 31.536s — OK (34 passed, 3 skipped, 0 failed)

Frontend Application Build:
Command: npm run build
Result:  vite build completed successfully (0 errors, dist/ generated in 1.04s)

Reference Dataset Validation:
Command: python backend/data_generation/validate_reference_data.py
Result:  ALL VALIDATION CHECKS PASSED ✓ (42 / 42 checks verified)
----------------------------------------------------------------------
```

---

##  Project Status & Disclaimers

>  **Academic & Research Prototype**: This application is developed strictly as an academic and research prototype for demonstrating hybrid AI-IoT remote patient monitoring and verification workflows.

### Explicit Non-Claims:
- No production clinical certification or FDA medical device approval.
- No official HIPAA compliance certification.
- No live connection to NMC (National Medical Commission) or State Medical Council registries.
- No live ABDM (Ayushman Bharat Digital Mission) integration.
- No real hospital or clinical deployment.

---

##  Security & Privacy Guidelines

1. **Secret Confidentiality**: Environment files (`.env`) are excluded from git via `.gitignore`.
2. **Access Control**: API endpoints enforce role-based and link-based access control.
3. **Protected Media**: Medical documents require JWT authentication and are not exposed publicly.
4. **Auditability**: Critical user actions are captured in immutable PostgreSQL audit logs.
5. **Synthetic Data**: All reference registries and demo profiles utilize synthetic data.

---

*Built for research in AI-IoT Remote Patient Monitoring.*
