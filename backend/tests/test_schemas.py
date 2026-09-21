from datetime import date
import uuid

import pytest
from pydantic import ValidationError

from app.schemas import AbsentRequestCreate
from app.config import Settings
from app.models import AbsentRequest, User
from app.services.email import build_decision_mailto, build_html, parse_decision
from app.services.gmail import _load_token


def test_absent_request_rejects_reversed_dates() -> None:
    with pytest.raises(ValidationError):
        AbsentRequestCreate(
            absent_type="Annual",
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 19),
            reason="Family event",
        )


def test_parse_decision_accepts_command_with_request_id() -> None:
    request_id = uuid.uuid4()
    assert parse_decision(f"Re: Absent request AR-{request_id}\nAPPROVE AR-{request_id}") == ("approve", request_id)


def test_parse_decision_rejects_unstructured_reply() -> None:
    assert parse_decision("Looks good, thanks") is None


def test_parse_decision_ignores_quoted_original_email() -> None:
    """Test that commands in quoted original email (mailto body) are ignored."""
    request_id = uuid.uuid4()
    # Simulate a reply where first line is "OK" but quoted text contains APPROVE command
    email_text = (
        f"Re: Absent request AR-{request_id}\n"
        f"OK\n"
        f"\n"
        f"On Mon, Sep 21, 2026 at 10:00 AM, System <system@example.com> wrote:\n"
        f"> APPROVE AR-{request_id}\n"
    )
    # Should return None because first non-empty line is "OK", not the command
    assert parse_decision(email_text) is None


def test_parse_decision_accepts_first_line_command() -> None:
    """Test that command on first non-empty line of reply is accepted."""
    request_id = uuid.uuid4()
    email_text = (
        f"Re: Absent request AR-{request_id}\n"
        f"APPROVE AR-{request_id}\n"
        f"\n"
        f"On Mon, Sep 21, 2026 at 10:00 AM, System <system@example.com> wrote:\n"
        f"> REJECT AR-{request_id}\n"
    )
    # Should match the first line "APPROVE" not the quoted "REJECT"
    assert parse_decision(email_text) == ("approve", request_id)


def test_decision_links_send_to_system_mailbox() -> None:
    settings = Settings(gmail_sender="system@example.com", email_template_file="templates/absent_request.html")
    request_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), username="Nguyen Van A", email="employee@example.com", hashed_password="hashed")
    request = AbsentRequest(
        id=request_id,
        employee_id=user.id,
        absent_type="Annual",
        start_date=date(2026, 9, 20),
        end_date=date(2026, 9, 21),
        reason="Family event",
    )
    request.user = user

    approve_link = build_decision_mailto(request, settings, "APPROVE")
    reject_link = build_decision_mailto(request, settings, "REJECT")

    assert approve_link.startswith("mailto:system@example.com?")
    assert f"APPROVE%20AR-{request_id}" in approve_link
    assert f"REJECT%20AR-{request_id}" in reject_link


def test_html_template_contains_two_decision_buttons() -> None:
    settings = Settings(gmail_sender="system@example.com", email_template_file="templates/absent_request.html")
    request_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), username="Nguyen Van A", email="employee@example.com", hashed_password="hashed")
    request = AbsentRequest(
        id=request_id,
        employee_id=user.id,
        absent_type="Annual",
        start_date=date(2026, 9, 20),
        end_date=date(2026, 9, 21),
        reason="Family event",
    )
    request.user = user

    content = build_html(request, settings)

    assert "Approve" in content
    assert "Disapprove" in content
    assert "mailto:system@example.com" in content


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
