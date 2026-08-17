import os
import mimetypes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse
from django.utils import timezone
from asgiref.sync import async_to_sync
import channels.layers

from chat.models import Conversation, ConversationParticipant, Message
from patients.models import Patient
from medical_records.views import is_user_authorized_for_patient
from accounts.utils import log_audit_trail
from notifications.utils import create_notification
from accounts.models import CustomUser
from doctors.models import DoctorPatientLink
from caregivers.models import CaregiverPatientLink
from patients.models import FamilyPatientLink

ALLOWED_ATTACHMENT_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'txt', 'mp4', 'mov', 'avi'}
EXECUTABLE_EXTENSIONS = {'exe', 'bat', 'cmd', 'sh', 'php', 'pl', 'py', 'js', 'jar', 'vbs', 'dll', 'so', 'bin'}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024 # 25 MB

class ConversationParticipantSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ConversationParticipant
        fields = ['id', 'user', 'user_name', 'user_email', 'role', 'joined_at', 'is_active']

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_role = serializers.SerializerMethodField()
    has_attachment = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_name', 'sender_role',
            'message_type', 'content', 'has_attachment', 'attachment_url',
            'attachment_original_name', 'attachment_mime_type', 'attachment_size',
            'created_at', 'delivered_at', 'read_at', 'priority', 'is_emergency'
        ]

    def get_sender_role(self, obj):
        part = ConversationParticipant.objects.filter(conversation=obj.conversation, user=obj.sender).first()
        return part.role if part else obj.sender.role

    def get_has_attachment(self, obj):
        return bool(obj.attachment)

    def get_attachment_url(self, obj):
        if obj.attachment:
            return f"/api/chat/messages/{obj.id}/attachment"
        return None

class ConversationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'patient', 'patient_name', 'status', 'created_at', 'updated_at', 'participants', 'last_message', 'unread_count']

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        return MessageSerializer(last_msg).data if last_msg else None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return 0
        return obj.messages.exclude(sender=request.user).filter(read_at__isnull=True).count()


def sync_conversation_participants(conversation):
    """
    Dynamically syncs authorized care team members into conversation participants based on existing relationship tables.
    """
    patient = conversation.patient
    # 1. Patient
    patient_users = CustomUser.objects.filter(role='patient')
    for pu in patient_users:
        if pu.patient_id == patient.id or pu.full_name == patient.name:
            ConversationParticipant.objects.get_or_create(
                conversation=conversation, user=pu, defaults={'role': 'patient', 'is_active': True}
            )

    # 2. Doctors
    doc_links = DoctorPatientLink.objects.filter(patient=patient)
    for link in doc_links:
        ConversationParticipant.objects.get_or_create(
            conversation=conversation, user=link.doctor, defaults={'role': 'doctor', 'is_active': True}
        )
    if patient.doctor_npi:
        doc_u = CustomUser.objects.filter(npi=patient.doctor_npi.npi).first()
        if doc_u:
            ConversationParticipant.objects.get_or_create(
                conversation=conversation, user=doc_u, defaults={'role': 'doctor', 'is_active': True}
            )

    # 3. Caregivers
    cg_links = CaregiverPatientLink.objects.filter(patient=patient, is_approved=True)
    for link in cg_links:
        ConversationParticipant.objects.get_or_create(
            conversation=conversation, user=link.caregiver, defaults={'role': 'caregiver', 'is_active': True}
        )

    # 4. Family
    fam_links = FamilyPatientLink.objects.filter(patient=patient, is_approved=True)
    for link in fam_links:
        ConversationParticipant.objects.get_or_create(
            conversation=conversation, user=link.family, defaults={'role': 'family', 'is_active': True}
        )


