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


