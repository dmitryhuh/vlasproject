from django.conf import settings
from django.db import models

class Conversation(models.Model):
    participant1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messenger_conversations_first")
    participant2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messenger_conversations_second")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["participant1", "participant2"], name="messenger_unique_pair")
        ]

    def other_user(self, user):
        return self.participant2 if self.participant1_id == user.id else self.participant1

    def __str__(self):
        return f"{self.participant1.username} — {self.participant2.username}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messenger_messages_sent")
    text = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["conversation", "created_at"], name="messenger_msg_created_idx")
        ]

    def __str__(self):
        return f"{self.sender.username}: {self.text[:40]}"