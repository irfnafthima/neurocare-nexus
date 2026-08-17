import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import CustomUser
from chat.models import Conversation
from medical_records.views import is_user_authorized_for_patient

@database_sync_to_async
def get_user_from_token(token_str):
    try:
        access_token = AccessToken(token_str)
        user_id = access_token['user_id']
        return CustomUser.objects.get(id=user_id)
    except Exception:
        return AnonymousUser()

@database_sync_to_async
def check_conversation_authorization(user, conv_id):
    if not user or not user.is_authenticated:
        return False
    conv = Conversation.objects.filter(id=conv_id).first()
    if not conv:
        return False
    return is_user_authorized_for_patient(user, conv.patient_id)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conv_id = self.scope['url_route']['kwargs']['conv_id']
        self.room_group_name = f"chat_{self.conv_id}"

        # Extract token from query params ?token=...
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        token = None
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break

        if token:
            self.scope['user'] = await get_user_from_token(token)

        user = self.scope.get('user', AnonymousUser())
        if not user or not user.is_authenticated:
            await self.close(code=4001) # Unauthorized
            return

        # STRICT SERVER-SIDE AUTHORIZATION CHECK BEFORE JOINING WEBSOCKET ROOM
        is_authorized = await check_conversation_authorization(user, self.conv_id)
        if not is_authorized:
            await self.close(code=4003) # Forbidden
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Broadcast user online presence
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_presence',
                'user_id': user.id,
                'user_name': user.full_name or user.email,
                'status': 'ONLINE'
            }
        )

    async def disconnect(self, close_code):
        user = self.scope.get('user', AnonymousUser())
        if user and user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_presence',
                    'user_id': user.id,
                    'user_name': user.full_name or user.email,
                    'status': 'OFFLINE'
                }
            )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type')
            user = self.scope.get('user', AnonymousUser())

            # Re-verify authorization on every incoming socket message
            is_authorized = await check_conversation_authorization(user, self.conv_id)
            if not is_authorized:
                await self.close(code=4003)
                return

            if msg_type == 'typing':
                is_typing = data.get('is_typing', False)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': user.id,
                        'user_name': user.full_name or user.email,
                        'role': user.role,
                        'is_typing': is_typing
                    }
                )
        except Exception:
            pass

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_presence(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_presence',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'status': event['status']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'role': event['role'],
            'is_typing': event['is_typing']
        }))
