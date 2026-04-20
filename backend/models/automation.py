from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base
import enum


class AutomationTrigger(str, enum.Enum):
    LEAD_CREATED = "lead_created"
    SCORE_ABOVE = "score_above"
    SCORE_BELOW = "score_below"
    NO_REPLY_24H = "no_reply_24h"
    NO_REPLY_48H = "no_reply_48h"
    KEYWORD_DETECTED = "keyword_detected"
    SOURCE_MATCH = "source_match"
    INTENT_MATCH = "intent_match"
    TEMPERATURE_MATCH = "temperature_match"


class AutomationAction(str, enum.Enum):
    SEND_WHATSAPP = "send_whatsapp"
    SEND_EMAIL = "send_email"
    UPDATE_SCORE = "update_score"
    UPDATE_STATUS = "update_status"
    ASSIGN_CAMPAIGN = "assign_campaign"
    NOTIFY_TEAM = "notify_team"
    AI_REPLY = "ai_reply"


class AutomationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Automation(Base):
    __tablename__ = "automations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(AutomationStatus), default=AutomationStatus.ACTIVE)

    # Trigger config
    trigger = Column(SAEnum(AutomationTrigger), nullable=False)
    trigger_config = Column(JSON, nullable=True)
    # Example: {"score_threshold": 70} or {"keyword": "price"} or {"hours": 24}

    # Action config
    action = Column(SAEnum(AutomationAction), nullable=False)
    action_config = Column(JSON, nullable=True)
    # Example: {"template": "Hi {name}!", "message_type": "whatsapp"}

    # Delay in minutes (0 = immediate)
    delay_minutes = Column(String(10), default="0")

    run_count = Column(String(10), default="0")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="automations")
    logs = relationship("AutomationLog", back_populates="automation", cascade="all, delete-orphan")


class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    automation_id = Column(UUID(as_uuid=True), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)

    status = Column(String(50), default="success")  # success | failed | skipped
    result = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    automation = relationship("Automation", back_populates="logs")
    lead = relationship("Lead", back_populates="automation_logs")
