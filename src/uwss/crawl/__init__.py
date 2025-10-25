from __future__ import annotations

import os
import json
import time
import random
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
from ..store.models import VisitedUrl


def safe_filename(s: str) -> str:
	return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in s)[:200]


def enrich_open_access_with_unpaywall(db_path: Path, contact_email: Optional[str] = None, limit: int = 50) -> int:
	"""Mark documents as open_access if Unpaywall reports OA and set source_url to best OA URL."""
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	# Session with retries/backoff and Retry-After respect
	s = requests.Session()
	retry = Retry(
		total=3,
		backoff_factor=0.5,
		status_forcelist=(429, 500, 502, 503, 504),
		respect_retry_after_header=True,
		allowed_methods=("GET",),
	)
	adapter = HTTPAdapter(max_retries=retry)
	s.mount("http://", adapter)
	s.mount("https://", adapter)

	metrics = {"unpaywall_ok": 0, "unpaywall_fail": 0, "unpaywall_429_5xx": 0}
	updated = 0
	try:
		q = session.execute(select(Document).where(Document.doi != None))
		for (doc,) in q:
			if updated >= limit:
				break
			if not doc.doi:
				continue
			url = f"https://api.unpaywall.org/v2/{doc.doi}?email={contact_email or 'example@example.com'}"
			r = s.get(url, timeout=30)
			if r.status_code != 200:
				metrics["unpaywall_fail"] += 1
				if r.status_code in (429, 500, 502, 503, 504):
					metrics["unpaywall_429_5xx"] += 1
					# Honor Retry-After if present
					ra = r.headers.get("Retry-After")
					if ra:
						try:
							wait = int(ra)
						except Exception:
							wait = 0
						if wait > 0:
							time.sleep(wait)
				continue
			js = r.json()
			is_oa = bool(js.get("is_oa"))
			best = js.get("best_oa_location") or {}
			best_pdf = best.get("url_for_pdf")
			best_html = best.get("url")
			if is_oa and (best_pdf or best_html):
				doc.open_access = True
				doc.oa_status = best.get("host_type") or js.get("oa_status") or None
				# license if available
				lic = best.get("license") or js.get("license")
				if lic:
					doc.license = lic
				# fill landing/pdf fields consistently without clobbering when already set
				if best_pdf:
					doc.pdf_url = best_pdf
				if best_html and not getattr(doc, "landing_url", None):
					doc.landing_url = best_html
				# keep source_url as-is; downloader prefers pdf_url
				updated += 1
				metrics["unpaywall_ok"] += 1
		session.commit()
		# Structured metrics log
		print(json.dumps({"uwss_event": "unpaywall_enrich_summary", "updated": updated, **metrics}))
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
	retry = Retry(
		total=3,
		backoff_factor=0.5,
		status_forcelist=(429, 500, 502, 503, 504),
		respect_retry_after_header=True,
		allowed_methods=("GET",),
	)
	adapter = HTTPAdapter(max_retries=retry)
	s.mount("http://", adapter)
	s.mount("https://", adapter)

	# Observability counters
	metrics = {
		"downloads_ok": 0,
		"downloads_fail": 0,
		"status_counts": {},
		"429_5xx_count": 0,
	}

	# Throttle config
	throttle_sec = float(os.getenv("UWSS_THROTTLE_SEC", "0"))
	jitter_max = float(os.getenv("UWSS_JITTER_SEC", "0.2"))
	last_request_per_host: dict[str, float] = {}
	count = 0
	try:
		# Only download documents that are open_access and missing local_path
		q = session.execute(select(Document).where((Document.open_access == True) & ((Document.local_path == None) | (Document.local_path == ""))))
		for (doc,) in q:
			if count >= limit:
				break
			# Prefer pdf_url if available; else landing/source_url
			url = getattr(doc, "pdf_url", None) or getattr(doc, "source_url", None)
			if not url:
				continue
			headers = {"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1"}
			# Per-host throttle + jitter
			host = None
			try:
				from urllib.parse import urlparse
				host = urlparse(url).netloc
			except Exception:
				host = None
			if host:
				last = last_request_per_host.get(host)
				if last is not None and throttle_sec > 0:
					elapsed = time.time() - last
					wait = max(0.0, throttle_sec - elapsed)
					if wait > 0:
						time.sleep(wait + random.uniform(0, jitter_max))
			r = s.get(url, headers=headers, timeout=30, allow_redirects=True)
			if host:
				last_request_per_host[host] = time.time()
			# Track status metrics
			metrics["status_counts"][str(r.status_code)] = metrics["status_counts"].get(str(r.status_code), 0) + 1
			if r.status_code in (429, 500, 502, 503, 504):
				metrics["429_5xx_count"] += 1
			# Non-OK responses
			if r.status_code != 200 or not r.content:
				metrics["downloads_fail"] += 1
				# Honor Retry-After if provided
				ra = r.headers.get("Retry-After")
				if ra:
					try:
						wait = int(ra)
					except Exception:
						wait = 0
					if wait > 0:
						time.sleep(wait)
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
			from datetime import datetime as _dt
			doc.fetched_at = _dt.utcnow()
			try:
				doc.checksum_sha256 = _sha256_bytes(r.content)
			except Exception:
				doc.checksum_sha256 = None
			# url hash for dedupe/logging
			try:
				doc.url_hash_sha1 = hashlib.sha1((url or "").encode("utf-8")).hexdigest()
			except Exception:
				doc.url_hash_sha1 = None
			# Mark URL visited in registry
			try:
				from datetime import datetime
				vu = VisitedUrl(url=url, last_seen=datetime.utcnow(), status=str(r.status_code))
				session.merge(vu)
			except Exception:
				pass
			count += 1
			metrics["downloads_ok"] += 1
		session.commit()
		# Structured metrics log
		print(json.dumps({"uwss_event": "download_summary", "downloaded": count, **metrics}))
		return count
	finally:
		session.close()


