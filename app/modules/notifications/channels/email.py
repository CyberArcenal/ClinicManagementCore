import logging
from typing import List, Optional
from app.core.config import settings

# Optional: use aiosmtplib for async email
# from aiosmtplib import SMTP
import asyncio

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> bool:
        """
        Send an email asynchronously.
        Currently logs the email; replace with actual SMTP or transactional email API.
        """
        try:
            # Simulate async send
            logger.info(f"[EMAIL] To: {to_email}, Subject: {subject}, Body: {body}")
            # Example with aiosmtplib:
            # smtp = SMTP(hostname=settings.SMTP_HOST, port=settings.SMTP_PORT, use_tls=True)
            # await smtp.connect()
            # await smtp.sendmail(from_email or settings.DEFAULT_FROM_EMAIL, [to_email], msg)
            # await smtp.quit()
            return True
        except Exception as e:
            logger.exception(f"Email send failed: {e}")
            return False