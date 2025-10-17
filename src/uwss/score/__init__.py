from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from sqlalchemy import select

from ..store import create_sqlite_engine, Document


def compile_keywords(keywords: Iterable[str]) -> List[re.Pattern]:
	patterns: List[re.Pattern] = []
	for kw in keywords:
		# allow partial matches around separators/spaces; prefer word-ish boundaries
		kw_escaped = re.escape(kw)
		patterns.append(re.compile(rf"(^|\W){kw_escaped}($|\W)", re.IGNORECASE))
	return patterns


def compute_keyword_score(text: str, patterns: List[re.Pattern]) -> float:
	if not text:
		return 0.0
	count = 0
	for p in patterns:
		count += len(p.findall(text))
	# simple normalization by sqrt length to avoid long-text bias
	norm = max(1.0, len(text) ** 0.5)
	return min(1.0, count / (norm / 10.0))


def score_documents(db_path: Path, keywords: List[str], min_score: float = 0.0) -> int:
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	try:
		patterns = compile_keywords(keywords)
		q = session.execute(select(Document))
		updated = 0
		for (doc,) in q:
			# normalize basic fields for cleanliness
			if doc.doi:
				doc.doi = doc.doi.strip().lower()
			if doc.title:
				doc.title = doc.title.strip()
			if doc.abstract:
				doc.abstract = doc.abstract.strip()
			# weight title higher than abstract
			title_text = (doc.title or "")
			abstract_text = (doc.abstract or "")
			score_title = compute_keyword_score(title_text, patterns)
			score_abs = compute_keyword_score(abstract_text, patterns)
			score = min(1.0, 0.7 * score_title + 0.3 * score_abs)
			doc.relevance_score = float(score)
			# record matched keywords for explainability
			found = []
			for p, k in zip(patterns, keywords):
				if p.search(title_text or "") or p.search(abstract_text or ""):
					found.append(k)
			doc.keywords_found = json.dumps(sorted(set(found)))
			updated += 1
		session.commit()
		return updated
	finally:
		session.close()


