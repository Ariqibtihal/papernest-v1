from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SearchAlert(Base):
    __tablename__ = "search_alerts"
    __table_args__ = (
        # Composite index for the most common query: list by user ordered by creation date
        Index("ix_search_alerts_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # user_id = NULL means anonymous/legacy; non-null means owned by a specific user
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    filters_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    frequency: Mapped[str] = mapped_column(String(16), default="daily")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
