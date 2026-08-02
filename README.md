#  NeuroCare Nexus

> **Hybrid AI-IoT system for multimodal physiological and neuro-behavioral anomaly detection, predictive risk analysis, and remote clinical monitoring in home healthcare.**

---

##  Overview

NeuroCare Nexus is a full-stack Remote Patient Monitoring (RPM) platform that combines AI-powered analytics with IoT sensor data to detect physiological and neuro-behavioral anomalies. It provides clinicians with a real-time dashboard to monitor patients remotely, enabling proactive intervention and reducing hospital readmissions.

---

##  Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 19 + Vite 8 | UI framework & build tool |
| React Router v7 | Client-side routing |
| Recharts | Data visualization & charts |
| Lucide React | Icon library |
| React Hook Form | Form state management |
| Tailwind CSS v4 | Utility-first styling |

### Backend
| Technology | Purpose |
|---|---|
| Node.js + Express | REST API server |
| PostgreSQL + pg | Relational database |
| dotenv | Environment variable management |
| CORS | Cross-origin resource sharing |

---

##  Project Structure

```
PROJECT NEUROCARE NEXUS/
├── src/                    # React frontend source
│   ├── components/         # Reusable UI components
│   ├── pages/              # Page-level route components
│   ├── routes/             # Route definitions
│   ├── hooks/              # Custom React hooks
│   ├── data/               # Static/mock data
│   ├── App.jsx             # Root application component
│   └── main.jsx            # Entry point
├── server/                 # Express backend
│   ├── server.js           # Main server & API routes
│   ├── db.js               # PostgreSQL connection pool
│   ├── schema.sql          # Database schema
│   ├── seed.sql            # Seed data
│   └── .env                # Environment variables (not committed)
├── public/                 # Static public assets
├── index.html              # HTML entry point
├── vite.config.js          # Vite configuration
└── package.json            # Frontend dependencies
```

---

##  Getting Started

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

```bash
cd server
```

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

## 📡 API Overview

The backend exposes a REST API for patient data, vitals, alerts, and monitoring sessions. The server runs on the port defined in `server/.env` (default: `5000`).

---

##  Environment Variables

>  **Never commit `.env` files.** The `server/.env` file is excluded via `.gitignore`.

| Variable | Description |
|---|---|
| `DB_HOST` | PostgreSQL host |
| `DB_PORT` | PostgreSQL port |
| `DB_NAME` | Database name |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `PORT` | Express server port |

---

##  Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

##  License

This project is for academic and research purposes.

---

*Built with  for smarter, safer home healthcare.*
