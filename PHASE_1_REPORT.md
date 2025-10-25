# Phase 1 Report — Foundation + Incremental Crawling Setup

## 1) Mục tiêu
- Xây nền kiến trúc chuyên nghiệp, dễ bảo trì/nâng cấp; nhận diện dữ liệu đầy đủ.
- Tránh trùng lặp khi chạy nhiều lần bằng registry URL; ưu tiên nguồn học thuật ổn định.

## 2) Đã làm gì
- Bổ sung nhận diện:
  - Trường `landing_url`, `pdf_url` trong bảng `documents` (ORM + migrate).
- Chống trùng lặp & incremental:
  - Bảng `visited_urls` lưu URL đã xử lý, tích hợp vào crawler/downloader để skip các lần sau.
- Discovery & nguồn:
  - Crossref, arXiv: dedupe theo DOI/title trước khi insert; điền `landing_url`/`pdf_url` khi có.
  - Europe PMC, Semantic Scholar: thêm mới, ánh xạ trường đầy đủ, dedupe trước insert.
  - OpenAlex: disable (API không ổn định theo yêu cầu).
- Download & Export:
  - Downloader ưu tiên `pdf_url`; lưu `checksum_sha256`, `mime_type`, `file_size`, `fetched_at`, `url_hash_sha1`.
  - Export thêm `landing_url`, `pdf_url`; tuỳ chọn `--include-full-text`.

## 3) Cách vận hành (ví dụ)
```bash
# Khởi tạo & migrate
python -m src.uwss.cli db-init --db data/uwss.sqlite
python -m src.uwss.cli db-migrate --db data/uwss.sqlite

# Thu thập ví dụ
python -m src.uwss.cli discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 50
python -m src.uwss.cli discover-eupmc --config config/config.yaml --db data/uwss.sqlite --max 50
python -m src.uwss.cli discover-semanticscholar --config config/config.yaml --db data/uwss.sqlite --max 50

# Tải file ưu tiên PDF
python -m src.uwss.cli fetch --db data/uwss.sqlite --outdir data/files --limit 10 --config config/config.yaml

# Xuất dữ liệu nhận diện đầy đủ
python -m src.uwss.cli export --db data/uwss.sqlite --out data/export/results.jsonl \
  --include-provenance --include-full-text --skip-missing-core
```

## 4) Kỹ thuật, kỹ năng
- SQLAlchemy ORM, migrate idempotent (thêm cột mới an toàn).
- Scrapy spider: obey robots, whitelist/blacklist domain/path, lọc theo từ khoá.
- Dedupe DOI/title, URL registry cho incremental crawling; provenance thu thập và lưu trữ.

## 5) Files/Hàm chính
- `src/uwss/store/models.py`: bổ sung `landing_url`, `pdf_url`, model `VisitedUrl`.
- `src/uwss/store/db.py`: `migrate_db()` thêm cột mới và tạo bảng `visited_urls` nếu thiếu.
- `src/uwss/cli.py`:
  - Disable `discover-openalex` (no-op).
  - Cập nhật `discover-crossref`, `discover-arxiv` điền trường mới + dedupe.
  - Thêm `discover-eupmc`, `discover-semanticscholar` (nguồn mới).
  - `export` thêm `landing_url`, `pdf_url`, `--include-full-text`.
- `src/uwss/crawl/__init__.py`: downloader ưu tiên `pdf_url`, ghi `VisitedUrl`.
- `src/uwss/crawl/scrapy_project/spiders/seed_spider.py`: skip URL đã visit, ghi `VisitedUrl`.
- `config/config.yaml`: loại OpenAlex, thêm Europe PMC & Semantic Scholar vào `domain_sources`.

## 6) Ví dụ hoạt động nhỏ
- Spider gặp `https://site/paper-123`, nếu chưa có trong `visited_urls`, lưu candidate `Document` (status `metadata_only`) và đánh dấu URL đã thấy. Ở run tiếp theo, URL này được skip.
- Downloader gặp bản ghi có `pdf_url`, tải file, điền `local_path`, `checksum_sha256`, `mime_type`, `file_size`, `fetched_at` và ghi nhận `VisitedUrl` với status HTTP.

## 7) Tác dụng
- Bảo đảm incremental: chạy nhiều lần không thu trùng URL; dữ liệu có nhận diện hoàn chỉnh; sẵn sàng mở rộng thêm nguồn học thuật.
