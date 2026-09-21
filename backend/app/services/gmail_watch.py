import base64
import json
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import AbsentRequest, AbsentStatus, GmailSyncState
from .email import parse_decision
from .gmail import gmail_service


def _header(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _message_text(payload: dict[str, Any]) -> str:
    body = payload.get("body", {}).get("data")
    if body:
        return base64.urlsafe_b64decode(body + "===").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _message_text(part)
        if text:
            return text
    return ""


def process_message(db: Session, message: dict[str, Any]) -> bool:
    payload = message.get("payload", {})
    sender = parseaddr(_header(payload.get("headers", []), "From"))[1].lower()
    subject = _header(payload.get("headers", []), "Subject")
    command = parse_decision(f"{subject}\n{_message_text(payload)}")
    if not command:
        return False
    action, request_id = command
    request = db.get(AbsentRequest, request_id)
    if request.status != AbsentStatus.PENDING.value:
        return False
    request.status = AbsentStatus.APPROVED.value if action == "approve" else AbsentStatus.REJECTED.value
    request.decision_message_id = message.get("id")
    request.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return True


def sync_history(db: Session, settings: Settings, history_id: str) -> int:
    service = gmail_service(settings)
    state = db.scalar(select(GmailSyncState).where(GmailSyncState.id == 1))
    if state is None:
        state = GmailSyncState(id=1, last_history_id=history_id)
        db.add(state)
        db.commit()
        return 0
    start_id = state.last_history_id or history_id
    result = service.users().history().list(userId="me", startHistoryId=start_id).execute()
    processed = 0
    for history in result.get("history", []):
        for entry in history.get("messagesAdded", []):
            message = service.users().messages().get(userId="me", id=entry["message"]["id"], format="full").execute()
            processed += int(process_message(db, message))
    state.last_history_id = history_id
    db.commit()
    return processed


def decode_pubsub_data(data: str) -> dict[str, str]:
    return json.loads(base64.b64decode(data).decode("utf-8"))


def start_watch(settings: Settings) -> dict[str, Any]:
    """Đăng ký Gmail watch với Pub/Sub topic"""
    service = gmail_service(settings)
    if not settings.pubsub_oidc_topic:
        raise RuntimeError("PUBSUB_OIDC_TOPIC is required to start Gmail watch")
    # Extract project from audience: projects/{project}/topics/{topic}
    topic = settings.pubsub_oidc_topic
    return service.users().watch(userId="me", body={"topicName": topic, "labelIds": ["INBOX"]}).execute()
