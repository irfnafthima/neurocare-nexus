-- Seed validation registries for Project Neurocare Nexus
-- (No active patients, telemetry, or audit logs are seeded to ensure a clean database)

-- Seed Synthetic NPIs (Simulated Provider Register)
INSERT INTO synthetic_npis (npi, name, hospital, status) VALUES
('1982039485', 'Dr. Sarah Jenkins', 'City Care Medical Center', 'Active - Verified Registry'),
('1092837465', 'Dr. Michael Chang', 'Riverside General Hospital', 'Active - Verified Registry'),
('1827364509', 'Dr. Elizabeth Vance', 'Apex Valley Hospital', 'Active - Verified Registry'),
('1029384756', 'Dr. Rachel Kim', 'Pacific Horizon Medical Center', 'Active - Verified Registry'),
('1203948576', 'Dr. Samuel Torres', 'Riverside General Hospital', 'Active - Verified Registry'),
('1492039482', 'Dr. Lisa Wang', 'City Care Medical Center', 'Active - Verified Registry'),
('1738291049', 'Dr. David Foster', 'Apex Valley Hospital', 'Active - Verified Registry'),
('1102938475', 'Dr. James Carter', 'Pacific Horizon Medical Center', 'Active - Verified Registry');

-- Seed Synthetic wearable device serial registers
INSERT INTO synthetic_devices (serial, mac, status) VALUES
('NP-101', '00:1B:44:11:3A:A1', 'Pre-registered / Unassigned'),
('NP-102', '00:1B:44:11:3A:B7', 'Pre-registered / Unassigned'),
('NP-103', '00:1B:44:11:3B:C5', 'Pre-registered / Unassigned'),
('NP-204', '00:1B:44:11:3C:A9', 'Pre-registered / Unassigned'),
('NP-108', '00:1B:44:11:3E:D2', 'Pre-registered / Unassigned'),
('NP-215', '00:1B:44:11:4A:11', 'Pre-registered / Unassigned'),
('NP-112', '00:1B:44:11:4B:22', 'Pre-registered / Unassigned'),
('NP-305', '00:1B:44:11:5C:33', 'Pre-registered / Unassigned');

-- Seed Synthetic caregiver agency certificates
INSERT INTO synthetic_caregivers (agency_id, name, agency, status) VALUES
('CG-204', 'Maria Santos, RN', 'Beacon Home Health Services', 'Active License'),
('CG-105', 'David Miller, LPN', 'Metro Visiting Nurses', 'Active License'),
('CG-302', 'Jessica Taylor, CNA', 'Apex Care Network', 'Active License'),
('CG-118', 'Robert Chen, RN', 'Beacon Home Health Services', 'Active License'),
('CG-245', 'Emily Watson, LPN', 'Metro Visiting Nurses', 'Active License');

-- Seed Synthetic patient access tokens
INSERT INTO synthetic_patients (patient_id, code, patient_name, status) VALUES
('P-102', 'P-102', 'Sarah Johnson', 'Consent Verified'),
('P-204', 'P-204', 'Marcus Williams', 'Consent Verified'),
('P-108', 'P-108', 'Elena Rodriguez', 'Consent Verified'),
('P-215', 'P-215', 'James Smith', 'Consent Verified'),
('P-112', 'P-112', 'Linda Davis', 'Consent Verified'),
('P-305', 'P-305', 'William Miller', 'Consent Verified');


