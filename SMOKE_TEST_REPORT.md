# Smoke Test Report (local)

## Scope
- Validate critical path end-to-end on small samples: migrate → discover (Crossref/EUPMC/S2/arXiv) → enrich+fetch → scrape-full-content → export.
- Ensure incremental resume works and identification fields are complete.

## Commands used
```powershell
# 0) Migrate
python -m src.uwss.cli db-migrate --db data/uwss.sqlite

# 1) Discover (small samples)
python -m src.uwss.cli discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 5 --cache-ttl-sec 86400
python -m src.uwss.cli discover-eupmc --config config/config.yaml --db data/uwss.sqlite --max 5 --cache-ttl-sec 86400
python -m src.uwss.cli discover-semanticscholar --config config/config.yaml --db data/uwss.sqlite --max 3 --cache-ttl-sec 86400
python -m src.uwss.cli discover-arxiv --config config/config.yaml --db data/uwss.sqlite --max 3 --resume

# 2) Enrich + fetch small
python -m src.uwss.cli fetch --db data/uwss.sqlite --outdir data/files --limit 2 --config config/config.yaml

# 3) Scrape full content for URLs
python -m src.uwss.cli scrape-full-content --db data/uwss.sqlite --content-dir data/content --limit 2 --config config/config.yaml

# 4) Export JSONL (embed full_content for verification)
python -m src.uwss.cli export --db data/uwss.sqlite --out data/export/smoke_small.jsonl \
  --include-provenance --include-full-text --skip-missing-core --embed-content
```

## Results (this run)
- Migrate: OK
- Crossref (max 5): Inserted 0 (cache/filters) → No error
- Europe PMC (max 5): Inserted 0 → No error
- Semantic Scholar (max 3): Inserted 2 → OK (batched per keyword to avoid 400)
- arXiv (max 3, resume): Inserted 2 → OK
- Enrich+Fetch (limit 2): Enriched 19 via Unpaywall; Downloaded 2 files (1×403 observed but handled)
- Scrape full content (limit 2): OK
- Export JSONL: Exported 146 records to `data/export/smoke_small.jsonl`

## Identification completeness
- Export includes: id, doi, title, authors, venue, year/date, source/source_url/landing_url, pdf_url, pdf_path, abstract, content_path, content_chars, full_content (when `--embed-content`), open_access, license, oa_status, provenance.

## API + Scrapy Coordination (short plan)
- Shared registry/state: `visited_urls` + `ingestion_state` unify incremental across APIs & Scrapy.
- Priority queue: API discoveries seed high-quality landing URLs; Scrapy respects whitelist/blacklist from config.
- Consistent throttling/retry: align per-host throttle + backoff.
- Unified export surface: JSONL/CSV/S3 with one schema.

