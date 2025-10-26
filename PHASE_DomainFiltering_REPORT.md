# Domain Filtering Phase — Clean Output for Civil Concrete Corrosion Domain

## 1) Mục tiêu
- Loại bỏ dữ liệu ngoài domain (ML/AI thuần) khỏi output chính.
- Duy trì identification đầy đủ, nâng tỷ lệ `pdf_url`/`full_content`.

## 2) Đã làm gì
- Re-score với `config/config.yaml` (civil domain) và re-export với bộ lọc chặt.
- Thêm cờ `--require-match` cho `export`: chỉ xuất bản ghi có `keywords_found`.
- Chạy lại full pipeline trên DB sạch: discover → score → enrich/fetch → scrape → export.

## 3) Cách vận hành
```bash
python -m src.uwss.cli score-keywords --config config/config.yaml --db data/uwss.sqlite
python -m src.uwss.cli export --db data/uwss.sqlite --out data/export/final_results_clean.jsonl \
  --min-score 0.05 --year-min 1995 --skip-missing-core --require-match
```

## 4) Kết quả
- `final_results_clean.jsonl`: 123 bản ghi (sạch domain), identification đầy đủ.
- Tỷ lệ có `pdf_path`/`content_path` tăng, ít nhiễu từ ML thuần.

## 5) Ghi chú
- Nếu cần còn chặt hơn: tăng `--min-score`, bổ sung “negative keywords”.
- Đã chuẩn bị logging JSON để dễ audit lệnh/nguồn.

## 6) Bổ sung resolver (publisher → PDF)
- Thêm bước `resolve_publisher_links` chạy trước Unpaywall trong `fetch`:
  - Theo link “View via Publisher” nếu có (vd. Semantic Scholar), cập nhật `landing_url` chuẩn.
  - Tìm PDF qua `meta[name=citation_pdf_url]`, `link[rel=alternate][type=application/pdf]`, anchor chứa `pdf`, hoặc follow DOI đến `Content-Type=application/pdf`.
- Kết quả smoke: `updated_pdf=11` (tăng số bài có `pdf_url`), download thành công 9/10 trong mẫu nhỏ.
