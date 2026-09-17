import base64
import html
import re
from email.message import EmailMessage
from urllib.parse import quote

from ..config import Settings
from ..models import LeaveRequest

COMMAND_PATTERN = re.compile(r"\b(APPROVE|REJECT)\s+LR-(\d+)\b", re.IGNORECASE)


def parse_decision(text: str) -> tuple[str, int] | None:
    match = COMMAND_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).lower(), int(match.group(2))


def build_mailto(request: LeaveRequest, settings: Settings) -> str:
    subject = f"Re: Leave request LR-{request.id}"
    body = (
        f"{request.employee_name},\n\n"
        f"Please reply with exactly one command:\nAPPROVE LR-{request.id}\n"
        f"or\nREJECT LR-{request.id}\n"
    )
    return (
        f"mailto:{quote(request.manager_email)}?"
        f"subject={quote(subject)}&body={quote(body)}"
    )


def build_html(request: LeaveRequest, settings: Settings) -> str:
    values = {
        "employee_name": html.escape(request.employee_name),
        "employee_email": html.escape(request.employee_email),
        "leave_type": html.escape(request.leave_type),
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "reason": html.escape(request.reason),
    }
    mailto = html.escape(build_mailto(request, settings), quote=True)
    return f"""<html><body>
<h2>Leave request LR-{request.id}</h2>
<p><strong>Employee:</strong> {values['employee_name']} ({values['employee_email']})</p>
<p><strong>Type:</strong> {values['leave_type']}</p>
<p><strong>Dates:</strong> {values['start_date']} to {values['end_date']}</p>
<p><strong>Reason:</strong> {values['reason']}</p>
<p>Reply using exactly <strong>APPROVE LR-{request.id}</strong> or <strong>REJECT LR-{request.id}</strong>.</p>
<p><a href="{mailto}">Open a prefilled reply email</a></p>
</body></html>"""


def build_message(request: LeaveRequest, settings: Settings) -> EmailMessage:
    message = EmailMessage()
    message["To"] = request.manager_email
    message["From"] = settings.gmail_sender
    message["Subject"] = f"Leave request LR-{request.id} from {request.employee_name}"
    message.set_content(f"Reply APPROVE LR-{request.id} or REJECT LR-{request.id}.")
    message.add_alternative(build_html(request, settings), subtype="html")
    return message


def encode_message(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
