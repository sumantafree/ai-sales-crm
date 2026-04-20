from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SAEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base
import enum


class MessageRole(str, enum.Enum):
    USER = "user"        # Incoming from lead
    ASSISTANT = "assistant"  # AI / agent reply
    SYSTEM = "system"    # System notifications


class MessageChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    CHAT = "chat"


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(SAEnum(MessageChannel), default=MessageChannel.WHATSAPP)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(SAEnum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    channel = Column(SAEnum(MessageChannel), default=MessageChannel.WHATSAPP)
    is_ai_generated = Column(Boolean, default=False)
    external_message_id = Column(String(255), nullable=True)  # Twilio SID, etc.

    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
