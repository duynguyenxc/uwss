# UWSS Progress Report

## Timeline / Milestones (high-level)
- Project setup (repo, venv, `src/uwss/`), SQLite + SQLAlchemy models, basic CLI.
- Discovery (Crossref, arXiv), export, stats/validate, deterministic dedupe and normalization.
- Provenance + downloader safety (no overwrite, unique filenames, checksums, mime), scoring with token+bigram + title weight, Scrapy whitelist/blacklist, content excerpt.
- Documentation improvements (`README.md`, `REPORT.md`), stable feature branch (`feat/clean-output-download-scoring`).
- Cloud preparation: Dockerfile, deploy guide, create `main-next`/`main-legacy` branches.
- Robustness & CI: retries/backoff + Retry-After, throttle+jitter, S3 upload CLI, Postgres DB URL helper, CI smoke workflow (`feat/cloud-ci-s3`).

## System Design (high-level)
- CLI Orchestrator (`src/uwss/cli.py`):
  - Commands map 1:1 to pipeline steps: config-validate, db-init/migrate, discover-*, score-keywords, normalize/dedupe, validate/stats, export, fetch, crawl-seeds, s3-upload.
  - Each command is small and composable; easy to schedule in cloud jobs.
- Storage Layer (`src/uwss/store/`):
  - SQLAlchemy models with SQLite by default, optional Postgres via `create_engine_from_url`.
  - Provenance fields kept on `documents` (http_status, file_size, mime_type, fetched_at, checksum_sha256, url_hash_sha1).
- Discovery Layer (`src/uwss/discovery/`):
  - Crossref/arXiv/OpenAlex helpers insert normalized metadata into DB.
  - Deterministic dedupe (DOI/title) keeps database clean.
- Scoring Layer (`src/uwss/score/`):
  - Token + bigram scoring with strong title weight produces meaningful `relevance_score` for filtering.
- Crawl/Fetch Layer (`src/uwss/crawl/`):
  - Scrapy seed spider with whitelist/blacklist reduces noise.
  - Downloader enforces safe filenames (`_id{doc.id}`), no overwrite, provenance capture, retries/backoff, throttle+jitter.
- Extract Layer (`src/uwss/extract/`):
  - Basic PDF/HTML text excerpt for preview; upgrade path to PyMuPDF if needed.
- Export Layer:
  - JSONL/CSV with optional provenance; full/OA/clean profiles to serve different consumers.
- Observability & CI:
  - JSON counters printed to stdout for CloudWatch ingestion; CI smoke checks on PRs/pushes.
- Cloud Integration:
  - Docker image, ECS Scheduled Tasks or Batch for recurring jobs, S3 for files, optional RDS for DB, CloudWatch for logs/alarms.

## From-scratch checklist (how to reproduce)
1) Python env
   - Create venv and install deps: `python -m venv .\.venv && .\.venv\Scripts\activate && pip install -r requirements.txt`
2) Config
   - Edit `config/config.yaml` (contact email, keywords, whitelist/blacklist). Run `config-validate`.
3) Database
   - `db-init` (first time) and `db-migrate` (idempotent). File at `data/uwss.sqlite`.
4) Discovery
   - Run `discover-crossref`/`discover-arxiv` with keywords file. Expect new rows in `documents` table.
5) Scoring & cleaning
   - `score-keywords`, `normalize-metadata`, `dedupe-resolve`.
6) Quality checks
   - `validate` (missing_core=0, dup_doi=0), `stats` (total/OA/by source/year).
7) Export
   - `export` JSONL (full/OA/clean with `--min-score 0.05`, optional `--include-provenance`).
8) Fetch
   - `fetch` with safe downloads, provenance, retries/backoff. Optional throttle via flags/ENV.
9) Optional S3
   - `s3-upload` to sync `data/files/` to S3.
10) Cloud
   - Build Docker; deploy to ECS Scheduled Tasks; stream logs to CloudWatch; set env/secrets.

## Detailed issues and fixes (selected)
- Missing dependency `rich` (ModuleNotFoundError)
  - Fix: `pip install -r requirements.txt`; keep `rich` pinned in requirements.
- Indentation/TabError and SyntaxError in several modules (`models.py`, `db.py`, `clean/__init__.py`, `score/__init__.py`, Scrapy spider)
  - Fix: Normalize indentation, remove stray `finally`, ensure consistent blocks; re-run lint/smoke.
- Fuzzy dedupe very slow (>30 min)
  - Decision: Skip by default; rely on deterministic dedupe; use `--min-score` for clean exports.
- Overwrite risk on downloads
  - Fix: Enforce unique filename suffix `_id{doc.id}`; only download when `local_path` is empty.
- Provenance gaps
  - Fix: Add `mime_type`, `text_excerpt`, `url_hash_sha1`, `checksum_sha256`; save `http_status`, `file_size`, `fetched_at` during download.
- Crawl noise
  - Fix: Scrapy whitelist domains + path blacklist from config; keyword filter in spider.
- Stability for network errors
  - Fix: HTTP retries/backoff with Retry-After, throttle+jitter, status counters.
