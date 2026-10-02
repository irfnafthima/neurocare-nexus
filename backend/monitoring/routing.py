from django.urls import re_path
from monitoring.consumers import TelemetryConsumer

websocket_urlpatterns = [
    re_path(r'ws/telemetry/patient/(?P<patient_id>[\w\-]+)/$', TelemetryConsumer.as_asgi()),
]
