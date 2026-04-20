from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from database import get_db
from models.automation import Automation, AutomationLog, AutomationTrigger, AutomationAction, AutomationStatus
from api.deps import get_current_user, get_current_workspace_id
from models.user import User

router = APIRouter(prefix="/api/automations", tags=["Automations"])


class AutomationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: AutomationTrigger
    trigger_config: Optional[dict] = None
    action: AutomationAction
    action_config: Optional[dict] = None
    delay_minutes: str = "0"


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[AutomationStatus] = None
    trigger_config: Optional[dict] = None
    action_config: Optional[dict] = None
    delay_minutes: Optional[str] = None


@router.get("")
def list_automations(
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    automations = db.query(Automation).filter(Automation.workspace_id == workspace_id).order_by(
        Automation.created_at.desc()
    ).all()
    return [_auto_dict(a) for a in automations]


@router.post("", status_code=201)
def create_automation(
    data: AutomationCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    automation = Automation(workspace_id=workspace_id, **data.dict())
    db.add(automation)
    db.commit()
    db.refresh(automation)
    return _auto_dict(automation)


@router.get("/{automation_id}")
def get_automation(
    automation_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    auto = _get_or_404(automation_id, workspace_id, db)
    return _auto_dict(auto)


@router.patch("/{automation_id}")
def update_automation(
    automation_id: uuid.UUID,
    data: AutomationUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    auto = _get_or_404(automation_id, workspace_id, db)
    for field, value in data.dict(exclude_none=True).items():
        setattr(auto, field, value)
    auto.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(auto)
    return _auto_dict(auto)


@router.delete("/{automation_id}", status_code=204)
def delete_automation(
    automation_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    auto = _get_or_404(automation_id, workspace_id, db)
    db.delete(auto)
    db.commit()


@router.get("/{automation_id}/logs")
def get_automation_logs(
    automation_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    auto = _get_or_404(automation_id, workspace_id, db)
    logs = db.query(AutomationLog).filter(AutomationLog.automation_id == automation_id).order_by(
        AutomationLog.executed_at.desc()
    ).limit(50).all()
    return [
        {
            "id": str(log.id),
            "lead_id": str(log.lead_id),
            "status": log.status,
            "result": log.result,
            "error": log.error,
            "executed_at": log.executed_at.isoformat(),
        }
        for log in logs
    ]


# ── Default automation templates ──────────────────────────────────────────────
@router.post("/seed-defaults", status_code=201)
def seed_default_automations(
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create the default automation flows for a workspace."""
    defaults = [
        {
            "name": "Instant Hot Lead Reply",
            "description": "Send WhatsApp instantly when score > 70",
            "trigger": AutomationTrigger.SCORE_ABOVE,
            "trigger_config": {"threshold": 70},
            "action": AutomationAction.SEND_WHATSAPP,
            "action_config": {"use_ai_reply": True},
            "delay_minutes": "0",
        },
        {
            "name": "24h Follow-up Email",
            "description": "Send follow-up email if no reply in 24 hours",
            "trigger": AutomationTrigger.NO_REPLY_24H,
            "trigger_config": {"hours": 24},
            "action": AutomationAction.SEND_EMAIL,
            "action_config": {
                "subject": "Following up on your inquiry",
                "template": "followup_24h",
            },
            "delay_minutes": "1440",
        },
        {
            "name": "Price Inquiry Pricing Template",
            "description": "Send pricing info when 'price' keyword detected",
            "trigger": AutomationTrigger.KEYWORD_DETECTED,
            "trigger_config": {"keywords": ["price", "cost", "pricing", "fee", "rate"]},
            "action": AutomationAction.SEND_WHATSAPP,
            "action_config": {"template": "pricing_info"},
            "delay_minutes": "0",
        },
        {
            "name": "48h WhatsApp Follow-up",
            "description": "Send WhatsApp if still no reply after 48 hours",
            "trigger": AutomationTrigger.NO_REPLY_48H,
            "trigger_config": {"hours": 48},
            "action": AutomationAction.SEND_WHATSAPP,
            "action_config": {"template": "final_followup"},
            "delay_minutes": "2880",
        },
    ]

    created = []
    for d in defaults:
        existing = db.query(Automation).filter(
            Automation.workspace_id == workspace_id,
            Automation.name == d["name"]
        ).first()
        if not existing:
            auto = Automation(workspace_id=workspace_id, **d)
            db.add(auto)
            created.append(d["name"])

    db.commit()
    return {"created": created, "message": f"Created {len(created)} default automations"}


def _get_or_404(automation_id, workspace_id, db):
    a = db.query(Automation).filter(
        Automation.id == automation_id, Automation.workspace_id == workspace_id
    ).first()
    if not a:
        raise HTTPException(status_code=404, detail="Automation not found")
    return a


def _auto_dict(a: Automation) -> dict:
    return {
        "id": str(a.id),
        "workspace_id": str(a.workspace_id),
        "name": a.name,
        "description": a.description,
        "status": a.status.value if a.status else "active",
        "trigger": a.trigger.value if a.trigger else None,
        "trigger_config": a.trigger_config,
        "action": a.action.value if a.action else None,
        "action_config": a.action_config,
        "delay_minutes": a.delay_minutes,
        "run_count": a.run_count,
        "created_at": a.created_at.isoformat(),
    }
