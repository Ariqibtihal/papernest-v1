from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doi: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    arxiv_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    pubmed_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    title_normalized: Mapped[str | None] = mapped_column(Text, index=True, nullable=True)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_open_access: Mapped[bool] = mapped_column(Boolean, default=False)
    landing_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    oa_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
