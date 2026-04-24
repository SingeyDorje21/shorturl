from datetime import datetime, timedelta, timezone

from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


def _default_active_till() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=30)


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    short_code: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    original_url: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)

    # Always store as UTC-aware datetime
    active_till: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_default_active_till,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_opened_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<URL {self.short_code} -> {self.original_url}>"
