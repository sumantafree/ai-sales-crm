"""
Background worker for scheduled follow-up automations.
Runs via APScheduler every hour.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import SessionLocal
from models.lead import Lead, LeadStatus
from models.automation import Automation, AutomationTrigger, AutomationStatus
from models.conversation import Message, Conversation

scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.add_job(run_followup_checks, "interval", hours=1, id="followup_check")
    scheduler.start()
    print("[Worker] Follow-up scheduler started")


def stop_scheduler():
    scheduler.shutdown()


async def run_followup_checks():
    """Check all leads for follow-up trigger conditions."""
    print(f"[Worker] Running follow-up checks at {datetime.utcnow()}")
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_48h = now - timedelta(hours=48)

        # Leads with no reply in 24h (never contacted or no recent contact)
        leads_24h = db.query(Lead).filter(
            Lead.status != LeadStatus.CONVERTED,
            Lead.status != LeadStatus.LOST,
            Lead.created_at <= cutoff_24h,
            Lead.follow_up_count == 0,
        ).all()

        for lead in leads_24h:
            automations = db.query(Automation).filter(
                Automation.workspace_id == lead.workspace_id,
                Automation.status == AutomationStatus.ACTIVE,
                Automation.trigger == AutomationTrigger.NO_REPLY_24H,
            ).all()
            for auto in automations:
                from services.automation_engine import _execute_action
                await _execute_action(auto, lead, db)

        # Leads with no reply in 48h
        leads_48h = db.query(Lead).filter(
            Lead.status != LeadStatus.CONVERTED,
            Lead.status != LeadStatus.LOST,
            Lead.created_at <= cutoff_48h,
            Lead.follow_up_count <= 1,
        ).all()

        for lead in leads_48h:
            automations = db.query(Automation).filter(
                Automation.workspace_id == lead.workspace_id,
                Automation.status == AutomationStatus.ACTIVE,
                Automation.trigger == AutomationTrigger.NO_REPLY_48H,
            ).all()
            for auto in automations:
                from services.automation_engine import _execute_action
                await _execute_action(auto, lead, db)

        print(f"[Worker] Processed {len(leads_24h)} 24h leads, {len(leads_48h)} 48h leads")

    except Exception as e:
        print(f"[Worker] Error in follow-up checks: {e}")
    finally:
        db.close()
