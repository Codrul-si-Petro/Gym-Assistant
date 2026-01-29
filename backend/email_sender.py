"""
Custom emails sent for Authentication and other purposes
"""

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from backend.emails.mailersend import send_email


class MailerSendPasswordResetForm(PasswordResetForm):
    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Override Django's email sending with MailerSend
        """

        user = context["user"]
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_url = (
            f"{settings.FRONTEND_URL}"
            f"{context['protocol']}://{context['domain']}"
            f"{context['url']}?uid={uid}&token={token}"
        )

        html = render_to_string(
            email_template_name,
            {
                "user": user,
                "reset_url": reset_url,
            },
        )

        text = f"""
        Hello {user.get_username()},

        Reset your password:
        {reset_url}

        If you didn’t request this, ignore this email.
        """

        send_email(
            subject="Reset your password",
            to=[{"email": to_email, "name": user.get_username()}],
            html=html,
            text=text,
        )
