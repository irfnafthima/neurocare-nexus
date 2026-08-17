import 'package:flutter_test/flutter_test.dart';
import '../lib/models/health_record_model.dart';

void main() {
  group('HealthRecordModel Unit Tests', () {
    test('Parses health record JSON payload safely', () {
      final jsonMap = {
        'patientId': 'P-101',
        'patientName': 'Riya Mathew',
        'age': 45,
        'gender': 'Female',
        'conditions': ['Epilepsy', 'Hypertension'],
        'allergies': ['Penicillin'],
        'medications': ['Levetiracetam 500mg'],
        'consultationHistory': [
          {
            'doctorName': 'Dr. Nishant Raja',
            'date': '2026-08-10',
            'reason': 'Epilepsy follow-up',
            'notes': 'EEG results stable.'
          }
        ],
        'nextConsultation': {
          'doctorName': 'Dr. Nishant Raja',
          'date': '2026-09-01',
          'time': '10:00 AM',
          'facility': 'Neuro Telemetry Suite'
        }
      };

      final record = HealthRecordModel.fromJson(jsonMap);

      expect(record.patientId, equals('P-101'));
      expect(record.patientName, equals('Riya Mathew'));
      expect(record.conditions.length, equals(2));
      expect(record.allergies.first, equals('Penicillin'));
      expect(record.consultationHistory.length, equals(1));
      expect(record.nextConsultation?.doctorName, equals('Dr. Nishant Raja'));
    });
  });
}
