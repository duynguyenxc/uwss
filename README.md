# 🚀 **UWSS - HỆ THỐNG THU THẬP DỮ LIỆU WEB TOÀN DIỆN**

> **Hệ thống tự động thu thập dữ liệu học thuật từ nhiều nguồn khác nhau, xử lý và xuất dữ liệu có chất lượng cao.**

## 🎯 **MỤC ĐÍCH DỰ ÁN**

**UWSS (Universal Web-Scraping System)** được phát triển để giải quyết vấn đề thu thập dữ liệu học thuật từ nhiều nguồn khác nhau một cách tự động và hiệu quả. Thay vì phải truy cập từng website riêng lẻ, hệ thống có thể:

- **Tự động tìm kiếm** tài liệu học thuật từ các nguồn uy tín
- **Lọc và đánh giá** mức độ liên quan của tài liệu
- **Tải xuống và lưu trữ** các file PDF/HTML
- **Xuất dữ liệu** theo nhiều định dạng khác nhau

## 🏗️ **Ý TƯỞNG HỆ THỐNG**

### **Vấn đề cần giải quyết**
- Thu thập dữ liệu học thuật thủ công rất tốn thời gian
- Các nguồn dữ liệu khác nhau có format khác nhau
- Khó đánh giá mức độ liên quan của tài liệu
- Dữ liệu trùng lặp và không đồng nhất

### **Giải pháp**
- **Tích hợp nhiều nguồn**: OpenAlex, Crossref, arXiv, web crawling
- **Scoring thông minh**: Đánh giá mức độ liên quan dựa trên keywords
- **Làm sạch dữ liệu**: Loại bỏ duplicates, chuẩn hóa format
- **Pipeline tự động**: Từ discovery đến export hoàn toàn tự động

## ⚙️ **CÁCH HOẠT ĐỘNG**

```
1. DISCOVERY (Khám phá)
   ├── OpenAlex API → Tìm kiếm papers
   ├── Crossref API → Metadata học thuật
   ├── arXiv API → Preprints
   └── Scrapy → Web crawling

2. PROCESSING (Xử lý)
   ├── Scoring → Đánh giá relevance
   ├── Cleaning → Loại bỏ duplicates
   ├── Normalization → Chuẩn hóa dữ liệu
   └── Validation → Kiểm tra chất lượng

3. OUTPUT (Xuất dữ liệu)
   ├── Download → Tải file PDF/HTML
   ├── Export → JSONL/CSV formats
   └── Statistics → Báo cáo thống kê
```

## 🛠️ **CÔNG NGHỆ SỬ DỤNG**

### **Backend**
- **Python 3.8+**: Ngôn ngữ chính
- **SQLAlchemy**: ORM cho database
- **SQLite**: Database local (có thể chuyển sang PostgreSQL)

### **Data Sources**
- **OpenAlex API**: Academic papers database
- **Crossref API**: DOI metadata
- **arXiv API**: Preprints
- **Scrapy**: Web crawling framework

### **Processing**
- **Requests**: HTTP client với retry logic
- **BeautifulSoup**: HTML parsing
- **pdfminer.six**: PDF text extraction
- **Token + Bigram**: Relevance scoring

### **Deployment**
- **Docker**: Containerization
- **AWS**: Cloud deployment (ECS, S3, RDS)

## 📁 **CẤU TRÚC DỰ ÁN**

```
uwss/
├── src/uwss/                    # Core package
│   ├── store/                   # Database models
│   ├── discovery/               # API integrations
│   ├── crawl/                   # Download & web crawling
│   ├── score/                   # Relevance scoring
│   ├── clean/                   # Data cleaning
│   ├── extract/                 # Text extraction
│   ├── upload/                  # S3 integration
│   └── cli.py                   # Command-line interface
├── config/                      # Configuration files
│   ├── config.yaml              # Main config
│   └── keywords_concrete.txt    # Domain keywords
├── data/                        # Local data
│   ├── uwss.sqlite              # SQLite database
│   ├── files/                   # Downloaded PDF/HTML files
│   └── export/                  # Export results
├── Dockerfile                   # Container config
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

### **Mục đích các file/folder**

- **`src/uwss/`**: Code chính của hệ thống
- **`config/`**: Cấu hình keywords và sources
- **`data/`**: Dữ liệu local (database, files, exports)
- **`Dockerfile`**: Để containerize ứng dụng
- **`requirements.txt`**: Danh sách thư viện Python cần thiết

## 🚀 **SETUP VÀ CHẠY TRÊN LOCAL**

### **Yêu cầu hệ thống**
- **Python 3.8+**: Có thể cài từ python.org
- **RAM**: Tối thiểu 2GB (khuyến nghị 4GB+)
- **Disk**: ~500MB cho dependencies + dữ liệu
- **OS**: Windows, macOS, Linux đều được

### **Bước 1: Clone và setup môi trường**
```bash
# Clone repository
git clone <repository-url>
cd uwss

