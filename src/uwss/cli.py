import argparse
import sys
from pathlib import Path
from typing import Any, Dict

import yaml
from rich.console import Console
from rich.table import Table


console = Console()


def load_config(config_path: Path) -> Dict[str, Any]:
	if not config_path.exists():
		raise FileNotFoundError(f"Config not found: {config_path}")
	with config_path.open("r", encoding="utf-8") as f:
		data = yaml.safe_load(f) or {}
	return data


def validate_config(data: Dict[str, Any]) -> None:
	required_keys = [
		"domain_keywords",
		"domain_sources",
		"max_depth",
		"file_types",
	]
	missing = [k for k in required_keys if k not in data]
	if missing:
		raise ValueError(f"Missing required config keys: {', '.join(missing)}")
	if not isinstance(data["domain_keywords"], list) or not data["domain_keywords"]:
		raise ValueError("domain_keywords must be a non-empty list")
	if not isinstance(data["domain_sources"], list) or not data["domain_sources"]:
		raise ValueError("domain_sources must be a non-empty list")
	if not isinstance(data["file_types"], list) or not data["file_types"]:
		raise ValueError("file_types must be a non-empty list")


def cmd_config_validate(args: argparse.Namespace) -> int:
	config_path = Path(args.config)
	try:
		data = load_config(config_path)
		validate_config(data)
		# Pretty print a brief summary
		table = Table(title="UWSS Config Summary")
		table.add_column("Field")
		table.add_column("Value")
		table.add_row("config_path", str(config_path))
		table.add_row("#domain_keywords", str(len(data.get("domain_keywords", []))))
		table.add_row("#domain_sources", str(len(data.get("domain_sources", []))))
		table.add_row("max_depth", str(data.get("max_depth", "")))
		table.add_row("file_types", ", ".join(map(str, data.get("file_types", []))))
		if "year_filter" in data:
			table.add_row("year_filter", str(data["year_filter"]))
		console.print(table)
		console.print("[green]Config validation passed.[/green]")
		return 0
	except Exception as e:
		console.print(f"[red]Config validation failed:[/red] {e}")
		return 1


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(prog="uwss", description="Universal Web-Scraping System (UWSS)")
	sub = parser.add_subparsers(dest="command")

	# config-validate
	p_validate = sub.add_parser("config-validate", help="Validate and summarize a config.yaml")
	p_validate.add_argument("--config", default=str(Path("config") / "config.yaml"), help="Path to config.yaml")
	p_validate.set_defaults(func=cmd_config_validate)

	# db-init
	p_db = sub.add_parser("db-init", help="Initialize SQLite database schema")
	p_db.add_argument("--db", default=str(Path("data") / "uwss.sqlite"), help="Path to SQLite DB file")

	def _cmd_db(args: argparse.Namespace) -> int:
		from .store import init_db
		db_path = Path(args.db)
		db_path.parent.mkdir(parents=True, exist_ok=True)
		init_db(db_path)
		console.print(f"[green]Initialized DB:[/green] {db_path}")
		return 0

	p_db.set_defaults(func=_cmd_db)

	# db-migrate
	p_mig = sub.add_parser("db-migrate", help="Run lightweight DB migrations")
	p_mig.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))

	def _cmd_migrate(args: argparse.Namespace) -> int:
		from .store import migrate_db
		migrate_db(Path(args.db))
		console.print(f"[green]DB migration completed:[/green] {args.db}")
		return 0

	p_mig.set_defaults(func=_cmd_migrate)

	# discover-openalex
	p_openalex = sub.add_parser("discover-openalex", help="Fetch candidate metadata from OpenAlex")
	p_openalex.add_argument("--config", default=str(Path("config") / "config.yaml"))
	p_openalex.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_openalex.add_argument("--max", type=int, default=100, help="Max records to fetch")

	def _cmd_openalex(args: argparse.Namespace) -> int:
		from .discovery import iter_openalex_results
		from .store import create_sqlite_engine, Document, Base
		import json
		
		data = load_config(Path(args.config))
		validate_config(data)
		keywords = data["domain_keywords"]
		contact_email = data.get("contact_email")
		year_filter = data.get("year_filter")
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		Base.metadata.create_all(engine)
		session = SessionLocal()
		inserted = 0
		try:
			for item in iter_openalex_results(keywords, year_filter, max_records=args.max, contact_email=contact_email):
				doi = (item.get("doi") or "")
				title = item.get("title")
				abstract = (item.get("abstract") or "")
				source = item.get("primary_location", {})
				source_url = source.get("source", {}).get("host_organization_url") or source.get("landing_page_url") or ""
				open_access = bool(item.get("open_access", {}).get("is_oa"))
				year = None
				pub_date = item.get("publication_date")
				if pub_date and len(pub_date) >= 4:
					year = int(pub_date[:4])
				authors = [a.get("author", {}).get("display_name") for a in item.get("authorships", []) if a.get("author")]
				doc = Document(
					source_url=source_url or item.get("id", ""),
					doi=doi,
					title=title,
					authors=json.dumps([a for a in authors if a]),
					venue=(item.get("host_venue", {}) or {}).get("display_name"),
					year=year,
					open_access=open_access,
					abstract=abstract,
					status="metadata_only",
				)
				session.add(doc)
				inserted += 1
			session.commit()
			console.print(f"[green]Inserted {inserted} OpenAlex records into {args.db}[/green]")
			return 0
		except Exception as e:
			session.rollback()
			console.print(f"[red]Discovery failed:[/red] {e}")
			return 1
		finally:
			session.close()

	p_openalex.set_defaults(func=_cmd_openalex)

	# discover-crossref
	p_crossref = sub.add_parser("discover-crossref", help="Fetch candidate metadata from Crossref")
	p_crossref.add_argument("--config", default=str(Path("config") / "config.yaml"))
	p_crossref.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_crossref.add_argument("--max", type=int, default=100)

	def _cmd_crossref(args: argparse.Namespace) -> int:
		from .discovery import iter_crossref_results
		from .store import create_sqlite_engine, Document, Base
		import json

		data = load_config(Path(args.config))
		validate_config(data)
		keywords = data["domain_keywords"]
		year_filter = data.get("year_filter")
		contact_email = data.get("contact_email")
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		Base.metadata.create_all(engine)
		session = SessionLocal()
		inserted = 0
		try:
			for item in iter_crossref_results(keywords, year_filter, max_records=args.max, contact_email=contact_email):
				doi = (item.get("DOI") or "")
				title_list = item.get("title") or []
				title = title_list[0] if title_list else None
				abstract = (item.get("abstract") or "")
				link = ""
				for l in item.get("link", []) or []:
					if l.get("URL"):
						link = l["URL"]
						break
				authors = []
				for a in item.get("author", []) or []:
					name = " ".join([x for x in [a.get("given"), a.get("family")] if x])
					if name:
						authors.append(name)
				year = None
				issued = (item.get("issued") or {}).get("date-parts")
				if issued and issued[0] and len(issued[0]) > 0:
					year = int(issued[0][0])
				# Deduplicate by DOI or title
				exists = None
				if doi:
					exists = session.query(Document).filter(Document.doi == doi).first()
				if not exists and title:
					exists = session.query(Document).filter(Document.title == title).first()
				if exists:
					continue
				else:
					doc = Document(
						source_url=link or item.get("URL", ""),
						doi=doi,
						title=title,
						authors=json.dumps(authors),
						venue=(item.get("container-title") or [None])[0],
						year=year,
						open_access=False,
						abstract=abstract,
						status="metadata_only",
					)
					session.add(doc)
					inserted += 1
			session.commit()
			console.print(f"[green]Inserted {inserted} Crossref records into {args.db}[/green]")
			return 0
		except Exception as e:
			session.rollback()
			console.print(f"[red]Discovery failed:[/red] {e}")
			return 1
		finally:
			session.close()

	p_crossref.set_defaults(func=_cmd_crossref)

	# score-keywords
	p_score = sub.add_parser("score-keywords", help="Compute keyword relevance scores for documents in DB")
	p_score.add_argument("--config", default=str(Path("config") / "config.yaml"))
	p_score.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_score.add_argument("--min", type=float, default=0.0)

	def _cmd_score(args: argparse.Namespace) -> int:
		from .score import score_documents
		data = load_config(Path(args.config))
		validate_config(data)
		keywords = data["domain_keywords"]
		updated = score_documents(Path(args.db), keywords, args.min)
		console.print(f"[green]Scored {updated} documents[/green]")
		return 0

	p_score.set_defaults(func=_cmd_score)

	# export-jsonl / export-csv
	p_export = sub.add_parser("export", help="Export documents to JSONL or CSV")
	p_export.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_export.add_argument("--out", required=True, help="Output file path (.jsonl or .csv)")
	p_export.add_argument("--min-score", type=float, default=0.0)
	p_export.add_argument("--year-min", type=int, default=None)
	p_export.add_argument("--sort", choices=["relevance", "year"], default="relevance")

	def _cmd_export(args: argparse.Namespace) -> int:
		from sqlalchemy import select
		from .store import create_sqlite_engine, Document
		import json, csv
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		session = SessionLocal()
		try:
			q = session.execute(select(Document))
			rows = []
			for (d,) in q:
				if d.relevance_score is not None and d.relevance_score < args.min_score:
					continue
				if args.year_min and d.year and d.year < args.year_min:
					continue
				rows.append({
					"id": d.id,
					"source_url": d.source_url,
					"doi": d.doi,
					"title": d.title,
					"authors": d.authors,
					"venue": d.venue,
					"year": d.year,
					"relevance_score": d.relevance_score,
					"status": d.status,
					"local_path": d.local_path,
					"open_access": d.open_access,
					"license": d.license,
					"file_size": d.file_size,
				})
			# Sorting
			if args.sort == "relevance":
				rows.sort(key=lambda x: (x.get("relevance_score") or 0.0), reverse=True)
			elif args.sort == "year":
				rows.sort(key=lambda x: (x.get("year") or 0))
			out_path = Path(args.out)
			out_path.parent.mkdir(parents=True, exist_ok=True)
			if out_path.suffix.lower() == ".jsonl":
				with open(out_path, "w", encoding="utf-8") as f:
					for r in rows:
						f.write(json.dumps(r, ensure_ascii=False) + "\n")
			elif out_path.suffix.lower() == ".csv":
				if rows:
					with open(out_path, "w", encoding="utf-8", newline="") as f:
						writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
						writer.writeheader()
						writer.writerows(rows)
			else:
				raise ValueError("Unsupported extension. Use .jsonl or .csv")
			console.print(f"[green]Exported {len(rows)} records to {out_path}[/green]")
			return 0
		finally:
			session.close()

	p_export.set_defaults(func=_cmd_export)

	# download-open (basic)
	p_dl = sub.add_parser("download-open", help="Download open-access links for a small batch")
	p_dl.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_dl.add_argument("--outdir", default=str(Path("data") / "files"))
	p_dl.add_argument("--limit", type=int, default=5)
	p_dl.add_argument("--config", default=str(Path("config") / "config.yaml"))

	def _cmd_dl(args: argparse.Namespace) -> int:
		from .crawl import download_open_links, enrich_open_access_with_unpaywall
		data = load_config(Path(args.config))
		contact_email = data.get("contact_email")
		# Try to enrich OA first to improve hit rate
		enriched = enrich_open_access_with_unpaywall(Path(args.db), contact_email=contact_email, limit=50)
		console.print(f"[blue]Enriched OA via Unpaywall: {enriched}[/blue]")
		n = download_open_links(Path(args.db), Path(args.outdir), limit=args.limit, contact_email=contact_email)
		console.print(f"[green]Downloaded {n} files[/green]")
		return 0

	p_dl.set_defaults(func=_cmd_dl)

	return parser


def main(argv: Any = None) -> int:
	parser = build_parser()
	args = parser.parse_args(argv)
	if not hasattr(args, "func"):
		parser.print_help()
		return 0
	return int(args.func(args))


if __name__ == "__main__":
	sys.exit(main())


