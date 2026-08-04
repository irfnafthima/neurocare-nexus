/**
 * Mock database for Project Neurocare Nexus.
 * Structures physiological telemetry strictly around specified physical sensors:
 * - MAX30102 (Heart Rate, SpO2)
 * - DS18B20 (Body Temperature)
 * - MPU6050 (3-Axis Acceleration, 3-Axis Gyroscope, Fall Detection)
 * - ESP32 (Diagnostics: Status, Battery, RSSI)
 */

export const mockPatients = [
  {
    id: 'P-102',
    name: 'Sarah Johnson',
    age: 72,
    gender: 'Female',
    room: '102',
    condition: 'Heart Failure Post-op',
    risk: 12,
    status: 'Normal',
    color: '#10B981',
    vitals: {
      max30102: { heartRate: 72, spo2: 98 },
      ds18b20: { temperature: 36.8 },
      mpu6050: { 
        accelX: 0.05, accelY: 0.98, accelZ: 0.04, 
        gyroX: 0.5, gyroY: -1.2, gyroZ: 0.3, 
        fallDetected: false 
      },
      esp32: { connected: true, battery: 92, rssi: -65 }
    }
  },
  {
    id: 'P-204',
    name: 'Marcus Williams',
    age: 68,
    gender: 'Male',
    room: '204',
    condition: 'Severe AFib Risk',
    risk: 85,
    status: 'Critical',
    color: '#EF4444',
    vitals: {
      max30102: { heartRate: 118, spo2: 94 },
      ds18b20: { temperature: 37.1 },
      mpu6050: { 
        accelX: 0.12, accelY: 0.85, accelZ: -0.22, 
        gyroX: 2.1, gyroY: 3.4, gyroZ: -1.5, 
        fallDetected: false 
      },
      esp32: { connected: true, battery: 42, rssi: -72 }
    }
  },
  {
    id: 'P-108',
    name: 'Elena Rodriguez',
    age: 45,
    gender: 'Female',
    room: '108',
    condition: 'Hypertension Tracking',
    risk: 45,
    status: 'Warning',
    color: '#F59E0B',
    vitals: {
      max30102: { heartRate: 88, spo2: 97 },
      ds18b20: { temperature: 38.2 },
      mpu6050: { 
        accelX: -0.02, accelY: 0.99, accelZ: 0.01, 
        gyroX: -0.2, gyroY: 0.1, gyroZ: 0.0, 
        fallDetected: false 
      },
      esp32: { connected: true, battery: 80, rssi: -68 }
    }
  },
  {
    id: 'P-215',
    name: 'James Smith',
    age: 74,
    gender: 'Male',
    room: '215',
    condition: 'Post-Stroke Telemetry',
    risk: 18,
    status: 'Normal',
    color: '#10B981',
    vitals: {
      max30102: { heartRate: 65, spo2: 99 },
      ds18b20: { temperature: 36.6 },
      mpu6050: { 
        accelX: 0.01, accelY: 0.97, accelZ: 0.08, 
        gyroX: 0.2, gyroY: -0.5, gyroZ: 0.2, 
        fallDetected: false 
      },
      esp32: { connected: true, battery: 14, rssi: -85 }
    }
  },
  {
    id: 'P-112',
    name: 'Linda Davis',
    age: 61,
    gender: 'Female',
    room: '112',
    condition: 'COPD & Cardiac Review',
    risk: 65,
    status: 'Critical',
    color: '#EF4444',
    vitals: {
      max30102: { heartRate: 90, spo2: 89 },
      ds18b20: { temperature: 37.0 },
      mpu6050: { 
        accelX: 0.08, accelY: 0.94, accelZ: 0.11, 
        gyroX: 1.1, gyroY: -2.1, gyroZ: 1.8, 
        fallDetected: false 
      },
      esp32: { connected: true, battery: 74, rssi: -70 }
    }
  }
];

export const mockHospitals = [
  { id: 'H-01', name: 'Mass General Hospital', location: 'Boston, MA', status: 'Online', systems: 'External Health Record Sync (Simulated)', usersCount: 450 },
  { id: 'H-02', name: 'Johns Hopkins Medicine', location: 'Baltimore, MD', status: 'Online', systems: 'Cerner Integration (Simulated)', usersCount: 312 },
  { id: 'H-03', name: 'Brigham Health', location: 'Boston, MA', status: 'Online', systems: 'External Health Record Sync (Simulated)', usersCount: 189 },
  { id: 'H-04', name: 'Stanford Health Care', location: 'Stanford, CA', status: 'Offline-Maintenance', systems: 'HL7 Legacy Engine', usersCount: 94 }
];

export const mockDevices = [
  { mac: '00:1B:44:11:3A:B7', id: 'NP-102', room: '102', battery: '92%', rssi: '-65dBm', status: 'Synced', patient: 'Sarah Johnson' },
  { mac: '00:1B:44:11:3C:A9', id: 'NP-204', room: '204', battery: '42%', rssi: '-70dBm', status: 'Synced', patient: 'Marcus Williams' },
  { mac: '00:1B:44:11:3E:D2', id: 'NP-108', room: '108', battery: '80%', rssi: '-68dBm', status: 'Synced', patient: 'Elena Rodriguez' },
  { mac: '00:1B:44:11:4A:11', id: 'NP-215', room: '215', battery: '14%', rssi: '-85dBm', status: 'Low Battery Alert', patient: 'James Smith' }
];

