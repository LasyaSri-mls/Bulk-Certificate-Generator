from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value


class GenerationRequest(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    issue_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    recipients: list[RecipientInput] = Field(min_length=1, max_length=5000)

    @field_validator("event_name")
    @classmethod
    def normalize_event_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Event name must not be blank")
        return value


class JobResponse(BaseModel):
    id: str
    event_name: str
    issue_date: str
    status: str
    total: int
    processed: int
    successful: int
    failed: int
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipientResponse(BaseModel):
    id: str
    name: str
    email: str
    status: str
    error_message: str | None = None
    download_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RecipientListResponse(BaseModel):
    job_id: str
    total: int
    recipients: list[RecipientResponse]
