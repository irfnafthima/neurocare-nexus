from django.urls import path
from monitoring.views import SimulationTriggerView, DeviceTelemetryIngestView

urlpatterns = [
    path('simulation/trigger', SimulationTriggerView.as_view(), name='simulation-trigger'),
    path('monitoring/device-telemetry', DeviceTelemetryIngestView.as_view(), name='device-telemetry-ingest'),
    path('monitoring/device-telemetry/', DeviceTelemetryIngestView.as_view(), name='device-telemetry-ingest-slash'),
]
