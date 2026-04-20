"""
Stripe Billing Service
Handles subscription creation, webhook processing, and plan management.
"""
import stripe
from core.config import settings
from models.subscription import Subscription
from models.workspace import Workspace

stripe.api_key = settings.STRIPE_SECRET_KEY

PLAN_CONFIG = {
    "free": {
        "name": "Free",
        "price_inr": 0,
        "leads_limit": 100,
        "members_limit": 2,
        "features": ["100 leads/month", "2 team members", "Basic AI scoring", "Email automation"],
    },
    "pro": {
        "name": "Pro",
        "price_inr": 999,
        "leads_limit": 5000,
        "members_limit": 10,
        "features": [
            "5,000 leads/month", "10 team members", "Advanced AI analysis",
            "WhatsApp + Email automation", "Facebook Lead Ads", "Analytics dashboard",
        ],
        "stripe_price_id": settings.STRIPE_PRO_PRICE_ID,
    },
    "agency": {
        "name": "Agency",
        "price_inr": 2999,
        "leads_limit": -1,
        "members_limit": -1,
        "features": [
            "Unlimited leads", "Unlimited team members", "Priority AI processing",
            "All automation features", "White-label ready", "Dedicated support",
        ],
        "stripe_price_id": settings.STRIPE_AGENCY_PRICE_ID,
    },
}


def get_or_create_customer(workspace: Workspace, user_email: str, user_name: str) -> str:
    """Get or create a Stripe customer for the workspace."""
    sub = workspace.subscription
    if sub and sub.stripe_customer_id:
        return sub.stripe_customer_id

    customer = stripe.Customer.create(
        email=user_email,
        name=user_name,
        metadata={"workspace_id": str(workspace.id), "workspace_name": workspace.name},
    )
    return customer.id


def create_checkout_session(
    workspace_id: str,
    plan: str,
    customer_id: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe Checkout session for plan upgrade."""
    plan_data = PLAN_CONFIG.get(plan, {})
    price_id = plan_data.get("stripe_price_id")

    if not price_id:
        raise ValueError(f"No Stripe price ID configured for plan: {plan}")

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"workspace_id": workspace_id, "plan": plan},
        subscription_data={
            "metadata": {"workspace_id": workspace_id, "plan": plan}
        },
    )
    return session.url


def create_billing_portal_session(customer_id: str, return_url: str) -> str:
    """Create a Stripe Customer Portal session for managing subscription."""
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


def handle_webhook_event(payload: bytes, signature: str) -> dict:
    """Process Stripe webhook events."""
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise ValueError("Invalid Stripe webhook signature")

    event_type = event["type"]
    data = event["data"]["object"]

    return {"event_type": event_type, "data": data}


def update_subscription_from_event(db, event_type: str, data: dict):
    """Update local subscription record based on Stripe event."""
    from datetime import datetime

    workspace_id = data.get("metadata", {}).get("workspace_id")
    if not workspace_id:
        return

    import uuid
    sub = db.query(Subscription).filter(
        Subscription.workspace_id == uuid.UUID(workspace_id)
    ).first()
    if not sub:
        return

    if event_type in ("customer.subscription.created", "customer.subscription.updated"):
        plan = data.get("metadata", {}).get("plan", "pro")
        plan_limits = Subscription.PLAN_LIMITS.get(plan, Subscription.PLAN_LIMITS["free"])

        sub.stripe_subscription_id = data.get("id")
        sub.stripe_customer_id = data.get("customer")
        sub.plan = plan
        sub.status = data.get("status", "active")
        sub.leads_limit = plan_limits["leads"]
        sub.members_limit = plan_limits["members"]

        period = data.get("current_period_end")
        if period:
            sub.current_period_end = datetime.fromtimestamp(period)

        # Update workspace plan
        db.query(Workspace).filter(
            Workspace.id == uuid.UUID(workspace_id)
        ).update({"plan": plan})

    elif event_type == "customer.subscription.deleted":
        sub.plan = "free"
        sub.status = "canceled"
        sub.canceled_at = datetime.utcnow()
        sub.leads_limit = 100
        sub.members_limit = 2

        db.query(Workspace).filter(
            Workspace.id == uuid.UUID(workspace_id)
        ).update({"plan": "free"})

    db.commit()


def get_plan_config():
    return PLAN_CONFIG
