from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

from database import get_db
from models.campaign import Campaign, CampaignStatus
from models.lead import Lead
from api.deps import get_current_user, get_current_workspace_id
from models.user import User

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    facebook_form_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@router.get("")
def list_campaigns(
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace_id).order_by(
        Campaign.created_at.desc()
    ).all()
    return [_campaign_dict(c) for c in campaigns]


@router.post("", status_code=201)
def create_campaign(
    data: CampaignCreate,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    campaign = Campaign(workspace_id=workspace_id, **data.dict(exclude_none=True))
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _campaign_dict(campaign)


@router.get("/{campaign_id}")
def get_campaign(
    campaign_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    campaign = _get_or_404(campaign_id, workspace_id, db)

    # Lead breakdown
    lead_counts = db.query(Lead.temperature, func.count(Lead.id)).filter(
        Lead.campaign_id == campaign_id
    ).group_by(Lead.temperature).all()

    breakdown = {r[0].value if r[0] else "unknown": r[1] for r in lead_counts}
    result = _campaign_dict(campaign)
    result["lead_breakdown"] = breakdown
    return result


@router.patch("/{campaign_id}")
def update_campaign(
    campaign_id: uuid.UUID,
    data: CampaignUpdate,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    campaign = _get_or_404(campaign_id, workspace_id, db)
    for field, value in data.dict(exclude_none=True).items():
        setattr(campaign, field, value)
    campaign.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(campaign)
    return _campaign_dict(campaign)


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    campaign = _get_or_404(campaign_id, workspace_id, db)
    db.delete(campaign)
    db.commit()


def _get_or_404(campaign_id, workspace_id, db):
    c = db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.workspace_id == workspace_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return c


def _campaign_dict(c: Campaign) -> dict:
    return {
        "id": str(c.id),
        "workspace_id": str(c.workspace_id),
        "name": c.name,
        "description": c.description,
        "status": c.status.value if c.status else "draft",
        "utm_source": c.utm_source,
        "utm_medium": c.utm_medium,
        "utm_campaign": c.utm_campaign,
        "facebook_form_id": c.facebook_form_id,
        "total_leads": c.total_leads,
        "converted_leads": c.converted_leads,
        "conversion_rate": c.conversion_rate,
        "revenue_generated": c.revenue_generated,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "created_at": c.created_at.isoformat(),
    }
