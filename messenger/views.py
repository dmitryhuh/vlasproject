from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from made_app.models import Profile
from .models import Conversation, Message

# Create your views here.

def get_user_conversation(user, conversation_id):
    return get_object_or_404(Conversation.objects.filter(Q(participant1=user) | Q(participant2=user)), pk=conversation_id)


def prepare_message(message, user):
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "sender": message.sender.username,
        "text": message.text,
        "time": timezone.localtime(message.created_at).strftime("%H:%M"),
        "is_mine": message.sender_id == user.id,
    }


@login_required
def inbox(request):
    query = request.GET.get("q", "").strip()

    conversations = (
        Conversation.objects.filter(Q(participant1=request.user) | Q(participant2=request.user))
        .select_related("participant1", "participant2")
        .prefetch_related(
            Prefetch(
                "messages",
                queryset=Message.objects.select_related("sender").order_by("-id")[:1],
                to_attr="last_messages",
            )
        )
        .annotate(
            unread_count=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender_id=request.user.id),
            )
        )
        .order_by("-updated_at")
    )

    if query:
        conversations = conversations.filter(
            Q(participant1=request.user, participant2__username__icontains=query)
            | Q(participant2=request.user, participant1__username__icontains=query)
        )

    for chat in conversations:
        chat.chat_user = chat.other_user(request.user)
        chat.chat_user_profile = Profile.objects.filter(user=chat.chat_user).first()
        chat.last_message = chat.last_messages[0] if chat.last_messages else None

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
        "conversations": conversations,
        "query": query,
        "search_users": search_users,
    })


@login_required
def start_chat(request, username):
    other_user = get_object_or_404(User, username=username)

    if other_user == request.user:
        return redirect("messenger:inbox")

    if request.user.id < other_user.id:
        first_user, second_user = request.user, other_user
    else:
        first_user, second_user = other_user, request.user

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

    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    chat_messages = list(
        chat.messages.select_related("sender").order_by("-id")[:60]
    )
    chat_messages.reverse()

    return render(request, "messenger/conversation.html", {
        "conversation": chat,
        "other_user": other_user,
        "other_profile": other_profile,
        "chat_messages": chat_messages,
        "last_message_id": chat_messages[-1].id if chat_messages else 0,
    })


@login_required
@require_GET
def conversation_messages(request, conversation_id):
    chat = get_user_conversation(request.user, conversation_id)
    chat.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    try:
        after_id = max(0, int(request.GET.get("after_id", "0")))
    except (TypeError, ValueError):
        after_id = 0

    new_messages = (
        chat.messages.filter(id__gt=after_id)
        .select_related("sender")
        .order_by("id")[:100]
    )

    return JsonResponse({
        "messages": [prepare_message(message, request.user) for message in new_messages]
    })


@login_required
@require_POST
def send_message(request, conversation_id):
    chat = get_user_conversation(request.user, conversation_id)
    text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({"ok": False, "error": "Напишіть повідомлення."}, status=400)

    if len(text) > 5000:
        return JsonResponse({
            "ok": False,
            "error": "Повідомлення має бути не довшим за 5000 символів.",
        }, status=400)

    message = Message.objects.create(
        conversation=chat,
        sender=request.user,
        text=text,
    )
    chat.save(update_fields=["updated_at"])

    return JsonResponse({"ok": True, "message": prepare_message(message, request.user)})