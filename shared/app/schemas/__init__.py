from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime


class URLCreate(BaseModel):
    original_url: HttpUrl
    # Accept any positive number of days up to URL_ACTIVE_DAYS_MAX (enforced in service)
    active_duration_days: int | None = Field(default=None, ge=1)


class URLInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    original_url: str
    short_code: str
    is_active: bool
    clicks: int
    short_url: str
    active_till: datetime | None = None


class HealthResponse(BaseModel):
    service: str
    status: str = "ok"
    version: str
