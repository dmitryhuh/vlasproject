from django.urls import path
from . import views

app_name = "messenger"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("start/<str:username>/", views.start_chat, name="start_chat"),
    path("<int:conversation_id>/", views.conversation, name="conversation"),
    path("<int:message_id>/delete/", views.delete_message, name="delete_message"),
]
