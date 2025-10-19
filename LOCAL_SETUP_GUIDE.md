# 🚀 UWSS - HƯỚNG DẪN SETUP LOCAL HOÀN CHỈNH

## 📋 YÊU CẦU HỆ THỐNG
- **Python**: 3.8+ (khuyến nghị 3.9+)
- **Git**: Để clone repository
- **Windows PowerShell**: Để chạy commands
- **Internet**: Để download dependencies và crawl data

## 🔧 BƯỚC 1: CLONE REPOSITORY
```bash
# Clone repository từ GitHub
git clone https://github.com/duynguyenxc/uwss.git
cd uwss

# Chuyển sang nhánh production-ready
git checkout feat/final-production-ready
```

## 🐍 BƯỚC 2: SETUP PYTHON ENVIRONMENT
```bash
# Tạo virtual environment
python -m venv .\.venv

# Activate virtual environment
.\.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install tất cả dependencies
pip install -r requirements.txt
```

## ⚙️ BƯỚC 3: KIỂM TRA CONFIGURATION
```bash
# Validate configuration file
python -m src.uwss.cli config-validate --config config\config.yaml
```

**Kết quả mong đợi**: `Configuration is valid` hoặc tương tự

## 🗄️ BƯỚC 4: KHỞI TẠO DATABASE
```bash
# Tạo database mới (lần đầu)
python -m src.uwss.cli db-init --db data\uwss.sqlite

# Chạy migration để thêm các cột mới
python -m src.uwss.cli db-migrate --db data\uwss.sqlite
```

**Kết quả mong đợi**: Database được tạo tại `data/uwss.sqlite`

## 🔍 BƯỚC 5: DISCOVERY DATA
```bash
# Discovery từ Crossref (25 records)
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 25

# Discovery từ arXiv (15 records)  
python -m src.uwss.cli discover-arxiv --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 15
```

**Kết quả mong đợi**: 
- Crossref: `Discovered X new records`
- arXiv: `Discovered Y new records`

## 🧮 BƯỚC 6: SCORE RELEVANCE
```bash
# Score relevance cho tất cả documents
python -m src.uwss.cli score-keywords --config config\config.yaml --db data\uwss.sqlite
```

**Kết quả mong đợi**: `Scored X documents`

## 🧹 BƯỚC 7: CLEAN DATA
```bash
# Normalize metadata
python -m src.uwss.cli normalize-metadata --db data\uwss.sqlite

# Resolve duplicates
python -m src.uwss.cli dedupe-resolve --db data\uwss.sqlite
```

**Kết quả mong đợi**: 
- Normalize: `Normalized X records`
- Dedupe: `Resolved X duplicate groups`

## ✅ BƯỚC 8: VALIDATE DATA QUALITY
```bash
# Validate data quality
python -m src.uwss.cli validate --db data\uwss.sqlite --json-out data\export\validation.json

# Generate statistics
python -m src.uwss.cli stats --db data\uwss.sqlite --json-out data\export\stats.json
```

**Kết quả mong đợi**:
- Validation: `{"dup_doi": [], "dup_title": [], "missing_core": [], "invalid_year": [], "missing_files": []}`
- Stats: Hiển thị tổng số records, OA count, distribution by source/year

## 📤 BƯỚC 9: EXPORT DATA
```bash
# Full export với provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates.jsonl --min-score 0.0 --year-min 1995 --sort relevance --skip-missing-core --include-provenance

# Open Access only export
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa.jsonl --min-score 0.0 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# Clean export (higher precision)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
```

**Kết quả mong đợi**: 
- `Exported X records to data\export\candidates.jsonl`
- `Exported Y records to data\export\candidates_oa.jsonl`
- `Exported Z records to data\export\candidates_clean_005.jsonl`

## 📥 BƯỚC 10: DOWNLOAD FILES
```bash
# Download Open Access files
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 5 --config config\config.yaml
```

**Kết quả mong đợi**: 
- `Downloaded X files`
- Files được lưu trong `data/files/` với tên unique `_id{doc.id}`

## 🔍 BƯỚC 11: KIỂM TRA KẾT QUẢ
```bash
# Kiểm tra validation results
Get-Content data\export\validation.json

# Kiểm tra statistics
Get-Content data\export\stats.json

# Kiểm tra export files
Get-ChildItem data\export\*.jsonl

# Kiểm tra downloaded files
Get-ChildItem data\files\
```

## 📊 CÁCH ĐỌC KẾT QUẢ

### **Validation Results** (`data/export/validation.json`)
```json
{
    "dup_doi": [],           // ✅ Should be empty
    "dup_title": [],         // ✅ Should be empty  
    "missing_core": [],     // ✅ Should be empty
    "invalid_year": [],      // ✅ Should be empty
    "missing_files": []      // ✅ Should be empty
}
```

### **Statistics** (`data/export/stats.json`)
```json
{
    "total": 142,                    // Total records
    "open_access": 57,               // Open access count
    "by_source": {                   // Distribution by source
        "arxiv": 40,
        "crossref": 53,
        "scrapy": 3,
        "web": 46
    },
    "by_year": {                     // Distribution by year
        "2024": 28,
        "2023": 17,
        // ... more years
    }
}
```

### **Export Files**
- **`candidates.jsonl`**: All records with provenance
- **`candidates_oa.jsonl`**: Open access records only
- **`candidates_clean_005.jsonl`**: High-relevance records (score ≥ 0.05)

### **Downloaded Files**
- **`data/files/`**: PDF/HTML files with unique names (`_id{doc.id}`)
- **No overwrites**: Each file has unique name
- **Provenance**: Full metadata captured

## 🚨 TROUBLESHOOTING

### **Lỗi thường gặp:**
1. **ModuleNotFoundError**: Chạy `pip install -r requirements.txt`
2. **Database locked**: Đóng tất cả connections, restart terminal
3. **Network timeout**: Chạy lại command, system có retry logic
4. **Permission denied**: Chạy PowerShell as Administrator

### **Kiểm tra hệ thống:**
```bash
# Kiểm tra Python version
python --version

# Kiểm tra virtual environment
.\.venv\Scripts\activate
python -c "import sys; print(sys.executable)"

# Kiểm tra dependencies
python -c "import requests, sqlalchemy, scrapy; print('All dependencies OK')"
```

## ✅ KẾT QUẢ MONG ĐỢI

Sau khi chạy hoàn chỉnh, bạn sẽ có:
- ✅ **Database**: `data/uwss.sqlite` với clean data
- ✅ **Exports**: Multiple JSONL files với provenance
- ✅ **Files**: Downloaded PDFs/HTMLs với unique names
- ✅ **Validation**: 100% clean data (0 issues)
- ✅ **Stats**: Balanced distribution by source/year

**Hệ thống sẵn sàng cho production deployment!**
