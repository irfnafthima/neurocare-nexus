"""
NeuroCare Nexus â€” Synthetic Reference Data Generator
=====================================================

PURPOSE:
    Generates synthetic professional healthcare reference datasets for the
    NeuroCare Nexus academic AI-IoT Remote Patient Monitoring prototype.

IMPORTANT DISCLAIMER:
    All records in this dataset are ENTIRELY FICTIONAL and SYNTHETIC.
    They do NOT represent real doctors, real medical registrations, real
    disciplinary actions, or real hospital affiliations.

    The schema structure is inspired by:
      - National Medical Commission (NMC) Indian Medical Register (IMR) concepts
      - Ayushman Bharat Digital Mission (ABDM) Healthcare Professional Registry (HPR)
      - ABDM Health Facility Registry (HFR)

    Individual records do NOT come from these registries and MUST NOT be
    treated as authoritative data from any official Indian medical body.

USAGE:
    python generate_reference_data.py

OUTPUT:
    Writes CSV files to: backend/reference_data/
    Writes summary JSON to: backend/reference_data/reference_data_summary.json

Author: NeuroCare Nexus Academic Team
"""

import csv
import json
import os
import random
import sys
import unicodedata
from datetime import date, timedelta

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SEED â€” fixed seed for reproducibility
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reference_data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CONTROLLED VOCABULARY
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

STATES_CONFIG = [
    # (State name, state code, council name, synthetic doctor count)
    # Synthetic distribution — NOT real population statistics
    # Total sums to exactly 5000
    ('Kerala',               'KER', 'Kerala Medical Council',               410),
    ('Tamil Nadu',           'TN',  'Tamil Nadu Medical Council',           650),
    ('Karnataka',            'KA',  'Karnataka Medical Council',            600),
    ('Maharashtra',          'MH',  'Maharashtra Medical Council',          600),
    ('Delhi',                'DL',  'Delhi Medical Council',                350),
    ('Telangana',            'TG',  'Telangana State Medical Council',      300),
    ('Andhra Pradesh',       'AP',  'Andhra Pradesh Medical Council',       300),
    ('West Bengal',          'WB',  'West Bengal Medical Council',          300),
    ('Gujarat',              'GJ',  'Gujarat Medical Council',              250),
    ('Uttar Pradesh',        'UP',  'Uttar Pradesh Medical Council',        250),
    ('Rajasthan',            'RJ',  'Rajasthan Medical Council',            200),
    ('Punjab',               'PB',  'Punjab Medical Council',               100),
    ('Madhya Pradesh',       'MP',  'Madhya Pradesh Medical Council',        80),
    ('Haryana',              'HR',  'Haryana Medical Council',               80),
    ('Odisha',               'OD',  'Odisha Medical Council',                70),
    ('Bihar',                'BR',  'Bihar Medical Council',                 50),
    ('Uttarakhand',          'UK',  'Uttarakhand Medical Council',           50),
    ('Goa',                  'GA',  'Goa Medical Council',                   50),
    ('Jammu & Kashmir',      'JK',  'Jammu and Kashmir Medical Council',     50),
    ('Assam',                'AS',  'Assam Medical Council',                 30),
    ('Jharkhand',            'JH',  'Jharkhand Medical Council',             30),
    ('Himachal Pradesh',     'HP',  'Himachal Pradesh Medical Council',      30),
    ('Chhattisgarh',         'CG',  'Chhattisgarh Medical Council',          30),
    ('Manipur',              'MN',  'Manipur Medical Council',               20),
    ('Meghalaya',            'ML',  'Meghalaya Medical Council',             20),
    ('Tripura',              'TR',  'Tripura Medical Council',               20),
    ('Puducherry',           'PY',  'Puducherry Medical Council',            20),
    ('Chandigarh',           'CH',  'Chandigarh Medical Council',            20),
    ('Nagaland',             'NL',  'Nagaland Medical Council',              10),
    ('Arunachal Pradesh',    'AR',  'Arunachal Pradesh Medical Council',     10),
    ('Mizoram',              'MZ',  'Mizoram Medical Council',               10),
    ('Sikkim',               'SK',  'Sikkim Medical Council',                 5),
    ('Lakshadweep',          'LD',  'Lakshadweep Medical Council',            5),
]


TOTAL_DOCTORS = 5000
# Internal validation
assert sum(c for *_, c in STATES_CONFIG) == TOTAL_DOCTORS, (
    f"STATES_CONFIG total {sum(c for *_, c in STATES_CONFIG)} != {TOTAL_DOCTORS}"
)




