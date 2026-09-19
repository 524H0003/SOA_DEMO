import base64
import html
import re
from email.message import EmailMessage
from urllib.parse import quote

from ..config import Settings
from ..models import AbsentRequest

COMMAND_PATTERN = re.compile(r"\b(APPROVE|REJECT)\s+AR-(\d+)\b", re.IGNORECASE)


def parse_decision(text: str) -> tuple[str, int] | None:
    match = COMMAND_PATTERN.search(text)
    if not match:
        return None
    return match.group(1).lower(), int(match.group(2))


def build_mailto(request: AbsentRequest, settings: Settings) -> str:
    subject = f"Re: Absent request AR-{request.id}"
    body = (
        f"{request.employee_name},\n\n"
        f"Please reply with exactly one command:\nAPPROVE AR-{request.id}\n"
        f"or\nREJECT AR-{request.id}\n"
    )
    return (
        f"mailto:{quote(request.manager_email)}?"
        f"subject={quote(subject)}&body={quote(body)}"
    )


def build_html(request: AbsentRequest, settings: Settings) -> str:
    values = {
        "employee_name": html.escape(request.employee_name),
        "employee_email": html.escape(request.employee_email),
        "absent_type": html.escape(request.absent_type),
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "reason": html.escape(request.reason),
    }
    mailto = html.escape(build_mailto(request, settings), quote=True)
    return f"""<html><body>
<h2>Absent request AR-{request.id}</h2>
<p><strong>Employee:</strong> {values['employee_name']} ({values['employee_email']})</p>
<p><strong>Type:</strong> {values['absent_type']}</p>
<p><strong>Dates:</strong> {values['start_date']} to {values['end_date']}</p>
<p><strong>Reason:</strong> {values['reason']}</p>
<p>Reply using exactly <strong>APPROVE AR-{request.id}</strong> or <strong>REJECT AR-{request.id}</strong>.</p>
<p><a href="{mailto}">Open a prefilled reply email</a></p>
</body></html>"""


def build_message(request: AbsentRequest, settings: Settings) -> EmailMessage:
    message = EmailMessage()
    message["To"] = request.manager_email
    message["From"] = settings.gmail_sender
    message["Subject"] = f"Absent request AR-{request.id} from {request.employee_name}"
    message.set_content(f"Reply APPROVE AR-{request.id} or REJECT AR-{request.id}.")
    message.add_alternative(build_html(request, settings), subtype="html")
    return message


def encode_message(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
