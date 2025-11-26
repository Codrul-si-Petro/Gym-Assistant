from django.shortcuts import render
from django.views import View


class LoginSuccessView(View):

    def get(self, request):
        return render(request, "login_success.html")
