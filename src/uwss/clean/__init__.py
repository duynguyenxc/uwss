from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy import select, func, delete

from ..store import create_sqlite_engine, Document


def _score_doc(doc: Document) -> int:
	# Higher is better
	score = 0
	if doc.open_access:
		score += 10
	if doc.abstract and len(doc.abstract) > 100:
		score += 5
	if doc.title:
		score += 2
	if doc.year:
		score += 1
	# Preference by source
	prefer = {"crossref": 5, "openalex": 4, "arxiv": 3, "scrapy": 1}
	score += prefer.get((doc.source or "").lower(), 0)
	return score


def _merge_docs(keep: Document, other: Document) -> None:
	# Fill missing fields on keep from other
	if not keep.title and other.title:
		keep.title = other.title
	if not keep.abstract and other.abstract:
		keep.abstract = other.abstract
	if not keep.venue and other.venue:
		keep.venue = other.venue
	if not keep.year and other.year:
		keep.year = other.year
	if not keep.authors and other.authors:
		keep.authors = other.authors
	if not keep.local_path and other.local_path:
		keep.local_path = other.local_path
	if not keep.file_size and other.file_size:
		keep.file_size = other.file_size
	if not keep.license and other.license:
		keep.license = other.license
	if not keep.oa_status and other.oa_status:
		keep.oa_status = other.oa_status
	if not keep.source and other.source:
		keep.source = other.source
	if other.open_access and not keep.open_access:
		keep.open_access = True


def resolve_duplicates(db_path) -> dict:
	engine, SessionLocal = create_sqlite_engine(db_path)
	s = SessionLocal()
	result = {"merged_by_doi": 0, "merged_by_title": 0, "deleted": 0}
	try:
		# By DOI
		groups = s.execute(
			select(Document.doi, func.count(Document.id))
			.where(Document.doi != None)
			.group_by(Document.doi)
			.having(func.count(Document.id) > 1)
		).all()
		for (doi, _cnt) in groups:
			recs: List[Document] = [d for (d,) in s.execute(select(Document).where(Document.doi == doi)).all()]
			if not recs:
				continue
			keep = max(recs, key=_score_doc)
			for doc in recs:
				if doc.id == keep.id:
					continue
				_merge_docs(keep, doc)
				s.delete(doc)
				result["deleted"] += 1
			s.add(keep)
			s.flush()
			result["merged_by_doi"] += 1

		# By title (lower) where DOI is null/empty
		groups = s.execute(
			select(func.lower(Document.title), func.count(Document.id))
			.where((Document.title != None) & ((Document.doi == None) | (Document.doi == "")))
			.group_by(func.lower(Document.title))
			.having(func.count(Document.id) > 1)
		).all()
		for (ltitle, _cnt) in groups:
			recs: List[Document] = [d for (d,) in s.execute(select(Document).where(func.lower(Document.title) == ltitle)).all()]
			if not recs:
				continue
			keep = max(recs, key=_score_doc)
			for doc in recs:
				if doc.id == keep.id:
					continue
				_merge_docs(keep, doc)
				s.delete(doc)
				result["deleted"] += 1
			s.add(keep)
			s.flush()
			result["merged_by_title"] += 1

		s.commit()
		return result
	finally:
		s.close()


def normalize_metadata(db_path) -> int:
	engine, SessionLocal = create_sqlite_engine(db_path)
	s = SessionLocal()
	try:
		count = 0
		for (doc,) in s.execute(select(Document)).all():
			changed = False
			if doc.doi:
				n = doc.doi.strip().lower()
				if n != doc.doi:
					doc.doi = n
					changed = True
			if doc.title:
				n = " ".join(doc.title.split())
				if n != doc.title:
					doc.title = n
					changed = True
			if doc.venue:
				n = " ".join(doc.venue.split())
				if n != doc.venue:
					doc.venue = n
					changed = True
			if doc.authors:
				try:
					arr = json.loads(doc.authors)
					if isinstance(arr, list):
						narr = [" ".join(str(a).split()) for a in arr]
						doc.authors = json.dumps(narr)
						changed = True
				except Exception:
					pass
			if changed:
				s.add(doc)
				count += 1
		s.commit()
		return count
	finally:
		s.close()


