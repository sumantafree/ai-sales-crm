"""
Email Service — SMTP / Gmail API
Handles automated follow-up emails and transactional emails.
"""
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from core.config import settings
from typing import Optional


# ── Email templates ───────────────────────────────────────────────────────────

EMAIL_TEMPLATES = {
    "followup_24h": {
        "subject": "Following up on your inquiry — {company_name}",
        "html": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
    <h1 style="color: white; margin: 0;">Following Up 👋</h1>
  </div>
  <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
    <p>Hi <strong>{{ name }}</strong>,</p>
    <p>I noticed you reached out to us recently but we haven't connected yet. I wanted to make sure you got the information you needed.</p>
    <p>We'd love to help you with your inquiry. Our team is ready to answer any questions.</p>
    <div style="text-align: center; margin: 30px 0;">
      <a href="{{ cta_url }}" style="background: #667eea; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">
        Let's Talk →
      </a>
    </div>
    <p style="color: #6b7280; font-size: 14px;">If you have any questions, simply reply to this email.</p>
    <p>Best regards,<br><strong>{{ sender_name }}</strong></p>
  </div>
</body>
</html>
""",
    },
    "welcome": {
        "subject": "Welcome to {company_name} — We're here to help!",
        "html": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 30px; border-radius: 10px 10px 0 0;">
    <h1 style="color: white; margin: 0;">Welcome! 🎉</h1>
  </div>
  <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
    <p>Hi <strong>{{ name }}</strong>,</p>
    <p>Thank you for reaching out! We're excited to connect with you.</p>
    <p>Here's what happens next:</p>
    <ul>
      <li>Our team will review your inquiry within 1 hour</li>
      <li>You'll receive a personalized response</li>
      <li>We'll schedule a free consultation if needed</li>
    </ul>
    <p>Best regards,<br><strong>{{ sender_name }}</strong></p>
  </div>
</body>
</html>
""",
    },
    "pricing_info": {
        "subject": "Pricing Information You Requested — {company_name}",
        "html": """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 10px 10px 0 0;">
    <h1 style="color: white; margin: 0;">Our Pricing 💎</h1>
  </div>
  <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
    <p>Hi <strong>{{ name }}</strong>,</p>
    <p>Here are our current pricing plans tailored for your needs:</p>
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <tr style="background: #667eea; color: white;">
        <th style="padding: 10px; text-align: left;">Plan</th>
        <th style="padding: 10px; text-align: center;">Price</th>
        <th style="padding: 10px; text-align: center;">Features</th>
      </tr>
      <tr style="background: white;">
        <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">Starter</td>
        <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">₹999/mo</td>
        <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">Up to 500 leads</td>
      </tr>
      <tr style="background: #f3f4f6;">
        <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">Pro</td>
        <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">₹2,499/mo</td>
        <td style="padding: 10px; text-align: center; border-bottom: 1px solid #e5e7eb;">Up to 5,000 leads</td>
      </tr>
      <tr style="background: white;">
        <td style="padding: 10px;">Agency</td>
        <td style="padding: 10px; text-align: center;">₹4,999/mo</td>
        <td style="padding: 10px; text-align: center;">Unlimited</td>
      </tr>
    </table>
    <p>Reply to this email or call us to discuss the best option for you.</p>
    <p>Best regards,<br><strong>{{ sender_name }}</strong></p>
  </div>
</body>
</html>
""",
    },
}


# ── Send functions ────────────────────────────────────────────────────────────

async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    plain_content: Optional[str] = None,
) -> bool:
    """Send an email via SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = f"{to_name} <{to_email}>"

        if plain_content:
            msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
        )
        return True
    except Exception as e:
        print(f"[Email] Send error: {e}")
        return False


async def send_template_email(
    to_email: str,
    to_name: str,
    template_name: str,
    variables: dict = None,
) -> bool:
    """Send an email using a named template."""
    template_data = EMAIL_TEMPLATES.get(template_name)
    if not template_data:
        template_data = EMAIL_TEMPLATES["welcome"]

    vars = {
        "name": to_name,
        "sender_name": settings.EMAIL_FROM_NAME,
        "company_name": settings.APP_NAME,
        "cta_url": "#",
        **(variables or {}),
    }

    subject = template_data["subject"].format(**vars)
    html = Template(template_data["html"]).render(**vars)

    return await send_email(to_email, to_name, subject, html)