SPECIALIZATIONS = [
    'General Medicine',
    'General Surgery',
    'Cardiology',
    'Neurology',
    'Neurosurgery',
    'Orthopedics',
    'Pediatrics',
    'Obstetrics and Gynecology',
    'Dermatology',
    'Psychiatry',
    'ENT',
    'Ophthalmology',
    'Pulmonology',
    'Gastroenterology',
    'Nephrology',
    'Endocrinology',
    'Oncology',
    'Radiology',
    'Anesthesiology',
    'Emergency Medicine',
    'Urology',
    'Rheumatology',
    'Diabetology',
]

QUALIFICATIONS = [
    'MBBS',
    'MBBS, MD',
    'MBBS, MS',
    'MBBS, DNB',
    'MBBS, MD, DM',
    'MBBS, MS, MCh',
    'MBBS, MD, DNB',
    'MBBS, MS, DNB',
]

QUAL_WEIGHTS = [15, 25, 20, 15, 10, 5, 5, 5]

REGISTRATION_STATUS = ['ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE', 'RETIRED']

FACILITY_TYPES = [
    'PRIVATE_HOSPITAL',
    'GOVERNMENT_HOSPITAL',
    'MEDICAL_COLLEGE_HOSPITAL',
    'SPECIALTY_HOSPITAL',
    'CLINIC',
    'HEALTHCARE_CENTRE',
]

EMPLOYMENT_TYPES = [
    'FULL_TIME',
    'PART_TIME',
    'VISITING_CONSULTANT',
    'CONSULTANT',
    'RESIDENT',
]

DESIGNATIONS = [
    'Senior Consultant',
    'Consultant',
    'Associate Consultant',
    'Junior Consultant',
    'Resident Physician',
    'Senior Resident',
    'Junior Resident',
    'Head of Department',
    'Medical Officer',
    'Registrar',
]

DEPARTMENTS = [
    'Department of Medicine',
    'Department of Surgery',
    'Department of Cardiology',
    'Department of Neurology',
    'Department of Neurosurgery',
    'Department of Orthopedics',
    'Department of Pediatrics',
    'Department of Obstetrics',
    'Department of Dermatology',
    'Department of Psychiatry',
    'Department of ENT',
    'Department of Ophthalmology',
    'Department of Pulmonology',
    'Department of Gastroenterology',
    'Department of Nephrology',
    'Department of Endocrinology',
    'Department of Oncology',
    'Department of Radiology',
    'Department of Anesthesiology',
    'Department of Emergency Medicine',
]

DISCIPLINARY_ACTIONS = {
    'SUSPENSION': 100,
    'BLACKLIST': 20,
    'RESTORATION': 20,
    'REMOVAL': 10,
}

DISC_REMARKS = "Synthetic test record; not a real disciplinary record."

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SYNTHETIC INDIAN NAME POOLS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FIRST_NAMES_MALE = [
    'Aarav', 'Aditya', 'Akash', 'Anand', 'Arjun', 'Arvind', 'Ashok', 'Balaji',
    'Deepak', 'Dinesh', 'Ganesh', 'Girish', 'Gopal', 'Hari', 'Harish', 'Jagadish',
    'Jayan', 'Kiran', 'Krishna', 'Kumar', 'Mahesh', 'Manoj', 'Mohan', 'Murali',
    'Naresh', 'Naveen', 'Nikhil', 'Nishant', 'Pavan', 'Prakash', 'Prasad',
    'Praveen', 'Priya', 'Rahul', 'Rajesh', 'Rakesh', 'Ram', 'Ramesh', 'Ravi',
    'Rohit', 'Sachin', 'Sameer', 'Sanjay', 'Santosh', 'Sathish', 'Shekhar',
    'Shiv', 'Shyam', 'Srikanth', 'Srinivas', 'Sudhir', 'Sunil', 'Suresh',
    'Vijay', 'Vinod', 'Vishal', 'Vivek', 'Yogesh', 'Suresh', 'Venkatesh',
]

