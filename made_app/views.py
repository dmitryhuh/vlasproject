from datetime import datetime
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .models import ( Bookmark, Comment, Follow, Like, Notification, Post, PostImage, Profile, Repost )

def prepare_posts(posts, user):
    like_totals = Like.objects.filter(post_id=OuterRef("pk")).order_by().values("post_id").annotate(total=Count("id")).values("total")
    comment_totals = Comment.objects.filter(post_id=OuterRef("pk")).order_by().values("post_id").annotate(total=Count("id")).values("total")
    repost_totals = Repost.objects.filter(post_id=OuterRef("pk")).order_by().values("post_id").annotate(total=Count("id")).values("total")

    posts = posts.select_related("author", "author__profile").prefetch_related(
        "images",
        "comments__author__profile",
    ).annotate(
        like_count=Coalesce(Subquery(like_totals, output_field=IntegerField()), Value(0)),
        comment_count=Coalesce(Subquery(comment_totals, output_field=IntegerField()), Value(0)),
        repost_count=Coalesce(Subquery(repost_totals, output_field=IntegerField()), Value(0)),
    )
    posts = list(posts)
    ids = [post.id for post in posts]

    if not user.is_authenticated or not ids:
        for post in posts:
            post.is_liked = False
            post.is_reposted = False
            post.is_bookmarked = False
        return posts

    liked = set(
        Like.objects.filter(user=user, post_id__in=ids)
        .values_list("post_id", flat=True)
    )

    reposted = set(
        Repost.objects.filter(user=user, post_id__in=ids)
        .values_list("post_id", flat=True)
    )

    bookmarked = set(
        Bookmark.objects.filter(user=user, post_id__in=ids)
        .values_list("post_id", flat=True)
    )

    for post in posts:
        post.is_liked = post.id in liked
        post.is_reposted = post.id in reposted
        post.is_bookmarked = post.id in bookmarked

    return posts

def home(request):
    posts = prepare_posts(Post.objects.all(), request.user)
    following_posts = []

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            follower=request.user
        ).values_list("following", flat=True)

        following_posts = prepare_posts(
            Post.objects.filter(author__in=following),
            request.user
        )

    return render(request, "home.html", {
        "posts": posts,
        "following_posts": following_posts,
    })

def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    context = {
        "step": 1,
    }

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        birthday = request.POST.get("birthday", "")

        context["step"] = 2

        if not first_name:
            messages.error(request, "Введіть своє ім’я.")
            context["step"] = 1
            return render(request, "register.html", context)

        if not birthday:
            messages.error(request, "Оберіть дату народження.")
            context["step"] = 1
            return render(request, "register.html", context)

        try:
            birthday_date = datetime.strptime(
                birthday,
                "%Y-%m-%d"
            ).date()
        except ValueError:
            messages.error(request, "Оберіть правильну дату народження.")
            context["step"] = 1
            return render(request, "register.html", context)

        if not username or not password or not password2:
            messages.error(request, "Заповніть усі поля.")
            return render(request, "register.html", context)

        if password != password2:
            messages.error(request, "Паролі не збігаються.")
            return render(request, "register.html", context)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Такий username уже існує.")
            return render(request, "register.html", context)

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        Profile.objects.create(
            user=user,
            birthday=birthday_date
        )

        login(request, user)

        return redirect("home")

    return render(request, "register.html", context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(
            username=username,
            password=password
        )

        if user:
            login(request, user)

            next_url = request.GET.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)

            return redirect("home")

        messages.error(
            request,
            "Неправильний username або пароль."
        )

    return render(request, "login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return JsonResponse({"ok": False}, status=403)

    post.delete()

    return JsonResponse({"ok": True})

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({"ok": False}, status=400)

    comment = Comment.objects.create(
        author=request.user,
        post=post,
        text=text,
    )

    if post.author != request.user:
        Notification.objects.create(
            user=post.author,
            message=f"{request.user.username} прокоментував вашу публікацію."
        )

    profile = Profile.objects.filter(
        user=request.user
    ).first()

    return JsonResponse({
        "ok": True,
        "id": comment.id,
        "username": request.user.username,
        "text": comment.text,
        "avatar": (
            profile.avatar.url
            if profile and profile.avatar
            else ""
        ),
        "delete_url": f"/comment/{comment.id}/delete/",
    })

@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(
        Comment,
        id=comment_id
    )

    if comment.author != request.user:
        return JsonResponse({"ok": False}, status=403)

    comment.delete()

    return JsonResponse({"ok": True})

@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like = Like.objects.filter(
        user=request.user,
        post=post
    ).first()

    if like:
        like.delete()
        active = False
    else:
        Like.objects.create(
            user=request.user,
            post=post
        )

        active = True

        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                message=f"{request.user.username} вподобав вашу публікацію."
            )

    return JsonResponse({
        "ok": True,
        "active": active,
        "count": post.likes.count(),
    })

@login_required
@require_POST
def repost_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    repost = Repost.objects.filter(
        user=request.user,
        post=post
    ).first()

    if repost:
        repost.delete()
        active = False
    else:
        Repost.objects.create(
            user=request.user,
            post=post
        )

        active = True

        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                message=f"{request.user.username} зробив репост вашої публікації."
            )

    return JsonResponse({
        "ok": True,
        "active": active,
        "count": post.reposts.count(),
    })

