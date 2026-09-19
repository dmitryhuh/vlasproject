from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("post/<int:post_id>/like/", views.like_post, name="like_post"),
    path("post/<int:post_id>/comment/", views.add_comment, name="add_comment"),
    path("comment/<int:comment_id>/delete/", views.delete_comment, name="delete_comment"),
    path("post/<int:post_id>/repost/", views.repost_post, name="repost_post"),
    path("post/<int:post_id>/bookmark/", views.bookmark_post, name="bookmark_post"),
    path("bookmarks/", views.bookmarks, name="bookmarks"),
    path("profile/<str:username>/", views.profile, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/<str:username>/follow/", views.follow_user, name="follow_user"),
    path("profile/<str:username>/followers/", views.followers, name="followers"),
    path("profile/<str:username>/following/", views.following, name="following"),
    path("notifications/", views.notifications, name="notifications"),
    path("search/", views.search, name="search"),
]