FIRST_NAMES_FEMALE = [
    'Akanksha', 'Ambika', 'Amita', 'Amruta', 'Ananya', 'Anjali', 'Anupama',
    'Archana', 'Asha', 'Ashwini', 'Bhavana', 'Deepa', 'Divya', 'Geetha',
    'Geeta', 'Indira', 'Jayalakshmi', 'Jyothi', 'Kavitha', 'Kiran', 'Lakshmi',
    'Lavanya', 'Leena', 'Madhavi', 'Mamta', 'Manasa', 'Meena', 'Meenakshi',
    'Mythili', 'Nandita', 'Nisha', 'Padmaja', 'Padmini', 'Parvathi', 'Pooja',
    'Preethi', 'Priya', 'Radha', 'Rajani', 'Rajini', 'Rekha', 'Revathi',
    'Rohini', 'Saritha', 'Savitha', 'Shilpa', 'Shobha', 'Sindhu', 'Sonal',
    'Sreedevi', 'Sudha', 'Sunita', 'Sushma', 'Usha', 'Vandana', 'Vasantha',
    'Vimala', 'Yashodha', 'Zarina', 'Nandini',
]

LAST_NAMES_KERALA = [
    'Menon', 'Nair', 'Pillai', 'Varma', 'Mohan', 'Krishnan', 'Kurup',
    'Panicker', 'Namboothiri', 'Iyer', 'Suresh', 'George', 'Thomas', 'Joseph',
    'Philip', 'Mathew', 'John', 'Abraham', 'Paul', 'Jacob',
]
LAST_NAMES_TN = [
    'Murugan', 'Rajan', 'Krishnamurthy', 'Sundaram', 'Annamalai', 'Subramaniam',
    'Shanmugam', 'Venkatesan', 'Ramaswamy', 'Balakrishnan', 'Subramanian',
    'Natarajan', 'Annamalai', 'Devarajan', 'Sekar', 'Kumar', 'Raja', 'Raj',
]
LAST_NAMES_KA = [
    'Gowda', 'Reddy', 'Naik', 'Hegde', 'Rao', 'Patil', 'Shetty', 'Kamath',
    'Bhat', 'Kulkarni', 'Nayak', 'Murthy', 'Swamy', 'Prasad', 'Raju',
]
LAST_NAMES_MH = [
    'Deshmukh', 'Patil', 'Kulkarni', 'Joshi', 'Deshpande', 'More', 'Naik',
    'Sawant', 'Pawar', 'Rane', 'Shinde', 'Salvi', 'Bhosale', 'Jadhav',
]
LAST_NAMES_DL = [
    'Sharma', 'Verma', 'Singh', 'Kumar', 'Gupta', 'Agarwal', 'Saxena',
    'Kapoor', 'Malhotra', 'Chopra', 'Chawla', 'Sinha', 'Pandey',
]
LAST_NAMES_GENERIC = [
    'Reddy', 'Rao', 'Kumar', 'Singh', 'Sharma', 'Patel', 'Shah', 'Mehta',
    'Jain', 'Gupta', 'Mishra', 'Prasad', 'Chandra', 'Das', 'Dey', 'Babu',
    'Anand', 'Varma', 'Nair', 'Iyer',
]

STATE_LASTNAMES = {
    'Kerala': LAST_NAMES_KERALA,
    'Tamil Nadu': LAST_NAMES_TN,
    'Karnataka': LAST_NAMES_KA,
    'Maharashtra': LAST_NAMES_MH,
    'Delhi': LAST_NAMES_DL,
}


def pick_last_name(state):
    pool = STATE_LASTNAMES.get(state, LAST_NAMES_GENERIC)
    return random.choice(pool)


def pick_first_name():
    all_names = FIRST_NAMES_MALE + FIRST_NAMES_FEMALE
    return random.choice(all_names)


