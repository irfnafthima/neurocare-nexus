import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import jwt from 'jsonwebtoken';
import pool from './db.js';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'neurocare_secret_token_key';

app.use(cors());
app.use(express.json());

// Token Verification Middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1]; // Expecting "Bearer <token>"

  if (!token) {
    return res.status(401).send('Access Denied: No authentication token provided.');
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).send('Access Denied: Invalid or expired session token.');
    }
    req.user = user;
    next();
  });
};

// Helper to seed demo accounts on server start if table is empty
const seedDemoAccounts = async () => {
  try {
    const checkUsers = await pool.query('SELECT COUNT(*) FROM users');
    if (parseInt(checkUsers.rows[0].count, 10) === 0) {
      console.log('Seeding preconfigured accounts in PostgreSQL...');
      
      const admin = {
        email: 'admin@nexus.com',
        fullName: 'System Administrator',
        phone: '+1 (555) 019-2834',
        role: 'admin',
        accessKey: 'ADM-90210'
      };

      const doctor = {
        email: 'doctor@nexus.com',
        fullName: 'Dr. Rachel Kim',
        phone: '+1 (555) 012-3456',
        role: 'doctor',
        npi: '1029384756'
      };

      const caregiver = {
        email: 'caregiver@nexus.com',
        fullName: 'Maria Santos, RN',
        phone: '+1 (555) 023-4567',
        role: 'caregiver',
        agencyId: 'CG-204'
      };

      const patient = {
        email: 'patient@nexus.com',
        fullName: 'Sarah Johnson',
        phone: '+1 (555) 034-5678',
        role: 'patient',
        deviceId: 'NP-102'
      };

      const family = {
        email: 'family@nexus.com',
        fullName: 'Relative of Sarah',
        phone: '+1 (555) 045-6789',
        role: 'family',
        patientId: 'P-102'
      };

      // Insert Admin
      await pool.query(
        `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key, approved) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
        [admin.email, 'demo_password_hash', admin.fullName, admin.phone, admin.role, '', '', '', '', admin.accessKey, true]
      );

      // Insert Doctor
      await pool.query(
        `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key, approved, specialization, experience, bio) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
        [doctor.email, 'demo_password_hash', doctor.fullName, doctor.phone, doctor.role, doctor.npi, '', '', '', '', true, 'Cardiologist', 12, 'Board-certified cardiologist specializing in clinical remote patient telemonitoring.']
      );

      // Insert Caregiver
      await pool.query(
        `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key, approved) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
        [caregiver.email, 'demo_password_hash', caregiver.fullName, caregiver.phone, caregiver.role, '', '', caregiver.agencyId, '', '', true]
      );

      // Insert Patient
      await pool.query(
        `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key, approved) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
        [patient.email, 'demo_password_hash', patient.fullName, patient.phone, patient.role, '', patient.deviceId, '', '', '', true]
      );

      // Insert Family
      await pool.query(
        `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key, approved) 
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`,
        [family.email, 'demo_password_hash', family.fullName, family.phone, family.role, '', '', '', family.patientId, '', true]
      );

      // Seed Patient details inside patients table for NP-102 -> P-102
      const checkPatient = await pool.query("SELECT * FROM patients WHERE id = 'P-102'");
      if (checkPatient.rows.length === 0) {
        await pool.query(
          `INSERT INTO patients (id, name, age, gender, room, condition, risk, status, ehr_notes, doctor_npi) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
          ['P-102', 'Sarah Johnson', 72, 'Female', '102', 'Heart Failure Post-op', 12, 'Normal', 'Patient stable. MAX30102 shows healthy BPM. No postural issues.', doctor.npi]
        );
        await pool.query(
          `INSERT INTO telemetry (patient_id, heart_rate, spo2, temperature, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, fall_detected, esp32_connected, esp32_battery, esp32_rssi)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
          ['P-102', 72, 98, 36.80, 0.05, 0.98, 0.04, 0.50, -1.20, 0.30, false, true, 92, -65]
        );
        await pool.query(
          `INSERT INTO appointments (patient_id, details, time) VALUES 
           ($1, $2, $3),
           ($4, $5, $6)`,
          [
            'P-102', 'Dr. Rachel Kim — Cardiology consultation with Sarah Johnson', 'Today, 02:00 PM',
            'P-102', 'Home Care Nurse — Patch replacement checkup', 'Tomorrow, 09:00 AM'
          ]
        );
      }

      const checkPatient2 = await pool.query("SELECT * FROM patients WHERE id = 'P-204'");
      if (checkPatient2.rows.length === 0) {
        await pool.query(
          `INSERT INTO patients (id, name, age, gender, room, condition, risk, status, ehr_notes, doctor_npi) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
          ['P-204', 'Marcus Williams', 65, 'Male', '204', 'Post-stroke Monitoring', 15, 'Normal', 'Vitals within baseline bounds.', doctor.npi]
        );
        await pool.query(
          `INSERT INTO telemetry (patient_id, heart_rate, spo2, temperature, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, fall_detected, esp32_connected, esp32_battery, esp32_rssi)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)`,
          ['P-204', 68, 97, 36.60, -0.02, 0.99, -0.05, -0.10, 0.80, -0.20, false, true, 85, -70]
        );
        await pool.query(
          `INSERT INTO appointments (patient_id, details, time) VALUES 
           ($1, $2, $3),
           ($4, $5, $6)`,
          [
            'P-204', 'Maria Santos, RN — Biometric review with Marcus Williams', 'Tomorrow, 10:30 AM',
            'P-204', 'Dr. Samuel Torres — EEG interpretation checkup', 'Next Monday, 04:00 PM'
          ]
        );
      }

      console.log('Demo accounts and patients seeded successfully.');
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

    // Enforce approval check for Doctor logins
    if (role === 'doctor' && !matchedUser.approved) {
      return res.status(403).send('Your professional credential verification is pending system administrator approval.');
    }

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

    // Sign JWT token
    const token = jwt.sign(
      { id: matchedUser.id, email: matchedUser.email, role: matchedUser.role, name: matchedUser.full_name },
      JWT_SECRET,
      { expiresIn: '24h' }
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
      accessKey: matchedUser.access_key,
      token: token
    });
  } catch (error) {
    console.error(error);
    res.status(500).send('Server Error: Database connection failure.');
  }
});

// Public endpoint to lookup synthetic NPI details (for doctor signup verification)
app.get('/api/npis/:npi', async (req, res) => {
  const { npi } = req.params;
  try {
    const result = await pool.query('SELECT npi, name, hospital, status FROM synthetic_npis WHERE npi = $1', [npi]);
    if (result.rows.length === 0) {
      return res.status(404).send('NPI not found in synthetic validation database.');
    }
    res.json(result.rows[0]);
  } catch (error) {
    console.error(error);
    res.status(500).send('Database error looking up NPI.');
  }
});

// Registration API (with Registry Checks)
app.post('/api/auth/register', async (req, res) => {
  const { fullName, email, phone, role, npi, deviceId, agencyId, patientId, accessKey, specialization, experience, bio } = req.body;
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

    // 2. Perform synthetic registry validations
    if (role === 'doctor') {
      const npiCheck = await pool.query('SELECT * FROM synthetic_npis WHERE npi = $1', [npi]);
      if (npiCheck.rows.length === 0) {
        return res.status(400).send('NPI not found in synthetic validation database.');
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
    const isDoctor = role === 'doctor';
    const insertUser = await pool.query(
      `INSERT INTO users (email, password_hash, full_name, phone, role, npi, device_id, agency_id, patient_id, access_key, approved, specialization, experience, bio)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14) RETURNING id`,
      [
        cleanEmail, 
        'registered_password_hash', 
        fullName, 
        phone || '', 
        role, 
        npi || '', 
        deviceId || '', 
        agencyId || '', 
        patientId || '', 
        accessKey || '', 
        !isDoctor,
        isDoctor ? specialization : null,
        isDoctor && experience ? parseInt(experience, 10) : null,
        isDoctor ? bio : null
      ]
    );
    const newUserId = insertUser.rows[0].id;

    // If role is patient, automatically create their clinical registry patient entry & telemetry
    if (role === 'patient') {
      const patientId = deviceId.trim().toUpperCase().replace('NP-', 'P-');
      const checkPatient = await pool.query('SELECT * FROM patients WHERE id = $1', [patientId]);
      if (checkPatient.rows.length === 0) {
        const roomNumber = deviceId.replace('NP-', '');
        await pool.query(
          `INSERT INTO patients (id, name, age, gender, room, condition, risk, status, ehr_notes, doctor_npi) 
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`,
          [patientId, fullName, 45, 'Male', roomNumber, 'Newly Enrolled Patient', 10, 'Normal', 'Patient enrolled via secure online signup. Vitals stream active.', null]
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

    if (isDoctor) {
      return res.json({
        name: fullName,
        email: cleanEmail,
        phone: phone || '',
        role,
        npi,
        approved: false,
        message: 'Doctor account registered successfully. Verification pending Administrator approval.'
      });
    }

    // Sign JWT token
    const token = jwt.sign(
      { id: newUserId, email: cleanEmail, role, name: fullName },
      JWT_SECRET,
      { expiresIn: '24h' }
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
      accessKey,
      approved: true,
      token
    });
  } catch (error) {
    console.error(error);
    res.status(500).send('Server Error during registration.');
  }
});


// ==================== PATIENT EHR & TELEMETRY ROUTES ====================

// Fetch All Patients List (Optionally filter by attending doctor's NPI)
app.get('/api/patients', authenticateToken, async (req, res) => {
  const { doctorNpi } = req.query;
  try {
    let queryText = `
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
    `;
    const queryValues = [];
    if (doctorNpi) {
      queryText += ' WHERE p.doctor_npi = $1';
      queryValues.push(doctorNpi);
    }
    queryText += ' ORDER BY p.risk DESC';

    const patientsQuery = await pool.query(queryText, queryValues);
    
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
      doctorNpi: row.doctor_npi,
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
app.get('/api/patients/notes', authenticateToken, async (req, res) => {
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
app.put('/api/patients/:id/notes', authenticateToken, async (req, res) => {
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

// Fetch verified doctors list
app.get('/api/doctors', authenticateToken, async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT u.full_name as name, u.npi, sn.hospital, sn.status, u.specialization, u.experience, u.bio 
       FROM users u
       JOIN synthetic_npis sn ON u.npi = sn.npi
       WHERE u.role = 'doctor' AND u.approved = true
       ORDER BY u.full_name ASC`
    );
    res.json(result.rows);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to fetch verified doctors list.');
  }
});

