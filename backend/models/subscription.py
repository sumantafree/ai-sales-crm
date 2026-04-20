from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Stripe
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    stripe_price_id = Column(String(255), nullable=True)

    # Plan details
    plan = Column(String(50), default="free")  # free | pro | agency
    status = Column(String(50), default="active")  # active | past_due | canceled | trialing

    # Limits
    leads_limit = Column(Integer, default=100)   # free: 100, pro: 5000, agency: unlimited
    members_limit = Column(Integer, default=2)   # free: 2, pro: 10, agency: unlimited

    # Dates
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="subscription")

    PLAN_LIMITS = {
        "free": {"leads": 100, "members": 2},
        "pro": {"leads": 5000, "members": 10},
        "agency": {"leads": -1, "members": -1},  # -1 = unlimited
    }