def generate_doctor_name(state):
    first = pick_first_name()
    last = pick_last_name(state)
    return f"{first} {last}"


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# NAME NORMALIZER
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def normalize_name(raw_name: str) -> str:
    """
    Normalizes a doctor name for registry comparison.

    Steps:
      1. Strip leading/trailing whitespace
      2. Remove common medical titles (Dr., Dr, Doctor, Prof., Prof)
      3. Normalize unicode characters to ASCII equivalents
      4. Remove punctuation except spaces
      5. Collapse multiple spaces to single space
      6. Convert to UPPERCASE

    Example:
      "Dr. Ananya Menon"  -> "ANANYA MENON"
      "Prof. Ravi  Kumar" -> "RAVI KUMAR"
      "ananya  menon"     -> "ANANYA MENON"
    """
    if not raw_name:
        return ''
    name = raw_name.strip()
    # Remove titles
    import re
    name = re.sub(
        r'^(Dr\.?\s*|Doctor\s*|Prof\.?\s*|Professor\s*)',
        '', name, flags=re.IGNORECASE
    )
    # Normalize unicode to ASCII
    name = unicodedata.normalize('NFKD', name)
    name = ''.join(c for c in name if not unicodedata.combining(c))
    # Remove punctuation except spaces
    name = re.sub(r'[^a-zA-Z\s]', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name.upper()


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# DATE HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def random_date(start_year=1985, end_year=2023):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def format_date(d):
    return d.strftime('%Y-%m-%d') if d else ''


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 1. GENERATE REFERENCE DOCTORS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_reference_doctors():
    print("Generating reference_doctors.csv ...")
    records = []
    global_counter = 1

    # Build flat state list honoring exact counts
    # STATES_CONFIG already sums to exactly TOTAL_DOCTORS via auto-adjustment
    state_slots = []
    for state, code, council, count in STATES_CONFIG:
        state_slots.extend([(state, code, council)] * count)

    # Verify exactly TOTAL_DOCTORS slots
    assert len(state_slots) == TOTAL_DOCTORS, (
        f"State slots sum to {len(state_slots)}, expected {TOTAL_DOCTORS}"
    )

    random.shuffle(state_slots)
    seen_reg_numbers = set()


    for state, code, council in state_slots:
        # Unique registration number
        while True:
            num_str = f"{global_counter:06d}"
            reg_num = f"SYN-{code}-MED-{num_str}"
            if reg_num not in seen_reg_numbers:
                seen_reg_numbers.add(reg_num)
                break
            global_counter += 1

        ref_id = f"REF-{code}-{num_str}"
        doctor_name = generate_doctor_name(state)
        normalized = normalize_name(doctor_name)
        reg_year = random.randint(1985, 2023)
        reg_date = date(reg_year, random.randint(1, 12), random.randint(1, 28))
        qualification = random.choices(QUALIFICATIONS, weights=QUAL_WEIGHTS, k=1)[0]
        specialization = random.choice(SPECIALIZATIONS)
        reg_status = random.choices(
            ['ACTIVE', 'INACTIVE', 'RETIRED'],
            weights=[85, 10, 5], k=1
        )[0]

        records.append({
            'reference_id': ref_id,
            'registration_number': reg_num,
            'doctor_name': doctor_name,
            'normalized_name': normalized,
            'state_medical_council': council,
            'registration_year': reg_year,
            'registration_date': format_date(reg_date),
            'qualification': qualification,
            'specialization': specialization,
            'registration_status': reg_status,
            'source_type': 'SYNTHETIC_REFERENCE',
            'source_reference': 'NMC_IMR_STRUCTURE_REFERENCE',
            'source_year': 2024,
        })
        global_counter += 1

    write_csv(
        os.path.join(OUTPUT_DIR, 'reference_doctors.csv'),
        records,
        fieldnames=[
            'reference_id', 'registration_number', 'doctor_name', 'normalized_name',
            'state_medical_council', 'registration_year', 'registration_date',
            'qualification', 'specialization', 'registration_status',
            'source_type', 'source_reference', 'source_year',
        ]
    )
    print(f"  âœ“ {len(records)} doctor records written.")
    return records


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 2. GENERATE REFERENCE FACILITIES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

FACILITY_CITIES = {
    'Kerala': ['Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Thrissur', 'Kannur', 'Palakkad'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Tirunelveli'],
    'Karnataka': ['Bengaluru', 'Mysuru', 'Hubballi', 'Mangaluru', 'Belagavi', 'Kalaburagi'],
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Aurangabad', 'Solapur'],
    'Delhi': ['New Delhi', 'North Delhi', 'South Delhi', 'East Delhi', 'West Delhi'],
    'Telangana': ['Hyderabad', 'Warangal', 'Karimnagar', 'Nizamabad', 'Khammam'],
    'Andhra Pradesh': ['Vijayawada', 'Visakhapatnam', 'Tirupati', 'Guntur', 'Rajahmundry'],
    'West Bengal': ['Kolkata', 'Howrah', 'Durgapur', 'Asansol', 'Siliguri'],
    'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar'],
    'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Ajmer'],
    'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Agra', 'Varanasi', 'Allahabad'],
    'Punjab': ['Chandigarh', 'Ludhiana', 'Amritsar', 'Jalandhar'],
    'Haryana': ['Gurugram', 'Faridabad', 'Ambala', 'Rohtak'],
    'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur'],
    'Odisha': ['Bhubaneswar', 'Cuttack', 'Rourkela'],
    'Bihar': ['Patna', 'Gaya', 'Muzaffarpur'],
    'Jharkhand': ['Ranchi', 'Jamshedpur', 'Dhanbad'],
    'Assam': ['Guwahati', 'Dibrugarh', 'Silchar'],
    'Himachal Pradesh': ['Shimla', 'Dharamshala', 'Kullu'],
    'Chhattisgarh': ['Raipur', 'Bhilai', 'Bilaspur'],
}

