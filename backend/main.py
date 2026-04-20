"""
AI Sales CRM — FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import json
from typing import List

from core.config import settings
from database import Base, engine

# Import all models so SQLAlchemy creates tables
from models import User, Workspace, WorkspaceMember, Lead, Campaign, Automation, AutomationLog, Conversation, Message, Subscription

# Import routers
from api.routes.auth import router as auth_router
from api.routes.leads import router as leads_router
from api.routes.campaigns import router as campaigns_router
from api.routes.automations import router as automations_router
from api.routes.conversations import router as conversations_router
from api.routes.analytics import router as analytics_router
from api.routes.billing import router as billing_router
from api.routes.webhooks import router as webhooks_router


# ── WebSocket Connection Manager ──────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workspace_id: str):
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)

    def disconnect(self, websocket: WebSocket, workspace_id: str):
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].remove(websocket)

    async def broadcast_to_workspace(self, workspace_id: str, message: dict):
        if workspace_id in self.active_connections:
            for connection in self.active_connections[workspace_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    print(f"✅ CORS allowed origins: {settings.cors_origins_list}")

    # Start background scheduler
    from workers.follow_up_worker import start_scheduler
    start_scheduler()
    print("✅ Follow-up scheduler started")

    yield

    from workers.follow_up_worker import stop_scheduler
    stop_scheduler()


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Sales CRM API",
    description="Complete AI-powered CRM with lead intelligence and automation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(leads_router)
app.include_router(campaigns_router)
app.include_router(automations_router)
app.include_router(conversations_router)
app.include_router(analytics_router)
app.include_router(billing_router)
app.include_router(webhooks_router)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@app.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    """Real-time notifications per workspace."""
    await manager.connect(websocket, workspace_id)
    try:
        while True:
            # Keep connection alive; ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_id)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0", "app": settings.APP_NAME}


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


# ── Notification broadcaster (used by services) ───────────────────────────────

async def notify_workspace(workspace_id: str, event_type: str, data: dict):
    """Send real-time notification to all connected workspace clients."""
    await manager.broadcast_to_workspace(workspace_id, {
        "type": event_type,
        "data": data,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    })
