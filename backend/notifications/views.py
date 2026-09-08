from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'category', 'target_id', 'is_read', 'timestamp']

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
