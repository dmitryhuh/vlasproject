from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from made_app.models import Notification
from .models import Conversation, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"chat_{self.conversation_id}"
        user = self.scope["user"]

        if not user.is_authenticated or not await self.can_join_chat(user.id):
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        text = content.get("text", "") if isinstance(content, dict) else ""
        if not isinstance(text, str):
            await self.send_json({"type": "error", "message": "Некоректне повідомлення."})
            return

        text = text.strip()
        if not text:
            return
        if len(text) > 5000:
            await self.send_json({"type": "error", "message": "Повідомлення має бути не довшим за 5000 символів."})
            return

        message = await self.create_message(text)
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "message": message},
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message", **event["message"]})

    async def chat_delete(self, event):
        await self.send_json({"type": "delete", "id": event["message_id"]})

    @database_sync_to_async
    def can_join_chat(self, user_id):
        return Conversation.objects.filter(pk=self.conversation_id).filter(
            Q(participant1_id=user_id) | Q(participant2_id=user_id)
        ).exists()

    @database_sync_to_async
    def create_message(self, text):
        user = self.scope["user"]
        chat = Conversation.objects.get(pk=self.conversation_id)
        message = Message.objects.create(
            conversation=chat,
            sender=user,
            text=text,
        )
        chat.save(update_fields=["updated_at"])

        recipient = chat.other_user(user)
        Notification.objects.create(
            user=recipient,
            message=f"@{user.username} написав вам повідомлення.",
        )

        return {
            "id": message.id,
            "sender_id": message.sender_id,
            "sender": user.username,
            "text": message.text,
            "time": timezone.localtime(message.created_at).strftime("%H:%M"),
            "delete_url": reverse("messenger:delete_message", args=[message.id]),
        }
