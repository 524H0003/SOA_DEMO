from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class AbsentRequestCreate(BaseModel):
    absent_type: str = Field(min_length=2, max_length=80)
    start_date: date
    end_date: date
    reason: str = Field(min_length=5, max_length=2000)

    @model_validator(mode="after")
    def validate_date_order(self) -> "AbsentRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class AbsentRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    absent_type: str
    start_date: date
    end_date: date
    reason: str
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime
    decided_at: datetime | None


class PubSubMessage(BaseModel):
    data: str
    message_id: str | None = None


class PubSubEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str | None = None
