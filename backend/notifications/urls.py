from django.urls import path
from notifications.views import (
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView
)

urlpatterns = [
    path('notifications', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/read', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('notifications/mark-all-read', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
]
