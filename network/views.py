import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from .models import User, Post, Follow, Like


def index(request):
    if request.user.is_authenticated:
       if request.method == "POST":
        user = request.user
        post = request.POST["post"]
        date = datetime.now()
        if post != "":
            Post.objects.create(user=user, post=post, date=date, likes=0)
    posts = Post.objects.all().order_by('-date')
    for post in posts:
        post.likes = Like.objects.filter(post=post.id).count()
        post.save()
    paginator = Paginator(posts, 10)
    page_num = request.GET.get('page')
    page_object = paginator.get_page(page_num)
    return render(request, "network/index.html", {
        "page_object": page_object,
    })

# THIS FUNCTION TO CREATE NEW POST
@login_required
def new_post(request):
    return render(request, "network/new_post.html")

# THIS FUNCTION FOR PROFILE USER
def profile(request, username):
    owner = User.objects.get(id=username)
    if request.user.is_authenticated:
        button = "Follow" if Follow.objects.filter(follower=request.user, following=owner).count() == 0 else "Unfollow"
    if request.method == "POST":
        if request.POST["button"] == "Follow":
            button = "Unfollow"
            Follow.objects.create(follower=request.user, following=owner)
        else:
            button = "Follow"
            Follow.objects.get(follower=request.user, following=owner).delete()
    posts = Post.objects.filter(user=owner.id).order_by('-date')
    for post in posts:
        post.likes = Like.objects.filter(post=post.id).count()
        post.save()
    paginator = Paginator(posts, 10)
    page_numb = request.GET.get('page')
    page_object = paginator.get_page(page_numb)

    return render(request, "network/profile.html", {
        "owner": owner,
        "followers": Follow.objects.filter(following=owner).count(),
        "following": Follow.objects.filter(follower=owner).count(),
        "page_object": page_object,
        "button": button
    })

# THIS FUNCTION FOR FOLLOWING
def following(request):
    user = request.user
    following = Follow.objects.filter(follower=request.user).values('following_id')

    posts = Post.objects.filter(user__in=following).order_by('-date')
    for post in posts:
        post.likes = Like.objects.filter(post=post.id).count()
        post.save()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "page_obj": page_obj
    })

@csrf_exempt
def edit(request, post_id):
    post = Post.objects.get(id=post_id)

    if request.method == "PUT":
        data = json.loads(request.body)
        if data.get("post") is not None:
            post.post = data["post"]
        post.save()
        return HttpResponse(status=204)

@csrf_exempt
def like(request, post_id):
    post = Post.objects.get(id=post_id)

    if request.method == "GET":
        return JsonResponse(post.serialize())

    if request.method == "PUT":
        data = json.loads(request.body)
        print(data.get("like"))
        if data.get("like"):
            Like.objects.create(user=request.user, post=post)
            post.likes = Like.objects.filter(post=post).count()
        else:
            Like.objects.filter(user=request.user, post=post).delete()
            post.likes = Like.objects.filter(post=post).count()
        post.save()
        return HttpResponse(status=204)

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")