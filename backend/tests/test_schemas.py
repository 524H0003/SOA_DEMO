from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import AbsentRequestCreate
from app.services.email import parse_decision


def test_absent_request_rejects_reversed_dates() -> None:
    with pytest.raises(ValidationError):
        AbsentRequestCreate(
            employee_name="Nguyen Van A",
            employee_email="employee@example.com",
            manager_email="manager@example.com",
            absent_type="Annual",
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 19),
            reason="Family event",
        )


def test_parse_decision_accepts_command_with_request_id() -> None:
    assert parse_decision("Re: Absent request AR-42\nAPPROVE AR-42") == ("approve", 42)


def test_parse_decision_rejects_unstructured_reply() -> None:
    assert parse_decision("Looks good, thanks") is None
