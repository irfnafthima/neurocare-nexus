import 'package:flutter_test/flutter_test.dart';
import '../lib/models/user_model.dart';

void main() {
  group('UserModel Parsing Unit Tests', () {
    test('Correctly parses Django REST login response JSON', () {
      final jsonMap = {
        'id': 1,
        'email': 'riya@gmail.com',
        'role': 'PATIENT',
        'name': 'Riya Mathew',
        'patient_id': 'P-101',
        'device_id': 'DEV-99'
      };

      final user = UserModel.fromJson(jsonMap);

      expect(user.id, equals(1));
      expect(user.email, equals('riya@gmail.com'));
      expect(user.role, equals('patient'));
      expect(user.name, equals('Riya Mathew'));
      expect(user.patientId, equals('P-101'));
      expect(user.deviceId, equals('DEV-99'));
    });

    test('Serializes to JSON accurately', () {
      final user = UserModel(
        id: 2,
        email: 'doctor@gmail.com',
        role: 'doctor',
        name: 'Dr. Nishant',
        npi: 'SYN-TN-MED-000006',
      );

      final json = user.toJson();
      expect(json['id'], equals(2));
      expect(json['email'], equals('doctor@gmail.com'));
      expect(json['role'], equals('doctor'));
      expect(json['npi'], equals('SYN-TN-MED-000006'));
    });
  });
}
