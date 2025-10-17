from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import select

from ..store import create_sqlite_engine, Document


def _first_n_chars(text: str, n: int = 500) -> str:
	if not text:
		return ""
	return (text[:n] + "…") if len(text) > n else text


def extract_text_excerpt(db_path: Path, limit: int = 20) -> int:
	"""Stub: populate text_excerpt using existing abstract/title for quick preview.
	Later can be replaced with PDF/HTML parsing.
	"""
	engine, SessionLocal = create_sqlite_engine(db_path)
	s = SessionLocal()
	try:
		count = 0
		for (doc,) in s.execute(select(Document)):
			if count >= limit:
				break
			if getattr(doc, "text_excerpt", None):
				continue
			text = (doc.abstract or "") or (doc.title or "")
			if not text:
				continue
			doc.text_excerpt = _first_n_chars(text, 600)
			s.add(doc)
			count += 1
		s.commit()
		return count
	finally:
		s.close()
