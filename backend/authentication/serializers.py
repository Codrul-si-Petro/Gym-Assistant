from rest_framework import serializers

from .models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class SignupSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        # Check if email already exists
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password1"],
        )
        return user


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password1 = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password2 = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True)
    new_password1 = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password2 = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password1"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        return attrs


class UpdateUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=3, max_length=150)


class UpdatePreferencesSerializer(serializers.Serializer):
    preferred_unit = serializers.ChoiceField(choices=["KG", "LBS"], required=False)
    workout_splits = serializers.ListField(
        child=serializers.CharField(max_length=50, allow_blank=False),
        required=False,
        max_length=20,
    )

    def validate(self, attrs):
        if "preferred_unit" not in attrs and "workout_splits" not in attrs:
            raise serializers.ValidationError("Provide preferred_unit and/or workout_splits.")
        return attrs

    def validate_workout_splits(self, value):
        cleaned = []
        seen = set()
        for raw in value:
            name = (raw or "").strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(name[:50])
        return cleaned
