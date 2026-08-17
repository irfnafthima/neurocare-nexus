import 'package:flutter_test/flutter_test.dart';

import 'package:neurocare_nexus_mobile/main.dart';

void main() {
  testWidgets('App startup smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const NeuroCareNexusApp());
  });
}
