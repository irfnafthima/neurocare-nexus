-- Project Neurocare Nexus PostgreSQL Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables if they exist
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS telemetry CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS synthetic_npis CASCADE;
DROP TABLE IF EXISTS synthetic_devices CASCADE;
DROP TABLE IF EXISTS synthetic_caregivers CASCADE;
DROP TABLE IF EXISTS synthetic_patients CASCADE;

-- 1. Users table (EHR accounts database)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL, -- 'doctor', 'patient', 'caregiver', 'family', 'admin'
    npi VARCHAR(10),
    device_id VARCHAR(20),
    agency_id VARCHAR(20),
    patient_id VARCHAR(20),
    access_key VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Patients registry
CREATE TABLE patients (
    id VARCHAR(20) PRIMARY KEY, -- e.g. 'P-102', 'P-204'
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    room VARCHAR(10) NOT NULL,
    condition VARCHAR(255) NOT NULL,
    risk INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Normal',
    ehr_notes TEXT DEFAULT ''
);

-- 3. Live physiological sensor telemetry (MAX30102, DS18B20, MPU6050, ESP32)
CREATE TABLE telemetry (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR(20) REFERENCES patients(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    -- MAX30102
    heart_rate INT,
    spo2 INT,
    -- DS18B20
    temperature NUMERIC(4,2),
    -- MPU6050
    accel_x NUMERIC(5,2),
    accel_y NUMERIC(5,2),
    accel_z NUMERIC(5,2),
    gyro_x NUMERIC(5,2),
    gyro_y NUMERIC(5,2),
    gyro_z NUMERIC(5,2),
    fall_detected BOOLEAN DEFAULT FALSE,
    -- ESP32
    esp32_connected BOOLEAN DEFAULT TRUE,
    esp32_battery INT,
    esp32_rssi INT
);

-- 4. HIPAA Audit logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    username VARCHAR(100) NOT NULL,
    action VARCHAR(255) NOT NULL,
    target VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Success'
);

-- 5. Synthetic provider NPI checks
CREATE TABLE synthetic_npis (
    npi VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    hospital VARCHAR(150) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active'
);

-- 6. Synthetic wearable device serial registers
CREATE TABLE synthetic_devices (
    serial VARCHAR(20) PRIMARY KEY,
    mac VARCHAR(30) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'Unassigned'
);

-- 7. Synthetic caregiver agency databases
CREATE TABLE synthetic_caregivers (
    agency_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    agency VARCHAR(150) NOT NULL,
    status VARCHAR(50) DEFAULT 'Active'
);

-- 8. Synthetic patient access tokens
CREATE TABLE synthetic_patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    patient_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'Consent Verified'
);