// Update Consulting Doctor for Patient
app.put('/api/patients/:id/doctor', authenticateToken, async (req, res) => {
  const { id } = req.params;
  const { doctorNpi, clinicianName } = req.body;
  try {
    await pool.query(
      'UPDATE patients SET doctor_npi = $1 WHERE id = $2',
      [doctorNpi || null, id]
    );

    // Get doctor name to make audit log friendly
    let docName = 'None';
    if (doctorNpi) {
      const docQuery = await pool.query('SELECT name FROM synthetic_npis WHERE npi = $1', [doctorNpi]);
      if (docQuery.rows.length > 0) {
        docName = docQuery.rows[0].name;
      }
    }

    // Log update audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [clinicianName || 'Patient Portal', 'Assigned Consulting Doctor', `Patient ID: ${id} linked to Doctor: ${docName} (NPI: ${doctorNpi || 'None'})`, 'Success']
    );

    res.send('Consulting doctor updated successfully.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to save consulting doctor.');
  }
});


// ==================== DOCTOR-PATIENT CONNECTION REQUESTS ====================

// Fetch connection requests for the logged-in user
app.get('/api/connections/requests', authenticateToken, async (req, res) => {
  try {
    if (req.user.role === 'doctor') {
      const result = await pool.query(
        `SELECT cr.id, cr.patient_id as "patientId", cr.doctor_npi as "doctorNpi", cr.status, cr.created_at as "createdAt",
                p.name as "patientName", p.condition as "patientCondition", p.risk as "patientRisk"
         FROM connection_requests cr
         JOIN patients p ON cr.patient_id = p.id
         WHERE cr.doctor_npi = $1 AND cr.status = 'Pending'
         ORDER BY cr.created_at DESC`,
        [req.user.npi]
      );
      res.json(result.rows);
    } else if (req.user.role === 'patient' || req.user.role === 'family') {
      const patientId = req.user.patientId || (req.user.deviceId ? req.user.deviceId.replace(/^NP-/i, 'P-') : null);
      if (!patientId) {
        return res.status(400).send('Patient session binding invalid.');
      }
      const result = await pool.query(
        `SELECT cr.id, cr.patient_id as "patientId", cr.doctor_npi as "doctorNpi", cr.status, cr.created_at as "createdAt",
                d.name as "doctorName", d.hospital as "doctorHospital"
         FROM connection_requests cr
         JOIN synthetic_npis d ON cr.doctor_npi = d.npi
         WHERE cr.patient_id = $1
         ORDER BY cr.created_at DESC`,
        [patientId]
      );
      res.json(result.rows);
    } else {
      // Admin/Caregiver: return all pending requests
      const result = await pool.query(
        `SELECT cr.id, cr.patient_id as "patientId", cr.doctor_npi as "doctorNpi", cr.status, cr.created_at as "createdAt",
                p.name as "patientName", d.name as "doctorName"
         FROM connection_requests cr
         JOIN patients p ON cr.patient_id = p.id
         JOIN synthetic_npis d ON cr.doctor_npi = d.npi
         ORDER BY cr.created_at DESC`
      );
      res.json(result.rows);
    }
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to fetch connection requests.');
  }
});

