"""MailerSend email integration."""

import logging
import os
from concurrent.futures import ThreadPoolExecutor

from mailersend import MailerSendClient
from mailersend.models.email import EmailContact, EmailRequest

logger = logging.getLogger(__name__)

# Bounded pool so password-reset (and any other) sends do not block a gunicorn
# request thread on the MailerSend HTTP round trip. Failures are logged / sent
# to Sentry; callers already return a generic success body.
_email_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="mailersend")


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


def _send_email_sync(
    subject: str,
    to: list[dict[str, str]],
    html: str,
    text: str,
) -> dict:
    return _get_default_client().send(subject=subject, to=to, html=html, text=text)


def _report_send_failure(exc: BaseException) -> None:
    logger.exception("Background MailerSend send failed")
    try:
        import sentry_sdk

        sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def send_email(
    subject: str,
    to: list[dict[str, str]],
    html: str,
    text: str,
) -> None:
    """
    Queue an email send on a background thread (does not wait for MailerSend).

    Password-reset responses are intentionally generic whether or not the send
    succeeds, so blocking the request thread on the HTTP round trip is wasteful.
    Errors are logged and reported to Sentry when configured.
    """

    def _run() -> None:
        try:
            _send_email_sync(subject=subject, to=to, html=html, text=text)
        except Exception as exc:
            _report_send_failure(exc)

    _email_executor.submit(_run)
