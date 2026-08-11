from django.urls import path
from monitoring.views import SimulationTriggerView

urlpatterns = [
    path('simulation/trigger', SimulationTriggerView.as_view(), name='simulation-trigger'),
]