// Create a connection request (Patient -> Doctor)
app.post('/api/connections/requests', authenticateToken, async (req, res) => {
  const { doctorNpi } = req.body;
  const patientId = req.user.patientId || (req.user.deviceId ? req.user.deviceId.replace(/^NP-/i, 'P-') : null);
  
  if (!patientId || !doctorNpi) {
    return res.status(400).send('Invalid request details. Patient ID and Doctor NPI required.');
  }

  try {
    const result = await pool.query(
      `INSERT INTO connection_requests (patient_id, doctor_npi, status) 
       VALUES ($1, $2, 'Pending') 
       ON CONFLICT (patient_id, doctor_npi) 
       DO UPDATE SET status = 'Pending', updated_at = NOW() 
       RETURNING *`,
      [patientId, doctorNpi]
    );

    // Get doctor name for audit log
    const docQuery = await pool.query('SELECT name FROM synthetic_npis WHERE npi = $1', [doctorNpi]);
    const docName = docQuery.rows.length > 0 ? docQuery.rows[0].name : doctorNpi;

    // Log update audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [req.user.name || 'Patient Portal', 'Dispatched Connection Request', `Attending Physician Link: ${docName} (NPI: ${doctorNpi})`, 'Success']
    );

    res.json(result.rows[0]);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to submit connection request.');
  }
});

