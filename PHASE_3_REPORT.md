# Phase 3 Report — Incremental “Since Last Run” State

## 1) Mục tiêu
- Thu thập lặp nhiều lần nhưng luôn lấy phần MỚI, không chạy lại dữ liệu cũ.
- Lưu checkpoint theo từng nguồn (offset/cursor) để resume an toàn.

## 2) Đã làm gì
- Thêm bảng `ingestion_state` (source, checkpoint_key, checkpoint_value, updated_at).
- Mở rộng discovery:
  - Crossref: `--resume` lưu/đọc offset (tham số `start_offset`).
  - Europe PMC: `--resume` đọc/sửa `cursor` (tham số `start_cursor`).
  - Semantic Scholar: `--resume` lưu/đọc offset.
- API iterators hỗ trợ tham số resume (offset/cursor) và tiếp tục từ vị trí đã lưu.

## 3) Cách vận hành (ví dụ)
```bash
# Crossref resume từ offset đã lưu
python -m src.uwss.cli discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 100 --resume --cache-ttl-sec 86400

# Europe PMC resume theo cursor
python -m src.uwss.cli discover-eupmc --config config/config.yaml --db data/uwss.sqlite --max 100 --resume --cache-ttl-sec 86400

# Semantic Scholar resume theo offset
python -m src.uwss.cli discover-semanticscholar --config config/config.yaml --db data/uwss.sqlite --max 100 --resume --cache-ttl-sec 86400
```

## 4) Kỹ thuật, kỹ năng
- SQL schema tối giản cho checkpoint; idempotent migration.
- Iterator có tham số `start_offset`/`start_cursor`; CLI `--resume` đọc/ghi state.
- Kết hợp HTTP cache TTL để ổn định kết quả và giảm quota.

## 5) Files/Hàm chính
- `src/uwss/store/models.py`: model `IngestionState`.
- `src/uwss/store/db.py`: tạo bảng `ingestion_state` trong migrate.
- `src/uwss/discovery/__init__.py`: thêm tham số `start_offset`/`start_cursor` vào `iter_*`.
- `src/uwss/cli.py`:
  - Crossref/Europe PMC/Semantic Scholar: cờ `--resume`, ghi/đọc state.

## 6) Ví dụ hoạt động nhỏ
- Lần 1 lấy 100 bản ghi Crossref, lưu offset=100. Lần 2 chạy `--resume`, bắt đầu từ offset=100, tránh lặp lại 100 bản ghi đầu.

## 7) Tác dụng
- Chạy lặp theo lịch (daily/weekly) luôn có dữ liệu mới, không trùng dữ liệu cũ.
