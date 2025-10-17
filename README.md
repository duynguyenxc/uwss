# UWSS — Universal Web‑Scraping System

UWSS discovers, filters, downloads, and exports web resources (not only papers) for a topic. It produces clean, stable outputs with full provenance and simple CLI operations. Local‑first by design, cloud‑ready when needed.

## Highlights
- Clean, reproducible data with provenance: `http_status`, `file_size`, `mime_type`, `fetched_at`, `checksum_sha256`, `url_hash_sha1`.
- Safer downloads: only fetch when `local_path` is empty; unique filenames include `_id{doc.id}` to avoid overwrites.
- Strong relevance scoring: token + bigram scoring with higher weight on title; supports a “clean” export using `--min-score 0.05`.
- Scrapy noise control: whitelist domains and blacklist paths via `config/config.yaml`.
- Clear exports: JSONL with optional provenance; OA‑only and "clean" profiles.
- Cloud‑ready: Dockerfile + `deploy-cloud.md` (AWS ECS/S3/RDS, scheduled tasks, logging).

## Repository overview
- `src/uwss/` — core package and CLI
  - `store/` — SQLAlchemy models, DB migration helpers
  - `discovery/` — Crossref, arXiv, OpenAlex search helpers
  - `crawl/` — downloader and Scrapy project for seed crawling
  - `score/` — keyword tokenizer + bigram relevance scoring
  - `clean/` — normalize, deterministic dedupe, utilities (delete/backfill)
  - `extract/` — text excerpt extraction (PDF/HTML)
- `config/` — `config.yaml`, domain keyword lists
- `data/` — local database (`uwss.sqlite`), files, and exports
- `Dockerfile`, `deploy-cloud.md` — container and cloud deployment notes
- `REPORT.md` — detailed progress and design report

## Quick start (Windows PowerShell)
```bash
# 0) Create and activate venv
python -m venv .\.venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 1) Validate config and migrate DB
python -m src.uwss.cli config-validate --config config\config.yaml
python -m src.uwss.cli db-migrate --db data\uwss.sqlite

# 2) Discover documents (examples)
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 25
python -m src.uwss.cli discover-arxiv   --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 15

# 3) Score relevance
python -m src.uwss.cli score-keywords --config config\config.yaml --db data\uwss.sqlite

# 4) Clean and quality checks
python -m src.uwss.cli dedupe-resolve      --db data\uwss.sqlite
python -m src.uwss.cli normalize-metadata  --db data\uwss.sqlite
python -m src.uwss.cli validate            --db data\uwss.sqlite --json-out data\export\validation.json
python -m src.uwss.cli stats               --db data\uwss.sqlite --json-out data\export\stats.json

# 5) Export (full and OA) with provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates.jsonl     --min-score 0.0  --year-min 1995 --sort relevance --skip-missing-core --include-provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa.jsonl  --min-score 0.0  --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# 6) Clean export profile (higher precision)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_clean_005.jsonl    --min-score 0.05 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# 7) Download some Open‑Access files (no overwrite)
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 5 --config config\config.yaml

# Optional: throttle/jitter and JSON metrics logs
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 3 --config config\config.yaml --throttle-sec 0.6 --jitter-sec 0.3
# Logs include JSON counters (downloads_ok/fail, status_counts, 429_5xx_count)

# 8) Optional: extract text excerpts (PDF/HTML)
pip install pdfminer.six beautifulsoup4
python -m src.uwss.cli extract-text-excerpt --db data\uwss.sqlite --limit 100

# CLI help
python -m src.uwss.cli --help
```

## Scrapy crawling (noise control)
Configure in `config/config.yaml`:
```yaml
scrapy_whitelist_domains:
  - www.concrete.org
  - arxiv.org
scrapy_path_blacklist:
  - /education
  - /certification
```
Run crawl:
```bash
python -m src.uwss.cli crawl-seeds --seeds https://example.com \
  --db data\uwss.sqlite --max-pages 10 --config config\config.yaml \
  --keywords-file config\keywords_concrete.txt
```

## What “good output” looks like
- `data/export/stats.json`: totals, OA ratio, by source/year trending up.
- `data/export/validation.json`: `missing_core` and `dup_doi` should be empty; a few `dup_title` groups are acceptable.
- Exports (`candidates*.jsonl`): meaningful `relevance_score`; the `clean_005` files contain fewer but more relevant items; when `--include-provenance` is used, records contain provenance fields.
- Files in `data/files/`: unique names with `_id{doc.id}` suffix; no overwrites.

## Design choices (short)
- Scrapy over Selenium: faster for static pages and API‑driven sites; Selenium only if pages are heavy JS.
- `requests` (sync) for simplicity now; can move to `httpx` (async) if we scale concurrency.
- SQLAlchemy ORM for portability and easier migrations; easy to switch to Postgres (RDS) later.
- `pdfminer.six` + `BeautifulSoup` for simple, pure‑Python text extraction.
- Token + bigram scoring with strong title weight to enable a reliable `--min-score` threshold.

## Cloud‑ready (AWS path)
- `Dockerfile` to containerize the app.
- `deploy-cloud.md` for ECS tasks (scheduled), S3 (files), RDS/PostgreSQL (DB), CloudWatch logging, and secrets via SSM/Secrets Manager.
- Configure via env vars (task definition or compose): contact email, user agent, DB URL, S3 bucket, rate limits.

## Branching
- Default branch: `main-next` (improved). Legacy preserved as `main-legacy`.

## Roadmap
- Sequence module (later): extract time/value/unit series from documents and run baseline forecasting.

## License / contributions
Internal research use. Open issues/PRs welcome.

Universal Web-Scraping System (Local-first)
Create venv: .\\.venv\\Scripts\\activate\
Install: pip install -r requirements.txt\n- Config: config/config.yaml\n
