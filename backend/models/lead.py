from sqlalchemy import Column, String, DateTime, Float, Integer, ForeignKey, Text, Enum as SAEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base
import enum


class LeadSource(str, enum.Enum):
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEBSITE = "website"
    MANUAL = "manual"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class LeadTemperature(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class LeadIntent(str, enum.Enum):
    BUYING = "buying"
    INQUIRY = "inquiry"
    CASUAL = "casual"
    UNKNOWN = "unknown"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)

    # Contact info
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)

    # Source
    source = Column(SAEnum(LeadSource), default=LeadSource.WEBSITE)
    external_id = Column(String(255), nullable=True)  # Facebook lead ID, etc.

    # AI Analysis
    score = Column(Float, default=0.0)  # 0-100
    temperature = Column(SAEnum(LeadTemperature), default=LeadTemperature.COLD)
    intent = Column(SAEnum(LeadIntent), default=LeadIntent.UNKNOWN)
    ai_summary = Column(Text, nullable=True)
    ai_suggested_action = Column(Text, nullable=True)
    ai_generated_reply = Column(Text, nullable=True)

    # Status
    status = Column(SAEnum(LeadStatus), default=LeadStatus.NEW)
    last_contacted_at = Column(DateTime, nullable=True)
    follow_up_count = Column(Integer, default=0)

    # Meta
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="leads")
    campaign = relationship("Campaign", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead", cascade="all, delete-orphan")
    automation_logs = relationship("AutomationLog", back_populates="lead", cascade="all, delete-orphan")