// Update connection request status (Doctor Approves or Declines)
app.put('/api/connections/requests/:id', authenticateToken, async (req, res) => {
  const { id } = req.params;
  const { status } = req.body; // 'Approved' or 'Declined'

  if (req.user.role !== 'doctor') {
    return res.status(403).send('Unauthorized: Attending clinician authentication required.');
  }

  try {
    const requestQuery = await pool.query('SELECT * FROM connection_requests WHERE id = $1', [id]);
    if (requestQuery.rows.length === 0) {
      return res.status(404).send('Connection request not found.');
    }
    const connReq = requestQuery.rows[0];

    if (status === 'Approved') {
      await pool.query(
        `UPDATE connection_requests SET status = 'Approved', updated_at = NOW() WHERE id = $1`,
        [id]
      );
      // Link doctor NPI to patient record
      await pool.query(
        `UPDATE patients SET doctor_npi = $1 WHERE id = $2`,
        [connReq.doctor_npi, connReq.patient_id]
      );

      // Log update audit log
      await pool.query(
        'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
        [req.user.name, 'Approved Connection Request', `Patient ID: ${connReq.patient_id}`, 'Success']
      );
    } else {
      await pool.query(
        `UPDATE connection_requests SET status = 'Declined', updated_at = NOW() WHERE id = $1`,
        [id]
      );

      // Log update audit log
      await pool.query(
        'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
        [req.user.name, 'Declined Connection Request', `Patient ID: ${connReq.patient_id}`, 'Success']
      );
    }

    res.send(`Connection request ${status.toLowerCase()} successfully.`);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to update connection request.');
  }
});

