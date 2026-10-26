from django.urls import path
from monitoring.views import (
    SimulationTriggerView, 
    DeviceTelemetryIngestView,
    PatientLatestTelemetryView
)

urlpatterns = [
    path('simulation/trigger', SimulationTriggerView.as_view(), name='simulation-trigger'),
    path('monitoring/device-telemetry', DeviceTelemetryIngestView.as_view(), name='device-telemetry-ingest'),
    path('monitoring/device-telemetry/', DeviceTelemetryIngestView.as_view(), name='device-telemetry-ingest-slash'),
    path('monitoring/patient-telemetry/<str:patient_id>/latest', PatientLatestTelemetryView.as_view(), name='patient-latest-telemetry'),
    path('monitoring/patient-telemetry/<str:patient_id>/latest/', PatientLatestTelemetryView.as_view(), name='patient-latest-telemetry-slash'),
]
