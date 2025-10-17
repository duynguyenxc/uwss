# UWSS Progress Report

## What was added in this iteration
- Project skeleton with Git, venv, src layout (`src/uwss/`).
- Config validator CLI: `uwss config-validate --config config/config.yaml`.
- SQLite storage with SQLAlchemy (`data/uwss.sqlite`) and `db-init` command.
- Discovery modules:
  - OpenAlex (currently blocked by 403 in this environment).
  - OpenAlex updated: per-keyword small pages + custom user agent/email; still zero returns here (likely remote throttling), but logic enabled.
  - Crossref discovery working end-to-end.
  - Unpaywall enrichment to mark open-access and best OA URL.
  - arXiv discovery (Atom API via feedparser), adds OA PDF links when available.
- CLI commands:
  - `uwss db-init --db data/uwss.sqlite`
  - `uwss db-migrate --db data/uwss.sqlite`
  - `uwss discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 25`
  - `uwss score-keywords --config config/config.yaml --db data/uwss.sqlite`
  - `uwss export --db data/uwss.sqlite --out data/export/candidates.jsonl --min-score 0.05`
  - `uwss download-open --db data/uwss.sqlite --outdir data/files --limit 3 --config config/config.yaml`
  - `uwss fetch --db data/uwss.sqlite --outdir data/files --limit 10 --config config/config.yaml`
  - `uwss crawl-seeds --seeds https://example.com --db data/uwss.sqlite --max-pages 10`
  - With keyword filter: `uwss crawl-seeds --seeds https://example.com --db data/uwss.sqlite --max-pages 10 --keywords-file config/keywords_scrapy.txt`
  - `uwss stats --db data/uwss.sqlite --json-out data/export/stats.json`
  - `uwss validate --db data/uwss.sqlite --json-out data/export/validation.json`

## Data cleanliness improvements
- Normalized DOI/title/abstract; recorded `keywords_found` for explainability.
- Added fields: `source`, `oa_status`, `file_size`; migration idempotent via `db-migrate`.
- Export supports `--oa-only`, sorting, and year filters.
 - Added `stats` and `validate` commands to monitor quality and detect duplicates/missing fields.
 - Deduplication resolver merges duplicates (prefers OA, richer metadata, better source) and deletes redundant rows.
 - Normalization utility standardizes DOI/title/venue/authors formatting.
 - Refactored package layout: `store/models.py`, `store/db.py` for clarity and maintainability.

## How to run locally (Windows PowerShell)
```bash
# From repo root
.\.venv\Scripts\activate
pip install -r requirements.txt

# Validate config
python -m src.uwss.cli config-validate --config config\config.yaml

# Initialize database
python -m src.uwss.cli db-init --db data\uwss.sqlite

# Run DB migration (adds file_size, idempotent)
python -m src.uwss.cli db-migrate --db data\uwss.sqlite

# Run discovery (Crossref) – example 50 items
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --max 50

# Run discovery (arXiv) – example 15 items
python -m src.uwss.cli discover-arxiv --config config\config.yaml --db data\uwss.sqlite --max 15

# Score relevance (keyword frequency-based)
python -m src.uwss.cli score-keywords --config config\config.yaml --db data\uwss.sqlite

# Export candidates (adjust min-score as needed)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates.jsonl --min-score 0.0 --year-min 1995 --sort relevance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa.jsonl --min-score 0.0 --year-min 1995 --sort relevance --oa-only

# Enrich OA and download a few files
python -m src.uwss.cli download-open --db data\uwss.sqlite --outdir data\files --limit 3 --config config\config.yaml

# Or use combined fetch command
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 10 --config config\config.yaml
```

## Results
- Crossref discovery inserted 50 records into `data/uwss.sqlite` (table `documents`).
- arXiv discovery inserted 15 records.
- Fields populated: `source_url, doi, title, authors, venue, year, abstract (if provided), status=metadata_only`.
- Scoring updated `relevance_score` for 75 docs (includes previously inserted).
 - Export produced `data/export/candidates.jsonl` (90 items at threshold 0.0).
 - OA-only export produced `data/export/candidates_oa.jsonl` (20 items).
 - After normalization + dedupe: total 68 docs; OA 19; no duplicate DOIs; titles dup reduced (2 groups remaining pending manual review).
 - Scrapy refined to save only keyword-relevant pages (title/body match) to reduce noise.
 - AI topic run: +50 (Crossref) +25 (arXiv); total 143 docs; OA 59; exports: `ai_candidates.jsonl` (138), `ai_candidates_oa.jsonl` (44); downloaded 5 OA PDFs; `ai_stats.json` and `ai_validation.json` saved.

## Advanced Fetch (DOI Negotiation + Retries + Checksums)
- Design: Try DOI content-negotiation (`Accept: application/pdf` to `doi.org/{doi}`); if fails, fallback to `source_url` with retries and exponential backoff; compute SHA-256 checksum to skip duplicates; update provenance (`file_size`, `status`).
- Usage:
```bash
python -m src.uwss.cli fetch-advanced --db data\uwss.sqlite --outdir data\files --limit 10 --config config\config.yaml
```
- System design:
  - Module `crawl/advanced_fetch.py`: `try_doi_pdf`, `download_with_retries`, `advanced_fetch_pdfs`.
  - Idempotent: checksum-based dedupe; respects `status != fetched`.
  - Extensible: can add per-domain rules.
- Unpaywall enrichment updated 5 records as open-access; downloader saved 3 files to `data/files/`.
  - Provenance: http_status + file_size được lưu khi tải.

## Notes / Next steps
- Add export commands (JSONL/CSV) and keyword-based relevance scoring.
- Add downloader for open-access PDFs/HTML (respect robots/ToS).
- Retry OpenAlex with proper contact email/domain (403 currently).
- Extend config for multiple domains and plug-in architecture for sources.
 - Add deduplication by DOI/title, and improve ranking (semantic embeddings).
 - Add provenance fields on download (HTTP status, size, extractor).
 - Plan Dockerfile and AWS setup after local stabilization.

