from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.workspace import Workspace
from models.subscription import Subscription
from api.deps import get_current_user, get_current_workspace_id
from models.user import User
import uuid

router = APIRouter(prefix="/api/billing", tags=["Billing"])


class CheckoutRequest(BaseModel):
    plan: str
    success_url: str
    cancel_url: str


@router.get("/plans")
def get_plans():
    from services.stripe_service import get_plan_config
    return get_plan_config()


@router.get("/subscription")
def get_subscription(
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(Subscription.workspace_id == workspace_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {
        "plan": sub.plan,
        "status": sub.status,
        "leads_limit": sub.leads_limit,
        "members_limit": sub.members_limit,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "stripe_customer_id": sub.stripe_customer_id,
        "stripe_subscription_id": sub.stripe_subscription_id,
    }


@router.post("/checkout")
def create_checkout(
    data: CheckoutRequest,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.plan not in ("pro", "agency"):
        raise HTTPException(status_code=400, detail="Invalid plan")

    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    from services.stripe_service import get_or_create_customer, create_checkout_session

    customer_id = get_or_create_customer(workspace, current_user.email, current_user.full_name)

    # Save customer_id
    sub = workspace.subscription
    if sub and not sub.stripe_customer_id:
        sub.stripe_customer_id = customer_id
        db.commit()

    checkout_url = create_checkout_session(
        workspace_id=str(workspace_id),
        plan=data.plan,
        customer_id=customer_id,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
    )
    return {"checkout_url": checkout_url}


@router.post("/portal")
def customer_portal(
    return_url: str,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(Subscription.workspace_id == workspace_id).first()
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found")

    from services.stripe_service import create_billing_portal_session
    url = create_billing_portal_session(sub.stripe_customer_id, return_url)
    return {"portal_url": url}
