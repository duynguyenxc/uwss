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
	p_openalex.add_argument("--keywords-file", default=None, help="Optional path to a newline-delimited keywords file")
	p_openalex.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_openalex.add_argument("--max", type=int, default=100, help="Max records to fetch")

	def _cmd_openalex(args: argparse.Namespace) -> int:
		from .discovery import iter_openalex_results
		from .store import create_sqlite_engine, Document, Base
		import json
		
		data = load_config(Path(args.config))
		validate_config(data)
		keywords = data["domain_keywords"]
		if args.keywords_file:
			keywords = [k.strip() for k in Path(args.keywords_file).read_text(encoding="utf-8").splitlines() if k.strip()]
		contact_email = data.get("contact_email")
		user_agent = data.get("user_agent")
		year_filter = data.get("year_filter")
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		Base.metadata.create_all(engine)
		session = SessionLocal()
		inserted = 0
		try:
			for item in iter_openalex_results(keywords, year_filter, max_records=args.max, contact_email=contact_email, user_agent=user_agent):
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
						source="openalex",
						topic=", ".join(keywords[:3]) if keywords else None,
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
	p_crossref.add_argument("--keywords-file", default=None)
	p_crossref.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_crossref.add_argument("--max", type=int, default=100)

	def _cmd_crossref(args: argparse.Namespace) -> int:
		from .discovery import iter_crossref_results
		from .store import create_sqlite_engine, Document, Base
		import json

		data = load_config(Path(args.config))
		validate_config(data)
		keywords = data["domain_keywords"]
		if args.keywords_file:
			keywords = [k.strip() for k in Path(args.keywords_file).read_text(encoding="utf-8").splitlines() if k.strip()]
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
						source="crossref",
						topic=", ".join(keywords[:3]) if keywords else None,
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

	# discover-arxiv
	p_arxiv = sub.add_parser("discover-arxiv", help="Fetch candidate metadata from arXiv")
	p_arxiv.add_argument("--config", default=str(Path("config") / "config.yaml"))
	p_arxiv.add_argument("--keywords-file", default=None)
	p_arxiv.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_arxiv.add_argument("--max", type=int, default=50)

	def _cmd_arxiv(args: argparse.Namespace) -> int:
		from .discovery import iter_arxiv_results
		from .store import create_sqlite_engine, Document, Base
		import json
		data = load_config(Path(args.config))
		validate_config(data)
		keywords = data["domain_keywords"]
		if args.keywords_file:
			keywords = [k.strip() for k in Path(args.keywords_file).read_text(encoding="utf-8").splitlines() if k.strip()]
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		Base.metadata.create_all(engine)
		session = SessionLocal()
		inserted = 0
		try:
			for item in iter_arxiv_results(keywords, max_records=args.max):
				title = item.get("title")
				pdf_link = item.get("pdf_link")
				year = None
				pub = item.get("published")
				if pub and len(pub) >= 4:
					year = int(pub[:4])
				authors = item.get("authors") or []
				# Deduplicate by title
				exists = None
				if title:
					exists = session.query(Document).filter(Document.title == title).first()
				if exists:
					continue
				doc = Document(
					source_url=pdf_link or item.get("id", ""),
					doi=None,
					title=title,
					authors=json.dumps(authors),
					venue="arXiv",
					year=year,
					open_access=True if pdf_link else False,
					abstract=item.get("summary") or "",
					status="metadata_only",
					source="arxiv",
					topic=", ".join(keywords[:3]) if keywords else None,
				)
				session.add(doc)
				inserted += 1
			session.commit()
			console.print(f"[green]Inserted {inserted} arXiv records into {args.db}[/green]")
			return 0
		except Exception as e:
			session.rollback()
			console.print(f"[red]Discovery failed:[/red] {e}")
			return 1
		finally:
			session.close()

	p_arxiv.set_defaults(func=_cmd_arxiv)

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
	p_export.add_argument("--oa-only", action="store_true")
	p_export.add_argument("--sort", choices=["relevance", "year"], default="relevance")
	# skip missing-core records (no title and no doi)
	p_export.add_argument("--skip-missing-core", action="store_true")

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
				if args.skip_missing_core and (not d.title and not d.doi):
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
					"source": d.source,
					"oa_status": d.oa_status,
					"topic": d.topic,
					"checksum_sha256": getattr(d, "checksum_sha256", None),
				})
			# OA filter
			if args.oa_only:
				rows = [r for r in rows if r.get("open_access")]
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

	# fetch: enrich OA + download
	p_fetch = sub.add_parser("fetch", help="Enrich OA (Unpaywall) then download files")
	p_fetch.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_fetch.add_argument("--outdir", default=str(Path("data") / "files"))
	p_fetch.add_argument("--limit", type=int, default=10)
	p_fetch.add_argument("--config", default=str(Path("config") / "config.yaml"))

	def _cmd_fetch(args: argparse.Namespace) -> int:
		from .crawl import download_open_links, enrich_open_access_with_unpaywall
		data = load_config(Path(args.config))
		contact_email = data.get("contact_email")
		enriched = enrich_open_access_with_unpaywall(Path(args.db), contact_email=contact_email, limit=200)
		console.print(f"[blue]Enriched OA via Unpaywall: {enriched}[/blue]")
		n = download_open_links(Path(args.db), Path(args.outdir), limit=args.limit, contact_email=contact_email)
		console.print(f"[green]Downloaded {n} files[/green]")
		return 0

	p_fetch.set_defaults(func=_cmd_fetch)

	# crawl-seeds (Scrapy wrapper)
	p_crawl = sub.add_parser("crawl-seeds", help="Crawl seed URLs using Scrapy and store candidates")
	p_crawl.add_argument("--seeds", required=True, help="Comma-separated seed URLs")
	p_crawl.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_crawl.add_argument("--max-pages", type=int, default=10)
	p_crawl.add_argument("--keywords-file", default=None)

	def _cmd_crawl(args: argparse.Namespace) -> int:
		# Run seed_spider via Scrapy's CrawlerProcess programmatically
		try:
			from scrapy.crawler import CrawlerProcess
			from .crawl.scrapy_project.spiders.seed_spider import SeedSpider
			from .crawl.scrapy_project import settings as uwss_settings
			process = CrawlerProcess(settings={
				"ROBOTSTXT_OBEY": True,
				"DOWNLOAD_DELAY": 1.0,
				"CONCURRENT_REQUESTS_PER_DOMAIN": 2,
				"DEFAULT_REQUEST_HEADERS": {
					"User-Agent": "uwss/0.1 (respect robots)"
				},
			})
			keywords_csv = None
			if args.keywords_file:
				keywords_csv = ",".join([k.strip() for k in Path(args.keywords_file).read_text(encoding="utf-8").splitlines() if k.strip()])
			process.crawl(SeedSpider, start_urls=args.seeds, db_path=args.db, max_pages=args.max_pages, keywords=keywords_csv)
			process.start()
			console.print("[green]Seed crawl completed[/green]")
			return 0
		except Exception as e:
			console.print(f"[red]Seed crawl failed:[/red] {e}")
			return 1

	p_crawl.set_defaults(func=_cmd_crawl)

	# stats
	p_stats = sub.add_parser("stats", help="Show dataset statistics (counts, OA ratio, by source/year)")
	p_stats.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_stats.add_argument("--json-out", default=None)

	def _cmd_stats(args: argparse.Namespace) -> int:
		from sqlalchemy import select, func
		from .store import create_sqlite_engine, Document
		import json
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		s = SessionLocal()
		try:
			stats = {}
			# totals
			total = s.execute(select(func.count(Document.id))).scalar() or 0
			stats["total"] = total
			# oa
			oa = s.execute(select(func.count(Document.id)).where(Document.open_access == True)).scalar() or 0
			stats["open_access"] = oa
			# by source
			rows = s.execute(select(Document.source, func.count(Document.id)).group_by(Document.source)).all()
			stats["by_source"] = {str(k): v for k, v in rows}
			# by year
			years = s.execute(select(Document.year, func.count(Document.id)).where(Document.year != None).group_by(Document.year)).all()
			stats["by_year"] = {int(k): v for k, v in years if k is not None}
			console.print(stats)
			if args.json_out:
				Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
				Path(args.json_out).write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
				console.print(f"[green]Saved stats to {args.json_out}[/green]")
			return 0
		finally:
			s.close()

	p_stats.set_defaults(func=_cmd_stats)

	# validate
	p_val = sub.add_parser("validate", help="Validate data quality: duplicates, missing fields, invalid years, broken files")
	p_val.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))
	p_val.add_argument("--json-out", default=None)

	def _cmd_validate(args: argparse.Namespace) -> int:
		from sqlalchemy import select, func
		from .store import create_sqlite_engine, Document
		import json, os
		engine, SessionLocal = create_sqlite_engine(Path(args.db))
		s = SessionLocal()
		issues = {"dup_doi": [], "dup_title": [], "missing_core": [], "invalid_year": [], "missing_files": []}
		try:
			# dup doi
			dup_doi = s.execute(select(Document.doi, func.count(Document.id)).where(Document.doi != None).group_by(Document.doi).having(func.count(Document.id) > 1)).all()
			issues["dup_doi"] = [{"doi": str(k), "count": int(c)} for (k, c) in dup_doi]
			# dup title (case-insensitive)
			dup_title = s.execute(select(func.lower(Document.title), func.count(Document.id)).where(Document.title != None).group_by(func.lower(Document.title)).having(func.count(Document.id) > 1)).all()
			issues["dup_title"] = [{"title": str(k), "count": int(c)} for (k, c) in dup_title]
			# missing core fields
			rows = s.execute(select(Document.id, Document.title, Document.doi)).all()
			for _id, title, doi in rows:
				if not (title or doi):
					issues["missing_core"].append(int(_id))
			# invalid year
			rows = s.execute(select(Document.id, Document.year)).all()
			for _id, year in rows:
				if year is not None and (year < 1900 or year > 2100):
					issues["invalid_year"].append(int(_id))
			# missing files
			rows = s.execute(select(Document.id, Document.local_path)).all()
			for _id, p in rows:
				if p and not os.path.exists(p):
					issues["missing_files"].append(int(_id))
			console.print(issues)
			if args.json_out:
				Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
				Path(args.json_out).write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")
				console.print(f"[green]Saved validation to {args.json_out}[/green]")
			return 0
		finally:
			s.close()

	p_val.set_defaults(func=_cmd_validate)

	# dedupe-resolve
	p_dedupe = sub.add_parser("dedupe-resolve", help="Resolve duplicates (DOI/title) and keep best record")
	p_dedupe.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))

	def _cmd_dedupe(args: argparse.Namespace) -> int:
		from .clean import resolve_duplicates
		res = resolve_duplicates(Path(args.db))
		console.print(res)
		return 0

	p_dedupe.set_defaults(func=_cmd_dedupe)

	# normalize-metadata
	p_norm = sub.add_parser("normalize-metadata", help="Normalize authors/venue/title/doi formatting")
	p_norm.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))

	def _cmd_norm(args: argparse.Namespace) -> int:
		from .clean import normalize_metadata
		n = normalize_metadata(Path(args.db))
		console.print(f"[green]Normalized {n} records[/green]")
		return 0

	p_norm.set_defaults(func=_cmd_norm)

	# backfill-source
	p_bfs = sub.add_parser("backfill-source", help="Backfill missing Document.source from URL/venue")
	p_bfs.add_argument("--db", default=str(Path("data") / "uwss.sqlite"))

	def _cmd_bfs(args: argparse.Namespace) -> int:
		from .clean import backfill_source
		n = backfill_source(Path(args.db))
		console.print(f"[green]Backfilled source for {n} records[/green]")
		return 0

	p_bfs.set_defaults(func=_cmd_bfs)

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


