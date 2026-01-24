from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from rest_framework.decorators import api_view
from rest_framework.response import Response


def login_success_view(request):
    return render(request, "auth/login_success.html")


def login_page_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            # After successful login, go to homepage
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "auth/login.html", {"form": form})


@api_view(["GET"])
def current_user(request):
    if request.user.is_authenticated:
        return Response({"username": request.user.username, "email": request.user.email, "id": request.user.id})
    return Response(None)