@login_required
@require_POST
def bookmark_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    bookmark = Bookmark.objects.filter(
        user=request.user,
        post=post
    ).first()

    if bookmark:
        bookmark.delete()
        active = False
    else:
        Bookmark.objects.create(
            user=request.user,
            post=post
        )

        active = True

    return JsonResponse({
        "ok": True,
        "active": active
    })

@login_required
def profile(request, username):
    user = get_object_or_404(
        User,
        username=username
    )

    profile, _ = Profile.objects.get_or_create(
        user=user
    )

    posts = prepare_posts(
        Post.objects.filter(author=user),
        request.user,
    )

    repost_posts = prepare_posts(
        Post.objects.filter(
            reposts__user=user
        ).distinct(),
        request.user,
    )

    saved_posts = []

    if request.user == user:
        saved_posts = prepare_posts(
            Post.objects.filter(
                bookmarks__user=user
            ),
            request.user,
        )

    followers = Follow.objects.filter(
        following=user
    )

    following = Follow.objects.filter(
        follower=user
    )

    is_following = Follow.objects.filter(
        follower=request.user,
        following=user,
    ).exists()

    tab = request.GET.get("tab", "posts")

    if tab not in ("posts", "reposts", "saved"):
        tab = "posts"

    if tab == "saved" and request.user != user:
        tab = "posts"

    return render(request, "profile.html", {
        "profile_user": user,
        "profile": profile,
        "posts": posts,
        "repost_posts": repost_posts,
        "saved_posts": saved_posts,
        "followers": followers,
        "following": following,
        "is_following": is_following,
        "active_tab": tab,
    })

@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        username = request.POST.get(
            "username",
            ""
        ).strip()

        bio = request.POST.get(
            "bio",
            ""
        ).strip()

        birthday = request.POST.get(
            "birthday",
            ""
        )

        avatar = request.FILES.get("avatar")

        if not first_name:
            messages.error(
                request,
                "Ім’я не може бути порожнім."
            )
            return redirect("edit_profile")

        if User.objects.filter(
            username=username
        ).exclude(
            id=request.user.id
        ).exists():
            messages.error(
                request,
                "Такий username уже існує."
            )
            return redirect("edit_profile")

        birthday_date = None

        if birthday:
            try:
                birthday_date = datetime.strptime(
                    birthday,
                    "%Y-%m-%d"
                ).date()
            except ValueError:
                messages.error(
                    request,
                    "Оберіть правильну дату народження."
                )
                return redirect("edit_profile")

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.username = username

        request.user.save(update_fields=[
            "first_name",
            "last_name",
            "username",
        ])

        profile.bio = bio
        profile.birthday = birthday_date

        if avatar:
            profile.avatar = avatar

        profile.save()

        return redirect(
            "profile",
            username=request.user.username,
        )

    return render(request, "edit_profile.html", {
        "profile": profile,
    })

@login_required
def follow_user(request, username):
    user = get_object_or_404(
        User,
        username=username
    )

    if user == request.user:
        return redirect(
            "profile",
            username=username
        )

    follow = Follow.objects.filter(
        follower=request.user,
        following=user,
    ).first()

    if follow:
        follow.delete()
    else:
        Follow.objects.create(
            follower=request.user,
            following=user,
        )

        Notification.objects.create(
            user=user,
            message=f"{request.user.username} підписався на вас."
        )

    return redirect(
        "profile",
        username=username
    )

@login_required
def followers(request, username):
    user = get_object_or_404(
        User,
        username=username
    )

    ids = Follow.objects.filter(
        following=user
    ).values_list(
        "follower_id",
        flat=True,
    )

    users = User.objects.filter(
        id__in=ids
    )

    return render(request, "users.html", {
        "title": "Підписники",
        "username": username,
        "users": users,
    })

@login_required
def following(request, username):
    user = get_object_or_404(
        User,
        username=username
    )

    ids = Follow.objects.filter(
        follower=user
    ).values_list(
        "following_id",
        flat=True,
    )

    users = User.objects.filter(
        id__in=ids
    )

    return render(request, "users.html", {
        "title": "Підписки",
        "username": username,
        "users": users,
    })

@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user)

    response = render(request, "notifications.html", {
        "notifications": notifications_list,
    })

    notifications_list.filter(is_read=False).update(is_read=True)

    return response

def search(request):
    query = request.GET.get(
        "q",
        ""
    ).strip()

    users = (
        User.objects.filter(
            username__icontains=query
        )
        if query
        else User.objects.none()
    )

    posts = (
        Post.objects.filter(
            Q(text__icontains=query) |
            Q(author__username__icontains=query)
        )
        if query
        else Post.objects.none()
    )

    if request.user.is_authenticated:
        posts = prepare_posts(
            posts,
            request.user
        )

    return render(request, "search.html", {
        "query": query,
        "users": users,
        "posts": posts,
    })

@login_required
def create_post(request):
    if request.method == "POST":
        text = request.POST.get(
            "text",
            ""
        ).strip()

        images = request.FILES.getlist(
            "images"
        )[:6]

        if text or images:
            post = Post.objects.create(
                author=request.user,
                text=text,
            )

            for image in images:
                PostImage.objects.create(
                    post=post,
                    image=image,
                )

            return redirect("home")

    return render(
        request,
        "create_post.html"
    )
