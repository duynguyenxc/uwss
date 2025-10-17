from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Set

from sqlalchemy import select

from ..store import create_sqlite_engine, Document


def _tokenize(text: str) -> List[str]:
	if not text:
		return []
	return re.findall(r"[a-z0-9]+", text.lower())


def _bigrams(tokens: List[str]) -> List[str]:
	return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens)-1)] if len(tokens) > 1 else []


def _build_keyword_lexicon(keywords: Iterable[str]) -> Dict[str, Set[str]]:
	uni: Set[str] = set()
	bi: Set[str] = set()
	phrases: List[str] = []
	for kw in keywords:
		phrases.append(kw)
		kt = _tokenize(kw)
		uni.update(kt)
		bi.update(_bigrams(kt))
	return {"uni": uni, "bi": bi, "phrases": set(phrases)}


def _score_text(tokens: List[str], bi_tokens: List[str], kw_uni: Set[str], kw_bi: Set[str]) -> float:
	if not tokens:
		return 0.0
	uni_hits = len(set(tokens) & kw_uni)
	bi_hits = len(set(bi_tokens) & kw_bi)
	# Combine hits with higher weight for bigrams; normalize by sqrt length to reduce bias
	raw = uni_hits + 2.0 * bi_hits
	norm = max(1.0, (len(tokens) ** 0.5))
	return raw / norm


def score_documents(db_path: Path, keywords: List[str], min_score: float = 0.0) -> int:
	engine, SessionLocal = create_sqlite_engine(db_path)
	session = SessionLocal()
	try:
		lex = _build_keyword_lexicon(keywords)
		kw_uni, kw_bi = lex["uni"], lex["bi"]
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
			# tokenize
			tokens_title = _tokenize(doc.title or "")
			bigrams_title = _bigrams(tokens_title)
			tokens_abs = _tokenize(doc.abstract or "")
			bigrams_abs = _bigrams(tokens_abs)
			# scores
			s_title = _score_text(tokens_title, bigrams_title, kw_uni, kw_bi)
			s_abs = _score_text(tokens_abs, bigrams_abs, kw_uni, kw_bi)
			# weight title higher
			score = min(1.0, 0.8 * s_title + 0.2 * s_abs)
			doc.relevance_score = float(score)
			# keywords_found: include phrases whose any token appears (or bigram present)
			found = []
			text_uni = set(tokens_title) | set(tokens_abs)
			text_bi = set(bigrams_title) | set(bigrams_abs)
			for phrase in lex["phrases"]:
				ptoks = set(_tokenize(phrase))
				pbis = set(_bigrams(list(ptoks)))
				if (ptoks & text_uni) or (pbis & text_bi):
					found.append(phrase)
			doc.keywords_found = json.dumps(sorted(set(found)))
			updated += 1
		session.commit()
		return updated
	finally:
		session.close()