// Delete connection request (Patient cancels pending connection request)
app.delete('/api/connections/requests/:id', authenticateToken, async (req, res) => {
  const { id } = req.params;
  try {
    const requestQuery = await pool.query('SELECT * FROM connection_requests WHERE id = $1', [id]);
    if (requestQuery.rows.length === 0) {
      return res.status(404).send('Connection request not found.');
    }
    const connReq = requestQuery.rows[0];

    await pool.query('DELETE FROM connection_requests WHERE id = $1', [id]);

    // Log update audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [req.user.name || 'Patient Portal', 'Cancelled Connection Request', `Physician NPI: ${connReq.doctor_npi}`, 'Success']
    );

    res.send('Connection request cancelled.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to cancel connection request.');
  }
});


// ==================== TELEMETRY SIMULATION CONTROLLER ====================

app.post('/api/simulation/trigger', authenticateToken, async (req, res) => {
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

app.get('/api/audit-logs', authenticateToken, async (req, res) => {
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

app.post('/api/audit-logs', authenticateToken, async (req, res) => {
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
app.get('/api/admin/stats', authenticateToken, async (req, res) => {
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

// Admin User Management routes
app.get('/api/admin/users', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).send('Unauthorized: Administrative access key required.');
  }
  try {
    const users = await pool.query(
      `SELECT id, email, full_name as "fullName", phone, role, npi, device_id as "deviceId", 
              agency_id as "agencyId", patient_id as "patientId", access_key as "accessKey", created_at as "createdAt" 
       FROM users 
       ORDER BY created_at DESC`
    );
    res.json(users.rows);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to fetch user accounts directory.');
  }
});

app.delete('/api/admin/users/:id', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).send('Unauthorized: Administrative access key required.');
  }
  const { id } = req.params;
  try {
    // Get user details for logging before deletion
    const userRes = await pool.query('SELECT full_name, email, role FROM users WHERE id = $1', [id]);
    if (userRes.rows.length === 0) {
      return res.status(404).send('User not found.');
    }
    const deletedUser = userRes.rows[0];

    await pool.query('DELETE FROM users WHERE id = $1', [id]);

    // Log HIPAA audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [req.user.name || 'System Admin', 'Revoked User Portal Access', `${deletedUser.full_name} (${deletedUser.email}) [${deletedUser.role.toUpperCase()}]`, 'Success']
    );

    res.send('User account revoked successfully.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to revoke user account.');
  }
});


// GET pending doctor verifications
app.get('/api/admin/pending-doctors', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).send('Unauthorized: Administrative access key required.');
  }
  try {
    const result = await pool.query(
      `SELECT u.id, u.full_name as "fullName", u.email, u.phone, u.npi, sn.hospital, u.created_at as "createdAt"
       FROM users u
       JOIN synthetic_npis sn ON u.npi = sn.npi
       WHERE u.role = 'doctor' AND u.approved = false
       ORDER BY u.created_at DESC`
    );
    res.json(result.rows);
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to fetch pending doctor verifications.');
  }
});

// Approve doctor verification
app.put('/api/admin/doctors/:id/approve', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).send('Unauthorized: Administrative access key required.');
  }
  const { id } = req.params;
  try {
    const userRes = await pool.query('SELECT full_name, email, npi FROM users WHERE id = $1 AND role = \'doctor\'', [id]);
    if (userRes.rows.length === 0) {
      return res.status(404).send('Doctor user not found.');
    }
    const doc = userRes.rows[0];

    await pool.query('UPDATE users SET approved = true WHERE id = $1', [id]);

    // Log HIPAA audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [req.user.name || 'System Admin', 'Approved Professional Doctor Account', `${doc.full_name} (NPI: ${doc.npi})`, 'Success']
    );

    res.send('Doctor approved successfully.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to approve doctor verification.');
  }
});

