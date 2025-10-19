# 🚀 **UWSS - COMPREHENSIVE WEB DATA COLLECTION SYSTEM**

> **Automated system for collecting academic data from multiple sources, processing and exporting high-quality data.**

## 🎯 **PROJECT PURPOSE**

**UWSS (Universal Web-Scraping System)** is developed to solve the problem of collecting academic data from multiple sources automatically and efficiently. Instead of having to access each website individually, the system can:

- **Automatically search** for academic documents from reliable sources
- **Filter and evaluate** document relevance
- **Download and store** PDF/HTML files
- **Export data** in various formats

## 🏗️ **SYSTEM CONCEPT**

### **Problems to solve**
- Manual academic data collection is time-consuming
- Different data sources have different formats
- Difficult to evaluate document relevance
- Duplicate and inconsistent data

### **Solution**
- **Multi-source integration**: OpenAlex, Crossref, arXiv, web crawling
- **Smart scoring**: Evaluate relevance based on keywords
- **Data cleaning**: Remove duplicates, standardize formats
- **Automated pipeline**: From discovery to export completely automated

## ⚙️ **HOW IT WORKS**

```
1. DISCOVERY
   ├── OpenAlex API → Search papers
   ├── Crossref API → Academic metadata
   ├── arXiv API → Preprints
   └── Scrapy → Web crawling

2. PROCESSING
   ├── Scoring → Evaluate relevance
   ├── Cleaning → Remove duplicates
   ├── Normalization → Standardize data
   └── Validation → Quality check

3. OUTPUT
   ├── Download → Download PDF/HTML files
   ├── Export → JSONL/CSV formats
   └── Statistics → Statistical reports
```

## 🛠️ **TECHNOLOGIES USED**

### **Backend**
- **Python 3.8+**: Main language
- **SQLAlchemy**: ORM for database
- **SQLite**: Local database (can switch to PostgreSQL)

### **Data Sources**
- **OpenAlex API**: Academic papers database
- **Crossref API**: DOI metadata
- **arXiv API**: Preprints
- **Scrapy**: Web crawling framework

### **Processing**
- **Requests**: HTTP client with retry logic
- **BeautifulSoup**: HTML parsing
- **pdfminer.six**: PDF text extraction
- **Token + Bigram**: Relevance scoring

### **Deployment**
- **Docker**: Containerization
- **AWS**: Cloud deployment (ECS, S3, RDS)

## 📁 **PROJECT STRUCTURE**

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

### **Purpose of files/folders**

- **`src/uwss/`**: Main system code
- **`config/`**: Keywords and sources configuration
- **`data/`**: Local data (database, files, exports)
- **`Dockerfile`**: For containerizing the application
- **`requirements.txt`**: List of required Python libraries

## 🚀 **SETUP AND RUN LOCALLY**

### **System requirements**
- **Python 3.8+**: Can be installed from python.org
- **RAM**: Minimum 2GB (recommended 4GB+)
- **Disk**: ~500MB for dependencies + data
- **OS**: Windows, macOS, Linux all supported

### **Step 1: Clone and setup environment**
```bash
# Clone repository
git clone <repository-url>
cd uwss

# Create virtual environment (recommended)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Initialize database**
```bash
# Validate config
python -m src.uwss.cli config-validate --config config/config.yaml

# Initialize database
python -m src.uwss.cli db-init --db data/uwss.sqlite

# Run migration (add new columns)
python -m src.uwss.cli db-migrate --db data/uwss.sqlite
```

### **Step 3: Run basic pipeline**
```bash
# Discover data (example: 10 records from each source)
python -m src.uwss.cli discover-openalex --config config/config.yaml --db data/uwss.sqlite --max 10
python -m src.uwss.cli discover-crossref --config config/config.yaml --db data/uwss.sqlite --max 10
python -m src.uwss.cli discover-arxiv --config config/config.yaml --db data/uwss.sqlite --max 10

# Process data
python -m src.uwss.cli score-keywords --config config/config.yaml --db data/uwss.sqlite
python -m src.uwss.cli normalize-metadata --db data/uwss.sqlite
python -m src.uwss.cli dedupe-resolve --db data/uwss.sqlite

# Quality check
python -m src.uwss.cli validate --db data/uwss.sqlite
python -m src.uwss.cli stats --db data/uwss.sqlite

# Export data
python -m src.uwss.cli export --db data/uwss.sqlite --out data/export/results.jsonl
```

### **Step 4: Download files (optional)**
```bash
# Download Open Access files
python -m src.uwss.cli fetch --db data/uwss.sqlite --outdir data/files --limit 5
```

## 📊 **RESULTS AND OUTPUT**

### **Database (`data/uwss.sqlite`)**
- Contains metadata of all documents
- Can be queried using SQL or CLI commands
- Automatic backup and migration

### **Export Files (`data/export/`)**
- **`results.jsonl`**: Complete data with metadata
- **`validation.json`**: Quality check results
- **`stats.json`**: Overview statistics

### **Downloaded Files (`data/files/`)**
- Downloaded PDF/HTML files
- Unique filenames to avoid overwrites
- Can be uploaded to S3 if needed

## 🔧 **CUSTOMIZATION FOR DIFFERENT MACHINES**

### **Weak machine (RAM < 4GB)**
```bash
# Reduce number of records to process
python -m src.uwss.cli discover-openalex --max 5
python -m src.uwss.cli fetch --limit 2
```

### **Powerful machine (RAM > 8GB)**
```bash
# Increase number of records to process
python -m src.uwss.cli discover-openalex --max 50
python -m src.uwss.cli fetch --limit 20
```

### **Slow network**
```bash
# Add throttling
python -m src.uwss.cli fetch --throttle-sec 1.0 --jitter-sec 0.5
```

## 🐳 **DOCKER (Optional)**

```bash
# Build image
docker build -t uwss:latest .

# Run container
docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/config:/app/config" uwss:latest python -m src.uwss.cli stats --db data/uwss.sqlite
```

## 📚 **REFERENCE DOCUMENTATION**

- **`REPORT.md`**: Detailed development process report
- **`LOCAL_SETUP_GUIDE.md`**: Detailed setup guide
- **`deploy-cloud.md`**: AWS deployment guide
- **`TEST_RESULTS.md`**: Test and validation results

## ⚠️ **IMPORTANT NOTES**

- **Rate Limiting**: System has throttling to avoid spamming APIs
- **Data Quality**: Not guaranteed 100% accuracy, manual review needed
- **Storage**: PDF files can take up significant space
- **Network**: Stable internet connection required

## 🎯 **CONCLUSION**

UWSS is an automated academic data collection system designed to:

- **Save time**: Automate the data collection process
- **Ensure quality**: Filter and clean data
- **Flexibility**: Can be customized for different domains
- **Easy to use**: Simple CLI, comprehensive documentation

**The system is suitable for academic research, data mining, and applications requiring data collection from multiple sources.**

---

*Universal Web-Scraping System - Automating academic data collection*