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

---

## Latest improvements (feature branch: `feat/clean-output-download-scoring`)

### Summary
- Added provenance and cleanliness features without touching `main`.
- Output now includes optional provenance fields; downloader avoids overwrites; exports can skip missing-core; discovery uses domain keyword file; simple content excerpt extraction enabled.

### What changed
- Storage/provenance:
  - Added columns: `mime_type`, `text_excerpt`, `url_hash_sha1`, `checksum_sha256`.
  - `db-migrate` updated to create missing columns idempotently.
- Downloader (fetch/download-open):
  - Only downloads OA docs missing `local_path`.
  - File names include `_id{doc.id}` to avoid overwrites.
  - Captures `mime_type`, `fetched_at`, `checksum_sha256`, `url_hash_sha1`.
- Scoring:
  - Token + bigram matching; weighted title (0.8) over abstract (0.2).
  - Enables clean export with min-score=0.05.
- Scrapy spider:
  - Skip common non-content pages (Education/ACI University/Cooperating Organizations).
  - Require keyword match in title/body when keywords provided.
- Export:
  - New flags: `--skip-missing-core` and `--include-provenance`.
- Backfill & maintenance:
  - `backfill-source` to fill `source` (crossref/arxiv/web) from URL.
  - `delete-doc` to remove bad records by id.
- Content excerpt (stub):
  - `extract-text-excerpt` fills `text_excerpt` using PDF (pdfminer.six) / HTML (BeautifulSoup) when available.
- Domain keywords file:
  - Added `config/keywords_concrete.txt` from provided list for discovery.

### How to run this batch
```bash
# Use domain keyword file for discovery
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 25

# Score with improved weighting (token+bigram, title-focused)
python -m src.uwss.cli score-keywords --config config\config.yaml --db data\uwss.sqlite

# Clean
python -m src.uwss.cli delete-doc --db data\uwss.sqlite --id 91  # remove missing-core example
python -m src.uwss.cli dedupe-resolve --db data\uwss.sqlite     # deterministic dedupe

# Generate excerpts (PDF/HTML preferred, else abstract/title)
python -m src.uwss.cli extract-text-excerpt --db data\uwss.sqlite --limit 100

# Validate & stats
python -m src.uwss.cli validate --db data\uwss.sqlite --json-out data\export\validation.json
python -m src.uwss.cli stats --db data\uwss.sqlite --json-out data\export\stats.json

# Export (with provenance)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates.jsonl --min-score 0.0 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa.jsonl --min-score 0.0 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# Clean export profiles (min-score=0.05)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# Fetch a few OA files (no overwrite)
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 5 --config config\config.yaml
```

### Results snapshot
- Totals: `total=147`, `open_access=59`.
- Sources: `arxiv 40`, `crossref 55`, `web 49`, `scrapy 3`.
- Validation: no missing-core; a few similar titles remain (kept to avoid false merges).
- Exports: `candidates.jsonl` (147, skip-missing-core + provenance), `candidates_oa.jsonl` (59).
- Clean exports: `candidates_clean_005.jsonl` (86), `candidates_oa_clean_005.jsonl` (29).
- Fetch: downloaded 5 additional OA PDFs; files named with `_id{doc.id}`; provenance fields populated.

### Notes
- Fuzzy title dedupe was skipped to keep runtime short; can be re-enabled later if needed.
- Next: whitelist/blacklist for Scrapy via config; S3/RDS wiring; scheduled jobs.