# Tạo virtual environment (khuyến nghị)
python -m venv .venv

# Kích hoạt virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### **Bước 2: Khởi tạo database**
```bash
# Validate config
python -m src.uwss.cli config-validate --config config/config.yaml

# Khởi tạo database
python -m src.uwss.cli db-init --db data/uwss.sqlite

# Chạy migration (thêm columns mới)
python -m src.uwss.cli db-migrate --db data/uwss.sqlite
```

### **Bước 3: Chạy pipeline cơ bản**
```bash
# Khám phá dữ liệu (ví dụ: 10 records từ mỗi source)
python -m src.uwss.cli discover-openalex --config config/config.yaml --db data/uwss.sqlite --max 10
python -m src.uwss.cli discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 10
python -m src.uwss.cli discover-arxiv --config config/config.yaml --db data/uwss.sqlite --max 10

# Xử lý dữ liệu
python -m src.uwss.cli score-keywords --config config/config.yaml --db data/uwss.sqlite
python -m src.uwss.cli normalize-metadata --db data/uwss.sqlite
python -m src.uwss.cli dedupe-resolve --db data/uwss.sqlite

# Kiểm tra chất lượng
python -m src.uwss.cli validate --db data/uwss.sqlite
python -m src.uwss.cli stats --db data/uwss.sqlite

# Xuất dữ liệu
python -m src.uwss.cli export --db data/uwss.sqlite --out data/export/results.jsonl
```

### **Bước 4: Tải xuống files (tùy chọn)**
```bash
# Tải xuống Open Access files
python -m src.uwss.cli fetch --db data/uwss.sqlite --outdir data/files --limit 5
```

## 📊 **KẾT QUẢ VÀ OUTPUT**

### **Database (`data/uwss.sqlite`)**
- Chứa metadata của tất cả documents
- Có thể query bằng SQL hoặc CLI commands
- Tự động backup và migration

### **Export Files (`data/export/`)**
- **`results.jsonl`**: Dữ liệu đầy đủ với metadata
- **`validation.json`**: Kết quả kiểm tra chất lượng
- **`stats.json`**: Thống kê tổng quan

### **Downloaded Files (`data/files/`)**
- PDF/HTML files được tải xuống
- Tên file unique để tránh overwrite
- Có thể upload lên S3 nếu cần

## 🔧 **TÙY CHỈNH CHO MÁY KHÁC NHAU**

### **Máy yếu (RAM < 4GB)**
```bash
# Giảm số records xử lý
python -m src.uwss.cli discover-openalex --max 5
python -m src.uwss.cli fetch --limit 2
```

### **Máy mạnh (RAM > 8GB)**
```bash
# Tăng số records xử lý
python -m src.uwss.cli discover-openalex --max 50
python -m src.uwss.cli fetch --limit 20
```

### **Mạng chậm**
```bash
# Thêm throttling
python -m src.uwss.cli fetch --throttle-sec 1.0 --jitter-sec 0.5
```

## 🐳 **DOCKER (Tùy chọn)**

```bash
# Build image
docker build -t uwss:latest .

# Chạy container
docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/config:/app/config" uwss:latest python -m src.uwss.cli stats --db data/uwss.sqlite
```

## 📚 **TÀI LIỆU THAM KHẢO**

- **`REPORT.md`**: Báo cáo chi tiết về quá trình phát triển
- **`LOCAL_SETUP_GUIDE.md`**: Hướng dẫn setup chi tiết
- **`deploy-cloud.md`**: Hướng dẫn deploy lên AWS
- **`TEST_RESULTS.md`**: Kết quả test và validation

## ⚠️ **LƯU Ý QUAN TRỌNG**

- **Rate Limiting**: Hệ thống có throttling để tránh spam APIs
- **Data Quality**: Không đảm bảo 100% accuracy, cần review thủ công
- **Storage**: Files PDF có thể chiếm nhiều dung lượng
- **Network**: Cần kết nối internet ổn định

## 🎯 **KẾT LUẬN**

UWSS là một hệ thống thu thập dữ liệu học thuật tự động, được thiết kế để:

- **Tiết kiệm thời gian**: Tự động hóa quá trình thu thập dữ liệu
- **Đảm bảo chất lượng**: Lọc và làm sạch dữ liệu
- **Linh hoạt**: Có thể tùy chỉnh cho nhiều domain khác nhau
- **Dễ sử dụng**: CLI đơn giản, documentation đầy đủ

**Hệ thống phù hợp cho nghiên cứu học thuật, data mining, và các ứng dụng cần thu thập dữ liệu từ nhiều nguồn khác nhau.**

---

*Universal Web-Scraping System - Tự động hóa thu thập dữ liệu học thuật*