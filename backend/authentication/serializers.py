from dj_rest_auth.serializers import PasswordResetSerializer


class CustomPasswordResetSerializer(PasswordResetSerializer):
    password_reset_form_class = None
    email_template_name = "emails/password_reset_email.html"
