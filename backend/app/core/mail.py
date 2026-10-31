import logging
from typing import Any, NamedTuple, Optional, Sequence
import httpx
from app.core.config import settings
from app.core.errors import AppError

logger = logging.getLogger("brightloop.mail")
RESEND_ENDPOINT = "https://api.resend.com/emails"


class Attachment(NamedTuple):
    filename: str
    content: bytes
    mime_type: str


_sent_emails: list[dict[str, Any]] = []


def send_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
    attachments: Optional[Sequence[Attachment]] = None,
) -> dict:
    """Sends an email via Resend API or records in simulation log."""
    email_record = {
        "to": to,
        "subject": subject,
        "html": html,
        "text": text,
        "attachments": list(attachments) if attachments else [],
    }
    _sent_emails.append(email_record)

    if (
        not settings.RESEND_API_KEY
        or settings.ENV == "test"
        or to.endswith(("@example.com", "@test.com", "@brightloop.test"))
    ):
        logger.info(f"[EMAIL SIMULATION] To: {to} | Subject: {subject}")
        return {"id": "simulated_id", "status": "simulated"}

    payload: dict[str, Any] = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(RESEND_ENDPOINT, headers=headers, json=payload)
            if response.status_code >= 400:
                logger.error(f"Resend API error {response.status_code}: {response.text}")
                raise AppError(
                    code="mail_delivery_failed",
                    message="Failed to send email via Resend",
                    status_code=502,
                )
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"Network error communicating with Resend: {exc}")
        raise AppError(
            code="mail_network_error",
            message="Network error during email dispatch",
            status_code=502,
        )


def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int = 5) -> dict:
    """Sends branded HTML password reset link."""
    subject = "Reset your Brightloop password"
    html = f"""
    <!DOCTYPE html>
    <html>
      <body style="font-family: sans-serif; color: #111;">
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password. This link expires in {expires_minutes} minutes:</p>
        <p><a href="{reset_url}" style="color: #2563eb; font-weight: bold;">Reset Password</a></p>
        <p>If you didn't request this, you can safely ignore this email.</p>
      </body>
    </html>
    """
    return send_email(to=to_email, subject=subject, html=html, text=f"Reset link: {reset_url}")


def send_welcome_email(to_email: str, full_name: str) -> dict:
    """Sends welcome onboarding email to new customers."""
    subject = "Welcome to Brightloop!"
    html = f"""
    <!DOCTYPE html>
    <html>
      <body style="font-family: sans-serif; color: #111;">
        <h2>Welcome to Brightloop, {full_name}!</h2>
        <p>Your account is ready. Log in to explore your subscriptions and invoices.</p>
      </body>
    </html>
    """
    return send_email(to=to_email, subject=subject, html=html, text=f"Welcome {full_name} to Brightloop!")


def send_staff_invite_email(to_email: str, invite_url: str, full_name: str) -> dict:
    """Sends an invitation email to a newly added staff member."""
    subject = "You're invited to join Brightloop Software"
    html = f"""
    <!DOCTYPE html>
    <html>
      <body style="font-family: sans-serif; color: #111;">
        <h2>Welcome to Brightloop, {full_name}!</h2>
        <p>An administrator has invited you to join the team as an internal staff member.</p>
        <p><a href="{invite_url}" style="color: #10b981; font-weight: bold;">Set Up Your Password & Sign In</a></p>
      </body>
    </html>
    """
    return send_email(to=to_email, subject=subject, html=html, text=f"Invite link: {invite_url}")

