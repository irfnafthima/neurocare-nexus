# 🧠 NeuroCare Nexus

> **Hybrid AI-IoT system for multimodal physiological and neuro-behavioral anomaly detection, predictive risk analysis, and remote clinical monitoring in home healthcare.**

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)](https://vite.dev)
[![Express](https://img.shields.io/badge/Express-4-000000?logo=express)](https://expressjs.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?logo=postgresql)](https://www.postgresql.org)

---

## 📖 Overview

NeuroCare Nexus is a full-stack **Remote Patient Monitoring (RPM)** platform that integrates real-time IoT sensor telemetry with a clinical dashboard to detect physiological and neuro-behavioral anomalies. It enables clinicians to monitor patients remotely with role-based access for doctors, patients, caregivers, family members, and administrators.

---

## 🏗️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 19 + Vite 8 | UI framework & build tool |
| React Router v7 | Client-side routing with route guards |
| Recharts | Physiological data visualization & charts |
| Lucide React | Icon library |
| React Hook Form | Form state management |
| Tailwind CSS v4 | Utility-first styling |

### Backend
| Technology | Purpose |
|---|---|
| Node.js + Express 4 | REST API server |
| PostgreSQL + pg | Relational database for EHR & telemetry |
| dotenv | Environment variable management |
| CORS | Cross-origin resource sharing |

---

## 📁 Project Structure

```
PROJECT NEUROCARE NEXUS/
├── src/                          # React frontend source
│   ├── components/
│   │   ├── auth/                 # LoginForm, RegisterForm
│   │   ├── common/               # Navbar, Sidebar, Footer, Button,
│   │   │                         # Card, Badge, Input, Toast
│   │   └── dashboard/            # StatCard, AlertCard, ActivityCard,
│   │                             # AppointmentCard, ChartPlaceholder
│   ├── pages/
│   │   ├── LandingPage.jsx       # Public marketing page
│   │   ├── LoginPage.jsx         # Role-based login
│   │   ├── RegisterPage.jsx      # Multi-role registration with registry validation
│   │   └── DashboardPage.jsx     # Main clinical monitoring dashboard
│   ├── routes/
│   │   └── AppRouter.jsx         # Protected & guest route wrappers
│   ├── hooks/
│   │   └── useAuth.jsx           # Authentication state hook
│   ├── data/
│   │   └── mockData.js           # Static fallback data
│   ├── App.jsx                   # Root application component
│   └── main.jsx                  # Entry point
├── server/                       # Express backend
│   ├── server.js                 # Main server & all API routes
│   ├── db.js                     # PostgreSQL connection pool
│   ├── schema.sql                # Full database schema (8 tables)
│   ├── seed.sql                  # Seed data for synthetic registries
│   └── .env                      # Environment variables (not committed)
├── public/                       # Static public assets
├── index.html                    # HTML entry point
├── vite.config.js                # Vite configuration
└── package.json                  # Frontend dependencies
```

---

## 🌐 Application Routes

| Route | Access | Description |
|---|---|---|
| `/` | Public | Landing / marketing page |
| `/login` | Guest only | Role-based login portal |
| `/register` | Guest only | Multi-role registration with registry validation |
| `/dashboard` | Authenticated | Clinical monitoring dashboard |

---

## 📡 API Reference

Base URL: `http://localhost:5000`

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Role-based login with credential verification |
| `POST` | `/api/auth/register` | New user registration with registry checks |

### Patient EHR & Telemetry
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patients` | Fetch all patients with latest telemetry |
| `GET` | `/api/patients/notes` | Fetch clinical EHR care notes |
| `PUT` | `/api/patients/:id/notes` | Update care notes for a patient |

### Telemetry Simulation
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/simulation/trigger` | Inject simulated IoT sensor readings |

### HIPAA Audit Logs
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/audit-logs` | Fetch latest 100 HIPAA audit trail entries |
| `POST` | `/api/audit-logs` | Write a new audit log entry |

### Admin
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/stats` | System-wide stats (patients, clinicians, devices, alarms) |

---

## 🗄️ Database Schema

The PostgreSQL database has **8 tables**:

| Table | Description |
|---|---|
| `users` | EHR accounts for all roles |
| `patients` | Clinical patient registry |
| `telemetry` | Live IoT sensor readings per patient |
| `audit_logs` | HIPAA-compliant event audit trail |
| `synthetic_npis` | Synthetic CMS NPPES NPI registry for doctor validation |
| `synthetic_devices` | Synthetic wearable device serial register |
| `synthetic_caregivers` | Synthetic home health agency registry |
| `synthetic_patients` | Synthetic patient consent token registry |

---

## 🩺 IoT Sensor Integration

Telemetry data is collected from the following sensors via **ESP32**:

| Sensor | Metrics |
|---|---|
| **MAX30102** | Heart rate, SpO₂ |
| **DS18B20** | Body temperature |
| **MPU6050** | 3-axis accelerometer, 3-axis gyroscope, fall detection |
| **ESP32** | Connectivity status, battery level, RSSI signal strength |

---

## 👥 User Roles & Credentials

The system supports **5 roles**, each with unique credential verification:

| Role | Credential Required | Registry Check |
|---|---|---|
| `doctor` | NPI number | Synthetic CMS NPPES registry |
| `patient` | Wearable device serial | Synthetic device manufacturer DB |
| `caregiver` | Agency certificate code | Synthetic Home Health Agency registry |
| `family` | Patient consent token | Synthetic patient consent registry |
| `admin` | Access key | Internal admin registry |

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18+
- **PostgreSQL** v14+
- **npm** v9+

### 1. Clone the Repository

```bash
git clone https://github.com/irfnafthima/neurocare-nexus.git
cd neurocare-nexus
```

### 2. Set Up the Database

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE neurocare_nexus;"

# Run schema and seed files
psql -U postgres -d neurocare_nexus -f server/schema.sql
psql -U postgres -d neurocare_nexus -f server/seed.sql
```

### 3. Configure the Backend

Create a `.env` file in the `server/` directory:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=neurocare_nexus
DB_USER=postgres
DB_PASSWORD=your_password
PORT=5000
```

Install backend dependencies and start the server:

```bash
cd server
npm install
npm start
```

The API will be available at `http://localhost:5000`.

### 4. Set Up the Frontend

From the project root:

```bash
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🔒 Environment Variables

> ⚠️ **Never commit `.env` files.** The `server/.env` file is excluded via `.gitignore`.

| Variable | Description |
|---|---|
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `PORT` | Express server port (default: `5000`) |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is for academic and research purposes.

---

*Built with ❤️ for smarter, safer home healthcare.*
