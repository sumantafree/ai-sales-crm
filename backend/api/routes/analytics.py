from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
import uuid

from database import get_db
from models.lead import Lead, LeadSource, LeadTemperature, LeadStatus
from models.campaign import Campaign
from api.deps import get_current_user, get_current_workspace_id
from models.user import User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard_metrics(
    days: int = Query(30, ge=1, le=365),
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(days=days)

    total_leads = db.query(func.count(Lead.id)).filter(Lead.workspace_id == workspace_id).scalar()
    new_leads = db.query(func.count(Lead.id)).filter(
        Lead.workspace_id == workspace_id, Lead.created_at >= since
    ).scalar()
    converted = db.query(func.count(Lead.id)).filter(
        Lead.workspace_id == workspace_id, Lead.status == LeadStatus.CONVERTED
    ).scalar()
    hot_leads = db.query(func.count(Lead.id)).filter(
        Lead.workspace_id == workspace_id, Lead.temperature == LeadTemperature.HOT
    ).scalar()
    avg_score = db.query(func.avg(Lead.score)).filter(Lead.workspace_id == workspace_id).scalar() or 0

    conversion_rate = round((converted / total_leads * 100), 2) if total_leads > 0 else 0

    # Leads by source
    by_source = db.query(Lead.source, func.count(Lead.id)).filter(
        Lead.workspace_id == workspace_id
    ).group_by(Lead.source).all()

    # Leads by temperature
    by_temp = db.query(Lead.temperature, func.count(Lead.id)).filter(
        Lead.workspace_id == workspace_id
    ).group_by(Lead.temperature).all()

    # Daily leads (last N days)
    daily = db.query(
        cast(Lead.created_at, Date).label("date"),
        func.count(Lead.id).label("count")
    ).filter(
        Lead.workspace_id == workspace_id,
        Lead.created_at >= since
    ).group_by(cast(Lead.created_at, Date)).order_by(cast(Lead.created_at, Date)).all()

    # Top campaign
    top_campaign = db.query(Campaign.name, Campaign.total_leads, Campaign.converted_leads).filter(
        Campaign.workspace_id == workspace_id
    ).order_by(Campaign.total_leads.desc()).first()

    return {
        "summary": {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "converted": converted,
            "hot_leads": hot_leads,
            "avg_score": round(float(avg_score), 1),
            "conversion_rate": conversion_rate,
        },
        "leads_by_source": {r[0].value if r[0] else "unknown": r[1] for r in by_source},
        "leads_by_temperature": {r[0].value if r[0] else "unknown": r[1] for r in by_temp},
        "daily_leads": [
            {"date": str(r[0]), "count": r[1]} for r in daily
        ],
        "top_campaign": {
            "name": top_campaign[0],
            "total_leads": top_campaign[1],
            "converted": top_campaign[2],
        } if top_campaign else None,
    }


@router.get("/ai-insights")
def ai_insights(
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return pre-computed AI-style insights about the workspace performance."""
    try:
        insights = []

        # WhatsApp vs Facebook comparison
        wa_leads = db.query(func.count(Lead.id)).filter(
            Lead.workspace_id == workspace_id, Lead.source == LeadSource.WHATSAPP
        ).scalar() or 0
        wa_converted = db.query(func.count(Lead.id)).filter(
            Lead.workspace_id == workspace_id,
            Lead.source == LeadSource.WHATSAPP,
            Lead.status == LeadStatus.CONVERTED
        ).scalar() or 0

        fb_leads = db.query(func.count(Lead.id)).filter(
            Lead.workspace_id == workspace_id, Lead.source == LeadSource.FACEBOOK
        ).scalar() or 0
        fb_converted = db.query(func.count(Lead.id)).filter(
            Lead.workspace_id == workspace_id,
            Lead.source == LeadSource.FACEBOOK,
            Lead.status == LeadStatus.CONVERTED
        ).scalar() or 0

        if wa_leads > 0 and fb_leads > 0:
            wa_rate = wa_converted / wa_leads
            fb_rate = fb_converted / fb_leads
            if wa_rate > fb_rate:
                insights.append({
                    "type": "positive",
                    "icon": "whatsapp",
                    "text": f"WhatsApp leads convert {round((wa_rate - fb_rate) * 100, 1)}% better than Facebook leads.",
                    "action": "Focus more budget on WhatsApp campaigns."
                })

        # Underperforming campaigns
        low_campaigns = db.query(Campaign).filter(
            Campaign.workspace_id == workspace_id,
            Campaign.total_leads > 10,
            Campaign.converted_leads == 0
        ).all()
        for c in low_campaigns[:2]:
            insights.append({
                "type": "warning",
                "icon": "campaign",
                "text": f"Campaign '{c.name}' has {c.total_leads} leads but 0 conversions.",
                "action": "Review targeting or messaging for this campaign."
            })

        # Hot leads not contacted
        hot_uncontacted = db.query(func.count(Lead.id)).filter(
            Lead.workspace_id == workspace_id,
            Lead.temperature == LeadTemperature.HOT,
            Lead.last_contacted_at.is_(None)
        ).scalar() or 0
        if hot_uncontacted > 0:
            insights.append({
                "type": "urgent",
                "icon": "fire",
                "text": f"{hot_uncontacted} hot leads have never been contacted!",
                "action": "Contact these leads immediately to maximize conversion."
            })

        # High score average
        avg_score = db.query(func.avg(Lead.score)).filter(
            Lead.workspace_id == workspace_id
        ).scalar() or 0
        if float(avg_score) > 70:
            insights.append({
                "type": "positive",
                "icon": "score",
                "text": f"Your average lead score is {round(float(avg_score), 1)} — excellent quality traffic.",
                "action": "Keep running current campaigns to maintain quality."
            })

        if not insights:
            insights.append({
                "type": "info",
                "icon": "info",
                "text": "Add more leads and campaigns to unlock AI insights.",
                "action": "Import leads or connect Facebook Lead Ads to start capturing leads."
            })

        return {"insights": insights}

    except Exception as e:
        print(f"[AI Insights ERROR] {e}")
        return {"insights": [{
            "type": "info",
            "icon": "info",
            "text": "AI insights will appear once you have leads in the system.",
            "action": "Add your first lead to get started."
        }]}


@router.get("/campaigns/roi")
def campaign_roi(
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    campaigns = db.query(Campaign).filter(Campaign.workspace_id == workspace_id).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "total_leads": c.total_leads,
            "converted_leads": c.converted_leads,
            "conversion_rate": c.conversion_rate,
            "revenue_generated": c.revenue_generated,
            "status": c.status.value if c.status else "draft",
        }
        for c in campaigns
    ]
