from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "participant1", "participant2", "created_at", "updated_at")
    search_fields = ("participant1__username", "participant2__username")
    list_select_related = ("participant1", "participant2")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
    search_fields = ("sender__username", "text")
    list_filter = ("created_at",)
    list_select_related = ("conversation", "sender")
    readonly_fields = ("created_at",)
