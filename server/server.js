import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import pool from './db.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Helper to seed demo accounts on server start if table is empty
const seedDemoAccounts = async () => {
  try {
    const checkUsers = await pool.query('SELECT COUNT(*) FROM users');
    if (parseInt(checkUsers.rows[0].count, 10) === 0) {
      console.log('Seeding preconfigured admin root account in PostgreSQL...');
      
      const admin = {
        email: 'admin@nexus.com',
        fullName: 'System Administrator',
        phone: '+1 (555) 019-2834',
        role: 'admin',
        accessKey: 'ADM-90210'
      };

      await pool.query(
        `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
        [admin.email, 'demo_password_hash', admin.fullName, admin.phone, admin.role, '', '', '', '', admin.accessKey]
      );
      console.log('Admin account seeded successfully.');
    }
  } catch (error) {
    console.error('Error seeding demo accounts:', error.message);
  }
};

seedDemoAccounts();

// ==================== AUTHENTICATION ROUTES ====================

// Login API
app.post('/api/auth/login', async (req, res) => {
  const { email, role, credentials } = req.body;
  const cleanEmail = String(email).trim().toLowerCase();

  try {
    const userQuery = await pool.query(
      'SELECT * FROM users WHERE LOWER(email) = $1 AND role = $2',
      [cleanEmail, role]
    );

    if (userQuery.rows.length === 0) {
      return res.status(401).send(`Access Denied: Unrecognized credentials for ${role.toUpperCase()} role.`);
    }

    const matchedUser = userQuery.rows[0];

    // Validate specific credential formats matching role schemas
    let isValid = false;
    if (role === 'doctor' && credentials.npi === matchedUser.npi) isValid = true;
    else if (role === 'patient' && credentials.deviceId === matchedUser.device_id) isValid = true;
    else if (role === 'caregiver' && credentials.agencyId === matchedUser.agency_id) isValid = true;
    else if (role === 'family' && credentials.patientId === matchedUser.patient_id) isValid = true;
    else if (role === 'admin' && credentials.accessKey === matchedUser.access_key) isValid = true;

    if (!isValid) {
      return res.status(401).send(`Access Denied: Credentials verification failed for role ${role.toUpperCase()}.`);
    }

    // Write login access audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [matchedUser.full_name, 'Login Session Initiated', `${role.toUpperCase()} Portal Access`, 'Success']
    );

    res.json({
      name: matchedUser.full_name,
      email: matchedUser.email,
      phone: matchedUser.phone,
      role: matchedUser.role,
      npi: matchedUser.npi,
      deviceId: matchedUser.device_id,
      agencyId: matchedUser.agency_id,
      patientId: matchedUser.patient_id,
      accessKey: matchedUser.access_key
    });
  } catch (error) {
    console.error(error);
    res.status(500).send('Server Error: Database connection failure.');
  }
});

// Registration API (with Registry Checks)
app.post('/api/auth/register', async (req, res) => {
  const { fullName, email, phone, role, npi, deviceId, agencyId, patientId, accessKey } = req.body;
  const cleanEmail = String(email).trim().toLowerCase();

  try {
    // 1. Check if user already exists
    const checkUser = await pool.query(
      'SELECT * FROM users WHERE LOWER(email) = $1 AND role = $2',
      [cleanEmail, role]
    );
    if (checkUser.rows.length > 0) {
      return res.status(400).send('An account with this email and role already exists.');
    }

    // 2. Perform synthetic CMS registry validations
    if (role === 'doctor') {
      const npiCheck = await pool.query('SELECT * FROM synthetic_npis WHERE npi = $1', [npi]);
      if (npiCheck.rows.length === 0) {
        return res.status(400).send('NPI not found in CMS NPPES Registry Database.');
      }
    } else if (role === 'patient') {
      const deviceCheck = await pool.query('SELECT * FROM synthetic_devices WHERE serial = $1', [deviceId]);
      if (deviceCheck.rows.length === 0) {
        return res.status(400).send('Wearable serial number not registered in manufacturer database.');
      }
    } else if (role === 'caregiver') {
      const agencyCheck = await pool.query('SELECT * FROM synthetic_caregivers WHERE agency_id = $1', [agencyId]);
      if (agencyCheck.rows.length === 0) {
        return res.status(400).send('Agency certificate code not found in Home Health Agency registry.');
      }
    } else if (role === 'family') {
      const consentCheck = await pool.query('SELECT * FROM synthetic_patients WHERE patient_id = $1', [patientId]);
      if (consentCheck.rows.length === 0) {
        return res.status(400).send('Patient consent token not verified or authorized access is restricted.');
      }
    }

    // 3. Create user record
    await pool.query(
      `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
      [cleanEmail, 'registered_password_hash', fullName, phone || '', role, npi, deviceId, agencyId, patientId, accessKey]
    );

    // If role is patient, automatically create their clinical registry patient entry & telemetry
    if (role === 'patient') {
      const patientId = deviceId.trim().toUpperCase().replace('NP-', 'P-');
      const checkPatient = await pool.query('SELECT * FROM patients WHERE id = $1', [patientId]);
      if (checkPatient.rows.length === 0) {
        const roomNumber = deviceId.replace('NP-', '');
        await pool.query(
          `INSERT INTO patients (id, name, age, gender, room, condition, risk, status, ehr_notes) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
          [patientId, fullName, 45, 'Male', roomNumber, 'Newly Enrolled Patient', 10, 'Normal', 'Patient enrolled via secure online signup. Vitals stream active.']
        );
        await pool.query(
          `INSERT INTO telemetry (patient_id, heart_rate, spo2, temperature, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, fall_detected, esp32_connected, esp32_battery, esp32_rssi)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
          [patientId, 72, 98, 36.80, 0.05, 0.98, 0.04, 0.50, -1.20, 0.30, false, true, 100, -55]
        );
      }
    }

    // 4. Log HIPAA audit trail
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [fullName, 'Registered Profile Created', `EHR Account Registry [${role.toUpperCase()}]`, 'Success']
    );

    res.json({
      name: fullName,
      email: cleanEmail,
      phone: phone || '',
      role,
      npi,
      deviceId,
      agencyId,
      patientId,
      accessKey
    });
  } catch (error) {
    console.error(error);
    res.status(500).send('Server Error during registration.');
  }
});


