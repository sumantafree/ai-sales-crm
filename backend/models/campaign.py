from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Float, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base
import enum


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT)

    # Source tracking
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    facebook_form_id = Column(String(100), nullable=True)

    # Metrics
    total_leads = Column(Integer, default=0)
    converted_leads = Column(Integer, default=0)
    revenue_generated = Column(Float, default=0.0)

    # Dates
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    workspace = relationship("Workspace", back_populates="campaigns")
    leads = relationship("Lead", back_populates="campaign")

    @property
    def conversion_rate(self):
        if self.total_leads == 0:
            return 0.0
        return round((self.converted_leads / self.total_leads) * 100, 2)
