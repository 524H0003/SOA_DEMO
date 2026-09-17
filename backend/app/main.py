import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db, init_db
from .models import LeaveRequest
from .schemas import LeaveRequestCreate, LeaveRequestResponse, PubSubEnvelope
from .services.gmail import send_leave_request
from .services.gmail_watch import decode_pubsub_data, sync_history

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/leave-requests", response_model=list[LeaveRequestResponse])
def list_leave_requests(db: Session = Depends(get_db)) -> list[LeaveRequest]:
    return list(db.scalars(select(LeaveRequest).order_by(LeaveRequest.created_at.desc())))


@app.post("/api/leave-requests", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
def create_leave_request(payload: LeaveRequestCreate, db: Session = Depends(get_db)) -> LeaveRequest:
    request = LeaveRequest(**payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    try:
        request.gmail_message_id = send_leave_request(request, settings)
        db.commit()
    except RuntimeError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Gmail is not configured")
    return request


@app.post("/api/webhooks/gmail", status_code=status.HTTP_204_NO_CONTENT)
async def gmail_webhook(
    envelope: PubSubEnvelope,
    token: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> None:
    if settings.pubsub_verification_token and token != settings.pubsub_verification_token:
        raise HTTPException(status_code=401, detail="Invalid Pub/Sub subscription")
    try:
        notification = decode_pubsub_data(envelope.message.data)
        history_id = notification["historyId"]
        sync_history(db, settings, history_id)
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail="Invalid Gmail notification") from error