// ==================== PATIENT EHR & TELEMETRY ROUTES ====================

// Fetch All Patients List
app.get('/api/patients', async (req, res) => {
  try {
    // Select patient profiles combined with their latest telemetry records
    const patientsQuery = await pool.query(`
      SELECT p.*, 
             t.heart_rate as "heartRate", 
             t.spo2, 
             t.temperature, 
             t.accel_x as "accelX", 
             t.accel_y as "accelY", 
             t.accel_z as "accelZ", 
             t.gyro_x as "gyroX", 
             t.gyro_y as "gyroY", 
             t.gyro_z as "gyroZ", 
             t.fall_detected as "fallDetected",
             t.esp32_connected as "esp32Connected", 
             t.esp32_battery as "esp32Battery", 
             t.esp32_rssi as "esp32Rssi"
      FROM patients p
      LEFT JOIN LATERAL (
         SELECT * FROM telemetry 
         WHERE patient_id = p.id 
         ORDER BY timestamp DESC LIMIT 1
      ) t ON TRUE
      ORDER BY p.risk DESC
    `);
    
    // Map database properties into camelCase fields for React bindings
    const patientsList = patientsQuery.rows.map(row => ({
      id: row.id,
      name: row.name,
      age: row.age,
      gender: row.gender,
      room: row.room,
      condition: row.condition,
      risk: row.risk,
      status: row.status,
      vitals: {
        max30102: {
          heartRate: row.heartRate || 72,
          spo2: row.spo2 || 98
        },
        ds18b20: {
          temperature: parseFloat(row.temperature || 36.80)
        },
        mpu6050: {
          accelX: parseFloat(row.accelX || 0.05),
          accelY: parseFloat(row.accelY || 0.98),
          accelZ: parseFloat(row.accelZ || 0.04),
          gyroX: parseFloat(row.gyroX || 0.50),
          gyroY: parseFloat(row.gyroY || -1.20),
          gyroZ: parseFloat(row.gyroZ || 0.30),
          fallDetected: !!row.fallDetected
        },
        esp32: {
          connected: row.esp32Connected !== false,
          battery: row.esp32Battery || 90,
          rssi: row.esp32Rssi || -60
        }
      }
    }));

    res.json(patientsList);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to fetch patient registries.');
  }
});

