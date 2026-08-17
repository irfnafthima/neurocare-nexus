from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import CustomUser
from patients.models import Patient
from doctors.models import DoctorPatientLink, SyntheticNPI
from caregivers.models import CaregiverPatientLink
from patients.models import FamilyPatientLink
from medical_records.models import (
    PatientCondition, PatientAllergy, PatientMedication, 
    PatientConsultation, NextConsultation, MedicalDocument
)

class MedicalRecordsModuleTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient_user = CustomUser.objects.create_user(
            email="patient1@gmail.com",
            password="password123",
            full_name="Test Patient One",
            role="patient",
            device_id="NP-901"
        )
        self.patient_record = Patient.objects.create(
            id="P-901",
            name="Test Patient One",
            age=30,
            gender="Female",
            room="901",
            condition="Stable"
        )
        self.doctor_user = CustomUser.objects.create_user(
            email="doc1@gmail.com",
            password="password123",
            full_name="Dr. Attending Doctor",
            role="doctor",
            npi="REG-901"
        )
        self.unlinked_doctor = CustomUser.objects.create_user(
            email="unlinked_doc@gmail.com",
            password="password123",
            full_name="Dr. Unlinked",
            role="doctor",
            npi="REG-902"
        )
        self.caregiver_user = CustomUser.objects.create_user(
            email="cg1@gmail.com",
            password="password123",
            full_name="Caregiver One",
            role="caregiver"
        )
        self.family_user = CustomUser.objects.create_user(
            email="fam1@gmail.com",
            password="password123",
            full_name="Family Member One",
            role="family",
            patient_id="P-901"
        )

        # Approved links
        DoctorPatientLink.objects.create(doctor=self.doctor_user, patient=self.patient_record)
        CaregiverPatientLink.objects.create(caregiver=self.caregiver_user, patient=self.patient_record, is_approved=True)
        FamilyPatientLink.objects.create(family=self.family_user, patient=self.patient_record, is_approved=True)

    def test_health_record_crud(self):
        self.client.force_authenticate(user=self.patient_user)

        # 1. Add Condition (Hypertension)
        res = self.client.post('/api/health-records', {'type': 'condition', 'conditionName': 'Hypertension', 'status': 'Active', 'description': 'Primary essential hypertension'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientCondition.objects.count(), 1)
        cond_id = res.data['id']

        # Update & Delete Condition
        res_u = self.client.put(f'/api/health-records/condition/{cond_id}', {'status': 'Managed'})
        self.assertEqual(res_u.status_code, status.HTTP_200_OK)
        self.assertEqual(PatientCondition.objects.get(id=cond_id).status, 'Managed')

        # 2. Add Allergy (Penicillin)
        res = self.client.post('/api/health-records', {'type': 'allergy', 'allergen': 'Penicillin', 'severity': 'Severe', 'reaction': 'Anaphylaxis'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientAllergy.objects.count(), 1)
        alg_id = res.data['id']

        # Update Allergy
        res_u = self.client.put(f'/api/health-records/allergy/{alg_id}', {'notes': 'Patient carries EpiPen'})
        self.assertEqual(res_u.status_code, status.HTTP_200_OK)

        # 3. Add Medication (Amlodipine 5mg - Once Daily)
        res = self.client.post('/api/health-records', {'type': 'medication', 'medicineName': 'Amlodipine 5mg', 'dosage': '5 mg', 'frequency': 'Once Daily', 'instructions': 'Take after breakfast'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientMedication.objects.count(), 1)

        # 4. Add Consultation (A real test consultation)
        res = self.client.post('/api/health-records', {'type': 'consultation', 'consultationDate': '2026-08-10', 'reason': 'Initial Cardiovascular & Remote Telemetry Assessment', 'doctorName': 'Dr. Attending Doctor'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PatientConsultation.objects.count(), 1)

        # 5. Add Next Consultation (Future date 2026-09-15)
        res = self.client.post('/api/health-records', {'type': 'next_consultation', 'consultationDate': '2026-09-15', 'time': '10:00 AM', 'facility': 'Cardiology Care Center'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NextConsultation.objects.count(), 1)

        # 6. Retrieve Health Records (Patient re-fetch / page refresh)
        res = self.client.get('/api/health-records')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['conditions']), 1)
        self.assertEqual(res.data['conditions'][0]['condition_name'], 'Hypertension')
        self.assertEqual(len(res.data['allergies']), 1)
        self.assertEqual(res.data['allergies'][0]['allergen'], 'Penicillin')
        self.assertEqual(len(res.data['medications']), 1)
        self.assertEqual(len(res.data['consultations']), 1)
        self.assertIsNotNone(res.data['nextConsultation'])
        self.assertEqual(res.data['nextConsultation']['consultation_date'], '2026-09-15')

    def test_authorization_matrix(self):
        # Create test records for patient P-901
        PatientCondition.objects.create(patient=self.patient_record, condition_name="Hypertension", status="Active")
        PatientAllergy.objects.create(patient=self.patient_record, allergen="Penicillin", severity="Severe")

        # 1. Patient accesses own records -> PASS (200 OK)
        self.client.force_authenticate(user=self.patient_user)
        res_pat = self.client.get('/api/health-records')
        self.assertEqual(res_pat.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_pat.data['conditions']), 1)

        # 2. Linked Authorized Doctor accesses patient records -> PASS (200 OK)
        self.client.force_authenticate(user=self.doctor_user)
        res_doc = self.client.get(f'/api/health-records?patientId=P-901')
        self.assertEqual(res_doc.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_doc.data['conditions']), 1)

        # 3. Approved Caregiver accesses patient records -> PASS (200 OK)
        self.client.force_authenticate(user=self.caregiver_user)
        res_cg = self.client.get(f'/api/health-records?patientId=P-901')
        self.assertEqual(res_cg.status_code, status.HTTP_200_OK)

        # 4. Approved Family Member accesses patient records -> PASS (200 OK)
        self.client.force_authenticate(user=self.family_user)
        res_fam = self.client.get(f'/api/health-records?patientId=P-901')
        self.assertEqual(res_fam.status_code, status.HTTP_200_OK)

        # 5. Unlinked Doctor is DENIED access -> FAIL/FORBIDDEN (403 Forbidden)
        self.client.force_authenticate(user=self.unlinked_doctor)
        res_unlinked_doc = self.client.get(f'/api/health-records?patientId=P-901')
        self.assertEqual(res_unlinked_doc.status_code, status.HTTP_403_FORBIDDEN)

        # 6. Unlinked Caregiver is DENIED access -> FAIL/FORBIDDEN (403 Forbidden)
        unlinked_cg = CustomUser.objects.create_user(email="unlinked_cg@gmail.com", password="password123", full_name="Unlinked CG", role="caregiver")
        self.client.force_authenticate(user=unlinked_cg)
        res_unlinked_cg = self.client.get(f'/api/health-records?patientId=P-901')
        self.assertEqual(res_unlinked_cg.status_code, status.HTTP_403_FORBIDDEN)

        # 7. Unlinked Family Member is DENIED access -> FAIL/FORBIDDEN (403 Forbidden)
        unlinked_fam = CustomUser.objects.create_user(email="unlinked_fam@gmail.com", password="password123", full_name="Unlinked Family", role="family", patient_id="P-999")
        self.client.force_authenticate(user=unlinked_fam)
        res_unlinked_fam = self.client.get(f'/api/health-records?patientId=P-901')
        self.assertEqual(res_unlinked_fam.status_code, status.HTTP_403_FORBIDDEN)

    def test_secure_document_upload_and_access(self):
        # 1. Patient Uploads Document
        self.client.force_authenticate(user=self.patient_user)
        dummy_file = SimpleUploadedFile("report.pdf", b"PDF_CONTENT_TEST_DATA", content_type="application/pdf")
        res = self.client.post('/api/documents', {'title': 'Blood Test August', 'documentType': 'Blood Test', 'file': dummy_file})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        doc_id = res.data['id']

        # 2. Linked Doctor can retrieve document metadata and download file
        self.client.force_authenticate(user=self.doctor_user)
        res_get = self.client.get(f'/api/documents?patientId=P-901')
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_get.data), 1)

        res_dl = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_dl.status_code, status.HTTP_200_OK)

        # 3. Unlinked Doctor is DENIED access
        self.client.force_authenticate(user=self.unlinked_doctor)
        res_unauth = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_unauth.status_code, status.HTTP_403_FORBIDDEN)

    def test_caregiver_and_family_document_upload_and_doctor_access(self):
        # 1. Caregiver uploads document for Patient A
        self.client.force_authenticate(user=self.caregiver_user)
        file_cg = SimpleUploadedFile("caregiver_report.pdf", b"CAREGIVER_DATA", content_type="application/pdf")
        res_cg = self.client.post('/api/documents', {'patientId': 'P-901', 'title': 'Caregiver Log Sheet', 'documentType': 'Clinical Record', 'file': file_cg})
        self.assertEqual(res_cg.status_code, status.HTTP_201_CREATED)
        cg_doc_id = res_cg.data['id']

        # 2. Family Member uploads document for Patient A
        self.client.force_authenticate(user=self.family_user)
        file_fam = SimpleUploadedFile("family_report.pdf", b"FAMILY_DATA", content_type="application/pdf")
        res_fam = self.client.post('/api/documents', {'patientId': 'P-901', 'title': 'Home Blood Pressure Log', 'documentType': 'Lab Report', 'file': file_fam})
        self.assertEqual(res_fam.status_code, status.HTTP_201_CREATED)
        fam_doc_id = res_fam.data['id']

        # 3. Patient A can view both documents
        self.client.force_authenticate(user=self.patient_user)
        res_pat_docs = self.client.get('/api/documents')
        self.assertEqual(res_pat_docs.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_pat_docs.data), 2)

        # 4. Approved Doctor A can view both caregiver and family uploaded documents
        self.client.force_authenticate(user=self.doctor_user)
        res_doc_docs = self.client.get('/api/documents?patientId=P-901')
        self.assertEqual(res_doc_docs.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_doc_docs.data), 2)

        res_dl_cg = self.client.get(f'/api/documents/{cg_doc_id}/download')
        self.assertEqual(res_dl_cg.status_code, status.HTTP_200_OK)

        res_dl_fam = self.client.get(f'/api/documents/{fam_doc_id}/download')
        self.assertEqual(res_dl_fam.status_code, status.HTTP_200_OK)

        # 5. Unauthorized Unlinked Doctor B receives 403 Forbidden
        self.client.force_authenticate(user=self.unlinked_doctor)
        res_unauth_cg = self.client.get(f'/api/documents/{cg_doc_id}/download')
        self.assertEqual(res_unauth_cg.status_code, status.HTTP_403_FORBIDDEN)

        res_unauth_fam = self.client.get(f'/api/documents/{fam_doc_id}/download')
        self.assertEqual(res_unauth_fam.status_code, status.HTTP_403_FORBIDDEN)

    def test_revoked_doctor_access_revocation_and_cross_patient_isolation(self):
        # Setup Patient B
        patient2 = Patient.objects.create(id="P-902", name="Patient Two", age=40, gender="Male", room="902")

        # 1. Doctor A (linked to Patient A) attempts to access Patient B -> 403 Forbidden
        self.client.force_authenticate(user=self.doctor_user)
        res_pat_b = self.client.get('/api/health-records?patientId=P-902')
        self.assertEqual(res_pat_b.status_code, status.HTTP_403_FORBIDDEN)

        res_doc_b = self.client.get('/api/documents?patientId=P-902')
        self.assertEqual(res_doc_b.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Revoke Doctor A link to Patient A
        DoctorPatientLink.objects.filter(doctor=self.doctor_user, patient=self.patient_record).delete()

        # 3. Doctor A immediately loses access to Patient A -> 403 Forbidden
        res_revoked = self.client.get('/api/health-records?patientId=P-901')
        self.assertEqual(res_revoked.status_code, status.HTTP_403_FORBIDDEN)

        res_revoked_doc = self.client.get('/api/documents?patientId=P-901')
        self.assertEqual(res_revoked_doc.status_code, status.HTTP_403_FORBIDDEN)

    def test_unapproved_and_revoked_caregiver_and_family_document_blocks(self):
        from accounts.models import AuditLog

        # Create unapproved caregiver & unauthorized family
        unapp_cg = CustomUser.objects.create_user(email="unapp_cg@gmail.com", password="password123", full_name="Unapproved Caregiver", role="caregiver")
        unauth_fam = CustomUser.objects.create_user(email="unauth_fam@gmail.com", password="password123", full_name="Unauthorized Family", role="family", patient_id="P-999")
        CaregiverPatientLink.objects.create(caregiver=unapp_cg, patient=self.patient_record, is_approved=False)

        # Upload document as patient
        self.client.force_authenticate(user=self.patient_user)
        test_file = SimpleUploadedFile("discharge_summary.pdf", b"DISCHARGE_SUMMARY_PDF_DATA", content_type="application/pdf")
        res_up = self.client.post('/api/documents', {'title': 'Discharge Summary 2026', 'documentType': 'Discharge Summary', 'file': test_file})
        self.assertEqual(res_up.status_code, status.HTTP_201_CREATED)
        doc_id = res_up.data['id']

        # Verify audit log created
        self.assertTrue(AuditLog.objects.filter(action='Uploaded Medical Document').exists())

        # Unapproved Caregiver -> 403 Forbidden
        self.client.force_authenticate(user=unapp_cg)
        res_cg_block = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_cg_block.status_code, status.HTTP_403_FORBIDDEN)

        # Unauthorized Family -> 403 Forbidden
        self.client.force_authenticate(user=unauth_fam)
        res_fam_block = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_fam_block.status_code, status.HTTP_403_FORBIDDEN)

        # Revoke approved caregiver
        CaregiverPatientLink.objects.filter(caregiver=self.caregiver_user, patient=self.patient_record).update(is_approved=False)

        # Revoked Caregiver -> 403 Forbidden
        self.client.force_authenticate(user=self.caregiver_user)
        res_rev_cg = self.client.get(f'/api/documents/{doc_id}/download')
        self.assertEqual(res_rev_cg.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_profile_update_and_audit_logging(self):
        self.client.force_authenticate(user=self.patient_user)
        res = self.client.put('/api/patients/P-901/profile', {
            'name': 'Test Patient One Updated',
            'dob': '1995-05-15',
            'phone': '+15550199',
            'address': '123 Health Ave, Suite 4',
            'emergencyContactName': 'Jane Doe',
            'emergencyContactPhone': '+15559900',
            'bloodGroup': 'O+'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.patient_record.refresh_from_db()
        self.assertEqual(self.patient_record.phone, '+15550199')
        self.assertEqual(self.patient_record.blood_group, 'O+')

        # Verify audit log
        from accounts.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action='Updated Patient Profile').exists())

    def test_manual_vitals_provenance_security_and_data_integrity(self):
        from medical_records.models import VitalMeasurement
        from django.core.exceptions import ValidationError
        self.client.force_authenticate(user=self.patient_user)

        # 1. Post valid manual vital record -> source MUST be MANUAL
        res = self.client.post('/api/health-records', {
            'type': 'manual_vital',
            'heartRate': 75,
            'spo2': 98,
            'temperature': 36.6,
            'systolicBp': 120,
            'diastolicBp': 80,
            'notes': 'Normal morning reading'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['source'], 'MANUAL')
        self.assertEqual(res.data['source_label'], 'Manual entry')
        self.assertEqual(res.data['heart_rate'], 75.0)

        # 2. SECURITY TEST: Impersonation attempt with source="DEVICE" -> Backend MUST force MANUAL
        res_sec = self.client.post('/api/health-records', {
            'type': 'manual_vital',
            'source': 'DEVICE', # Impersonation attempt
            'heartRate': 80,
            'spo2': 99
        })
        self.assertEqual(res_sec.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_sec.data['source'], 'MANUAL') # Must remain MANUAL
        self.assertEqual(res_sec.data['source_label'], 'Manual entry')

        # 3. Empty vital record rejection -> 400 Bad Request
        res_empty = self.client.post('/api/health-records', {
            'type': 'manual_vital',
            'notes': 'No numbers'
        })
        self.assertEqual(res_empty.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Out-of-bounds input rejection -> 400 Bad Request
        res_oob = self.client.post('/api/health-records', {
            'type': 'manual_vital',
            'heartRate': 999 # Malformed/impossible input
        })
        self.assertEqual(res_oob.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Unusual valid measurement -> Store exact value unaltered, return neutral warning
        res_unusual = self.client.post('/api/health-records', {
            'type': 'manual_vital',
            'heartRate': 140 # Unusual but valid
        })
        self.assertEqual(res_unusual.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_unusual.data['heart_rate'], 140.0) # Unaltered value
        self.assertEqual(res_unusual.data['warning'], 'Please verify this measurement.')

        # 6. Device vital fixture -> source_label = "Device / ESP32"
        dev_vital = VitalMeasurement.objects.create(
            patient=self.patient_record,
            source='DEVICE',
            heart_rate=72.0,
            spo2=98.0
        )
        self.assertEqual(dev_vital.source_label, 'Device / ESP32')

        # 7. Model invalid source rejection
        inv_vital = VitalMeasurement(patient=self.patient_record, source='INVALID', heart_rate=70)
        with self.assertRaises(ValidationError):
            inv_vital.full_clean()

    def test_ml_query_filtering_compatibility(self):
        from medical_records.models import VitalMeasurement
        VitalMeasurement.objects.create(patient=self.patient_record, source='MANUAL', heart_rate=72)
        VitalMeasurement.objects.create(patient=self.patient_record, source='DEVICE', heart_rate=75)

        self.client.force_authenticate(user=self.patient_user)

        # Filter DEVICE only
        res_dev = self.client.get('/api/vitals?patientId=P-901&source=DEVICE')
        self.assertEqual(res_dev.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_dev.data), 1)
        self.assertEqual(res_dev.data[0]['source'], 'DEVICE')

        # Filter MANUAL only
        res_man = self.client.get('/api/vitals?patientId=P-901&source=MANUAL')
        self.assertEqual(res_man.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_man.data), 1)
        self.assertEqual(res_man.data[0]['source'], 'MANUAL')

        # Filter ALL
        res_all = self.client.get('/api/vitals?patientId=P-901&source=ALL')
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 2)

    def test_caregiver_and_family_edit_permissions(self):
        # 1. Read-Only Caregiver -> Blocked from posting clinical data (403 Forbidden)
        CaregiverPatientLink.objects.filter(caregiver=self.caregiver_user, patient=self.patient_record).update(is_read_only=True)
        self.client.force_authenticate(user=self.caregiver_user)
        res_cg_block = self.client.post('/api/health-records', {
            'type': 'condition',
            'patientId': 'P-901',
            'conditionName': 'Migraine'
        })
        self.assertEqual(res_cg_block.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Editable Caregiver -> Permitted to post clinical data (201 Created)
        CaregiverPatientLink.objects.filter(caregiver=self.caregiver_user, patient=self.patient_record).update(is_read_only=False)
        res_cg_ok = self.client.post('/api/health-records', {
            'type': 'condition',
            'patientId': 'P-901',
            'conditionName': 'Migraine'
        })
        self.assertEqual(res_cg_ok.status_code, status.HTTP_201_CREATED)

        # 3. Read-Only Family Member -> Blocked from posting clinical data (403 Forbidden)
        FamilyPatientLink.objects.filter(family=self.family_user, patient=self.patient_record).update(can_edit_clinical=False)
        self.client.force_authenticate(user=self.family_user)
        res_fam_block = self.client.post('/api/health-records', {
            'type': 'allergy',
            'patientId': 'P-901',
            'allergen': 'Latex'
        })
        self.assertEqual(res_fam_block.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Editable Family Member -> Permitted to post clinical data (201 Created)
        FamilyPatientLink.objects.filter(family=self.family_user, patient=self.patient_record).update(can_edit_clinical=True)
        res_fam_ok = self.client.post('/api/health-records', {
            'type': 'allergy',
            'patientId': 'P-901',
            'allergen': 'Latex'
        })
        self.assertEqual(res_fam_ok.status_code, status.HTTP_201_CREATED)