// Reject doctor registration (purges user record)
app.put('/api/admin/doctors/:id/reject', authenticateToken, async (req, res) => {
  if (req.user.role !== 'admin') {
    return res.status(403).send('Unauthorized: Administrative access key required.');
  }
  const { id } = req.params;
  try {
    const userRes = await pool.query('SELECT full_name, email, npi FROM users WHERE id = $1 AND role = \'doctor\'', [id]);
    if (userRes.rows.length === 0) {
      return res.status(404).send('Doctor user not found.');
    }
    const doc = userRes.rows[0];

    await pool.query('DELETE FROM users WHERE id = $1', [id]);

    // Log HIPAA audit log
    await pool.query(
      'INSERT INTO audit_logs (username, action, target, status) VALUES ($1, $2, $3, $4)',
      [req.user.name || 'System Admin', 'Rejected Professional Doctor Account (Registration Purged)', `${doc.full_name} (NPI: ${doc.npi})`, 'Success']
    );

    res.send('Doctor registration rejected and purged.');
  } catch (error) {
    console.error(error);
    res.status(500).send('Failed to reject doctor registration.');
  }
});


// Rate limiting store for Chatbot API
const chatRateLimits = new Map();

// AI Clinical Chatbot Route
app.post('/api/chat', authenticateToken, async (req, res) => {
  const { message } = req.body;
  if (!message || String(message).trim() === '') {
    return res.status(400).send('Message body is required.');
  }

  const userId = req.user.id;
  const role = req.user.role;
  const name = req.user.name;

  // 1. Enforce rate limiting: max 20 requests per hour per user
  const now = Date.now();
  const limitWindow = 60 * 60 * 1000; // 1 hour
  const limitCount = 20;

  if (!chatRateLimits.has(userId)) {
    chatRateLimits.set(userId, { count: 1, windowStart: now });
  } else {
    const limit = chatRateLimits.get(userId);
    if (now - limit.windowStart > limitWindow) {
      limit.count = 1;
      limit.windowStart = now;
    } else {
      if (limit.count >= limitCount) {
        return res.status(429).send('Rate limit exceeded: Max 20 chatbot queries per hour.');
      }
      limit.count++;
    }
  }

  try {
    let patientId = null;
    let patientContext = '';
    const userContext = { name, role, appointments: [], alerts: [] };

    // Fetch user details from database
    const userRes = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
    if (userRes.rows.length > 0) {
      const dbUser = userRes.rows[0];
      if (role === 'patient') {
        patientId = dbUser.device_id ? dbUser.device_id.trim().toUpperCase().replace('NP-', 'P-') : null;
      } else if (role === 'family') {
        patientId = dbUser.patient_id ? dbUser.patient_id.trim().toUpperCase() : null;
      }
    }

    // 2. Fetch patient's upcoming appointments and recent telemetry alerts if role is patient or family
    if (patientId && (role === 'patient' || role === 'family')) {
      // Query Appointments
      const apptRes = await pool.query(
        'SELECT details, time FROM appointments WHERE patient_id = $1 ORDER BY id ASC',
        [patientId]
      );
      userContext.appointments = apptRes.rows;

      // Query Telemetry/Alerts (last 5 entries)
      const telemetryRes = await pool.query(
        'SELECT timestamp, heart_rate, spo2, temperature, fall_detected FROM telemetry WHERE patient_id = $1 ORDER BY timestamp DESC LIMIT 5',
        [patientId]
      );
      userContext.alerts = telemetryRes.rows;

      // Format clinical context string for system prompt
      const apptStr = userContext.appointments.length > 0
        ? userContext.appointments.map(a => `- ${a.details} (${a.time})`).join('\n')
        : 'None scheduled.';
      
      const recentVitals = userContext.alerts.length > 0 ? userContext.alerts[0] : null;
      const vitalsStr = recentVitals 
        ? `Heart Rate: ${recentVitals.heart_rate} BPM, SpO2: ${recentVitals.spo2}%, Temp: ${recentVitals.temperature}°C, Fall Detected: ${recentVitals.fall_detected}`
        : 'No live vitals data streamed yet.';

      patientContext = `\nPatient File Context (Patient ID: ${patientId}):\n- Upcoming Appointments:\n${apptStr}\n- Latest Biometric Telemetry:\n  ${vitalsStr}`;
    }

    // 3. Assemble System Prompt
    const systemPrompt = `You are the NeuroCare Nexus AI Clinical Assistant, an empathetic, highly professional digital health companion.
Your goal is to answer general questions about remote health monitoring, neuro-wearables (MAX30102, DS18B20, MPU6050), and help patients/family members interpret their dashboard data.

Here is the current clinical and environmental context of the user:
- User Role: ${role}
- User Name: ${name}${patientContext}

Rules:
1. Always maintain a warm, reassuring, and professional tone.
2. Clearly state that your advice is for informational and educational purposes only and cannot replace professional medical consults.
3. If the user presents symptoms of a medical emergency (e.g. chest pain, severe shortness of breath, sudden numbness/paralysis), immediately advise them to call 112 or contact their emergency services.
4. Keep answers concise, actionable, and structured with clean formatting.
5. Refer to their upcoming appointments or recent telemetry alerts where relevant to reassure them or guide them.`;

    // 4. Request completion from LLM API (Groq/OpenAI) or fall back to simulation
    let assistantMessage = '';
    const apiKey = process.env.GROQ_API_KEY || process.env.OPENAI_API_KEY;

    if (apiKey) {
      const isGroq = !!process.env.GROQ_API_KEY;
      const url = isGroq 
        ? 'https://api.groq.com/openai/v1/chat/completions' 
        : 'https://api.openai.com/v1/chat/completions';
      
      const model = isGroq ? 'llama-3.3-70b-specdec' : 'gpt-4o-mini';

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
          model,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: message }
          ],
          temperature: 0.7
        })
      });

      if (response.ok) {
        const data = await response.json();
        assistantMessage = data.choices[0].message.content;
      } else {
        const errorText = await response.text();
        console.error('LLM API Error:', errorText);
        assistantMessage = getSimulatedChatbotResponse(message, userContext);
      }
    } else {
      assistantMessage = getSimulatedChatbotResponse(message, userContext);
    }

    res.json({ response: assistantMessage });
  } catch (error) {
    console.error('Chatbot API Error:', error);
    res.status(500).send('Failed to process request.');
  }
});

