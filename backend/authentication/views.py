from allauth.account.models import EmailAddress
from allauth.account.views import LoginView, PasswordChangeView, SignupView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from backend.email_sender import MailerSendPasswordResetForm

from .serializers import LoginSerializer, SignupSerializer


@swagger_auto_schema(
    method="post",
    operation_description="Login with username and password. Returns user information on success.",
    request_body=LoginSerializer,
    responses={
        200: openapi.Response(
            description="Login successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                    "email": openapi.Schema(type=openapi.TYPE_STRING),
                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        400: "Invalid credentials or missing fields",
        401: "Authentication failed",
    },
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if email is verified
            email_address = EmailAddress.objects.filter(user=user, primary=True).first()
            if email_address and not email_address.verified:
                return Response(
                    {"error": "Please verify your email address before logging in."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            login(request, user)
            return Response(
                {
                    "username": user.username,
                    "email": user.email,
                    "id": user.id,
                    "message": "Login successful",
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    operation_description="Register a new user account. Returns user information on success.",
    request_body=SignupSerializer,
    responses={
        201: openapi.Response(
            description="User created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                    "email": openapi.Schema(type=openapi.TYPE_STRING),
                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        400: "Invalid data or validation errors",
    },
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "username": user.username,
                "email": user.email,
                "id": user.id,
                "message": "User created. Please log in to your account.",
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    operation_description="Logout the currently authenticated user.",
    responses={
        200: openapi.Response(
            description="Logout successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        401: "User not authenticated",
    },
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    logout(request)
    return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="delete",
    operation_description="Delete the currently authenticated user's account. This action is irreversible and will permanently delete all user data.",
    responses={
        200: openapi.Response(
            description="Account deleted successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
        ),
        401: "User not authenticated",
    },
    tags=["Authentication"],
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def api_delete_account(request):
    """Delete the authenticated user's account."""
    user = request.user
    username = user.username
    user.delete()
    logout(request)
    return Response(
        {"message": f"Account for user '{username}' has been permanently deleted."},
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="get",
    operation_description="Get the currently authenticated user's information. Returns user details if authenticated, null otherwise.",
    responses={
        200: openapi.Response(
            description="User information if authenticated, null if not authenticated",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "username": openapi.Schema(type=openapi.TYPE_STRING),
                    "email": openapi.Schema(type=openapi.TYPE_STRING),
                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                },
            ),
        ),
    },
    tags=["Authentication"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def current_user(request):
    if request.user.is_authenticated:
        return Response({"username": request.user.username, "email": request.user.email, "id": request.user.id})
    return Response(None)


# Override Django's built-in password reset views to use custom templates in auth/ folder
class CustomPasswordResetView(PasswordResetView):
    template_name = "auth/password_reset_request_form.html"
    email_template_name = "emails/password_reset_email.html"
    form_class = MailerSendPasswordResetForm  # Use MailerSend instead of Django's email backend


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "auth/password_reset_email_sent.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "auth/password_reset_confirm_token.html"


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "auth/password_reset_complete_success.html"


# Override django-allauth views to use custom templates in auth/ folder
class CustomAllauthLoginView(LoginView):
    template_name = "auth/login_with_social_providers.html"

    def dispatch(self, request, *args, **kwargs):
        # If already logged in, redirect to home
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


class CustomAllauthSignupView(SignupView):
    template_name = "auth/signup_with_social_providers.html"

    def dispatch(self, request, *args, **kwargs):
        # If already logged in, redirect to home
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordChangeView(PasswordChangeView):
    template_name = "auth/password_change.html"
    success_url = reverse_lazy("account_login")
