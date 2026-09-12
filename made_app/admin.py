from django.contrib import admin
from made_app.models import *

# Register your models here.

admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Repost)
admin.site.register(Bookmark)
admin.site.register(Notification)
admin.site.register(Follow)

