"""MailerSend email integration."""

import os

from mailersend import MailerSendClient
from mailersend.models.email import EmailContact, EmailRequest


class MailerSendEmailClient:
    """Client for sending emails via MailerSend API."""

    def __init__(
        self,
        api_token: str | None = None,
        from_email: str | None = None,
        from_name: str = "Gym Assistant",
    ):
        """
        Initialize MailerSend client.

        Args:
            api_token: MailerSend API token. Defaults to MAILERSEND_API_TOKEN env var.
            from_email: Sender email address. Defaults to MAILERSEND_FROM_EMAIL env var.
            from_name: Sender display name.
        """
        self.api_token = api_token or os.getenv("MAILERSEND_API_TOKEN")
        self.from_email = from_email or os.getenv("MAILERSEND_FROM_EMAIL")
        self.from_name = from_name

        if not self.api_token:
            raise ValueError("MAILERSEND_API_TOKEN environment variable is required")
        if not self.from_email:
            raise ValueError("MAILERSEND_FROM_EMAIL environment variable is required")

        self.client = MailerSendClient(self.api_token)

    def send(
        self,
        subject: str,
        to: list[dict[str, str]],
        html: str,
        text: str,
    ) -> dict:
        """
        Send an email using MailerSend.

        Args:
            subject: Email subject line.
            to: List of recipients [{"email": "...", "name": "..."}].
            html: HTML content of the email.
            text: Plain text content of the email.

        Returns:
            Response from MailerSend API.
        """
        # Build EmailContact objects for recipients
        recipients = [EmailContact(email=r["email"], name=r.get("name")) for r in to]

        # Build the email request
        email_request = EmailRequest(
            from_email=EmailContact(email=self.from_email, name=self.from_name),
            to=recipients,
            subject=subject,
            html=html,
            text=text,
        )

        # Send the email
        response = self.client.emails.send(email_request)
        return {"status": "sent", "response": str(response)}


# Module-level convenience function using default client
_default_client: MailerSendEmailClient | None = None


def _get_default_client() -> MailerSendEmailClient:
    """Get or create the default MailerSend client."""
    global _default_client
    if _default_client is None:
        _default_client = MailerSendEmailClient()
    return _default_client


def send_email(
    subject: str,
    to: list[dict[str, str]],
    html: str,
    text: str,
) -> dict:
    """
    Send an email using the default MailerSend client.

    Args:
        subject: Email subject line.
        to: List of recipients [{"email": "...", "name": "..."}].
        html: HTML content of the email.
        text: Plain text content of the email.

    Returns:
        Response from MailerSend API.
    """
    return _get_default_client().send(subject=subject, to=to, html=html, text=text)
