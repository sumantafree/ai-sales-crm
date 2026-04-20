from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uuid

from database import get_db
from models.conversation import Conversation, Message, MessageRole, MessageChannel
from models.lead import Lead
from api.deps import get_current_user, get_current_workspace_id
from models.user import User

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


class SendMessageRequest(BaseModel):
    content: str
    channel: MessageChannel = MessageChannel.WHATSAPP
    use_ai: bool = False


@router.get("/lead/{lead_id}")
def get_lead_conversations(
    lead_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.workspace_id == workspace_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    conversations = db.query(Conversation).filter(
        Conversation.lead_id == lead_id,
        Conversation.workspace_id == workspace_id
    ).order_by(Conversation.created_at.desc()).all()

    return [_conv_dict(c) for c in conversations]


@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: uuid.UUID,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conv = _get_conv_or_404(conversation_id, workspace_id, db)
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()

    return {
        "conversation": _conv_dict(conv),
        "messages": [_msg_dict(m) for m in messages],
    }


@router.post("/{conversation_id}/send")
async def send_message(
    conversation_id: uuid.UUID,
    data: SendMessageRequest,
    background_tasks: BackgroundTasks,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    conv = _get_conv_or_404(conversation_id, workspace_id, db)

    # If AI-assisted, generate reply first
    content = data.content
    is_ai = False
    if data.use_ai:
        from services.ai_service import generate_contextual_reply
        lead = db.query(Lead).filter(Lead.id == conv.lead_id).first()
        history = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(
            Message.created_at.asc()
        ).limit(10).all()
        content = await generate_contextual_reply(lead, history)
        is_ai = True

    # Save message
    msg = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=content,
        channel=data.channel,
        is_ai_generated=is_ai,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # Send via channel
    if data.channel == MessageChannel.WHATSAPP:
        lead = db.query(Lead).filter(Lead.id == conv.lead_id).first()
        if lead and lead.phone:
            background_tasks.add_task(_send_whatsapp, lead.phone, content, str(msg.id), db)

    return _msg_dict(msg)


@router.post("/lead/{lead_id}/start")
def start_conversation(
    lead_id: uuid.UUID,
    channel: MessageChannel = MessageChannel.WHATSAPP,
    workspace_id: uuid.UUID = Depends(get_current_workspace_id),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.workspace_id == workspace_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    conv = Conversation(lead_id=lead_id, workspace_id=workspace_id, channel=channel)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _conv_dict(conv)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _send_whatsapp(phone: str, content: str, message_id: str, db: Session):
    from services.whatsapp_service import send_whatsapp_message
    try:
        sid = await send_whatsapp_message(phone, content)
        db.query(Message).filter(Message.id == uuid.UUID(message_id)).update(
            {"external_message_id": sid}
        )
        db.commit()
    except Exception as e:
        print(f"WhatsApp send error: {e}")


def _get_conv_or_404(conversation_id, workspace_id, db):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.workspace_id == workspace_id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


def _conv_dict(c: Conversation) -> dict:
    return {
        "id": str(c.id),
        "lead_id": str(c.lead_id),
        "channel": c.channel.value if c.channel else "whatsapp",
        "is_active": c.is_active,
        "message_count": len(c.messages) if c.messages else 0,
        "created_at": c.created_at.isoformat(),
        "updated_at": c.updated_at.isoformat(),
    }


def _msg_dict(m: Message) -> dict:
    return {
        "id": str(m.id),
        "conversation_id": str(m.conversation_id),
        "role": m.role.value if m.role else "user",
        "content": m.content,
        "channel": m.channel.value if m.channel else "whatsapp",
        "is_ai_generated": m.is_ai_generated,
        "created_at": m.created_at.isoformat(),
    }
