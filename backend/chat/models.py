import os
import uuid
from django.db import models
from django.conf import settings
from patients.models import Patient

def chat_attachment_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    safe_filename = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return os.path.join('private_chat_attachments', safe_filename)

class Conversation(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('ARCHIVED', 'Archived'),
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='conversations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Care Team Chat for Patient {self.patient_id} ({self.status})"

class ConversationParticipant(models.Model):
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('caregiver', 'Caregiver'),
        ('family', 'Family'),
        ('admin', 'Admin'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_participants')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('conversation', 'user')

    def __str__(self):
        return f"{self.user.full_name or self.user.email} in Conv {self.conversation_id} ({self.role})"

class Message(models.Model):
    TYPE_CHOICES = (
        ('TEXT', 'Text'),
        ('IMAGE', 'Image'),
        ('DOCUMENT', 'Document'),
        ('VIDEO', 'Video'),
    )
    PRIORITY_CHOICES = (
        ('NORMAL', 'Normal'),
        ('URGENT', 'Urgent'),
        ('EMERGENCY', 'Emergency'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TEXT')
    content = models.TextField(blank=True, default='')
    attachment = models.FileField(upload_to=chat_attachment_upload_path, blank=True, null=True)
    attachment_original_name = models.CharField(max_length=255, blank=True, default='')
    attachment_mime_type = models.CharField(max_length=100, blank=True, default='')
    attachment_size = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    is_emergency = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg {self.id} from {self.sender.email} in Conv {self.conversation_id} ({self.priority})"
