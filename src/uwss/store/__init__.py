from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
	pass


class Document(Base):
	__tablename__ = "documents"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	source_url: Mapped[str] = mapped_column(String(1000))
	doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	title: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
	authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of author names
	venue: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
	open_access: Mapped[bool] = mapped_column(Boolean, default=False)
	abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	local_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
	keywords_found: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of matched keywords
	relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	status: Mapped[str] = mapped_column(String(40), default="not_fetched")

	# provenance
	fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
	http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	extractor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	license: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


def create_sqlite_engine(db_path: Path) -> tuple:
	engine = create_engine(f"sqlite:///{db_path}", future=True)
	SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
	return engine, SessionLocal


def init_db(db_path: Path) -> None:
	engine, _ = create_sqlite_engine(db_path)
	Base.metadata.create_all(engine)

