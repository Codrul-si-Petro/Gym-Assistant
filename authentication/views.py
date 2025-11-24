from django.shortcuts import render


def LoginSuccessView(request):
    return render(request, 'login_success.html')
