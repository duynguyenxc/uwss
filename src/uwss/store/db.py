from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import text as sql_text
from sqlalchemy.orm import sessionmaker

from .models import Base


def create_sqlite_engine(db_path: Path):
	engine = create_engine(f"sqlite:///{db_path}", future=True)
	SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
	return engine, SessionLocal


def init_db(db_path: Path) -> None:
	engine, _ = create_sqlite_engine(db_path)
	Base.metadata.create_all(engine)


def migrate_db(db_path: Path) -> None:
	engine, _ = create_sqlite_engine(db_path)
	with engine.connect() as conn:
		cols = conn.execute(sql_text("PRAGMA table_info(documents)")).fetchall()
		names = {c[1] for c in cols}
		if "file_size" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN file_size INTEGER"))
			conn.commit()
		if "source" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN source VARCHAR(50)"))
			conn.commit()
		if "oa_status" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN oa_status VARCHAR(50)"))
			conn.commit()
		if "topic" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN topic VARCHAR(100)"))
			conn.commit()
		if "checksum_sha256" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN checksum_sha256 VARCHAR(64)"))
			conn.commit()
		if "mime_type" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN mime_type VARCHAR(100)"))
			conn.commit()
		if "text_excerpt" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN text_excerpt TEXT"))
			conn.commit()
		if "url_hash_sha1" not in names:
			conn.execute(sql_text("ALTER TABLE documents ADD COLUMN url_hash_sha1 VARCHAR(40)"))
			conn.commit()


