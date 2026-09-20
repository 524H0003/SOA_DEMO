"""Send a small Hello World email through the Gmail API."""

import argparse
import base64
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CREDENTIALS = SCRIPT_DIR / "credentials.json"
DEFAULT_TOKEN = SCRIPT_DIR / "token.json"


def get_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    elif not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        credentials = flow.run_local_server(port=0)

    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def send_email(
    recipient: str,
    credentials_path: Path,
    token_path: Path,
    subject: str,
    body: str,
) -> str:
    credentials = get_credentials(credentials_path, token_path)

    message = EmailMessage()
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")

    service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
    response = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw_message})
        .execute()
    )
    return str(response["id"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a Hello World email with Gmail API")
    parser.add_argument("recipient", help="Email address that receives the message")
    parser.add_argument(
        "--credentials",
        type=Path,
        default=DEFAULT_CREDENTIALS,
        help=f"OAuth client JSON path (default: {DEFAULT_CREDENTIALS})",
    )
    parser.add_argument(
        "--token",
        type=Path,
        default=DEFAULT_TOKEN,
        help=f"OAuth token path (default: {DEFAULT_TOKEN})",
    )
    parser.add_argument("--subject", default="Hello World", help="Email subject")
    parser.add_argument("--body", default="Hello World!", help="Email body")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.credentials.exists():
        raise SystemExit(
            f"OAuth client file not found: {args.credentials}\n"
            "See script/README.md for setup instructions."
        )

    message_id = send_email(
        recipient=args.recipient,
        credentials_path=args.credentials,
        token_path=args.token,
        subject=args.subject,
        body=args.body,
    )
    print(f"Email sent successfully. Gmail message id: {message_id}")


if __name__ == "__main__":
    main()