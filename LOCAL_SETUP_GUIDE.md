# 🚀 UWSS - COMPLETE LOCAL SETUP GUIDE

## 📋 SYSTEM REQUIREMENTS
- **Python**: 3.8+ (recommended 3.9+)
- **Git**: To clone repository
- **Windows PowerShell**: To run commands
- **Internet**: To download dependencies and crawl data

## 🔧 STEP 1: CLONE REPOSITORY
```bash
# Clone repository from GitHub
git clone https://github.com/duynguyenxc/uwss.git
cd uwss

# Switch to production-ready branch
git checkout feat/final-production-ready
```

## 🐍 STEP 2: SETUP PYTHON ENVIRONMENT
```bash
# Create virtual environment
python -m venv .\.venv

# Activate virtual environment
.\.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

## ⚙️ STEP 3: CHECK CONFIGURATION
```bash
# Validate configuration file
python -m src.uwss.cli config-validate --config config\config.yaml
```

**Expected result**: `Configuration is valid` or similar

## 🗄️ STEP 4: INITIALIZE DATABASE
```bash
# Create new database (first time)
python -m src.uwss.cli db-init --db data\uwss.sqlite

# Run migration to add new columns
python -m src.uwss.cli db-migrate --db data\uwss.sqlite
```

**Expected result**: Database created at `data/uwss.sqlite`

## 🔍 STEP 5: DISCOVERY DATA
```bash
# Discovery from Crossref (25 records)
python -m src.uwss.cli discover-crossref --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 25

# Discovery from arXiv (15 records)  
python -m src.uwss.cli discover-arxiv --config config\config.yaml --db data\uwss.sqlite --keywords-file config\keywords_concrete.txt --max 15
```

**Expected result**: 
- Crossref: `Discovered X new records`
- arXiv: `Discovered Y new records`

## 🧮 STEP 6: SCORE RELEVANCE
```bash
# Score relevance for all documents
python -m src.uwss.cli score-keywords --config config\config.yaml --db data\uwss.sqlite
```

**Expected result**: `Scored X documents`

## 🧹 STEP 7: CLEAN DATA
```bash
# Normalize metadata
python -m src.uwss.cli normalize-metadata --db data\uwss.sqlite

# Resolve duplicates
python -m src.uwss.cli dedupe-resolve --db data\uwss.sqlite
```

**Expected result**: 
- Normalize: `Normalized X records`
- Dedupe: `Resolved X duplicate groups`

## ✅ STEP 8: VALIDATE DATA QUALITY
```bash
# Validate data quality
python -m src.uwss.cli validate --db data\uwss.sqlite --json-out data\export\validation.json

# Generate statistics
python -m src.uwss.cli stats --db data\uwss.sqlite --json-out data\export\stats.json
```

**Expected result**:
- Validation: `{"dup_doi": [], "dup_title": [], "missing_core": [], "invalid_year": [], "missing_files": []}`
- Stats: Shows total records, OA count, distribution by source/year

## 📤 STEP 9: EXPORT DATA
```bash
# Full export with provenance
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates.jsonl --min-score 0.0 --year-min 1995 --sort relevance --skip-missing-core --include-provenance

# Open Access only export
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_oa.jsonl --min-score 0.0 --year-min 1995 --sort relevance --oa-only --skip-missing-core --include-provenance

# Clean export (higher precision)
python -m src.uwss.cli export --db data\uwss.sqlite --out data\export\candidates_clean_005.jsonl --min-score 0.05 --year-min 1995 --sort relevance --skip-missing-core --include-provenance
```

**Expected result**: 
- `Exported X records to data\export\candidates.jsonl`
- `Exported Y records to data\export\candidates_oa.jsonl`
- `Exported Z records to data\export\candidates_clean_005.jsonl`

## 📥 STEP 10: DOWNLOAD FILES
```bash
# Download Open Access files
python -m src.uwss.cli fetch --db data\uwss.sqlite --outdir data\files --limit 5 --config config\config.yaml
```

**Expected result**: 
- `Downloaded X files`
- Files saved in `data/files/` with unique names `_id{doc.id}`

## 🔍 STEP 11: CHECK RESULTS
```bash
# Check validation results
Get-Content data\export\validation.json

# Check statistics
Get-Content data\export\stats.json

# Check export files
Get-ChildItem data\export\*.jsonl

# Check downloaded files
Get-ChildItem data\files\
```

## 📊 HOW TO READ RESULTS

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

### **Common errors:**
1. **ModuleNotFoundError**: Run `pip install -r requirements.txt`
2. **Database locked**: Close all connections, restart terminal
3. **Network timeout**: Run command again, system has retry logic
4. **Permission denied**: Run PowerShell as Administrator

### **System check:**
```bash
# Check Python version
python --version

# Check virtual environment
.\.venv\Scripts\activate
python -c "import sys; print(sys.executable)"

# Check dependencies
python -c "import requests, sqlalchemy, scrapy; print('All dependencies OK')"
```

## ✅ EXPECTED RESULTS

After running completely, you will have:
- ✅ **Database**: `data/uwss.sqlite` with clean data
- ✅ **Exports**: Multiple JSONL files with provenance
- ✅ **Files**: Downloaded PDFs/HTMLs with unique names
- ✅ **Validation**: 100% clean data (0 issues)
- ✅ **Stats**: Balanced distribution by source/year

**System ready for production deployment!**

