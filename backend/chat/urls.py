from django.urls import path
from chat.views import (
    ConversationListCreateView,
    MessageListCreateView,
    MessageAttachmentDownloadView,
    MarkConversationReadView
)

urlpatterns = [
    path('chat/conversations', ConversationListCreateView.as_view(), name='chat-conversations'),
    path('chat/conversations/<int:conv_id>/messages', MessageListCreateView.as_view(), name='chat-messages'),
    path('chat/messages/<int:message_id>/attachment', MessageAttachmentDownloadView.as_view(), name='chat-attachment'),
    path('chat/conversations/<int:conv_id>/read', MarkConversationReadView.as_view(), name='chat-mark-read'),
]