export const mockAccessList = [
  { name: 'Dr. Rachel Kim', role: 'Physician / Cardiologist', status: 'Authorized', accessType: 'Read/Write EHR', activity: '2m ago' },
  { name: 'Maria Santos, RN', role: 'Nurse Practitioner', status: 'Authorized', accessType: 'Read/Write EHR', activity: '15m ago' },
  { name: 'Dr. Samuel Torres', role: 'Physician / Neurologist', status: 'Authorized', accessType: 'Read/Write EHR', activity: '1h ago' },
  { name: 'Admin Root User', role: 'System Admin', status: 'Authorized', accessType: 'Full Root Access', activity: 'Just Now' }
];

export const seedAuditLogs = [
  { id: 'AUD-3021', time: '12:15 PM', user: 'Dr. Rachel Kim', action: 'Accessed Patient EHR file', target: 'Sarah Johnson (ID: P-102)', status: 'Success' },
  { id: 'AUD-3022', time: '12:02 PM', user: 'Maria Santos, RN', action: 'Modified Care Notes', target: 'Elena Rodriguez (ID: P-108)', status: 'Success' },
  { id: 'AUD-3023', time: '11:45 AM', user: 'Dr. Samuel Torres', action: 'Downloaded Holter ECG report', target: 'Marcus Williams (ID: P-204)', status: 'Success' },
  { id: 'AUD-3024', time: '11:15 AM', user: 'ESP32 IoT Bridge', action: 'Automated telemetry packet sync', target: 'All active rooms', status: 'Success' }
];

export const seedAlarms = [
  { id: 1, type: 'critical', desc: 'MAX30102: Marcus Williams arrhythmia threshold exceeded', time: '2m ago', patient: 'Marcus Williams', isCritical: true },
  { id: 2, type: 'warning', desc: 'DS18B20: Elena Rodriguez elevated temp (38.2°C)', time: '15m ago', patient: 'Elena Rodriguez', isCritical: false },
  { id: 3, type: 'normal', desc: 'ESP32: Device synced: NeuroPatch NP-102 calibrated', time: '1h ago', patient: 'Sarah Johnson', isCritical: false }
];

// Synthetic registries for credentials validation
export const syntheticNpis = [
  { npi: '1982039485', name: 'Dr. Sarah Jenkins', hospital: 'Mayo Clinic', status: 'Active - NPPES Verified' },
  { npi: '1092837465', name: 'Dr. Michael Chang', hospital: 'Mass General Hospital', status: 'Active - NPPES Verified' },
  { npi: '1827364509', name: 'Dr. Elizabeth Vance', hospital: 'Johns Hopkins Medicine', status: 'Active - NPPES Verified' },
  { npi: '1029384756', name: 'Dr. Rachel Kim', hospital: 'Stanford Health Care', status: 'Active - NPPES Verified' },
  { npi: '1203948576', name: 'Dr. Samuel Torres', hospital: 'Mass General Hospital', status: 'Active - NPPES Verified' },
  { npi: '1492039482', name: 'Dr. Lisa Wang', hospital: 'Mayo Clinic', status: 'Active - NPPES Verified' },
  { npi: '1738291049', name: 'Dr. David Foster', hospital: 'Johns Hopkins Medicine', status: 'Active - NPPES Verified' },
  { npi: '1102938475', name: 'Dr. James Carter', hospital: 'Stanford Health Care', status: 'Active - NPPES Verified' }
];

export const syntheticDeviceSerials = [
  { serial: 'NP-101', mac: '00:1B:44:11:3A:A1', status: 'Pre-registered / Unassigned' },
  { serial: 'NP-102', mac: '00:1B:44:11:3A:B7', status: 'Assigned - Sarah Johnson' },
  { serial: 'NP-103', mac: '00:1B:44:11:3B:C5', status: 'Pre-registered / Unassigned' },
  { serial: 'NP-204', mac: '00:1B:44:11:3C:A9', status: 'Assigned - Marcus Williams' },
  { serial: 'NP-108', mac: '00:1B:44:11:3E:D2', status: 'Assigned - Elena Rodriguez' },
  { serial: 'NP-215', mac: '00:1B:44:11:4A:11', status: 'Assigned - James Smith' },
  { serial: 'NP-112', mac: '00:1B:44:11:4B:22', status: 'Pre-registered / Unassigned' },
  { serial: 'NP-305', mac: '00:1B:44:11:5C:33', status: 'Pre-registered / Unassigned' }
];

export const syntheticCaregivers = [
  { agencyId: 'CG-204', name: 'Maria Santos, RN', agency: 'Bayada Home Health Care', status: 'Active License' },
  { agencyId: 'CG-105', name: 'David Miller, LPN', agency: 'Visiting Nurse Service', status: 'Active License' },
  { agencyId: 'CG-302', name: 'Jessica Taylor, CNA', agency: 'Interim HealthCare', status: 'Active License' },
  { agencyId: 'CG-118', name: 'Robert Chen, RN', agency: 'Bayada Home Health Care', status: 'Active License' },
  { agencyId: 'CG-245', name: 'Emily Watson, LPN', agency: 'Visiting Nurse Service', status: 'Active License' }
];

export const syntheticPatients = [
  { patientId: 'P-102', code: 'P-102', patientName: 'Sarah Johnson', status: 'Consent Verified' },
  { patientId: 'P-204', code: 'P-204', patientName: 'Marcus Williams', status: 'Consent Verified' },
  { patientId: 'P-108', code: 'P-108', patientName: 'Elena Rodriguez', status: 'Consent Verified' },
  { patientId: 'P-215', code: 'P-215', patientName: 'James Smith', status: 'Consent Verified' },
  { patientId: 'P-112', code: 'P-112', patientName: 'Linda Davis', status: 'Consent Verified' },
  { patientId: 'P-305', code: 'P-305', patientName: 'William Miller', status: 'Consent Verified' }
];

