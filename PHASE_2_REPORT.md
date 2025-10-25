# Phase 2 Report — HTTP Cache for Discovery

## 1) Mục tiêu
- Tăng tốc và giảm chi phí/quota API khi chạy lặp.
- Ổn định kết quả giữa các lần chạy gần nhau (trong TTL). 

## 2) Đã làm gì
- Thêm `src/uwss/utils/cache.py`: cache đĩa theo (url+params) với TTL.
- Tích hợp cache cho Crossref, Europe PMC, Semantic Scholar.
- Thêm cờ CLI `--cache-ttl-sec` cho các lệnh discovery.

## 3) Cách vận hành (ví dụ)
```bash
python -m src.uwss.cli discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 100 --cache-ttl-sec 86400
python -m src.uwss.cli discover-eupmc --config config/config.yaml --db data/uwss.sqlite --max 100 --cache-ttl-sec 86400
python -m src.uwss.cli discover-semanticscholar --config config/config.yaml --db data/uwss.sqlite --max 100 --cache-ttl-sec 86400
```

## 4) Kỹ thuật, kỹ năng
- Khoá cache SHA1 từ URL + tham số ổn định (params sorted), file `.json`/`.txt` trong `data/cache/`.
- TTL kiểm soát độ tươi; hết hạn thì gọi HTTP và ghi đè cache.

## 5) Files/Hàm chính
- `src/uwss/utils/cache.py`: `fetch_json_with_cache`, `fetch_text_with_cache`.
- `src/uwss/discovery/__init__.py`:
  - Crossref: `fetch_crossref_page(..., cache_ttl_sec)`.
  - Europe PMC: `fetch_eupmc_page(..., cache_ttl_sec)`.
  - Semantic Scholar: `fetch_s2_page(..., cache_ttl_sec)`.
- `src/uwss/cli.py`: thêm `--cache-ttl-sec` cho các lệnh discovery.

## 6) Ví dụ hoạt động nhỏ
- Lần 1 gọi Crossref: tạo file cache; lần 2 trong TTL: trả về từ cache ngay.

## 7) Tác dụng
- Giảm latency, hạn chế gọi API dư thừa; phù hợp cho chạy lặp hàng ngày.