- Binary artifacts accidentally committed
  - Fix: Remove PDFs from index; keep repo clean; prefer S3 for artifacts.

## Technology choices (simple rationale)
- Scrapy over Selenium: faster, polite, good for static/API pages; add browser automation only per-domain if needed.
- requests (sync) first: simpler to maintain; can switch to httpx (async) if high concurrency is required later.
- SQLAlchemy (SQLite local): clean schema/migration; easy to move to Postgres using URL helper.
- pdfminer.six + BeautifulSoup: pure Python, good baseline; optional PyMuPDF later for tricky PDFs.
- Docker: same runtime everywhere; easy ECS/Batch deploy.
- AWS (S3, ECS, RDS, CloudWatch): standard, durable storage; managed compute and DB; native logging/alarms.
- GitHub Actions: automatic smoke checks on PRs; prevent simple regressions.

## What output looks like (how to judge quality)
- `validation.json`: should show `missing_core=[]`, `dup_doi=[]`, limited `dup_title` groups.
- `stats.json`: healthy totals; OA count; distribution by source/year.
- Exports (`candidates*.jsonl`): meaningful `relevance_score`; clean profile smaller but more relevant; with provenance fields when enabled.
- `data/files/`: new files with `_id{doc.id}`; integrity via checksum; mime_type recorded.

## Risks and limitations
- Fuzzy dedupe disabled by default due to time cost; can enable for special runs.
- Basic excerpt extraction; PyMuPDF fallback to consider for tough PDFs (feature-flag).
- JS-heavy pages are out-of-scope unless whitelisted for browser rendering.

## Cloud readiness and ops
- Current state: Ready for pilot ECS Scheduled Task; logs as JSON counters to CloudWatch.
- Next: optional RDS Postgres; minimal CloudWatch alarms; per-domain throttling tune.

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

---

## New improvements (feature branch: `feat/cloud-ci-s3`)

### Summary
This iteration focuses on robustness, cloud integration, and developer workflow: retries during downloads, optional S3 uploads, a Postgres-ready DB URL helper, and a CI smoke workflow.

### What changed
- Download robustness: added retries/backoff (3 attempts, 0.5s backoff) for `fetch` HTTP requests. This reduces flakiness for transient 429/5xx/network issues.
- S3 upload command: new CLI `s3-upload` to push files from `data/files/` to `s3://<bucket>/<prefix>`, using `boto3` with standard retry settings.
- DB portability: new helper `create_engine_from_url(db_url)` to support Postgres (e.g., RDS) alongside local SQLite.
- CI workflow: added GitHub Actions smoke checks (install deps, import libs, parse CLI, help output) on PRs and feature pushes.

### Observability and rate-limit tuning (this iteration)
- Added structured counters/logs in downloader and Unpaywall enrichment:
  - `downloads_ok`, `downloads_fail`, `status_counts`, `429_5xx_count`, `unpaywall_ok`, `unpaywall_fail`.
  - Summary logs are emitted as JSON lines for easy CloudWatch ingestion.
- Respect `Retry-After` header on `429/5xx` and use exponential backoff with jitter.
- Per-host throttle + jitter, configurable via ENV or CLI flags:
  - ENV: `UWSS_THROTTLE_SEC`, `UWSS_JITTER_SEC`
  - CLI: `fetch --throttle-sec ... --jitter-sec ...`

#### How to verify quickly
```bash
# Example: run fetch with explicit throttle/jitter
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 3 --config config\config.yaml --throttle-sec 0.6 --jitter-sec 0.3
# Observe console JSON lines like:
{"uwss_event": "unpaywall_enrich_summary", "updated": 12, "unpaywall_ok": 12, "unpaywall_fail": 3, "unpaywall_429_5xx": 1}
{"uwss_event": "download_summary", "downloaded": 3, "downloads_ok": 3, "downloads_fail": 0, "status_counts": {"200": 3}, "429_5xx_count": 0}
```

### How to run (Windows PowerShell)
```bash
# Install new dependency
pip install -r requirements.txt

# Optional: Upload downloaded files to S3
python -m src.uwss.cli s3-upload --db data\uwss.sqlite --files-dir data\files --bucket YOUR_BUCKET --prefix uwss/ --region ap-southeast-1

# Example: retries are automatic when fetching
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 5 --config config\config.yaml
```

### Verification
- Fewer transient failures during `fetch` when network is unstable (observe logs/counts).
- Files appear in `s3://<bucket>/<prefix>` with the same filenames as in `data/files/`.
- CI runs on PRs to `main-next` and on `feat/**` pushes, ensuring environment and CLI parser remain healthy.

### Notes
- S3 credentials use standard AWS credential chain; for production use IAM roles/SSM/Secrets Manager.
- Postgres wiring is optional; use `create_engine_from_url` when moving DB to RDS.

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


## Comprehensive Review (simple English, detailed)

### 1) System status and pipeline
- The system is stable. The full pipeline runs end-to-end:
  1) Discover → 2) Score → 3) Clean (normalize + dedupe) → 4) Validate/Stats → 5) Export (with provenance) → 6) Fetch open-access files.
