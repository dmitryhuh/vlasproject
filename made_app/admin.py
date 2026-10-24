from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile, Post, PostImage, Comment, Like, Repost, Bookmark, Follow, Notification

class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0

class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Основне", {"fields": ("first_name", "last_name")}),
        ("Права", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Дати", {"fields": ("last_login", "date_joined")}),
    )

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 0

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("author", "text", "created_at")
    search_fields = ("author__username", "text")
    inlines = [PostImageInline]

@admin.register(PostImage)
class PostImageAdmin(admin.ModelAdmin):
    list_display = ("post", "image")
    search_fields = ("post__author__username",)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "text", "created_at")
    search_fields = ("author__username", "post__text", "text")

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__text")

@admin.register(Repost)
class RepostAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__text")

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    search_fields = ("user__username", "post__text")

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "message")
