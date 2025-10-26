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
from bs4 import BeautifulSoup


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


def _build_session() -> requests.Session:
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
	return s


def resolve_publisher_links(db_path: Path, limit: int = 50, contact_email: Optional[str] = None) -> int:
	"""Try to resolve publisher landing/PDF links starting from landing_url/source_url.
	- For Semantic Scholar pages: follow "View via Publisher" link
	- On publisher pages: detect PDF via common selectors and meta tags
	- If only DOI is present or pdf_url is a doi.org URL: follow redirects to get final landing/PDF
	"""
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	client = _build_session()
	updated = 0
	updated_pdf = 0
	try:
		q = session.execute(select(Document))
		for (doc,) in q:
			if updated >= limit:
				break
			landing = getattr(doc, "landing_url", None) or getattr(doc, "source_url", None)
			if not landing:
				continue
			# Skip if already has a clear PDF (non-doi)
			pdf_url = getattr(doc, "pdf_url", None)
			if pdf_url and ("doi.org" not in pdf_url.lower()):
				continue
			headers = {"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1"}
			try:
				r = client.get(landing, headers=headers, timeout=20, allow_redirects=True)
			except Exception:
				continue
			if r.status_code != 200:
				continue
			final_url = r.url or landing
			html = r.text or ""
			# If this is a Semantic Scholar page, find View via Publisher link
			if "semanticscholar.org" in final_url.lower():
				try:
					soup = BeautifulSoup(html, "html.parser")
					publisher_a = None
					for a in soup.find_all("a"):
						text = (a.get_text(" ", strip=True) or "").lower()
						if "view via publisher" in text or "publisher" in text:
							publisher_a = a
							break
					if publisher_a and publisher_a.get("href"):
						landing2 = publisher_a.get("href")
						# follow publisher page
						try:
							r2 = client.get(landing2, headers=headers, timeout=20, allow_redirects=True)
						except Exception:
							landing2 = None
						if r2 is not None and r2.status_code == 200:
							final_url = r2.url or landing2 or final_url
							html = r2.text or html
							doc.landing_url = final_url
							session.add(doc)
							updated += 1
				except Exception:
					pass

			# On final page, try to detect PDF
			try:
				soup = BeautifulSoup(html, "html.parser")
				# meta citation_pdf_url
				meta_pdf = soup.find("meta", attrs={"name": "citation_pdf_url"})
				if meta_pdf and meta_pdf.get("content"):
					doc.pdf_url = meta_pdf["content"].strip()
					session.add(doc)
					updated_pdf += 1
					continue
				# link rel alternate type application/pdf
				lnk = soup.find("link", attrs={"rel": "alternate", "type": "application/pdf"})
				if lnk and lnk.get("href"):
					doc.pdf_url = lnk["href"].strip()
					session.add(doc)
					updated_pdf += 1
					continue
				# any anchor to *.pdf
				for a in soup.find_all("a"):
					href = (a.get("href") or "").strip()
					txt = (a.get_text(" ", strip=True) or "").lower()
					if href.lower().endswith(".pdf") or "pdf" in txt:
						doc.pdf_url = href
						session.add(doc)
						updated_pdf += 1
						break
			except Exception:
				pass

			# If pdf_url is a DOI link or still empty but DOI present, try doi.org redirect
			doi = getattr(doc, "doi", None)
			if (not getattr(doc, "pdf_url", None)) and doi:
				try:
					rh = client.get(f"https://doi.org/{doi}", headers=headers, timeout=20, allow_redirects=True)
					if rh.status_code == 200:
						ct = rh.headers.get("Content-Type", "").lower()
						if "application/pdf" in ct or (rh.url or "").lower().endswith(".pdf"):
							doc.pdf_url = rh.url
							updated_pdf += 1
						else:
							doc.landing_url = rh.url or doc.landing_url
						session.add(doc)
				except Exception:
					pass

		session.commit()
		# simple structured log to stdout
		try:
			print(json.dumps({"uwss_event": "resolve_publisher_done_detail", "updated_landing": updated, "updated_pdf": updated_pdf}))
		except Exception:
			pass
		return max(updated, updated_pdf)
	finally:
		session.close()