- No file overwrite. Downloaded files use a suffix `_id{doc.id}`.
- We save rich provenance for each file and record: `http_status`, `file_size`, `mime_type`, `fetched_at`, `checksum_sha256`, `url_hash_sha1`.
- Scrapy now has whitelist domains and blacklist paths from `config/config.yaml` to reduce noise.

### 2) All improvements done (summary)
- Storage & provenance: added `mime_type`, `text_excerpt`, `url_hash_sha1`, `checksum_sha256`; idempotent DB migration.
- Downloader: only downloads when `local_path` is empty; writes provenance; unique file names.
- Scoring: changed to token + bigram, stronger weight on title; now a clean export with `min-score=0.05` is possible.
- Scrapy: whitelist for domains; blacklist for common paths that do not contain target content; require keyword match in title/body.
- Export: `--skip-missing-core` and `--include-provenance` flags; clean and full profiles.
- Utilities: `delete-doc` (remove bad records), `backfill-source` (infer source), `extract-text-excerpt` (PDF/HTML to text excerpt).
- Domain keywords file for concrete/corrosion discovery.

### 3) Strengths of the project
- Clean data with full provenance (easy to audit and reproduce).
- No file overwrite; we also have checksum for integrity.
- Less noise from crawling due to whitelist/blacklist rules.
- Better scoring separates useful records; a clean export profile is available.
- JSONL exports are simple and ready for next steps (like sequence extraction or analytics).

### 4) What improved and why it matters
- Before: many records had `relevance_score = 0.0`; hard to make a clean export. Less provenance; risk of file overwrite.
- After: token+bigram scoring and title weight raise scores for relevant items; provenance is full; files never overwrite; clean profile at `min-score=0.05` is meaningful.

### 5) Notable features
- Rich provenance fields for traceability.
- Clean export and OA clean export.
- Scrapy domain/path controls to reduce noise.
- Content excerpt (simple) from PDF/HTML to preview text quickly.

### 6) How to run (short guide)
```bash
# 1) Validate and migrate
python -m src.uwss.cli config-validate --config config\config.yaml
python -m src.uwss.cli db-migrate --db data\uwss.sqlite

# 2) Discovery and scoring
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 25
python -m src.uwss.cli score-keywords --config config\config.yaml --db data\uwss.sqlite

# 3) Clean and check
python -m src.uwss.cli dedupe-resolve --db data\uwss.sqlite
python -m src.uwss.cli validate --db data\uwss.sqlite --json-out data\export\validation.json
python -m src.uwss.cli stats --db data\uwss.sqlite --json-out data\export\stats.json

# 4) Export (full and OA)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates.jsonl --min-score 0.0 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa.jsonl --min-score 0.0 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# 5) Clean export (min-score=0.05)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# 6) Download a few open-access files
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 5 --config config\config.yaml

# 7) Scrapy crawl with whitelist/blacklist
python -m src.uwss.cli crawl-seeds --seeds https://example.com --db data\uwss.sqlite --max-pages 10 --config config\config.yaml --keywords-file config\keywords_concrete.txt
```

### 7) How to view outputs and know it is improved
- Check `data/export/stats.json` for totals, OA count, by source, and by year.
- Check `data/export/validation.json` for duplicates and missing core fields (should be empty for missing_core).
- Check JSONL exports: confirm `relevance_score` in clean files is ≥ 0.05; confirm provenance fields exist when `--include-provenance` is used.
- Inspect `data/files/` to see new PDFs with `_id{doc.id}` suffix and no overwrite.

### 8) Cloud readiness (what we prepared and why)
- Dockerfile added: containerized app for simple and repeatable runs on ECS/Batch.
- `deploy-cloud.md`: a guide for AWS ECS + S3 + RDS + logging + scheduling.
- Why ECS/S3/RDS: simple to operate for batch jobs, scalable, cost-effective; S3 is durable for files; RDS gives a robust DB when scaling beyond SQLite.
- ENV/Secrets: use AWS Secrets Manager or Parameter Store for safe configuration.

### 9) Why these libraries and not others
- Scrapy (vs Selenium first): Scrapy is fast and polite for static pages and respects robots.txt; Selenium is heavier for JS pages (use later if needed).
- requests (vs httpx): simple and good enough for current sync flow; can switch to httpx if we move to async at scale.
- pdfminer.six (vs PyMuPDF first): pure Python and easy to integrate; PyMuPDF is faster but needs extra native deps (we can add later for speed).
- BeautifulSoup (vs lxml only): easy and enough for quick HTML text extraction; we can add lxml when parsing needs more speed.
- SQLAlchemy (vs raw sqlite3): cleaner code, easier migration, and simpler to switch to Postgres.

### 10) Sequence module (later)
- Current data and files are clean and ready for sequence extraction.
- Next steps after cloud-ready: extract time/value/unit/config from tables/figures/text, save JSON with provenance (page/caption), then build a simple next-step prediction baseline.

