from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
	source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # crossref|arxiv|openalex|...
	topic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	# content summary and types
	mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	text_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	# provenance
	fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
	http_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	extractor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
	license: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
	file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	oa_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
	# file integrity
	checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
	# url hash for dedupe
	url_hash_sha1: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)


