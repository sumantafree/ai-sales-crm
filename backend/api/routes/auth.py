from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr
import uuid

from database import get_db
from models.user import User
from models.workspace import Workspace, WorkspaceMember, WorkspaceRole
from models.subscription import Subscription
from core.security import verify_password, get_password_hash, create_access_token
from core.config import settings
from api.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    workspace_name: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    current_workspace_id: str | None
    avatar_url: str | None


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/signup", status_code=201)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    """Register a new user + create their first workspace."""

    # Check if email exists
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        is_verified=True,  # skip email verification for now
    )
    db.add(user)
    db.flush()

    # Create workspace
    slug = data.workspace_name.lower().replace(" ", "-") + "-" + str(uuid.uuid4())[:8]
    workspace = Workspace(name=data.workspace_name, slug=slug)
    db.add(workspace)
    db.flush()

    # Add user as workspace owner
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.OWNER)
    db.add(member)

    # Create free subscription
    sub = Subscription(workspace_id=workspace.id, plan="free", leads_limit=100, members_limit=2)
    db.add(sub)

    # Set current workspace
    user.current_workspace_id = workspace.id
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(user),
    }


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with email + password."""
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": _user_dict(user),
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return _user_dict(current_user)


@router.post("/switch-workspace/{workspace_id}")
def switch_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")

    current_user.current_workspace_id = workspace_id
    db.commit()
    return {"message": "Workspace switched", "workspace_id": str(workspace_id)}


def _user_dict(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "current_workspace_id": str(user.current_workspace_id) if user.current_workspace_id else None,
        "created_at": user.created_at.isoformat(),
    }
