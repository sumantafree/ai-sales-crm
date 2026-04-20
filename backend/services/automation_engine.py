"""
Automation Engine — rule-based trigger system.
Evaluates automations and executes configured actions.
"""
from database import SessionLocal
from models.lead import Lead, LeadTemperature
from models.automation import Automation, AutomationLog, AutomationTrigger, AutomationAction, AutomationStatus
from models.conversation import Conversation, Message, MessageRole, MessageChannel
import uuid
from datetime import datetime


async def trigger_automations(lead_id: str, trigger_type: str, extra: dict = None):
    """Evaluate all active automations for a given trigger type and lead."""
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return

        automations = db.query(Automation).filter(
            Automation.workspace_id == lead.workspace_id,
            Automation.status == AutomationStatus.ACTIVE,
        ).all()

        for automation in automations:
            if await _should_trigger(automation, lead, trigger_type, extra):
                await _execute_action(automation, lead, db)

    except Exception as e:
        print(f"[AutoEngine] Error: {e}")
    finally:
        db.close()


async def _should_trigger(automation: Automation, lead: Lead, trigger_type: str, extra: dict) -> bool:
    """Check if an automation should fire for this lead."""
    t = automation.trigger
    cfg = automation.trigger_config or {}

    if t == AutomationTrigger.LEAD_CREATED:
        return trigger_type == "lead_created"

    elif t == AutomationTrigger.SCORE_ABOVE:
        threshold = cfg.get("threshold", 70)
        return trigger_type in ("lead_scored", "lead_created") and lead.score >= threshold

    elif t == AutomationTrigger.SCORE_BELOW:
        threshold = cfg.get("threshold", 30)
        return trigger_type in ("lead_scored", "lead_created") and lead.score < threshold

    elif t == AutomationTrigger.KEYWORD_DETECTED:
        keywords = cfg.get("keywords", [])
        message = (lead.message or "").lower()
        return trigger_type == "lead_created" and any(kw.lower() in message for kw in keywords)

    elif t == AutomationTrigger.SOURCE_MATCH:
        source = cfg.get("source", "")
        return trigger_type == "lead_created" and (lead.source.value if lead.source else "") == source

    elif t == AutomationTrigger.INTENT_MATCH:
        intent = cfg.get("intent", "")
        return trigger_type == "lead_scored" and (lead.intent.value if lead.intent else "") == intent

    elif t == AutomationTrigger.TEMPERATURE_MATCH:
        temp = cfg.get("temperature", "hot")
        return trigger_type == "lead_scored" and (lead.temperature.value if lead.temperature else "") == temp

    elif t in (AutomationTrigger.NO_REPLY_24H, AutomationTrigger.NO_REPLY_48H):
        # Handled by the follow-up worker scheduler
        return False

    return False


async def _execute_action(automation: Automation, lead: Lead, db):
    """Execute the automation action and log the result."""
    action = automation.action
    cfg = automation.action_config or {}
    result = None
    error = None

    try:
        if action == AutomationAction.SEND_WHATSAPP:
            result = await _action_whatsapp(lead, cfg, db)

        elif action == AutomationAction.SEND_EMAIL:
            result = await _action_email(lead, cfg)

        elif action == AutomationAction.AI_REPLY:
            result = await _action_ai_reply(lead, cfg, db)

        elif action == AutomationAction.UPDATE_STATUS:
            new_status = cfg.get("status", "contacted")
            lead.status = new_status
            db.commit()
            result = f"Status updated to {new_status}"

        elif action == AutomationAction.NOTIFY_TEAM:
            result = f"Team notification sent for lead {lead.name}"

        # Update run count
        try:
            count = int(automation.run_count or 0) + 1
            automation.run_count = str(count)
        except (ValueError, TypeError):
            automation.run_count = "1"

    except Exception as e:
        error = str(e)
        print(f"[AutoEngine] Action failed: {e}")

    # Log the execution
    log = AutomationLog(
        automation_id=automation.id,
        lead_id=lead.id,
        status="success" if not error else "failed",
        result=result,
        error=error,
    )
    db.add(log)
    db.commit()


async def _action_whatsapp(lead: Lead, cfg: dict, db) -> str:
    from services.whatsapp_service import send_whatsapp_message, send_whatsapp_template

    if not lead.phone:
        return "Skipped: no phone number"

    use_ai_reply = cfg.get("use_ai_reply", False)
    template = cfg.get("template")

    if use_ai_reply and lead.ai_generated_reply:
        message = lead.ai_generated_reply
    elif template:
        message = None  # use template
    else:
        message = cfg.get("message", f"Hi {lead.name}! Thanks for your interest. How can I help?")

    if template and not message:
        sid = await send_whatsapp_template(lead.phone, template, {"name": lead.name})
    else:
        sid = await send_whatsapp_message(lead.phone, message)

    # Save to conversation
    conv = db.query(Conversation).filter(
        Conversation.lead_id == lead.id,
        Conversation.channel == MessageChannel.WHATSAPP
    ).first()

    if not conv:
        conv = Conversation(
            lead_id=lead.id,
            workspace_id=lead.workspace_id,
            channel=MessageChannel.WHATSAPP,
        )
        db.add(conv)
        db.flush()

    msg = Message(
        conversation_id=conv.id,
        role=MessageRole.ASSISTANT,
        content=message or template,
        channel=MessageChannel.WHATSAPP,
        is_ai_generated=use_ai_reply,
        external_message_id=sid,
    )
    db.add(msg)

    lead.last_contacted_at = datetime.utcnow()
    lead.follow_up_count = (lead.follow_up_count or 0) + 1
    db.commit()

    return f"WhatsApp sent. SID: {sid}"


async def _action_email(lead: Lead, cfg: dict) -> str:
    from services.email_service import send_template_email, send_email

    if not lead.email:
        return "Skipped: no email address"

    template = cfg.get("template", "followup_24h")
    subject = cfg.get("subject")

    if subject:
        from services.email_service import EMAIL_TEMPLATES
        from jinja2 import Template
        tmpl = EMAIL_TEMPLATES.get(template, EMAIL_TEMPLATES["welcome"])
        html = Template(tmpl["html"]).render(name=lead.name, sender_name="Sales Team", company_name="AI Sales CRM")
        await send_email(lead.email, lead.name, subject, html)
    else:
        await send_template_email(lead.email, lead.name, template)

    lead.last_contacted_at = datetime.utcnow()
    lead.follow_up_count = (lead.follow_up_count or 0) + 1
    return f"Email sent to {lead.email}"


async def _action_ai_reply(lead: Lead, cfg: dict, db) -> str:
    from services.ai_service import analyze_lead
    await analyze_lead(str(lead.id))
    return "AI analysis + reply generated"
