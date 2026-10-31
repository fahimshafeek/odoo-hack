import logging
from typing import Sequence, NamedTuple, Optional

logger = logging.getLogger("brightloop.mail")


class Attachment(NamedTuple):
    filename: str
    content: bytes
    mime_type: str


def send_email(
    *,
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None,
    attachments: Sequence[Attachment] = (),
) -> None:
    """Mock/local-first mail sender; logs output safely without leaking credentials."""
    logger.info("Sent email to %s: subject=%s, attachments=%d", to, subject, len(attachments))
