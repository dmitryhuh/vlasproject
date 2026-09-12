from django.shortcuts import render
from django.contrib.auth.models import User
from made_app.models import *


def home(request):
    posts = Post.objects.all()
    return render(request, 'home.html', {'posts': posts})

def profile(request, username):
    user = User.objects.get(username=username)
    profile = Profile.objects.get(user=user)
    posts = Post.objects.filter(author=user)
    return render(request, 'profile.html', {'profile': profile, 'posts': posts})
