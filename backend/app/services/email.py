import base64
import html
import re
import uuid
from pathlib import Path
from string import Template
from email.message import EmailMessage
from urllib.parse import quote

from ..config import Settings
from ..models import AbsentRequest

COMMAND_PATTERN = re.compile(r"\b(APPROVE|REJECT)\s+AR-([a-f0-9-]{36})\b", re.IGNORECASE)


def parse_decision(text: str) -> tuple[str, uuid.UUID] | None:
    """
    Parse decision from email text. Only checks the first non-empty line of the
    message body (after subject) to avoid matching commands in quoted original email.
    """
    # Split into lines, skip subject line (first line), find first non-empty body line
    lines = text.splitlines()
    if len(lines) < 2:
        return None
    
    # Get the first non-empty line after subject (the actual reply content)
    for line in lines[1:]:
        line = line.strip()
        if line:  # Found first non-empty line of reply
            match = COMMAND_PATTERN.search(line)
            if match:
                return match.group(1).lower(), uuid.UUID(match.group(2))
            break  # Only check the first non-empty line
    return None


def build_decision_mailto(
    request: AbsentRequest, settings: Settings, action: str
) -> str:
    command = f"{action.upper()} AR-{request.id}"
    subject = f"Re: Absent request AR-{request.id}"
    body = f"{command}"

    return (
        f"mailto:{(settings.gmail_sender)}?"
        f"subject={quote(subject)}&body={quote(body)}"
    )


def build_mailto(request: AbsentRequest, settings: Settings) -> str:
    """Build the approve link for callers that still need one decision link."""
    return build_decision_mailto(request, settings, "APPROVE")


def build_html(request: AbsentRequest, settings: Settings) -> str:
    values = {
        "employee_name": html.escape(request.user.username),
        "employee_email": html.escape(request.user.email),
        "absent_type": html.escape(request.absent_type),
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "reason": html.escape(request.reason),
    }
    approve_mailto = html.escape(
        build_decision_mailto(request, settings, "APPROVE"), quote=True
    )
    reject_mailto = html.escape(
        build_decision_mailto(request, settings, "REJECT"), quote=True
    )
    template_path = Path(settings.email_template_file)
    if not template_path.is_absolute():
        template_path = Path(__file__).resolve().parents[2] / template_path
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.safe_substitute(
        **values,
        request_id=str(request.id),
        approve_command=f"APPROVE AR-{request.id}",
        reject_command=f"REJECT AR-{request.id}",
        approve_mailto=approve_mailto,
        reject_mailto=reject_mailto,
    )


def build_message(request: AbsentRequest, settings: Settings) -> EmailMessage:
    message = EmailMessage()
    message["To"] = settings.manager_email
    message["From"] = settings.gmail_sender
    message["Subject"] = f"Absent request AR-{request.id} from {request.user.username}"
    message.set_content(f"Reply APPROVE AR-{request.id} or REJECT AR-{request.id}.")
    message.add_alternative(build_html(request, settings), subtype="html")
    return message


def encode_message(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
