from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_status_view(request):
    return JsonResponse({
        'status': 'online',
        'name': 'NeuroCare Nexus REST API Backend',
        'frontend_url': 'http://localhost:5173',
        'message': 'Backend API is running successfully. Open http://localhost:5173 in your browser to access the NeuroCare Nexus web application.'
    })

urlpatterns = [
    path('', root_status_view, name='root-status'),
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/', include('doctors.urls')),
    path('api/', include('patients.urls')),
    path('api/', include('caregivers.urls')),
    path('api/', include('monitoring.urls')),
    path('api/', include('ai_services.urls')),
    path('api/', include('medical_records.urls')),
    path('api/', include('prescriptions.urls')),
    path('api/', include('notifications.urls')),
]
