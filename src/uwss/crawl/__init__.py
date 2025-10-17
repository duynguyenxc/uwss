from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy import select

from ..store import create_sqlite_engine, Document


def safe_filename(s: str) -> str:
	return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)[:200]


def enrich_open_access_with_unpaywall(db_path: Path, contact_email: Optional[str] = None, limit: int = 50) -> int:
	"""Mark documents as open_access if Unpaywall reports OA and set source_url to best OA URL."""
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	updated = 0
	try:
		q = session.execute(select(Document).where(Document.doi != None))
		for (doc,) in q:
			if updated >= limit:
				break
			if not doc.doi:
				continue
			url = f"https://api.unpaywall.org/v2/{doc.doi}?email={contact_email or 'example@example.com'}"
			r = requests.get(url, timeout=30)
			if r.status_code != 200:
				continue
			js = r.json()
			is_oa = bool(js.get("is_oa"))
			best = js.get("best_oa_location") or {}
			best_url = best.get("url_for_pdf") or best.get("url")
			if is_oa and best_url:
				doc.open_access = True
				# Prefer OA URL for download
				doc.source_url = best_url
				updated += 1
		session.commit()
		return updated
	finally:
		session.close()


def download_open_links(db_path: Path, out_dir: Path, limit: int = 10, contact_email: Optional[str] = None) -> int:
	out_dir.mkdir(parents=True, exist_ok=True)
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	count = 0
	try:
		q = session.execute(select(Document).where(Document.open_access == True))
		for (doc,) in q:
			if count >= limit:
				break
			url = doc.source_url
			if not url:
				continue
			headers = {"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1"}
			r = requests.get(url, headers=headers, timeout=30)
			if r.status_code != 200 or not r.content:
				continue
			ext = ".pdf" if "application/pdf" in r.headers.get("Content-Type", "") or url.lower().endswith(".pdf") else ".html"
			name = safe_filename(doc.doi or doc.title or f"doc_{doc.id}") or f"doc_{doc.id}"
			path = out_dir / f"{name}{ext}"
			with open(path, "wb") as f:
				f.write(r.content)
			doc.local_path = str(path)
			doc.status = "fetched"
			count += 1
		session.commit()
		return count
	finally:
		session.close()


