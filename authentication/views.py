from django.shortcuts import render


def login_success_view(request):
    return render(request, 'login_success.html')
