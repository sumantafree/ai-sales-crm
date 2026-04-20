"""
WhatsApp Service using Twilio
Handles sending messages and processing incoming webhooks.
"""
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from core.config import settings
import re


def get_twilio_client() -> Client:
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def _format_phone(phone: str) -> str:
    """Ensure phone is in whatsapp: format."""
    phone = re.sub(r"[^\d+]", "", phone)
    if not phone.startswith("+"):
        phone = "+" + phone
    return f"whatsapp:{phone}"


async def send_whatsapp_message(to_phone: str, message: str) -> str:
    """Send a WhatsApp message via Twilio. Returns message SID."""
    client = get_twilio_client()
    msg = client.messages.create(
        body=message,
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=_format_phone(to_phone),
    )
    return msg.sid


async def send_whatsapp_template(to_phone: str, template_name: str, variables: dict = None) -> str:
    """Send a pre-approved WhatsApp template message."""
    templates = {
        "welcome": "Hi {name}! 👋 Thanks for reaching out. How can I help you today?",
        "followup_24h": "Hi {name}! Just following up on your inquiry. We'd love to help you. Reply anytime!",
        "final_followup": "Hi {name}! Last follow-up from our side. Feel free to reach out whenever you're ready. 😊",
        "pricing_info": "Hi {name}! Here's our pricing:\n\n💎 Starter: ₹999/mo\n🚀 Pro: ₹2,499/mo\n🏢 Enterprise: Custom\n\nWant to know more?",
        "hot_lead_response": "Hi {name}! 🔥 Great to hear from you! I can see you're serious about this. Let's talk — when's a good time for a quick call?",
    }

    template = templates.get(template_name, templates["welcome"])
    message = template.format(**(variables or {}))

    return await send_whatsapp_message(to_phone, message)


def validate_twilio_signature(url: str, params: dict, signature: str) -> bool:
    """Validate that incoming webhook is genuinely from Twilio."""
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return validator.validate(url, params, signature)


def parse_incoming_webhook(form_data: dict) -> dict:
    """Parse Twilio incoming WhatsApp webhook payload."""
    return {
        "message_sid": form_data.get("MessageSid"),
        "from_phone": form_data.get("From", "").replace("whatsapp:", ""),
        "to_phone": form_data.get("To", "").replace("whatsapp:", ""),
        "body": form_data.get("Body", ""),
        "num_media": int(form_data.get("NumMedia", 0)),
        "profile_name": form_data.get("ProfileName"),
        "wa_id": form_data.get("WaId"),
    }
