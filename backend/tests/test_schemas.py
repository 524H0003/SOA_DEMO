from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import AbsentRequestCreate
from app.config import Settings
from app.models import AbsentRequest
from app.services.email import build_decision_mailto, build_html, parse_decision
from app.services.gmail import _load_token


def test_absent_request_rejects_reversed_dates() -> None:
    with pytest.raises(ValidationError):
        AbsentRequestCreate(
            employee_name="Nguyen Van A",
            employee_email="employee@example.com",
            absent_type="Annual",
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 19),
            reason="Family event",
        )


def test_parse_decision_accepts_command_with_request_id() -> None:
    assert parse_decision("Re: Absent request AR-42\nAPPROVE AR-42") == ("approve", 42)


def test_parse_decision_rejects_unstructured_reply() -> None:
    assert parse_decision("Looks good, thanks") is None


def test_decision_links_send_to_system_mailbox() -> None:
    settings = Settings(gmail_sender="system@example.com", email_template_file="templates/absent_request.html")
    request = AbsentRequest(id=42, employee_name="Nguyen Van A", employee_email="employee@example.com", manager_email="manager@example.com", absent_type="Annual", start_date=date(2026, 9, 20), end_date=date(2026, 9, 21), reason="Family event")

    approve_link = build_decision_mailto(request, settings, "APPROVE")
    reject_link = build_decision_mailto(request, settings, "REJECT")

    assert approve_link.startswith("mailto:system%40example.com?")
    assert "APPROVE%20AR-42" in approve_link
    assert "REJECT%20AR-42" in reject_link


def test_html_template_contains_two_decision_buttons() -> None:
    settings = Settings(gmail_sender="system@example.com", email_template_file="templates/absent_request.html")
    request = AbsentRequest(id=42, employee_name="Nguyen Van A", employee_email="employee@example.com", manager_email="manager@example.com", absent_type="Annual", start_date=date(2026, 9, 20), end_date=date(2026, 9, 21), reason="Family event")

    content = build_html(request, settings)

    assert "Approve" in content
    assert "Disapprove" in content
    assert "mailto:system%40example.com" in content


def test_token_can_be_loaded_from_base64_env() -> None:
    import base64
    import json
    from pathlib import Path

    from google.oauth2.credentials import Credentials

    token = Credentials(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=["https://www.googleapis.com/auth/gmail.modify"],
    ).to_json()
    encoded = base64.b64encode(token.encode()).decode()
    settings = Settings(gmail_token_json_base64=encoded)

    loaded = _load_token(settings, Path("missing-token.json"))

    assert loaded is not None
    assert loaded.refresh_token == json.loads(token)["refresh_token"]
