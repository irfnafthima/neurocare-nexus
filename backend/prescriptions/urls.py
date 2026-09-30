from django.urls import path
from prescriptions.views import (
    PrescriptionListCreateView, 
    PrescriptionDetailView,
    MedicationScheduleView,
    MedicationTodayTimelineView,
    MedicationDoseActionView,
    MedicationAdherenceView,
    MedicationHistoryView
)

urlpatterns = [
    # Prescriptions
    path('prescriptions', PrescriptionListCreateView.as_view(), name='prescriptions-list-create'),
    path('prescriptions/', PrescriptionListCreateView.as_view(), name='prescriptions-list-create-slash'),
    path('prescriptions/<int:id>', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('prescriptions/<int:id>/', PrescriptionDetailView.as_view(), name='prescription-detail-slash'),

    # Medication Schedules
    path('medications/schedule', MedicationScheduleView.as_view(), name='medications-schedule'),
    path('medications/schedule/', MedicationScheduleView.as_view(), name='medications-schedule-slash'),

    # Medication Today Timeline
    path('medications/today', MedicationTodayTimelineView.as_view(), name='medications-today'),
    path('medications/today/', MedicationTodayTimelineView.as_view(), name='medications-today-slash'),

    # Medication Dose Actions (Take / Skip)
    path('medications/doses/<int:schedule_id>/<str:action_type>', MedicationDoseActionView.as_view(), name='medications-dose-action'),
    path('medications/doses/<int:schedule_id>/<str:action_type>/', MedicationDoseActionView.as_view(), name='medications-dose-action-slash'),

    # Medication Adherence Analytics
    path('medications/adherence', MedicationAdherenceView.as_view(), name='medications-adherence'),
    path('medications/adherence/', MedicationAdherenceView.as_view(), name='medications-adherence-slash'),

    # Medication Dose History
    path('medications/history', MedicationHistoryView.as_view(), name='medications-history'),
    path('medications/history/', MedicationHistoryView.as_view(), name='medications-history-slash'),
]

