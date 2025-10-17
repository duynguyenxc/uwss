# UWSS Progress Report

## What was added in this iteration
- Project skeleton with Git, venv, src layout (`src/uwss/`).
- Config validator CLI: `uwss config-validate --config config/config.yaml`.
- SQLite storage with SQLAlchemy (`data/uwss.sqlite`) and `db-init` command.
- Discovery modules:
  - OpenAlex (currently blocked by 403 in this environment).
  - Crossref discovery working end-to-end.
- CLI commands:
  - `uwss db-init --db data/uwss.sqlite`
  - `uwss discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 25`

## How to run locally (Windows PowerShell)
```bash
# From repo root
.\.venv\Scripts\activate
pip install -r requirements.txt

# Validate config
python -m src.uwss.cli config-validate --config config\config.yaml

# Initialize database
python -m src.uwss.cli db-init --db data\uwss.sqlite

# Run discovery (Crossref)
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --max 25
```

## Results
- Crossref discovery inserted 25 records into `data/uwss.sqlite` (table `documents`).
- Fields populated: `source_url, doi, title, authors, venue, year, abstract (if provided), status=metadata_only`.

## Notes / Next steps
- Add export commands (JSONL/CSV) and keyword-based relevance scoring.
- Add downloader for open-access PDFs/HTML (respect robots/ToS).
- Retry OpenAlex with proper contact email/domain (403 currently).
- Extend config for multiple domains and plug-in architecture for sources.

