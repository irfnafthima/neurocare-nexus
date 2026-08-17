import 'package:flutter_test/flutter_test.dart';
import '../lib/core/config/api_config.dart';

void main() {
  group('ApiConfig Unit Tests', () {
    test('Default base URL should point to Android emulator host 10.0.2.2:8000', () {
      expect(ApiConfig.baseUrl, equals('http://10.0.2.2:8000'));
    });

    test('Custom base URL can be configured dynamically', () {
      ApiConfig.setBaseUrl('http://192.168.1.100:8000/');
      expect(ApiConfig.baseUrl, equals('http://192.168.1.100:8000'));
      expect(ApiConfig.loginUrl, equals('http://192.168.1.100:8000/api/auth/login'));
      expect(ApiConfig.healthRecordsUrl('P-101'), equals('http://192.168.1.100:8000/api/health-records?patientId=P-101'));
      expect(ApiConfig.prescriptionsUrl('P-101'), equals('http://192.168.1.100:8000/api/prescriptions?patientId=P-101'));
      expect(ApiConfig.documentsUrl('P-101'), equals('http://192.168.1.100:8000/api/documents?patientId=P-101'));
      expect(ApiConfig.documentDownloadUrl(5), equals('http://192.168.1.100:8000/api/documents/5/download'));
    });
  });
}
