from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Iterator

import requests


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


def fetch_openalex_page(params: Dict[str, str], cursor: Optional[str] = None, contact_email: Optional[str] = None) -> Dict:
	p = dict(params)
	if cursor:
		p["cursor"] = cursor
	headers = {}
	if contact_email:
		headers["User-Agent"] = f"uwss/0.1 (+{contact_email})"
	resp = requests.get(OPENALEX_BASE, params=p, headers=headers, timeout=30)
	resp.raise_for_status()
	return resp.json()


def iter_openalex_results(keywords: Iterable[str], year_filter: Optional[int] = None, max_records: int = 100, contact_email: Optional[str] = None) -> Iterable[Dict]:
	params = build_openalex_query(keywords, year_filter, contact_email=contact_email)
	cursor = "*"
	count = 0
	while True:
		data = fetch_openalex_page(params, cursor, contact_email=contact_email)
		results = data.get("results", [])
		for item in results:
			yield item
			count += 1
			if count >= max_records:
				return
		cursor = data.get("meta", {}).get("next_cursor")
		if not cursor:
			return


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

