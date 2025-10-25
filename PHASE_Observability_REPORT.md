# Observability Phase Report — Logging & Metrics

## 1) Mục tiêu
- Tăng khả năng quan sát: log JSON có cấu trúc + metrics cơ bản (số bản ghi, thời gian chạy) cho các lệnh quan trọng.
- Dễ giám sát khi chạy local/CI/Cloud, không phá vỡ UX hiện tại.

## 2) Đã làm gì
- Thêm `_log_json(enabled, event, **fields)` trong `cli.py`.
- `stats`: cờ `--log-json` → log `stats_done` kèm elapsed và counters.
- `fetch`: cờ `--log-json` → log `fetch_done` kèm elapsed, enriched, downloaded.
- Không thay đổi logic cốt lõi; tương thích ngược hoàn toàn.

## 3) Cách vận hành (ví dụ)
```bash
# Stats có log JSON
python -m src.uwss.cli stats --db data/uwss.sqlite --json-out data/export/stats.json --log-json

# Fetch có log JSON
python -m src.uwss.cli fetch --db data/uwss.sqlite --outdir data/files --limit 10 --config config/config.yaml --log-json
```

## 4) Kỹ thuật, kỹ năng
- Log JSON đơn giản, không phụ thuộc framework ngoài; in ra stdout để tương thích CloudWatch/ELK.
- Metrics: elapsed time, counters enriched/downloaded/total.
- Có thể mở rộng nhanh cho discover/crawl/export trong bước tiếp theo.

## 5) Tác dụng
- Dễ theo dõi tiến trình và trạng thái khi chạy batch hoặc cloud tasks.
- Giảm thời gian debug, chuẩn bị cho giám sát cloud.
