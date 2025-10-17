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
		kw_escaped = re.escape(kw)
		patterns.append(re.compile(rf"\b{kw_escaped}\b", re.IGNORECASE))
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
			text = (doc.abstract or "") + "\n" + (doc.title or "")
			score = compute_keyword_score(text, patterns)
			doc.relevance_score = float(score)
			updated += 1
		session.commit()
		return updated
	finally:
		session.close()


