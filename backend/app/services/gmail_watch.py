import base64, json, re, uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import AbsentRequest, AbsentStatus, GmailSyncState
from .email import parse_decision
from .gmail import gmail_service


def _header(headers: list[dict[str, str]], name: str) -> str:
    return next(
        (h["value"] for h in headers if h.get("name", "").lower() == name.lower()), ""
    )


def _message_text(payload: dict[str, Any]) -> str:
    if body := payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(body + "===").decode("utf-8", errors="replace")
    return next((t for p in payload.get("parts", []) if (t := _message_text(p))), "")


REQUEST_ID_IN_SUBJECT = re.compile(r"AR-([a-f0-9-]{36})", re.I)


def _extract_request_id_from_subject(subject: str) -> uuid.UUID | None:
    return (
        (m := REQUEST_ID_IN_SUBJECT.search(subject)) and uuid.UUID(m.group(1)) or None
    )


def _extract_decision_from_message(message: dict[str, Any]) -> tuple[str, uuid.UUID, str] | None:
    """Extract decision command from Gmail message."""
    payload = message.get("payload", {})
    subject = _header(payload.get("headers", []), "Subject")
    body = _message_text(payload)
    return parse_decision(f"{subject}\n{body}")


def _validate_request(db: Session, request_id: uuid.UUID, security_code: str) -> AbsentRequest | None:
    """Validate that request exists and is pending with matching security code."""
    request = db.scalar(select(AbsentRequest).where(AbsentRequest.id == request_id))
    if not request:
        return None
    if request.status != AbsentStatus.PENDING.value or request.security_code != security_code:
        return None
    return request


def _update_request_status(request: AbsentRequest, action: str, message_id: str) -> None:
    """Update request status based on decision action."""
    request.status = (
        AbsentStatus.APPROVED.value if action == "approve" else AbsentStatus.REJECTED.value
    )
    request.decision_message_id = message_id
    request.decided_at = datetime.now(timezone.utc).replace(tzinfo=None)


def process_message(db: Session, message: dict[str, Any]) -> bool:
    """Process a Gmail message and update absent request if valid decision found."""
    command = _extract_decision_from_message(message)
    if not command:
        return False
    
    action, request_id, security_code = command
    request = _validate_request(db, request_id, security_code)
    if not request:
        return False
    
    _update_request_status(request, action, message.get("id"))
    db.commit()
    return True


def _get_or_create_sync_state(db: Session, settings: Settings, history_id: str) -> GmailSyncState:
    """Get existing sync state or create new one."""
    state_id = settings.gmail_sync_state_id
    state = db.scalar(select(GmailSyncState).where(GmailSyncState.id == state_id))
    if state is None:
        state = GmailSyncState(id=state_id, last_history_id=history_id)
        db.add(state)
        db.commit()
    return state


def _fetch_history_messages(service: Any, start_history_id: str) -> list[dict]:
    """Fetch new messages from Gmail history API."""
    result = (
        service.users()
        .history()
        .list(userId="me", startHistoryId=start_history_id, historyTypes=["messageAdded"])
        .execute()
    )
    return result.get("history", [])


def _fetch_message_metadata(service: Any, message_id: str) -> dict:
    """Fetch message metadata including subject."""
    return (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="metadata", metadataHeaders=["Subject"])
        .execute()
    )


def _fetch_full_message(service: Any, message_id: str) -> dict:
    """Fetch full message content."""
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()


def _process_single_message(service: Any, db: Session, message_id: str) -> bool:
    """Process a single message if it contains a valid request ID."""
    meta = _fetch_message_metadata(service, message_id)
    subject = _header(meta.get("payload", {}).get("headers", []), "Subject")
    
    if not _extract_request_id_from_subject(subject):
        return False
    
    message = _fetch_full_message(service, message_id)
    return process_message(db, message)


def sync_history(db: Session, settings: Settings, history_id: str) -> int:
    """Sync Gmail history and process new messages."""
    service = gmail_service(settings)
    state = _get_or_create_sync_state(db, settings, history_id)
    
    if state.last_history_id is None:
        state.last_history_id = history_id
        db.commit()
        return 0
    
    start_id = state.last_history_id
    histories = _fetch_history_messages(service, start_id)
    
    processed = 0
    processed_msg_ids = set()
    
    for history in histories:
        for entry in history.get("messagesAdded", []):
            msg_id = entry["message"]["id"]
            if msg_id in processed_msg_ids:
                continue
            processed_msg_ids.add(msg_id)
            
            if _process_single_message(service, db, msg_id):
                processed += 1
    
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
    return (
        service.users()
        .watch(userId="me", body={"topicName": topic, "labelIds": ["INBOX"]})
        .execute()
    )
