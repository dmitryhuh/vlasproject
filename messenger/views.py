from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from made_app.models import Profile
from .models import Conversation, Message

def get_user_conversation(user, conversation_id):
    return get_object_or_404(
        Conversation.objects.filter(Q(participant1=user) | Q(participant2=user)),
        pk=conversation_id,
    )

@login_required
def inbox(request):
    query = request.GET.get("q", "").strip()
    conversations = (
        Conversation.objects.filter(
            (Q(participant1=request.user) | Q(participant2=request.user)),
            messages__isnull=False,
        )
        .distinct()
        .select_related("participant1", "participant2")
        .prefetch_related(
            Prefetch(
                "messages",
                queryset=Message.objects.select_related("sender").order_by("-id")[:1],
                to_attr="last_messages",
            )
        )
        .order_by("-updated_at")
    )

    if query:
        conversations = conversations.filter(
            Q(participant1=request.user, participant2__username__icontains=query)
            | Q(participant2=request.user, participant1__username__icontains=query)
        )

    visible_conversations = []
    seen_user_ids = set()

    for chat in conversations:
        chat_user = chat.other_user(request.user)
        if chat_user.id in seen_user_ids:
            continue
        seen_user_ids.add(chat_user.id)
        chat.chat_user = chat_user
        chat.chat_user_profile = Profile.objects.filter(user=chat_user).first()
        chat.last_message = chat.last_messages[0] if chat.last_messages else None
        visible_conversations.append(chat)

    search_users = User.objects.none()
    if query:
        search_users = (
            User.objects.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
            .exclude(id=request.user.id)[:10]
        )

    return render(request, "messenger/inbox.html", {
        "conversations": visible_conversations,
        "query": query,
        "search_users": search_users,
    })

@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    if other_user == request.user:
        return redirect("messenger:inbox")

    first_user, second_user = sorted(
        (request.user, other_user),
        key=lambda item: item.id,
    )
    chat, _ = Conversation.objects.get_or_create(
        participant1=first_user,
        participant2=second_user,
    )
    return redirect("messenger:conversation", conversation_id=chat.id)

@login_required
def conversation(request, conversation_id):
    chat = get_user_conversation(request.user, conversation_id)
    other_user = chat.other_user(request.user)
    other_profile = Profile.objects.filter(user=other_user).first()
    chat_messages = list(
        chat.messages.select_related("sender").order_by("-id")[:60]
    )
    chat_messages.reverse()

    return render(request, "messenger/conversation.html", {
        "conversation": chat,
        "other_user": other_user,
        "other_profile": other_profile,
        "chat_messages": chat_messages,
    })

@login_required
@require_POST
def delete_message(request, message_id):
    message = get_object_or_404(
        Message.objects.filter(
            Q(conversation__participant1=request.user)
            | Q(conversation__participant2=request.user)
        ),
        pk=message_id,
    )

    if message.sender_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Можна видаляти лише ваші повідомлення."}, status=403)

    conversation_id = message.conversation_id
    message.delete()
    async_to_sync(get_channel_layer().group_send)(
        f"chat_{conversation_id}",
        {"type": "chat.delete", "message_id": message_id},
    )
    return JsonResponse({"ok": True, "id": message_id})
