"""
Email sending for invoices in M3 (INV-3).
"""

from __future__ import annotations

from app.core.clock import now
from app.core.mail import Attachment, send_email
from app.billing.models import Invoice
from app.billing.pdf import generate_invoice_pdf, render_invoice_html


def send_invoice_email(
    invoice: Invoice,
    recipient_email: str,
    customer_name: str = "Valued Customer",
) -> None:
    """
    Renders invoice PDF and sends via email with PDF attachment.
    """
    pdf_bytes = generate_invoice_pdf(
        invoice, customer_name=customer_name, customer_email=recipient_email
    )
    html_body = render_invoice_html(
        invoice, customer_name=customer_name, customer_email=recipient_email
    )

    attachment = Attachment(
        filename=f"{invoice.number}.pdf",
        content=pdf_bytes,
        mime_type="application/pdf",
    )

    send_email(
        to=recipient_email,
        subject=f"Your Brightloop Invoice: {invoice.number}",
        html=html_body,
        text=f"Please find attached your invoice {invoice.number} for INR {invoice.total:.2f}.",
        attachments=[attachment],
    )

    invoice.sent_at = now()
