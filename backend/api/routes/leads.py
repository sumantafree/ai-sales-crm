from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

from database import get_db
from models.lead import Lead, LeadSource, LeadStatus, LeadTemperature
from models.campaign import Campaign
from api.deps import get_current_user, get_current_workspace_id
from models.user import User

router = APIRouter(prefix="/api/leads", tags=["Leads"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    message: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    campaign_id: Optional[str] = None
    extra_data: Optional[dict] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[LeadStatus] = None
    campaign_id: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    name: str
    phone: Optional[str]
    email: Optional[str]
    message: Optional[str]
    source: str
    score: float
    temperature: str
    intent: str
    status: str
    ai_summary: Optional[str]
    ai_suggested_action: Optional[str]
    ai_generated_reply: Optional[str]
    campaign_id: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
def list_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    temperature: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    campaign_id: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Lead).filter(Lead.workspace_id == workspace_id)

    if temperature:
        query = query.filter(Lead.temperature == temperature)
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if campaign_id:
        query = query.filter(Lead.campaign_id == uuid.UUID(campaign_id))
    if search:
        query = query.filter(
            (Lead.name.ilike(f"%{search}%")) |
            (Lead.email.ilike(f"%{search}%")) |
            (Lead.phone.ilike(f"%{search}%"))
        )

    total = query.count()

    col = getattr(Lead, sort_by, Lead.created_at)
    query = query.order_by(desc(col) if order == "desc" else col)
    leads = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "leads": [_lead_dict(l) for l in leads],
    }


@router.post("", status_code=201)
async def create_lead(
    data: LeadCreate,
    background_tasks: BackgroundTasks,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from services.ai_service import analyze_lead
    from services.automation_engine import trigger_automations

    lead = Lead(
        workspace_id=workspace_id,
        name=data.name,
        phone=data.phone,
        email=data.email,
        message=data.message,
        source=data.source,
        campaign_id=uuid.UUID(data.campaign_id) if data.campaign_id else None,
        extra_data=data.extra_data,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    # Update campaign lead count
    if lead.campaign_id:
        db.query(Campaign).filter(Campaign.id == lead.campaign_id).update(
            {"total_leads": Campaign.total_leads + 1}
        )
        db.commit()

    # Async: AI analysis + automations
    background_tasks.add_task(analyze_lead, str(lead.id))
    background_tasks.add_task(trigger_automations, str(lead.id), "lead_created")

    return _lead_dict(lead)


@router.get("/{lead_id}")
def get_lead(
    lead_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lead = _get_lead_or_404(lead_id, workspace_id, db)
    return _lead_dict(lead)


@router.patch("/{lead_id}")
def update_lead(
    lead_id: uuid.UUID,
    data: LeadUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lead = _get_lead_or_404(lead_id, workspace_id, db)
    for field, value in data.dict(exclude_none=True).items():
        setattr(lead, field, value)
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return _lead_dict(lead)


@router.delete("/{lead_id}", status_code=204)
def delete_lead(
    lead_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lead = _get_lead_or_404(lead_id, workspace_id, db)
    db.delete(lead)
    db.commit()


@router.post("/{lead_id}/re-analyze")
async def re_analyze_lead(
    lead_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lead = _get_lead_or_404(lead_id, workspace_id, db)
    from services.ai_service import analyze_lead
    background_tasks.add_task(analyze_lead, str(lead.id))
    return {"message": "Re-analysis queued", "lead_id": str(lead.id)}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_lead_or_404(lead_id, workspace_id, db) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.workspace_id == workspace_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def _lead_dict(lead: Lead) -> dict:
    return {
        "id": str(lead.id),
        "workspace_id": str(lead.workspace_id),
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "message": lead.message,
        "source": lead.source.value if lead.source else None,
        "score": lead.score,
        "temperature": lead.temperature.value if lead.temperature else "cold",
        "intent": lead.intent.value if lead.intent else "unknown",
        "status": lead.status.value if lead.status else "new",
        "ai_summary": lead.ai_summary,
        "ai_suggested_action": lead.ai_suggested_action,
        "ai_generated_reply": lead.ai_generated_reply,
        "campaign_id": str(lead.campaign_id) if lead.campaign_id else None,
        "follow_up_count": lead.follow_up_count,
        "last_contacted_at": lead.last_contacted_at.isoformat() if lead.last_contacted_at else None,
        "created_at": lead.created_at.isoformat(),
        "updated_at": lead.updated_at.isoformat(),
    }
