from __future__ import annotations

import os
from pathlib import Path
import hashlib
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sqlalchemy import select
from datetime import datetime
import mimetypes

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
				doc.oa_status = best.get("host_type") or js.get("oa_status") or None
				# Prefer OA URL for download
				doc.source_url = best_url
				updated += 1
		session.commit()
		return updated
	finally:
		session.close()


def _sha256_bytes(data: bytes) -> str:
	h = hashlib.sha256()
	h.update(data)
	return h.hexdigest()


def download_open_links(db_path: Path, out_dir: Path, limit: int = 10, contact_email: Optional[str] = None) -> int:
	out_dir.mkdir(parents=True, exist_ok=True)
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	# Build a requests session with retries/backoff for robustness
	s = requests.Session()
	retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
	adapter = HTTPAdapter(max_retries=retry)
	s.mount("http://", adapter)
	s.mount("https://", adapter)
	count = 0
	try:
		# Only download documents that are open_access and missing local_path
		q = session.execute(select(Document).where((Document.open_access == True) & ((Document.local_path == None) | (Document.local_path == ""))))
		for (doc,) in q:
			if count >= limit:
				break
			url = doc.source_url
			if not url:
				continue
			headers = {"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1"}
			r = s.get(url, headers=headers, timeout=30, allow_redirects=True)
			if r.status_code != 200 or not r.content:
				continue
			content_type = r.headers.get("Content-Type", "")
			if not content_type:
				guess, _ = mimetypes.guess_type(url)
				content_type = guess or ""
			ext = ".pdf" if "application/pdf" in content_type or url.lower().endswith(".pdf") else ".html"
			base = safe_filename(doc.doi or doc.title or f"doc_{doc.id}") or f"doc_{doc.id}"
			# add id suffix to avoid name collision
			name = f"{base}_id{doc.id}{ext}"
			path = out_dir / name
			with open(path, "wb") as f:
				f.write(r.content)
			doc.local_path = str(path)
			doc.status = "fetched"
			# provenance
			doc.http_status = r.status_code
			doc.file_size = path.stat().st_size if path.exists() else None
			doc.mime_type = content_type or None
			doc.fetched_at = datetime.utcnow()
			try:
				doc.checksum_sha256 = _sha256_bytes(r.content)
			except Exception:
				doc.checksum_sha256 = None
			# url hash for dedupe/logging
			try:
				doc.url_hash_sha1 = hashlib.sha1((url or "").encode("utf-8")).hexdigest()
			except Exception:
				doc.url_hash_sha1 = None
			count += 1
		session.commit()
		return count
	finally:
		session.close()


