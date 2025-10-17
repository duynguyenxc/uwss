from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy import select

from ..store import create_sqlite_engine, Document


def sha256_bytes(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def try_doi_pdf(doi: str, contact_email: Optional[str]) -> Optional[bytes]:
	if not doi:
		return None
	headers = {
		"Accept": "application/pdf",
		"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1",
	}
	# Content negotiation via doi.org
	url = f"https://doi.org/{doi}"
	resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
	if resp.status_code == 200 and "application/pdf" in resp.headers.get("Content-Type", ""):
		return resp.content
	return None


def download_with_retries(url: str, headers: dict, attempts: int = 3, backoff: float = 1.5) -> Optional[bytes]:
	delay = 1.0
	for i in range(attempts):
		try:
			resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
			if resp.status_code == 200 and resp.content:
				return resp.content
		except Exception:
			pass
		time.sleep(delay)
		delay *= backoff
	return None


def advanced_fetch_pdfs(db_path: Path, out_dir: Path, limit: int, contact_email: Optional[str]) -> int:
	"""Fetch PDFs using DOI content-negotiation first, then fallback to source_url with retries.
	Skips duplicates via checksum, records provenance fields, and updates local_path/status."""
	out_dir.mkdir(parents=True, exist_ok=True)
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	count = 0
	try:
		headers = {"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1"}
		q = session.execute(select(Document).where(Document.status != "fetched"))
		seen_hashes = set()
		for (doc,) in q:
			if count >= limit:
				break
			content: Optional[bytes] = None
			# Try DOI-based PDF
			content = try_doi_pdf(doc.doi or "", contact_email) or None
			# Fallback to source_url
			if content is None and doc.source_url:
				content = download_with_retries(doc.source_url, headers=headers)
			if not content:
				continue
			hashv = sha256_bytes(content)
			if hashv in seen_hashes:
				continue
			seen_hashes.add(hashv)
			# Save file
			ext = ".pdf"
			name = (doc.doi or doc.title or f"doc_{doc.id}").replace("/", "_")[:200]
			path = out_dir / f"{name}{ext}"
			with open(path, "wb") as f:
				f.write(content)
			doc.local_path = str(path)
			doc.status = "fetched"
			doc.file_size = path.stat().st_size
			count += 1
		session.commit()
		return count
	finally:
		session.close()


