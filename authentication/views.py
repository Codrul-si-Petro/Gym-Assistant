from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

def login_success_view(request):
    return render(request, "login_success.html") # TODO: move these pages to a subdirectory


def login_page_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            login(request, form.get_user())
            return redirect('login_success')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html", {"form": form})
