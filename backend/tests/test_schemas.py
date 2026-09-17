from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas import LeaveRequestCreate
from app.services.email import parse_decision


def test_leave_request_rejects_reversed_dates() -> None:
    with pytest.raises(ValidationError):
        LeaveRequestCreate(
            employee_name="Nguyen Van A",
            employee_email="employee@example.com",
            manager_email="manager@example.com",
            leave_type="Annual leave",
            start_date=date(2026, 9, 20),
            end_date=date(2026, 9, 19),
            reason="Family event",
        )


def test_parse_decision_accepts_command_with_request_id() -> None:
    assert parse_decision("Re: Leave request LR-42\nAPPROVE LR-42") == ("approve", 42)


def test_parse_decision_rejects_unstructured_reply() -> None:
    assert parse_decision("Looks good, thanks") is None
