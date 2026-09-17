from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import Settings
from ..models import LeaveRequest
from .email import build_message, encode_message

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def gmail_service(settings: Settings) -> Any:
    credentials = None
    token_path = Path(settings.gmail_token_file)
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not credentials or not credentials.valid:
        if not settings.gmail_credentials_file:
            raise RuntimeError("GMAIL_CREDENTIALS_FILE is required to use Gmail API")
        flow = InstalledAppFlow.from_client_secrets_file(settings.gmail_credentials_file, SCOPES)
        credentials = flow.run_local_server(port=0)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def send_leave_request(request: LeaveRequest, settings: Settings) -> str:
    service = gmail_service(settings)
    response = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": encode_message(build_message(request, settings))})
        .execute()
    )
    return str(response["id"])


def start_watch(settings: Settings) -> dict[str, Any]:
    service = gmail_service(settings)
    if not settings.google_cloud_project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is required to start Gmail watch")
    topic = f"projects/{settings.google_cloud_project}/topics/gmail-leave-updates"
    return service.users().watch(userId="me", body={"topicName": topic, "labelIds": ["INBOX"]}).execute()
