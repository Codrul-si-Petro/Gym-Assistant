from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from backend.email_sender import MailerSendPasswordResetForm

from .models import UserWorkoutSplit
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    SignupSerializer,
    UpdatePreferencesSerializer,
    UpdateUsernameSerializer,
)

User = get_user_model()


def _frontend_url(path: str) -> str:
    frontend_url = (settings.FRONTEND_URL or "").rstrip("/")
    return f"{frontend_url}{path}"


def redirect_to_frontend_login(request):
    return redirect(_frontend_url("/pages/auth/login.html"))


def redirect_to_frontend_signup(request):
    return redirect(_frontend_url("/pages/auth/signup.html"))


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


def _user_workout_split_names(user):
    return list(user.workout_splits.order_by("position", "id").values_list("name", flat=True))


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
                    "preferred_unit": openapi.Schema(type=openapi.TYPE_STRING),
                    "workout_splits": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                    ),
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
        return Response(
            {
                "username": request.user.username,
                "email": request.user.email,
                "id": request.user.id,
                "preferred_unit": request.user.preferred_unit,
                "workout_splits": _user_workout_split_names(request.user),
            }
        )
    return Response(None)


@swagger_auto_schema(
    method="post",
    operation_description="Request a password reset email for the given address.",
    request_body=PasswordResetRequestSerializer,
    responses={200: "If the email exists, a reset link will be sent."},
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    form = MailerSendPasswordResetForm({"email": serializer.validated_data["email"]})
    if form.is_valid():
        form.save(
            request=request,
            use_https=not settings.DEBUG,
            email_template_name="emails/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        )

    return Response(
        {"message": "If an account exists for that email, a reset link has been sent."},
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="post",
    operation_description="Confirm password reset with uid, token, and new password.",
    request_body=PasswordResetConfirmSerializer,
    responses={200: "Password reset successful", 400: "Invalid or expired token"},
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
def api_password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    uid = serializer.validated_data["uid"]
    token = serializer.validated_data["token"]
    new_password = serializer.validated_data["new_password1"]

    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password, user)
    except ValidationError as exc:
        return Response({"error": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Password reset successful. You can log in now."}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="post",
    operation_description="Change password for the authenticated user.",
    request_body=ChangePasswordSerializer,
    responses={200: "Password changed", 400: "Validation error"},
    tags=["Authentication"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    current_password = serializer.validated_data["current_password"]
    if not user.check_password(current_password):
        return Response({"current_password": ["Incorrect password."]}, status=status.HTTP_400_BAD_REQUEST)

    new_password = serializer.validated_data["new_password1"]
    try:
        validate_password(new_password, user)
    except ValidationError as exc:
        return Response({"new_password1": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method="patch",
    operation_description="Update username for the authenticated user.",
    request_body=UpdateUsernameSerializer,
    responses={200: "Username updated", 400: "Validation error"},
    tags=["Authentication"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def api_update_username(request):
    serializer = UpdateUsernameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    new_username = serializer.validated_data["username"].strip()
    if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
        return Response({"username": ["This username is already taken."]}, status=status.HTTP_400_BAD_REQUEST)

    user.username = new_username
    user.save(update_fields=["username"])
    return Response(
        {"message": "Username updated successfully.", "username": user.username},
        status=status.HTTP_200_OK,
    )


@swagger_auto_schema(
    method="patch",
    operation_description="Update authenticated user preferences.",
    request_body=UpdatePreferencesSerializer,
    responses={200: "Preferences updated", 400: "Validation error"},
    tags=["Authentication"],
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def api_update_preferences(request):
    serializer = UpdatePreferencesSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    update_fields = []
    if "preferred_unit" in serializer.validated_data:
        user.preferred_unit = serializer.validated_data["preferred_unit"]
        update_fields.append("preferred_unit")
    if update_fields:
        user.save(update_fields=update_fields)

    if "workout_splits" in serializer.validated_data:
        names = serializer.validated_data["workout_splits"]
        user.workout_splits.all().delete()
        UserWorkoutSplit.objects.bulk_create(
            [UserWorkoutSplit(user=user, name=name, position=index) for index, name in enumerate(names)]
        )

    return Response(
        {
            "message": "Preferences updated.",
            "preferred_unit": user.preferred_unit,
            "workout_splits": _user_workout_split_names(user),
        },
        status=status.HTTP_200_OK,
    )
