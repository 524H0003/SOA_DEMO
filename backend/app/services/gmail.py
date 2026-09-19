import base64
import json
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import Settings
from ..models import AbsentRequest
from .email import build_message, encode_message

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def gmail_service(settings: Settings) -> Any:
    credentials = None
    token_path = Path(settings.gmail_token_file)
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not credentials or not credentials.valid:
        flow = _oauth_flow(settings)
        credentials = flow.run_local_server(port=0)
        token_path.write_text(credentials.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _oauth_flow(settings: Settings) -> InstalledAppFlow:
    if settings.gmail_credentials_json_base64:
        try:
            raw_credentials = base64.b64decode(settings.gmail_credentials_json_base64).decode("utf-8")
            client_config = json.loads(raw_credentials)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError("GMAIL_CREDENTIALS_JSON_BASE64 is not valid Google OAuth JSON") from error
        return InstalledAppFlow.from_client_config(client_config, SCOPES)
    if settings.gmail_credentials_json:
        try:
            client_config = json.loads(settings.gmail_credentials_json)
        except json.JSONDecodeError as error:
            raise RuntimeError("GMAIL_CREDENTIALS_JSON is not valid Google OAuth JSON") from error
        return InstalledAppFlow.from_client_config(client_config, SCOPES)
    if settings.gmail_credentials_file:
        return InstalledAppFlow.from_client_secrets_file(settings.gmail_credentials_file, SCOPES)
    raise RuntimeError("Set GMAIL_CREDENTIALS_JSON_BASE64 or GMAIL_CREDENTIALS_FILE to use Gmail API")


def send_absent_request(request: AbsentRequest, settings: Settings) -> str:
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
    topic = f"projects/{settings.google_cloud_project}/topics/gmail-absent-updates"
    return service.users().watch(userId="me", body={"topicName": topic, "labelIds": ["INBOX"]}).execute()
