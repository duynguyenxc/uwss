from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import select

from ..store import create_sqlite_engine, Document
from bs4 import BeautifulSoup

def extract_from_html(path: Path) -> str:
	try:
		html = path.read_text(encoding="utf-8", errors="ignore")
		soup = BeautifulSoup(html, "html.parser")
		# prefer title + first paragraphs
		title = (soup.title.get_text(strip=True) if soup.title else "")
		paras = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p")[:10])
		content = (title + "\n" + paras).strip()
		return content
	except Exception:
		return ""

def extract_from_pdf(path: Path) -> str:
	# lightweight fallback using text extraction if pdfminer.six not installed at runtime
	try:
		from pdfminer.high_level import extract_text
		text = extract_text(str(path)) or ""
		return text
	except Exception:
		return ""


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
			# try from local file when available
			lp = getattr(doc, "local_path", None)
			if lp and Path(lp).exists():
				p = Path(lp)
				if p.suffix.lower() == ".pdf":
					text = extract_from_pdf(p) or text
				elif p.suffix.lower() in (".html", ".htm"):
					text = extract_from_html(p) or text
			if not text:
				continue
			doc.text_excerpt = _first_n_chars(text, 600)
			s.add(doc)
			count += 1
		s.commit()
		return count
	finally:
		s.close()