// Fetch Attending Care Notes for Patient
app.get('/api/patients/notes', async (req, res) => {
  try {
    const result = await pool.query('SELECT id, ehr_notes FROM patients');
    const notesMap = {};
    result.rows.forEach(r => {
      notesMap[r.id] = r.ehr_notes || 'No checkup logs saved.';
    });
    res.json(notesMap);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to load clinical care notes.');
  }
});

// Update Care Notes
app.put('/api/patients/:id/notes', async (req, res) => {
  const { id } = req.params;
  const { notes, clinicianName } = req.body;

  try {
    await pool.query(
      'UPDATE patients SET ehr_notes = $1 WHERE id = $2',
      [notes, id]
    );

    // Log update audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [clinicianName || 'Clinician', 'Modified EHR Notes', `Patient Record ID: ${id}`, 'Success']
    );

    res.send('Care notes updated successfully.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to save care notes.');
  }
});


// ==================== TELEMETRY SIMULATION CONTROLLER ====================

app.post('/api/simulation/trigger', async (req, res) => {
  const { patientId, vitals, riskScore, statusState, auditAction, userName } = req.body;

  try {
    // 1. Insert new telemetry row
    await pool.query(
      `INSERT INTO telemetry (patient_id, heart_rate, spo2, temperature, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, fall_detected, esp32_connected, esp32_battery, esp32_rssi)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
      [
        patientId,
        vitals.max30102.heartRate,
        vitals.max30102.spo2,
        vitals.ds18b20.temperature,
        vitals.mpu6050.accelX,
        vitals.mpu6050.accelY,
        vitals.mpu6050.accelZ,
        vitals.mpu6050.gyroX,
        vitals.mpu6050.gyroY,
        vitals.mpu6050.gyroZ,
        vitals.mpu6050.fallDetected,
        vitals.esp32.connected,
        vitals.esp32.battery,
        vitals.esp32.rssi
      ]
    );

    // 2. Update overall patient health risk index status
    await pool.query(
      'UPDATE patients SET risk = $1, status = $2 WHERE id = $3',
      [riskScore, statusState, patientId]
    );

    // 3. Log simulated compliance event
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [userName || 'Telemetry Simulator', auditAction, `Room Patient ID: ${patientId}`, 'Success']
    );

    res.send('Simulated telemetry update recorded.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to log simulated telemetry update.');
  }
});


// ==================== HIPAA AUDIT LOGS ====================

app.get('/api/audit-logs', async (req, res) => {
  try {
    const logs = await pool.query('SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100');
    res.json(logs.rows.map(l => ({
      id: l.id,
      timestamp: l.timestamp.toISOString(),
      username: l.username,
      action: l.action,
      target: l.target,
      status: l.status
    })));
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to load HIPAA audit trails.');
  }
});

app.post('/api/audit-logs', async (req, res) => {
  const { username, action, target } = req.body;
  try {
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [username, action, target, 'Success']
    );
    res.send('Audit log entry created.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to insert audit trail.');
  }
});

// Fetch Admin System Stats
app.get('/api/admin/stats', async (req, res) => {
  try {
    const patientsCount = await pool.query('SELECT COUNT(*) FROM patients');
    const cliniciansCount = await pool.query("SELECT COUNT(*) FROM users WHERE role IN ('doctor', 'caregiver')");
    const devicesCount = await pool.query('SELECT COUNT(*) FROM synthetic_devices');
    const alarmsCount = await pool.query('SELECT COUNT(*) FROM telemetry WHERE fall_detected = true');

    res.json({
      totalPatients: parseInt(patientsCount.rows[0].count, 10),
      totalClinicians: parseInt(cliniciansCount.rows[0].count, 10),
      totalDevices: parseInt(devicesCount.rows[0].count, 10),
      criticalAlarms: parseInt(alarmsCount.rows[0].count, 10)
    });
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to fetch admin statistics.');
  }
});

app.listen(PORT, () => {
  console.log(`NeuroCare Nexus Backend server listening on port ${PORT}`);
});
