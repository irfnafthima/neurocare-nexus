import 'package:flutter_test/flutter_test.dart';
import '../lib/models/doctor_model.dart';
import '../lib/models/connection_request_model.dart';

void main() {
  group('DoctorModel & ConnectionRequestModel Unit Tests', () {
    test('Parses operational approved doctor correctly', () {
      final jsonMap = {
        'id': 1,
        'name': 'Dr. Nishant Raja',
        'npi': 'SYN-TN-MED-000006',
        'specialization': 'Neurology',
        'qualification': 'MD, DM Neurology',
        'status': 'VERIFIED',
        'hospital': 'Apollo Hospital',
        'experience': 12,
        'bio': 'Senior neurologist specializing in epilepsy and stroke telemetry.'
      };

      final doc = DoctorModel.fromJson(jsonMap);

      expect(doc.id, equals(1));
      expect(doc.name, equals('Dr. Nishant Raja'));
      expect(doc.npi, equals('SYN-TN-MED-000006'));
      expect(doc.specialization, equals('Neurology'));
      expect(doc.status, equals('VERIFIED'));
    });

    test('Parses connection request correctly', () {
      final jsonMap = {
        'id': 100,
        'patientId': 'P-101',
        'doctorNpi': 'SYN-TN-MED-000006',
        'status': 'Pending',
        'createdAt': '2026-08-15',
        'doctorName': 'Dr. Nishant Raja',
        'hospital': 'Apollo Hospital'
      };

      final req = ConnectionRequestModel.fromJson(jsonMap);

      expect(req.id, equals(100));
      expect(req.doctorNpi, equals('SYN-TN-MED-000006'));
      expect(req.status, equals('Pending'));
    });
  });
}
