-- Seed validation registries for Project Neurocare Nexus
-- (No active patients, telemetry, or audit logs are seeded to ensure a clean database)

-- Seed Synthetic NPIs (CMS NPPES Provider Register)
INSERT INTO synthetic_npis (npi, name, hospital, status) VALUES
('1982039485', 'Dr. Sarah Jenkins', 'Mayo Clinic', 'Active - NPPES Verified'),
('1092837465', 'Dr. Michael Chang', 'Mass General Hospital', 'Active - NPPES Verified'),
('1827364509', 'Dr. Elizabeth Vance', 'Johns Hopkins Medicine', 'Active - NPPES Verified'),
('1029384756', 'Dr. Rachel Kim', 'Stanford Health Care', 'Active - NPPES Verified');

-- Seed Synthetic wearable device serial registers
INSERT INTO synthetic_devices (serial, mac, status) VALUES
('NP-101', '00:1B:44:11:3A:A1', 'Pre-registered / Unassigned'),
('NP-102', '00:1B:44:11:3A:B7', 'Pre-registered / Unassigned'),
('NP-103', '00:1B:44:11:3B:C5', 'Pre-registered / Unassigned'),
('NP-204', '00:1B:44:11:3C:A9', 'Pre-registered / Unassigned'),
('NP-108', '00:1B:44:11:3E:D2', 'Pre-registered / Unassigned'),
('NP-215', '00:1B:44:11:4A:11', 'Pre-registered / Unassigned');

-- Seed Synthetic caregiver agency certificates
INSERT INTO synthetic_caregivers (agency_id, name, agency, status) VALUES
('CG-204', 'Maria Santos, RN', 'Bayada Home Health Care', 'Active License'),
('CG-105', 'David Miller, LPN', 'Visiting Nurse Service', 'Active License'),
('CG-302', 'Jessica Taylor, CNA', 'Interim HealthCare', 'Active License');

-- Seed Synthetic patient access tokens
INSERT INTO synthetic_patients (patient_id, code, patient_name, status) VALUES
('P-102', 'P-102', 'Sarah Johnson', 'Consent Verified'),
('P-204', 'P-204', 'Marcus Williams', 'Consent Verified'),
('P-108', 'P-108', 'Elena Rodriguez', 'Consent Verified'),
('P-215', 'P-215', 'James Smith', 'Consent Verified'),
('P-112', 'P-112', 'Linda Davis', 'Consent Verified');
