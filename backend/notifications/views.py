from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification, NotificationPreference
from notifications.notification_service import get_user_notification_preferences
from accounts.utils import log_audit_trail

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'category', 'target_id', 'is_read', 'timestamp']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'critical_alerts_in_app',
            'critical_alerts_email',
            'prescription_updates_email',
            'medication_reminder_in_app',
            'medication_reminder_email',
            'missed_dose_in_app',
            'missed_dose_email',
            'adherence_escalation_in_app',
            'adherence_escalation_email',
        ]


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Notification.objects.filter(user=request.user).order_by('-timestamp')
        serializer = NotificationSerializer(queryset, many=True)
        unread_count = queryset.filter(is_read=False).count()
        return Response({
            'notifications': serializer.data,
            'unreadCount': unread_count,
            'unread_count': unread_count,
            'results': serializer.data
        }, status=status.HTTP_200_OK)


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def _mark_read(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return Response({'status': 'success', 'id': pk, 'is_read': True}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found or unauthorized.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        return self._mark_read(request, pk)

    def put(self, request, pk):
        return self._mark_read(request, pk)


class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]

    def _mark_all_read(self, request):
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'success', 'updatedCount': updated_count, 'updated_count': updated_count}, status=status.HTTP_200_OK)

    def post(self, request):
        return self._mark_all_read(request)

    def put(self, request):
        return self._mark_all_read(request)


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        prefs = get_user_notification_preferences(request.user)
        return Response(prefs, status=status.HTTP_200_OK)

    def put(self, request):
        return self._save_preferences(request)

    def patch(self, request):
        return self._save_preferences(request)

    def _save_preferences(self, request):
        user = request.user
        pref_obj, _ = NotificationPreference.objects.get_or_create(user=user)

        data = request.data.copy()
        # Enforce safety invariant: Critical in-app alert delivery is mandatory
        data['critical_alerts_in_app'] = True

        serializer = NotificationPreferenceSerializer(pref_obj, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_audit_trail(
                request=request,
                action='Updated Notification Preferences',
                target=f"Preferences for {user.email}",
                result='Success'
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
