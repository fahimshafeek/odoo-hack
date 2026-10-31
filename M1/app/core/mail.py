import logging
import httpx
from app.core.config import settings
from app.core.errors import AppError

logger = logging.getLogger("brightloop.mail")
RESEND_ENDPOINT = "https://api.resend.com/emails"

def send_email(
    to: str,
    subject: str,
    html: str,
    text: str | None = None
) -> dict:
    """
    Sends an email via the Resend API using the configured API key and From address.
    """
    if not settings.RESEND_API_KEY or settings.ENV == "test" or to.endswith(("@example.com", "@test.com", "@brightloop.test")):
        logger.info(f"[EMAIL SIMULATION] To: {to} | Subject: {subject}")
        return {"id": "simulated_id", "status": "simulated"}

    payload = {
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
                    status_code=502
                )
            return response.json()
    except httpx.RequestError as exc:
        logger.error(f"Network error communicating with Resend: {exc}")
        raise AppError(
            code="mail_network_error",
            message="Network error during email dispatch",
            status_code=502
        )

def send_password_reset_email(to_email: str, reset_url: str, expires_minutes: int = 5) -> dict:
    """Sends a branded HTML password reset link (valid for 5 minutes)."""
    subject = "Reset your Brightloop password"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; padding: 40px 20px;">
      <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="color: #111827; margin-top: 0;">Password Reset Request</h2>
        <p style="color: #4b5563; font-size: 15px; line-height: 1.5;">
          You requested to reset your password for your <strong>Brightloop</strong> account.
        </p>
        <p style="color: #ef4444; font-size: 14px; font-weight: 600;">
          ⚠️ This link will expire in {expires_minutes} minutes.
        </p>
        <div style="margin: 28px 0; text-align: center;">
          <a href="{reset_url}" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-size: 15px; font-weight: 500; display: inline-block;">
            Reset Password
          </a>
        </div>
        <p style="color: #6b7280; font-size: 13px; line-height: 1.4;">
          If the button above does not work, copy and paste this link into your browser:<br>
          <a href="{reset_url}" style="color: #2563eb; word-break: break-all;">{reset_url}</a>
        </p>
        <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 24px 0;">
        <p style="color: #9ca3af; font-size: 12px; margin-bottom: 0;">
          If you did not request this, you can safely ignore this email.
        </p>
      </div>
    </body>
    </html>
    """
    return send_email(to=to_email, subject=subject, html=html)

def send_staff_invite_email(to_email: str, invite_url: str, full_name: str) -> dict:
    """Sends an invitation email to a newly added staff member."""
    subject = "You're invited to join Brightloop Software"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; padding: 40px 20px;">
      <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <h2 style="color: #111827; margin-top: 0;">Welcome to Brightloop, {full_name}!</h2>
        <p style="color: #4b5563; font-size: 15px; line-height: 1.5;">
          An administrator has invited you to join the team as an internal staff member.
        </p>
        <div style="margin: 28px 0; text-align: center;">
          <a href="{invite_url}" style="background-color: #10b981; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-size: 15px; font-weight: 500; display: inline-block;">
            Set Up Your Password & Sign In
          </a>
        </div>
        <p style="color: #6b7280; font-size: 13px;">
          This invitation link is valid for 24 hours.
        </p>
      </div>
    </body>
    </html>
    """
    return send_email(to=to_email, subject=subject, html=html)
