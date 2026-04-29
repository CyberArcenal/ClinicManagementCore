import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SMSService:
    @staticmethod
    async def send_sms(to_number: str, message: str, from_number: Optional[str] = None) -> bool:
        try:
            logger.info(f"[SMS] To: {to_number}, Message: {message}")
            # Integrate with Twilio: 
            # from twilio.rest import Client
            # client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            # client.messages.create(body=message, from_=from_number, to=to_number)
            return True
        except Exception as e:
            logger.exception(f"SMS send failed: {e}")
            return False