class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        all_convs = Conversation.objects.filter(status='ACTIVE')
        authorized_convs = []

        for conv in all_convs:
            if is_user_authorized_for_patient(user, conv.patient_id):
                sync_conversation_participants(conv)
                authorized_convs.append(conv)

        serializer = ConversationSerializer(authorized_convs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        patient_id = request.data.get('patientId') or request.query_params.get('patientId')
        
        if not patient_id:
            if user.role == 'patient':
                from patients.views import find_patient_by_identifier
                p = find_patient_by_identifier(user.full_name) or find_patient_by_identifier(user.patient_id)
                patient_id = p.id if p else user.patient_id

        if not is_user_authorized_for_patient(user, patient_id):
            return Response("Unauthorized: You do not have an approved relationship with this patient.", status=status.HTTP_403_FORBIDDEN)

        patient = Patient.objects.filter(id=patient_id).first()
        if not patient:
            return Response("Patient record not found.", status=status.HTTP_404_NOT_FOUND)

        conv, created = Conversation.objects.get_or_create(patient=patient, status='ACTIVE')
        sync_conversation_participants(conv)

        if created:
            log_audit_trail(request, 'Created Care-Team Conversation', f"Care-team chat initialized for Patient {patient.id}", 'Success')

        serializer = ConversationSerializer(conv, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, conv_id):
        conv = Conversation.objects.filter(id=conv_id).first()
        if not conv:
            return Response("Conversation not found.", status=status.HTTP_404_NOT_FOUND)

        # STRICT SERVER-SIDE AUTHORIZATION CHECK
        if not is_user_authorized_for_patient(request.user, conv.patient_id):
            return Response("Unauthorized: Access denied to this patient care-team conversation.", status=status.HTTP_403_FORBIDDEN)

        sync_conversation_participants(conv)

        # Mark unread messages sent by others as read
        unread_msgs = conv.messages.exclude(sender=request.user).filter(read_at__isnull=True)
        if unread_msgs.exists():
            unread_msgs.update(read_at=timezone.now(), delivered_at=timezone.now())

        messages = conv.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, conv_id):
        conv = Conversation.objects.filter(id=conv_id).first()
        if not conv:
            return Response("Conversation not found.", status=status.HTTP_404_NOT_FOUND)

        # STRICT SERVER-SIDE AUTHORIZATION CHECK
        if not is_user_authorized_for_patient(request.user, conv.patient_id):
            return Response("Unauthorized: Access denied to send message in this care-team conversation.", status=status.HTTP_403_FORBIDDEN)

        sync_conversation_participants(conv)

        content = request.data.get('content', '').strip()
        priority = request.data.get('priority', 'NORMAL').upper()
        if priority not in ['NORMAL', 'URGENT', 'EMERGENCY']:
            priority = 'NORMAL'

        is_emergency = (priority == 'EMERGENCY')
        file_obj = request.FILES.get('attachment')
        msg_type = 'TEXT'

        # File validation
        orig_filename = ''
        mime_type = ''
        file_size = None

        if file_obj:
            orig_filename = file_obj.name
            file_size = file_obj.size
            if file_size > MAX_FILE_SIZE_BYTES:
                return Response(f"Attachment exceeds maximum limit of 25MB.", status=status.HTTP_400_BAD_REQUEST)

            ext = orig_filename.split('.')[-1].lower() if '.' in orig_filename else ''
            if ext in EXECUTABLE_EXTENSIONS or ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
                return Response("Invalid attachment type. Executables and unapproved file extensions are prohibited.", status=status.HTTP_400_BAD_REQUEST)

            mime_type, _ = mimetypes.guess_type(orig_filename)
            mime_type = mime_type or 'application/octet-stream'

            if ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                msg_type = 'IMAGE'
            elif ext in ['mp4', 'mov', 'avi']:
                msg_type = 'VIDEO'
            else:
                msg_type = 'DOCUMENT'

        if not content and not file_obj:
            return Response("Message content or attachment is required.", status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conv,
            sender=request.user,
            message_type=msg_type,
            content=content,
            attachment=file_obj if file_obj else None,
            attachment_original_name=orig_filename,
            attachment_mime_type=mime_type,
            attachment_size=file_size,
            priority=priority,
            is_emergency=is_emergency,
            delivered_at=timezone.now()
        )

        conv.updated_at = timezone.now()
        conv.save(update_fields=['updated_at'])

        # Audit Logging
        action_name = 'Sent Emergency Message' if is_emergency else ('Uploaded Chat Attachment' if file_obj else 'Sent Chat Message')
        log_audit_trail(request, action_name, f"Message ID {message.id} in Conv {conv.id} (Priority: {priority})", 'Success')

        # Broadcast via WebSocket Channel Layer
        try:
            channel_layer = channels.layers.get_channel_layer()
            if channel_layer:
                serialized_msg = MessageSerializer(message).data
                async_to_sync(channel_layer.group_send)(
                    f"chat_{conv.id}",
                    {
                        "type": "chat_message",
                        "message": serialized_msg
                    }
                )
        except Exception as e:
            pass

        # Trigger Database Notification for Recipient Care Team Members
        participants = conv.participants.filter(is_active=True).exclude(user=request.user)
        for part in participants:
            create_notification(
                user=part.user,
                title="New Care-Team Message" if not is_emergency else "🚨 Emergency Care-Team Message",
                message=f"New message from {request.user.full_name or request.user.email}",
                category="chat",
                target_id=conv.id
            )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class MessageAttachmentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        message = Message.objects.filter(id=message_id).first()
        if not message or not message.attachment:
            return Response("Attachment file not found.", status=status.HTTP_404_NOT_FOUND)

        # STRICT SERVER-SIDE RE-EVALUATION OF PATIENT AUTHORIZATION
        if not is_user_authorized_for_patient(request.user, message.conversation.patient_id):
            return Response("Unauthorized: Permission denied to access this protected attachment.", status=status.HTTP_403_FORBIDDEN)

        file_path = message.attachment.path
        if not os.path.exists(file_path):
            return Response("Attachment file missing on server storage.", status=status.HTTP_404_NOT_FOUND)

        log_audit_trail(request, 'Accessed Protected Chat Attachment', f"Attachment for Message {message.id} (Conv {message.conversation_id})", 'Success')

        response = FileResponse(open(file_path, 'rb'), content_type=message.attachment_mime_type or 'application/octet-stream')
        filename = message.attachment_original_name or os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class MarkConversationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conv_id):
        conv = Conversation.objects.filter(id=conv_id).first()
        if not conv:
            return Response("Conversation not found.", status=status.HTTP_404_NOT_FOUND)

        if not is_user_authorized_for_patient(request.user, conv.patient_id):
            return Response("Unauthorized: Access denied.", status=status.HTTP_403_FORBIDDEN)

        unread_count = conv.messages.exclude(sender=request.user).filter(read_at__isnull=True).update(read_at=timezone.now(), delivered_at=timezone.now())
        return Response({'status': 'success', 'readCount': unread_count}, status=status.HTTP_200_OK)
