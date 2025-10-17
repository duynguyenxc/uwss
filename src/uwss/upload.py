from __future__ import annotations

from pathlib import Path
from typing import Optional
import os

import boto3
from botocore.config import Config as BotoConfig

from .store import create_sqlite_engine, Document
from sqlalchemy import select


def upload_files_to_s3(db_path: Path, files_dir: Path, bucket: str, prefix: str = "uwss/", region: Optional[str] = None) -> int:
	"""
	Upload downloaded files referenced by Document.local_path to S3.
	Skips files that are missing locally. Uses key: prefix + basename(local_path).
	"""
	s3 = boto3.client("s3", region_name=region, config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}))
	engine, SessionLocal = create_sqlite_engine(db_path)
	s = SessionLocal()
	count = 0
	try:
		q = s.execute(select(Document).where((Document.local_path != None) & (Document.local_path != "")))
		for (doc,) in q:
			p = Path(doc.local_path)
			if not p.is_absolute():
				p = files_dir / p
			if not p.exists():
				continue
			key = prefix.rstrip("/") + "/" + p.name
			s3.upload_file(str(p), bucket, key)
			count += 1
		return count
	finally:
		s.close()


