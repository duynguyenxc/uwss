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


