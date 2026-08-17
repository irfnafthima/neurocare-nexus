import 'package:flutter_test/flutter_test.dart';
import '../lib/models/prescription_model.dart';

void main() {
  group('PrescriptionModel Unit Tests', () {
    test('Parses prescription object correctly', () {
      final jsonMap = {
        'id': 10,
        'patientId': 'P-101',
        'medicine': 'Levetiracetam',
        'dosage': '500 mg',
        'frequency': 'Twice Daily (BID)',
        'duration': '30 Days',
        'instructions': 'Take after meals.',
        'prescriptionDate': '2026-08-10',
        'prescribingDoctorName': 'Dr. Nishant Raja'
      };

      final rx = PrescriptionModel.fromJson(jsonMap);

      expect(rx.id, equals(10));
      expect(rx.medicine, equals('Levetiracetam'));
      expect(rx.dosage, equals('500 mg'));
      expect(rx.prescribingDoctorName, equals('Dr. Nishant Raja'));
    });
  });
}
