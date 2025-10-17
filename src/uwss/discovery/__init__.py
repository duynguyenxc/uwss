from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Iterator

import requests
import feedparser


OPENALEX_BASE = "https://api.openalex.org/works"


def build_openalex_query(keywords: Iterable[str], year_filter: Optional[int] = None, per_page: int = 25, contact_email: Optional[str] = None) -> Dict[str, str]:
	search = " ".join(keywords)
	params: Dict[str, str] = {
		"search": search,
		"per_page": str(per_page),
		"sort": "relevance_score:desc",
	}
	if year_filter:
		params["from_publication_date"] = f"{year_filter}-01-01"
	if contact_email:
		params["mailto"] = contact_email
	return params


def fetch_openalex_page(params: Dict[str, str], cursor: Optional[str] = None, contact_email: Optional[str] = None, user_agent: Optional[str] = None) -> Dict:
	p = dict(params)
	if cursor:
		p["cursor"] = cursor
	headers = {}
	if contact_email:
		headers["User-Agent"] = user_agent or f"uwss/0.1 (+{contact_email})"
	resp = requests.get(OPENALEX_BASE, params=p, headers=headers, timeout=30)
	resp.raise_for_status()
	return resp.json()


def iter_openalex_results(keywords: Iterable[str], year_filter: Optional[int] = None, max_records: int = 100, contact_email: Optional[str] = None, user_agent: Optional[str] = None) -> Iterable[Dict]:
    # Safer strategy: iterate per keyword with small pages and cursors, stop early
    per_kw = max(10, min(25, max_records // max(1, len(list(keywords)))))
    for kw in keywords:
        params = build_openalex_query([kw], year_filter, per_page=per_kw, contact_email=contact_email)
        cursor = "*"
        got = 0
        while True:
            try:
                data = fetch_openalex_page(params, cursor, contact_email=contact_email, user_agent=user_agent)
            except Exception:
                break
            results = data.get("results", [])
            for item in results:
                yield item
                got += 1
                if got >= per_kw:
                    break
            if got >= per_kw:
                break
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break


# ------------------------ Crossref ------------------------
CROSSREF_BASE = "https://api.crossref.org/works"


def build_crossref_params(keywords: Iterable[str], year_filter: Optional[int], rows: int, offset: int, contact_email: Optional[str]) -> Dict[str, str]:
	query = " ".join(keywords)
	params: Dict[str, str] = {
		"query": query,
		"rows": str(rows),
		"offset": str(offset),
	}
	if year_filter:
		params["filter"] = f"from-pub-date:{year_filter}-01-01"
	return params


def fetch_crossref_page(params: Dict[str, str], contact_email: Optional[str]) -> Dict:
	headers = {
		"User-Agent": f"uwss/0.1 ({contact_email})" if contact_email else "uwss/0.1",
		"Accept": "application/json",
	}
	resp = requests.get(CROSSREF_BASE, params=params, headers=headers, timeout=30)
	resp.raise_for_status()
	return resp.json()


def iter_crossref_results(keywords: Iterable[str], year_filter: Optional[int] = None, max_records: int = 100, contact_email: Optional[str] = None) -> Iterator[Dict]:
	rows = 20
	offset = 0
	count = 0
	while count < max_records:
		params = build_crossref_params(keywords, year_filter, rows, offset, contact_email)
		data = fetch_crossref_page(params, contact_email)
		items = (data.get("message") or {}).get("items", [])
		if not items:
			break
		for item in items:
			yield item
			count += 1
			if count >= max_records:
				break
		offset += rows


# ------------------------ arXiv ------------------------
ARXIV_API = "http://export.arxiv.org/api/query"


def iter_arxiv_results(keywords: Iterable[str], max_records: int = 50) -> Iterator[Dict]:
	# arXiv query uses + for spaces; limit simple OR across keywords
	query_terms = [kw.replace(" ", "+") for kw in keywords]
	query = "+OR+".join(f"all:{q}" for q in query_terms)
	params = {
		"search_query": query,
		"start": 0,
		"max_results": max_records,
	}
	url = ARXIV_API + "?" + "&".join(f"{k}={v}" for k, v in params.items())
	feed = feedparser.parse(url)
	for entry in feed.entries:
		links = entry.get("links", [])
		pdf_link = None
		for l in links:
			if l.get("type") == "application/pdf":
				pdf_link = l.get("href")
				break
		yield {
			"id": entry.get("id"),
			"title": entry.get("title"),
			"summary": entry.get("summary"),
			"published": entry.get("published"),
			"authors": [a.get("name") for a in entry.get("authors", [])],
			"pdf_link": pdf_link,
		}

