from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


@dataclass
class InputMessageMeta:
    platform: str = "gmail"
    client_name: Optional[str] = None
    client_mail: Optional[str] = None
    message: Optional[str] = None


@dataclass
class OutputMessageMeta:
    platform: str
    client_name: str
    client_mail: str
    message: str
    timestamp: datetime
    group: Optional[str] = None


# Pydantic Schemas for FastAPI request/response validation & serialization
class EmailParseRequest(BaseModel):
    """
    Flexible input payload. Can accept raw email content in `message`, `raw_message`,
    or pre-separated fields as in InputMessageMeta.
    """
    platform: str = Field(default="gmail", description="Source platform (e.g., gmail)")
    client_name: Optional[str] = Field(default=None, description="Sender / Client name")
    client_mail: Optional[str] = Field(default=None, description="Sender / Client email")
    message: Optional[str] = Field(default=None, description="Message body or raw email text")
    raw_message: Optional[str] = Field(default=None, description="Raw email text if message is used for something else")
    group: Optional[str] = Field(default=None, description="Optional override for group/category")


class EmailParseResponse(BaseModel):
    platform: str = Field(default="gmail", description="Source platform (e.g., gmail)")
    client_name: str = Field(..., description="Client name")
    client_mail: str = Field(..., description="Client email address")
    message: str = Field(..., description="Clean extracted message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of parsing")
    group: Optional[str] = Field(default=None, description="Form name or categorized group")
