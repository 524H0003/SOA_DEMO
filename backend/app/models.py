from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class AbsentStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AbsentRequest(Base):
    __tablename__ = "absent_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_name: Mapped[str] = mapped_column(String(120))
    employee_email: Mapped[str] = mapped_column(String(320))
    manager_email: Mapped[str] = mapped_column(String(320))
    absent_type: Mapped[str] = mapped_column(String(80))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=AbsentStatus.PENDING.value)
    gmail_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    decision_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class GmailSyncState(Base):
    __tablename__ = "gmail_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    last_history_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    watch_expiration: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
