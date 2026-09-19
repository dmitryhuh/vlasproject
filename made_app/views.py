from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Bookmark, Comment, Follow, Like, Notification, Post, Profile, Repost


def home(request):
    posts = Post.objects.all()

    if request.user.is_authenticated:
        following = Follow.objects.filter(follower=request.user).values_list("following", flat=True)
        following_posts = Post.objects.filter(author__in=following)
    else:
        following_posts = Post.objects.none()

    return render(request, "home.html", {
        "posts": posts,
        "following_posts": following_posts
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if not username or not password or not password2:
            messages.error(request, "Заповніть усі поля.")
            return redirect("register")

        if password != password2:
            messages.error(request, "Паролі не збігаються.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Такий користувач вже існує.")
            return redirect("register")

        user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=user)

        login(request, user)
        return redirect("home")

    return render(request, "register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect("home")

        messages.error(request, "Неправильний username або пароль.")

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like = Like.objects.filter(user=request.user, post=post).first()

    if like:
        like.delete()
    else:
        Like.objects.create(user=request.user, post=post)

        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                message=f"{request.user.username} вподобав вашу публікацію."
            )

    return redirect("home")


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == "POST":
        text = request.POST.get("text")

        if text:
            Comment.objects.create(
                author=request.user,
                post=post,
                text=text
            )

            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    message=f"{request.user.username} прокоментував вашу публікацію."
                )

    return redirect("home")


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author == request.user:
        comment.delete()

    return redirect("home")


@login_required
def repost_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    repost = Repost.objects.filter(user=request.user, post=post).first()

    if repost:
        repost.delete()
    else:
        Repost.objects.create(user=request.user, post=post)

        if post.author != request.user:
            Notification.objects.create(
                user=post.author,
                message=f"{request.user.username} зробив репост вашої публікації."
            )

    return redirect("home")


@login_required
def bookmark_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    bookmark = Bookmark.objects.filter(user=request.user, post=post).first()

    if bookmark:
        bookmark.delete()
    else:
        Bookmark.objects.create(user=request.user, post=post)

    return redirect("home")


@login_required
def bookmarks(request):
    posts = Post.objects.filter(bookmarks__user=request.user)

    return render(request, "bookmarks.html", {
        "posts": posts
    })


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = Profile.objects.get_or_create(user=user)

    posts = Post.objects.filter(author=user)
    followers = Follow.objects.filter(following=user)
    following = Follow.objects.filter(follower=user)

    is_following = Follow.objects.filter(
        follower=request.user,
        following=user
    ).exists()

    return render(request, "profile.html", {
        "profile_user": user,
        "profile": profile,
        "posts": posts,
        "followers": followers,
        "following": following,
        "is_following": is_following
    })


@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        username = request.POST.get("username")
        bio = request.POST.get("bio")
        birthday = request.POST.get("birthday")
        avatar = request.FILES.get("avatar")

        if username:
            username_exists = User.objects.filter(
                username=username
            ).exclude(id=request.user.id).exists()

            if username_exists:
                messages.error(request, "Такий username уже існує.")
                return redirect("edit_profile")

            request.user.username = username
            request.user.save()

        profile.bio = bio

        if birthday:
            profile.birthday = birthday

        if avatar:
            profile.avatar = avatar

        profile.save()

        return redirect("profile", username=request.user.username)

    return render(request, "edit_profile.html", {
        "profile": profile
    })


@login_required
def follow_user(request, username):
    user = get_object_or_404(User, username=username)

    if user == request.user:
        return redirect("profile", username=username)

    follow = Follow.objects.filter(
        follower=request.user,
        following=user
    ).first()

    if follow:
        follow.delete()
    else:
        Follow.objects.create(
            follower=request.user,
            following=user
        )

        Notification.objects.create(
            user=user,
            message=f"{request.user.username} підписався на вас."
        )

    return redirect("profile", username=username)


@login_required
def followers(request, username):
    user = get_object_or_404(User, username=username)

    users = User.objects.filter(
        followers__follower__following=user
    ).distinct()

    return render(request, "users.html", {
        "title": "Підписники",
        "users": users
    })


@login_required
def following(request, username):
    user = get_object_or_404(User, username=username)

    users = User.objects.filter(
        following__following=user
    ).distinct()

    return render(request, "users.html", {
        "title": "Підписки",
        "users": users
    })


@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user)

    notifications_list.filter(is_read=False).update(is_read=True)

    return render(request, "notifications.html", {
        "notifications": notifications_list
    })


def search(request):
    query = request.GET.get("q", "")

    users = User.objects.filter(username__icontains=query)

    posts = Post.objects.filter(
        Q(text__icontains=query) |
        Q(author__username__icontains=query)
    )

    return render(request, "search.html", {
        "query": query,
        "users": users,
        "posts": posts
    })
