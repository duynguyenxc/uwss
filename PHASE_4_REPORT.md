# Phase 4 Report — Full Content from URL (HTML/PDF) + Export Embedding

## 1) Mục tiêu
- Đảm bảo `full_content` là nội dung của chính URL (HTML hoặc PDF) kể cả khi không có file tải về.
- Cải thiện identification: có `content_path`, và tùy chọn nhúng `full_content` vào export.

## 2) Đã làm gì
- Thêm lệnh `scrape-full-content`: tải trực tiếp `landing_url`/`source_url`, trích xuất text HTML hoặc PDF bytes, lưu `.txt` vào `data/content/`, cập nhật `content_path`, `content_chars`.
- `export` bổ sung cờ `--embed-content` để xuất thêm trường `full_content` (đọc từ `content_path`).

## 3) Cách vận hành (ví dụ)
```bash
# Scrape full content theo URL (HTML/PDF), 50 bản ghi
python -m src.uwss.cli scrape-full-content --db data/uwss.sqlite --content-dir data/content --limit 50 --config config/config.yaml

# Export JSONL có nhúng full_content (thận trọng kích thước file)
python -m src.uwss.cli export --db data/uwss.sqlite --out data/export/full_with_content.jsonl \
  --include-provenance --include-full-text --embed-content --skip-missing-core
```

## 4) Kỹ thuật, kỹ năng
- HTTP session với retry/backoff; nhận diện mime (PDF vs HTML); pdfminer cho PDF, BeautifulSoup cho HTML, lọc tag (title/h1/h2/p/li).
- Lưu `.txt` an toàn UTF-8; ghi `content_path`, `content_chars` trong DB.
- Export đọc `content_path` khi `--embed-content`.

## 5) Files/Hàm chính
- `src/uwss/extract/__init__.py`: `scrape_full_content`, `_session_with_retries`.
- `src/uwss/cli.py`: lệnh `scrape-full-content`; `export` nhận `--embed-content`.

## 6) Ví dụ hoạt động nhỏ
- URL bài HTML không có link PDF: trích xuất toàn bộ nội dung hiển thị (title + headings + paragraphs), lưu `data/content/doc_{id}_url.txt`, cập nhật DB, export có thể nhúng `full_content` khi cần.

## 7) Tác dụng
- Identification “đầy đủ” đúng yêu cầu: luôn có `full_content` từ URL, ngay cả khi không có file PDF tải được.
