import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def print_section(title):
    print("\n" + "="*50)
    print(f" TESTING: {title}")
    print("="*50)

def test_login(email, password, role, credentials=None):
    url = f"{BASE_URL}/auth/login"
    payload = {
        "email": email,
        "password": password,
        "role": role,
        "credentials": credentials or {}
    }
    res = requests.post(url, json=payload)
    print(f"Login {role} ({email}) -> Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        print(f"Success! Token: {data['token'][:40]}...")
        return data['token']
    else:
        print(f"Error: {res.text}")
        return None

def main():
    print_section("AUTHENTICATION & PORTAL LOGINS")
    
    # 1. Doctor login (should succeed if approved, doc is pre-seeded as approved)
    doc_token = test_login("doctor@nexus.com", "password123", "doctor", {"npi": "1029384756"})
    
    # 2. Patient login (deviceId seeded)
    pat_token = test_login("patient@nexus.com", "password123", "patient", {"deviceId": "NP-102"})
    
    # 3. Family login (patientId seeded)
    fam_token = test_login("family@nexus.com", "password123", "family", {"patientId": "P-102"})
    
    # 4. Caregiver login (agencyId seeded)
    cg_token = test_login("caregiver@nexus.com", "password123", "caregiver", {"agencyId": "CG-204"})
    
    # 5. Admin login (accessKey seeded)
    admin_token = test_login("admin@nexus.com", "password123", "admin", {"accessKey": "ADM-90210"})

    if not all([doc_token, pat_token, fam_token, cg_token, admin_token]):
        print("\nERROR: One or more pre-seeded logins failed. Ensure seed.py ran successfully.")
        return

    # Verify Patient List Retrieval
    print_section("PATIENT DIRECTORY LISTINGS")
    headers = {"Authorization": f"Bearer {doc_token}"}
    res = requests.get(f"{BASE_URL}/patients", headers=headers)
    print(f"Doctor fetches patients -> Status: {res.status_code}")
    if res.status_code == 200:
        patients = res.json()
        print(f"Returned {len(patients)} patients:")
        for p in patients:
            print(f"- ID: {p['id']}, Name: {p['name']}, Risk: {p['risk']}, Consulting NPI: {p['doctorNpi']}")
            print(f"  Vitals: HR={p['vitals']['max30102']['heartRate']} BPM, SpO2={p['vitals']['max30102']['spo2']}%")

    # Verify Doctor Approval workflow
    print_section("ADMIN DOCTOR VERIFICATIONS")
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Register a new pending doctor to verify approval flow
    reg_url = f"{BASE_URL}/auth/register"
    reg_payload = {
        "fullName": "Dr. Verification Test",
        "email": "testdoc@nexus.com",
        "phone": "+1 (555) 999-8888",
        "role": "doctor",
        "npi": "5556667778",
        "specialization": "Neurology",
        "experience": "10 years",
        "bio": "Researching EEG micro-alerts."
    }
    res = requests.post(reg_url, json=reg_payload)
    print(f"Register pending doctor -> Status: {res.status_code}")
    
    # Get pending doctors list
    res = requests.get(f"{BASE_URL}/admin/pending-doctors", headers=headers)
    print(f"Admin fetch pending doctors -> Status: {res.status_code}")
    pending_id = None
    if res.status_code == 200:
        pending = res.json()
        print(f"Pending doctors list: {len(pending)} docs")
        for d in pending:
            print(f"- ID: {d['id']}, Name: {d['fullName']}, NPI: {d['npi']}, Hospital: {d['hospital']}")
            if d['npi'] == "5556667778":
                pending_id = d['id']
                
    if pending_id:
        # Approve doctor
        approve_res = requests.put(f"{BASE_URL}/admin/doctors/{pending_id}/approve", headers=headers)
        print(f"Admin approves doctor ID {pending_id} -> Status: {approve_res.status_code} ({approve_res.text})")
        
        # Verify they can login now
        test_login("testdoc@nexus.com", "password123", "doctor", {"npi": "5556667778"})
        
        # Delete/revoke the test user
        del_res = requests.delete(f"{BASE_URL}/admin/users/{pending_id}", headers=headers)
        print(f"Admin cleanup/revoke test user -> Status: {del_res.status_code} ({del_res.text})")

    # Verify connection requests
    print_section("DOCTOR-PATIENT CONNECTION REQUESTS")
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    
    # Create request (Patient -> Doctor NPI Rachel Kim: 1029384756)
    req_res = requests.post(f"{BASE_URL}/connections/requests", json={"doctorNpi": "1029384756"}, headers=pat_headers)
    print(f"Patient sends connection request -> Status: {req_res.status_code}")
    req_id = None
    if req_res.status_code == 200:
        req_obj = req_res.json()
        req_id = req_obj['id']
        print(f"Request ID: {req_id}, Status: {req_obj['status']}")
        
    # Doctor lists pending requests
    list_res = requests.get(f"{BASE_URL}/connections/requests", headers=doc_headers)
    print(f"Doctor fetches pending connection requests -> Status: {list_res.status_code}")
    if list_res.status_code == 200:
        reqs = list_res.json()
        print(f"Pending requests: {len(reqs)}")
        for r in reqs:
            print(f"- ID: {r['id']}, Patient: {r['patientName']}, Condition: {r['patientCondition']}, Risk: {r['patientRisk']}")
            
    if req_id:
        # Doctor approves request
        approve_res = requests.put(f"{BASE_URL}/connections/requests/{req_id}", json={"status": "Approved"}, headers=doc_headers)
        print(f"Doctor approves request -> Status: {approve_res.status_code} ({approve_res.text})")

    # Verify Telemetry streams & Emergency press bypass rule
    print_section("TELEMETRY SIMULATOR & EMERGENCY ALERTS")
    sim_payload = {
        "patientId": "P-102",
        "riskScore": 85,
        "statusState": "Critical",
        "vitals": {
            "max30102": {"heartRate": 125, "spo2": 88},
            "ds18b20": {"temperature": 39.10},
            "mpu6050": {
                "accelX": 0.12, "accelY": 0.85, "accelZ": 0.18,
                "gyroX": 1.5, "gyroY": -2.4, "gyroZ": 0.8,
                "fallDetected": False
            },
            "esp32": {
                "connected": True, "battery": 78, "rssi": -65,
                "emergency_pressed": True
            }
        }
    }
    
    sim_res = requests.post(f"{BASE_URL}/simulation/trigger", json=sim_payload, headers=pat_headers)
    print(f"Submit telemetry update (Emergency Button = True) -> Status: {sim_res.status_code} ({sim_res.text})")

    # Verify chatbot context resolution
    print_section("AI CLINICAL CHATBOT ASSISTANT")
    chat_res = requests.post(f"{BASE_URL}/chat", json={"message": "Do I have any appointments or high vitals?"}, headers=pat_headers)
    print(f"Patient sends message to chatbot -> Status: {chat_res.status_code}")
    if chat_res.status_code == 200:
        print(f"AI Assistant Message:\n{chat_res.json()['response']}")

if __name__ == "__main__":
    main()
