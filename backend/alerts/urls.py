from django.urls import path
from alerts.views import AlertListView, AlertResolveView

urlpatterns = [
    path('alerts', AlertListView.as_view(), name='alert-list'),
    path('alerts/', AlertListView.as_view(), name='alert-list-slash'),
    path('alerts/<int:pk>/resolve', AlertResolveView.as_view(), name='alert-resolve'),
    path('alerts/<int:pk>/resolve/', AlertResolveView.as_view(), name='alert-resolve-slash'),
    path('alerts/<int:pk>', AlertResolveView.as_view(), name='alert-detail'),
    path('alerts/<int:pk>/', AlertResolveView.as_view(), name='alert-detail-slash'),
]
