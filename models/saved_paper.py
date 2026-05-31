from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedPaper(Base):
    __tablename__ = "saved_papers"
    __table_args__ = (
        # Composite index for the most common query: list by user ordered by save date
        Index("ix_saved_papers_user_id_saved_at", "user_id", "saved_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # user_id = NULL means anonymous/legacy; non-null means owned by a specific user
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    pubmed_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    venue: Mapped[str | None] = mapped_column(String(512), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_open_access: Mapped[bool] = mapped_column(Boolean, default=False)
    landing_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    oa_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    topics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    saved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
