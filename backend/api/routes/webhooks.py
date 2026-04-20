"""
Webhook handlers for:
- Twilio WhatsApp (incoming messages)
- Meta Facebook Lead Ads
- Stripe billing events
"""
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from database import get_db
from core.config import settings
import hashlib, hmac, json, uuid
from datetime import datetime

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


# ════════════════════════════════════════════════════════════
# TWILIO WHATSAPP WEBHOOK
# ════════════════════════════════════════════════════════════

@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Receive incoming WhatsApp messages from Twilio."""
    form_data = await request.form()
    form_dict = dict(form_data)

    from services.whatsapp_service import parse_incoming_webhook, validate_twilio_signature

    # Optional signature validation
    if settings.TWILIO_AUTH_TOKEN:
        signature = request.headers.get("X-Twilio-Signature", "")
        url = str(request.url)
        # validate_twilio_signature(url, form_dict, signature)  # Enable in prod

    parsed = parse_incoming_webhook(form_dict)
    phone = parsed["from_phone"]
    body = parsed["body"]
    profile_name = parsed.get("profile_name", "Unknown")

    background_tasks.add_task(
        _process_incoming_whatsapp,
        phone=phone,
        body=body,
        profile_name=profile_name,
        message_sid=parsed["message_sid"],
    )

    # Twilio expects a TwiML response (even if empty)
    return PlainTextResponse(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


async def _process_incoming_whatsapp(phone: str, body: str, profile_name: str, message_sid: str):
    """Process incoming WhatsApp — find or create lead, store message, trigger AI."""
    from database import SessionLocal
    from models.lead import Lead, LeadSource
    from models.conversation import Conversation, Message, MessageRole, MessageChannel
    from services.ai_service import analyze_lead
    from services.automation_engine import trigger_automations

    db = SessionLocal()
    try:
        # Find workspace by phone (first workspace that has this number configured)
        # In production: match by Twilio number → workspace mapping
        # For now: use the first active workspace
        from models.workspace import Workspace
        workspace = db.query(Workspace).filter(Workspace.is_active == True).first()
        if not workspace:
            return

        # Find existing lead by phone
        lead = db.query(Lead).filter(
            Lead.workspace_id == workspace.id,
            Lead.phone == phone,
        ).first()

        if not lead:
            # Create new lead from WhatsApp message
            lead = Lead(
                workspace_id=workspace.id,
                name=profile_name or phone,
                phone=phone,
                message=body,
                source=LeadSource.WHATSAPP,
            )
            db.add(lead)
            db.flush()

        # Find or create conversation
        conv = db.query(Conversation).filter(
            Conversation.lead_id == lead.id,
            Conversation.channel == MessageChannel.WHATSAPP,
            Conversation.is_active == True,
        ).first()

        if not conv:
            conv = Conversation(
                lead_id=lead.id,
                workspace_id=workspace.id,
                channel=MessageChannel.WHATSAPP,
            )
            db.add(conv)
            db.flush()

        # Store incoming message
        msg = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content=body,
            channel=MessageChannel.WHATSAPP,
            external_message_id=message_sid,
        )
        db.add(msg)
        db.commit()

        # Trigger AI analysis + automations
        await analyze_lead(str(lead.id))
        await trigger_automations(str(lead.id), "lead_created", {"message": body})

    except Exception as e:
        print(f"[WhatsApp Webhook] Error: {e}")
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
# FACEBOOK LEAD ADS WEBHOOK
# ════════════════════════════════════════════════════════════

@router.get("/facebook")
def facebook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Facebook webhook verification challenge."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/facebook")
async def facebook_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Receive Facebook Lead Ads events."""
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.META_APP_SECRET and not _verify_facebook_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid Facebook signature")

    payload = json.loads(body)
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "leadgen":
                value = change.get("value", {})
                lead_id = value.get("leadgen_id")
                form_id = value.get("form_id")
                page_id = value.get("page_id")
                if lead_id:
                    background_tasks.add_task(_fetch_facebook_lead, lead_id, form_id, page_id)

    return {"status": "ok"}


async def _fetch_facebook_lead(lead_gen_id: str, form_id: str, page_id: str):
    """Fetch lead data from Meta Graph API and save."""
    import httpx
    from database import SessionLocal
    from models.lead import Lead, LeadSource
    from services.ai_service import analyze_lead
    from services.automation_engine import trigger_automations

    if not settings.META_ACCESS_TOKEN:
        print("[FB] No access token configured")
        return

    db = SessionLocal()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://graph.facebook.com/v19.0/{lead_gen_id}",
                params={"access_token": settings.META_ACCESS_TOKEN},
            )
            resp.raise_for_status()
            data = resp.json()

        field_data = {f["name"]: f["values"][0] for f in data.get("field_data", [])}

        name = field_data.get("full_name") or field_data.get("name", "Unknown")
        email = field_data.get("email")
        phone = field_data.get("phone_number") or field_data.get("phone")

        from models.workspace import Workspace
        workspace = db.query(Workspace).filter(Workspace.is_active == True).first()
        if not workspace:
            return

        # Find campaign by form_id
        campaign_id = None
        if form_id:
            from models.campaign import Campaign
            campaign = db.query(Campaign).filter(
                Campaign.workspace_id == workspace.id,
                Campaign.facebook_form_id == form_id
            ).first()
            if campaign:
                campaign_id = campaign.id
                campaign.total_leads += 1
                db.flush()

        lead = Lead(
            workspace_id=workspace.id,
            name=name,
            email=email,
            phone=phone,
            source=LeadSource.FACEBOOK,
            external_id=lead_gen_id,
            campaign_id=campaign_id,
            extra_data={"form_id": form_id, "page_id": page_id, "raw": field_data},
        )
        db.add(lead)
        db.commit()

        await analyze_lead(str(lead.id))
        await trigger_automations(str(lead.id), "lead_created")

    except Exception as e:
        print(f"[FB Lead] Error: {e}")
    finally:
        db.close()


# ════════════════════════════════════════════════════════════
# WEBSITE FORM WEBHOOK (public endpoint)
# ════════════════════════════════════════════════════════════

@router.post("/form/{workspace_slug}")
async def website_form_webhook(
    workspace_slug: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Capture leads from website contact forms."""
    from models.workspace import Workspace
    from models.lead import Lead, LeadSource

    workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    data = await request.json()
    lead = Lead(
        workspace_id=workspace.id,
        name=data.get("name", "Unknown"),
        email=data.get("email"),
        phone=data.get("phone"),
        message=data.get("message") or data.get("inquiry"),
        source=LeadSource.WEBSITE,
        extra_data=data,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    from services.ai_service import analyze_lead
    from services.automation_engine import trigger_automations
    background_tasks.add_task(analyze_lead, str(lead.id))
    background_tasks.add_task(trigger_automations, str(lead.id), "lead_created")

    return {"success": True, "lead_id": str(lead.id), "message": "Thank you! We'll be in touch soon."}


# ════════════════════════════════════════════════════════════
# STRIPE BILLING WEBHOOK
# ════════════════════════════════════════════════════════════

@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe billing events."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    from services.stripe_service import handle_webhook_event, update_subscription_from_event
    try:
        event = handle_webhook_event(payload, sig)
        update_subscription_from_event(db, event["event_type"], event["data"])
        return {"status": "processed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Helpers ────────────────────────────────────────────────────────────────────

def _verify_facebook_signature(body: bytes, signature: str) -> bool:
    expected = "sha256=" + hmac.new(
        settings.META_APP_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