// Helper for simulated responses when no API keys are available
function getSimulatedChatbotResponse(message, userContext) {
  const msgLower = message.toLowerCase();
  
  if (msgLower.includes('appointment')) {
    if (userContext.appointments && userContext.appointments.length > 0) {
      const list = userContext.appointments.map(a => `- ${a.details} at ${a.time}`).join('\n');
      return `According to your files, you have the following upcoming appointments:\n${list}\n\nIs there anything specific you would like to prepare for these sessions?`;
    }
    return `I don't see any upcoming appointments scheduled in your local file. If you need to book a consultation, please contact Riverside General Hospital administration.`;
  }
  
  if (msgLower.includes('alert') || msgLower.includes('vitals') || msgLower.includes('heart') || msgLower.includes('spo2') || msgLower.includes('pulse')) {
    if (userContext.alerts && userContext.alerts.length > 0) {
      const recent = userContext.alerts[0];
      return `Checking your wearable telemetry:\n- Heart Rate: ${recent.heart_rate || 'N/A'} BPM\n- SpO₂: ${recent.spo2 || 'N/A'}%\n- Temperature: ${recent.temperature || 'N/A'}°C\n\nYour biometric streams appear stable. Please note that this is a simulated reading. If you are experiencing symptoms, please seek professional care.`;
    }
    return `No active telemetry alerts are on file for your wearable node. Ensure your NeuroPatch device is correctly connected and synced.`;
  }
  
  if (msgLower.includes('fall')) {
    return `The MPU6050 accelerometer sensor tracks sudden changes in velocity. I do not see any fall events logged in your audit ledger. Always wear the device securely on your wrist.`;
  }
  
  return `Hello ${userContext.name}! I am your NeuroCare clinical assistant. I can help explain your wearable vitals (heart rate, SpO₂), track upcoming consultations, or answer general wellness questions. \n\n*General questions only — not medical advice.*`;
}

app.listen(PORT, () => {
  console.log(`NeuroCare Nexus Backend server listening on port ${PORT}`);
});
