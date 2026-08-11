from django.test import TestCase
from doctors.utils import verify_doctor_credentials
from doctors.models import ReferenceDoctorRegistry, DoctorDisciplinaryRecord

class DoctorVerificationEngineTest(TestCase):
    def setUp(self):
        # Create test reference doctor records
        self.doc1 = ReferenceDoctorRegistry.objects.create(
            registration_number="REF-12345",
            council="Maharashtra Medical Council",
            doctor_name="Arvind Kulkarni",
            qualification="MBBS, MD",
            registration_year=2012
        )
        self.doc2 = ReferenceDoctorRegistry.objects.create(
            registration_number="REF-67890",
            council="Karnataka Medical Council",
            doctor_name="Ananya Sen",
            qualification="MBBS",
            registration_year=2018
        )
        # Disciplinary record for doc2
        DoctorDisciplinaryRecord.objects.create(
            disciplinary_id="DISC-101",
            doctor=self.doc2,
            registration_number="REF-67890",
            doctor_name="Ananya Sen",
            state_medical_council="Karnataka Medical Council",
            action_type="SUSPENSION",
            status="ACTIVE"
        )

    def test_1_exact_match(self):
        # Real registration number + matching name
        res = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertEqual(res['result'], 'EXACT_MATCH')
        self.assertIsNotNone(res['reference_record'])
        self.assertEqual(res['reference_record'].registration_number, "REF-12345")

    def test_2_likely_match(self):
        # Same registration number + normalized name variation
        res = verify_doctor_credentials("REF-12345", "Dr. Arvind K. Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertEqual(res['result'], 'LIKELY_MATCH')

    def test_3_wrong_name_mismatch(self):
        # Correct registration number + wrong name
        res = verify_doctor_credentials("REF-12345", "Sanjay Gupta", "Maharashtra Medical Council", "MBBS")
        self.assertEqual(res['result'], 'MISMATCH')

    def test_4_not_found(self):
        # Registration number not present in database
        res = verify_doctor_credentials("REF-99999", "Unknown Doctor", "Maharashtra Medical Council", "MBBS")
        self.assertEqual(res['result'], 'NOT_FOUND')
        self.assertIsNone(res['reference_record'])

    def test_5_active_disciplinary_block(self):
        # Correct doctor with active disciplinary block
        res = verify_doctor_credentials("REF-67890", "Ananya Sen", "Karnataka Medical Council", "MBBS")
        self.assertEqual(res['result'], 'STATUS_BLOCKED')
        self.assertEqual(res['checks']['disciplinary_check'], 'BLOCKED')

    def test_6_wrong_state_council(self):
        # Wrong state medical council
        res = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Tamil Nadu Medical Council", "MBBS")
        self.assertIn(res['result'], ['MANUAL_REVIEW', 'MISMATCH'])
        self.assertEqual(res['checks']['council_check'], 'MISMATCH')

    def test_7_qualification_mismatch(self):
        # Qualification mismatch
        res = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "BAMS")
        self.assertEqual(res['checks']['qualification_check'], 'MISMATCH')

    def test_8_reference_record_db_confirmation_and_dynamic_change(self):
        # 1. Verify exact match against current DB record
        res1 = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertEqual(res1['result'], 'EXACT_MATCH')
        self.assertEqual(res1['reference_record'].doctor_name, "Arvind Kulkarni")

        # 2. Dynamically modify the database record in PostgreSQL
        self.doc1.doctor_name = "Different Doctor Name"
        self.doc1.save()

        # 3. Run the exact same verification request again -> Result MUST change
        res2 = verify_doctor_credentials("REF-12345", "Arvind Kulkarni", "Maharashtra Medical Council", "MBBS, MD")
        self.assertNotEqual(res2['result'], 'EXACT_MATCH')
        self.assertEqual(res2['result'], 'MISMATCH')
        self.assertEqual(res2['reference_record'].doctor_name, "Different Doctor Name")


