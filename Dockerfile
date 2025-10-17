FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (if needed for lxml/pdfminer performance)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install pdfminer.six

COPY . .

# The application expects working dir root with config/ and data/ mounted
VOLUME ["/app/data", "/app/config", "/app/data/files", "/app/data/export"]

# Default command prints CLI help; override with args, e.g.:
# docker run --rm -v $PWD/data:/app/data uwss:latest python -m src.uwss.cli stats --db data/uwss.sqlite
CMD ["python", "-m", "src.uwss.cli"]