FACILITY_SUFFIXES = [
    'Medical Centre', 'Hospital', 'Healthcare Institute', 'Health Centre',
    'Medical Institute', 'Specialty Hospital', 'Wellness Centre', 'Medical Academy',
    'Research Hospital', 'Medical Foundation',
]


def generate_reference_facilities():
    print("Generating reference_facilities.csv ...")
    records = []
    all_states = list(FACILITY_CITIES.keys())

    facility_counter = 1
    seen_fac_ids = set()

    # Distribute 500 across states
    per_state_base = 500 // len(all_states)
    remainder = 500 % len(all_states)
    state_counts = {s: per_state_base for s in all_states}
    for s in random.sample(all_states, remainder):
        state_counts[s] += 1

    for state, count in state_counts.items():
        cities = FACILITY_CITIES.get(state, ['City'])
        state_code = next((c for _, c, _, _ in STATES_CONFIG if _ == 0 or True), 'GN')
        sc = next((code for st, code, *_ in STATES_CONFIG if st == state), 'GN')

        for i in range(count):
            fac_num = f"{facility_counter:04d}"
            fac_id = f"FAC-{sc}-{fac_num}"
            if fac_id in seen_fac_ids:
                fac_id = f"FAC-{sc}-X{fac_num}"
            seen_fac_ids.add(fac_id)

            fac_type = random.choice(FACILITY_TYPES)
            city = random.choice(cities)

            if fac_type == 'MEDICAL_COLLEGE_HOSPITAL':
                name = f"NeuroCare Reference Medical College & Hospital {fac_num}"
            elif fac_type == 'GOVERNMENT_HOSPITAL':
                name = f"NeuroCare Reference Government Hospital {fac_num}"
            elif fac_type == 'CLINIC':
                name = f"NeuroCare Reference Clinic {fac_num}"
            elif fac_type == 'SPECIALTY_HOSPITAL':
                name = f"NeuroCare Reference Specialty Hospital {fac_num}"
            elif fac_type == 'HEALTHCARE_CENTRE':
                name = f"NeuroCare Reference Healthcare Centre {fac_num}"
            else:
                name = f"NeuroCare Reference {random.choice(FACILITY_SUFFIXES)} {fac_num}"

            fac_identifier = f"SYN-FAC-{sc}-{fac_num}"
            ver_status = random.choices(
                ['PENDING', 'VERIFIED'],
                weights=[30, 70], k=1
            )[0]

            records.append({
                'facility_id': fac_id,
                'facility_name': name,
                'facility_type': fac_type,
                'city': city,
                'district': city,  # simplified: district = city for synthetic data
                'state': state,
                'facility_identifier': fac_identifier,
                'verification_status': ver_status,
                'source_type': 'SYNTHETIC_REFERENCE',
            })
            facility_counter += 1

    write_csv(
        os.path.join(OUTPUT_DIR, 'reference_facilities.csv'),
        records,
        fieldnames=[
            'facility_id', 'facility_name', 'facility_type', 'city',
            'district', 'state', 'facility_identifier',
            'verification_status', 'source_type',
        ]
    )
    print(f"  âœ“ {len(records)} facility records written.")
    return records


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 3. GENERATE DOCTOR-FACILITY AFFILIATIONS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_affiliations(doctor_records, facility_records):
    print("Generating doctor_facility_affiliations.csv ...")
    records = []
    aff_counter = 1

    doctor_ids = [d['reference_id'] for d in doctor_records]
    facility_ids = [f['facility_id'] for f in facility_records]

    # Assign 0, 1, 2, or 3 affiliations per doctor
    # Weights chosen to land 8000â€“10000 total
    affiliation_counts = random.choices(
        [0, 1, 2, 3],
        weights=[5, 40, 40, 15],
        k=len(doctor_ids)
    )

    for doc_id, n_affiliations in zip(doctor_ids, affiliation_counts):
        used_facilities = set()
        for _ in range(n_affiliations):
            fac_id = random.choice(facility_ids)
            while fac_id in used_facilities:
                fac_id = random.choice(facility_ids)
            used_facilities.add(fac_id)

            aff_num = f"{aff_counter:06d}"
            aff_id = f"AFF-{aff_num}"

            emp_type = random.choice(EMPLOYMENT_TYPES)
            designation = random.choice(DESIGNATIONS)
            department = random.choice(DEPARTMENTS)

            status = random.choices(['CURRENT', 'ENDED'], weights=[70, 30], k=1)[0]
            start_date = random_date(2000, 2022)
            if status == 'ENDED':
                end_date = start_date + timedelta(days=random.randint(180, 3650))
                end_date_str = format_date(end_date)
            else:
                end_date_str = ''

            ver_status = random.choices(
                ['PENDING', 'VERIFIED'],
                weights=[25, 75], k=1
            )[0]

            records.append({
                'affiliation_id': aff_id,
                'reference_doctor_id': doc_id,
                'facility_id': fac_id,
                'department': department,
                'designation': designation,
                'employment_type': emp_type,
                'status': status,
                'start_date': format_date(start_date),
                'end_date': end_date_str,
                'verification_status': ver_status,
                'source_type': 'SYNTHETIC_REFERENCE',
            })
            aff_counter += 1

    write_csv(
        os.path.join(OUTPUT_DIR, 'doctor_facility_affiliations.csv'),
        records,
        fieldnames=[
            'affiliation_id', 'reference_doctor_id', 'facility_id',
            'department', 'designation', 'employment_type',
            'status', 'start_date', 'end_date',
            'verification_status', 'source_type',
        ]
    )
    print(f"  âœ“ {len(records)} affiliation records written.")
    return records


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 4. GENERATE DISCIPLINARY RECORDS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_disciplinary_records(doctor_records):
    print("Generating disciplinary_records.csv ...")
    records = []
    disc_counter = 1

    # Pick 150 unique doctors to assign disciplinary records to
    sample_doctors = random.sample(doctor_records, 150)

    action_types = []
    for action, count in DISCIPLINARY_ACTIONS.items():
        action_types.extend([action] * count)
    # Exactly 150
    random.shuffle(action_types)

    for doctor, action_type in zip(sample_doctors, action_types):
        disc_num = f"{disc_counter:04d}"
        disc_id = f"DISC-{disc_num}"

        council = doctor['state_medical_council']
        suspended_date = random_date(2000, 2022)
        suspended_date_str = format_date(suspended_date)

        if action_type == 'RESTORATION':
            restored_date = suspended_date + timedelta(days=random.randint(90, 730))
            restored_date_str = format_date(restored_date)
            disc_status = 'RESTORED'
        else:
            restored_date_str = ''
            if action_type == 'SUSPENSION':
                disc_status = 'ACTIVE'
            elif action_type == 'BLACKLIST':
                disc_status = 'BLACKLISTED'
            else:
                disc_status = 'REMOVED'

        records.append({
            'disciplinary_id': disc_id,
            'registration_number': doctor['registration_number'],
            'doctor_name': doctor['doctor_name'],
            'state_medical_council': council,
            'action_type': action_type,
            'status': disc_status,
            'suspended_date': suspended_date_str,
            'restored_date': restored_date_str,
            'source_type': 'SYNTHETIC_TEST_REFERENCE',
            'source_reference': 'NMC_BLACKLIST_STRUCTURE_REFERENCE',
            'remarks': DISC_REMARKS,
        })
        disc_counter += 1

    write_csv(
        os.path.join(OUTPUT_DIR, 'disciplinary_records.csv'),
        records,
        fieldnames=[
            'disciplinary_id', 'registration_number', 'doctor_name',
            'state_medical_council', 'action_type', 'status',
            'suspended_date', 'restored_date',
            'source_type', 'source_reference', 'remarks',
        ]
    )
    print(f"  âœ“ {len(records)} disciplinary records written.")
    return records


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# 5. GENERATE VERIFICATION TEST CASES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def generate_verification_test_cases(doctor_records, disciplinary_records):
    print("Generating verification_test_cases.csv ...")
    records = []
    tc_counter = 1

    disc_reg_numbers = {d['registration_number'] for d in disciplinary_records}
    disc_restored = {
        d['registration_number']
        for d in disciplinary_records
        if d['status'] == 'RESTORED'
    }
    disc_blocked = disc_reg_numbers - disc_restored

    active_doctors = [d for d in doctor_records if d['registration_status'] == 'ACTIVE']
    blocked_doctors = [d for d in doctor_records if d['registration_number'] in disc_blocked]

    def make_tc(case_type, reg_num, submitted_name, submitted_council, expected_result, notes):
        nonlocal tc_counter
        tc_id = f"TC-{tc_counter:04d}"
        tc_counter += 1
        return {
            'test_case_id': tc_id,
            'case_type': case_type,
            'registration_number': reg_num,
            'submitted_name': submitted_name,
            'submitted_council': submitted_council,
            'expected_result': expected_result,
            'notes': notes,
        }

    # 30 EXACT_MATCH
    for d in random.sample(active_doctors, 30):
        records.append(make_tc(
            'EXACT_MATCH',
            d['registration_number'],
            d['doctor_name'],
            d['state_medical_council'],
            'EXACT_MATCH',
            'Exact registration number, council and name submitted.'
        ))

    # 20 NAME_VARIATION â€” submit normalized/slightly altered name
    for d in random.sample(active_doctors, 20):
        varied = d['doctor_name'].upper()  # title-stripped and uppercased
        records.append(make_tc(
            'NAME_VARIATION',
            d['registration_number'],
            varied,
            d['state_medical_council'],
            'LIKELY_MATCH',
            'Name submitted in uppercase without title; should fuzzy-match.'
        ))

    # 10 WRONG_NAME
    for d in random.sample(active_doctors, 10):
        wrong_name = generate_doctor_name('Delhi')  # random unrelated name
        records.append(make_tc(
            'WRONG_NAME',
            d['registration_number'],
            wrong_name,
            d['state_medical_council'],
            'MISMATCH',
            'Correct registration number but entirely different name submitted.'
        ))

    # 10 REGISTRATION_NOT_FOUND
    for i in range(10):
        fake_reg = f"SYN-XX-MED-{99000 + i:06d}"
        records.append(make_tc(
            'REGISTRATION_NOT_FOUND',
            fake_reg,
            generate_doctor_name('Tamil Nadu'),
            'Tamil Nadu Medical Council',
            'NOT_FOUND',
            'Registration number does not exist in reference registry.'
        ))

    # 10 WRONG_COUNCIL
    for d in random.sample(active_doctors, 10):
        wrong_council = random.choice([
            c for _, _, c, _ in STATES_CONFIG
            if c != d['state_medical_council']
        ])
        records.append(make_tc(
            'WRONG_COUNCIL',
            d['registration_number'],
            d['doctor_name'],
            wrong_council,
            'MISMATCH',
            'Correct registration number and name but wrong council submitted.'
        ))

    # 10 MISSING_REGISTRATION
    for d in random.sample(active_doctors, 10):
        records.append(make_tc(
            'MISSING_REGISTRATION',
            '',
            d['doctor_name'],
            d['state_medical_council'],
            'INVALID',
            'Registration number field is empty; required for lookup.'
        ))

    # 10 MISSING_COUNCIL
    for d in random.sample(active_doctors, 10):
        records.append(make_tc(
            'MISSING_COUNCIL',
            d['registration_number'],
            d['doctor_name'],
            '',
            'INVALID',
            'Council field is empty; required for verification.'
        ))

    # 10 DISCIPLINARY_STATUS â€” use blocked doctors
    blocked_sample = blocked_doctors[:10] if len(blocked_doctors) >= 10 else blocked_doctors
    while len(blocked_sample) < 10:
        blocked_sample.append(blocked_sample[-1])  # pad if needed
    for d in blocked_sample:
        records.append(make_tc(
            'DISCIPLINARY_STATUS',
            d['registration_number'],
            d['doctor_name'],
            d['state_medical_council'],
            'STATUS_BLOCKED',
            'Doctor has an active disciplinary record; verification should flag.'
        ))

    # 5 DUPLICATE_REFERENCE
    dup_docs = random.sample(active_doctors, 5)
    for d in dup_docs:
        records.append(make_tc(
            'DUPLICATE_REFERENCE',
            d['registration_number'],
            d['doctor_name'],
            d['state_medical_council'],
            'MANUAL_REVIEW',
            'Registration number submitted twice; deduplication needed.'
        ))

    # 5 QUALIFICATION_MISMATCH
    for d in random.sample(active_doctors, 5):
        wrong_qual = random.choice([q for q in QUALIFICATIONS if q != d['qualification']])
        records.append(make_tc(
            'QUALIFICATION_MISMATCH',
            d['registration_number'],
            d['doctor_name'],
            d['state_medical_council'],
            'MANUAL_REVIEW',
            f"Submitted qualification '{wrong_qual}' does not match registry '{d['qualification']}'."
        ))

    # 10 STANDARD_LOOKUP
    for d in random.sample(active_doctors, 10):
        records.append(make_tc(
            'STANDARD_LOOKUP',
            d['registration_number'],
            d['doctor_name'],
            d['state_medical_council'],
            'EXACT_MATCH',
            'Standard verification lookup with all correct fields.'
        ))

    write_csv(
        os.path.join(OUTPUT_DIR, 'verification_test_cases.csv'),
        records,
        fieldnames=[
            'test_case_id', 'case_type', 'registration_number',
            'submitted_name', 'submitted_council',
            'expected_result', 'notes',
        ]
    )
    print(f"  âœ“ {len(records)} verification test cases written.")
    return records


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# HELPERS
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def write_csv(filepath, records, fieldnames):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(records)


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SUMMARY JSON
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def write_summary(doctors, facilities, affiliations, disciplinary, test_cases):
    summary = {
        "dataset": "NeuroCare Nexus Synthetic Reference Dataset",
        "version": "1.0.0",
        "generated_date": date.today().isoformat(),
        "disclaimer": (
            "This dataset is synthetic and intended only for academic development, "
            "testing and demonstration. It does not establish the real-world registration, "
            "employment, practice status, disciplinary status or identity of any individual."
        ),
        "source_structure_reference": [
            "National Medical Commission (NMC) Indian Medical Register (IMR) â€” structural schema only",
            "Ayushman Bharat Digital Mission (ABDM) Healthcare Professional Registry (HPR) â€” structural schema only",
            "Ayushman Bharat Digital Mission (ABDM) Health Facility Registry (HFR) â€” structural schema only",
        ],
        "record_counts": {
            "reference_doctors": len(doctors),
            "reference_facilities": len(facilities),
            "doctor_facility_affiliations": len(affiliations),
            "disciplinary_records": len(disciplinary),
            "verification_test_cases": len(test_cases),
        },
        "state_distribution": {},
        "specialization_distribution": {},
        "qualification_distribution": {},
        "facility_type_distribution": {},
        "disciplinary_action_distribution": {},
        "test_case_type_distribution": {},
    }

    from collections import Counter
    summary["state_distribution"] = dict(Counter(d['state_medical_council'] for d in doctors))
    summary["specialization_distribution"] = dict(Counter(d['specialization'] for d in doctors))
    summary["qualification_distribution"] = dict(Counter(d['qualification'] for d in doctors))
    summary["facility_type_distribution"] = dict(Counter(f['facility_type'] for f in facilities))
    summary["disciplinary_action_distribution"] = dict(Counter(d['action_type'] for d in disciplinary))
    summary["test_case_type_distribution"] = dict(Counter(tc['case_type'] for tc in test_cases))

    with open(os.path.join(OUTPUT_DIR, 'reference_data_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("  âœ“ reference_data_summary.json written.")


# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MAIN
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    print("=" * 60)
    print("NeuroCare Nexus â€” Synthetic Reference Data Generator")
    print("=" * 60)
    print(f"Output directory: {os.path.abspath(OUTPUT_DIR)}")
    print()

    doctors = generate_reference_doctors()
    facilities = generate_reference_facilities()
    affiliations = generate_affiliations(doctors, facilities)
    disciplinary = generate_disciplinary_records(doctors)
    test_cases = generate_verification_test_cases(doctors, disciplinary)

    print()
    print("Writing summary JSON ...")
    write_summary(doctors, facilities, affiliations, disciplinary, test_cases)

    print()
    print("=" * 60)
    print("GENERATION COMPLETE")
    print(f"  reference_doctors.csv          : {len(doctors):,} records")
    print(f"  reference_facilities.csv       : {len(facilities):,} records")
    print(f"  doctor_facility_affiliations.csv: {len(affiliations):,} records")
    print(f"  disciplinary_records.csv       : {len(disciplinary):,} records")
    print(f"  verification_test_cases.csv    : {len(test_cases):,} records")
    print("=" * 60)
    print()
    print("Run validate_reference_data.py to verify integrity.")


if __name__ == '__main__':
    main()

