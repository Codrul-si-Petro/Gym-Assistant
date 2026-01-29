"""Custom adapters for django-allauth email integration with MailerSend."""

from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string

from backend.emails.mailersend import send_email


class MailerSendAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter that sends emails via MailerSend instead of Django's email backend.
    Uses templates from templates/emails/ directory.
    """

    def send_confirmation_mail(self, request, emailconfirmation, signup: bool) -> None:
        """
        Send email confirmation using MailerSend.

        Args:
            request: The HTTP request
            emailconfirmation: The email confirmation object
            signup: Whether this is during signup
        """
        user = emailconfirmation.email_address.user
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)

        # Render HTML template
        html_body = render_to_string(
            "emails/email_confirmation.html",
            {
                "user": user,
                "activate_url": activate_url,
            },
        )

        # Plain text fallback
        text_body = f"""
Hello {user.get_username()},

Please confirm your email address by clicking the link below:
{activate_url}

If you didn't create an account, you can ignore this email.
        """

        send_email(
            subject="Confirm your email address",
            to=[{"email": emailconfirmation.email_address.email, "name": user.get_username()}],
            html=html_body,
            text=text_body,
        )
