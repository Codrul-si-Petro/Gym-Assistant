from django.shortcuts import render


def login_success(request):
    return render(request, 'login_success.html')
