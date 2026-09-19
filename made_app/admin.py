from django.contrib import admin
from django.contrib.auth.models import User

from .models import (
    Profile,
    Post,
    Comment,
    Like,
    Repost,
    Bookmark,
    Follow,
    Notification,
)


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0


class UserAdmin(admin.ModelAdmin):
    inlines = [ProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "text", "created_at")
    search_fields = ("author__username", "text")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "text", "created_at")


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(Repost)
class RepostAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at", "is_read")