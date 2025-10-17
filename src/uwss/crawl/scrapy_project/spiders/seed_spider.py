import scrapy
from urllib.parse import urljoin, urlparse
import re
from sqlalchemy import select
from src.uwss.store import create_sqlite_engine, Document, Base


class SeedSpider(scrapy.Spider):
	name = "seed_spider"
	custom_settings = {
		"ROBOTSTXT_OBEY": True,
	}

	def __init__(self, start_urls=None, db_path="data/uwss.sqlite", max_pages: int = 10, keywords: str|None = None, allowed_domains_extra: str|None = None, path_blocklist: str|None = None, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.start_urls = start_urls.split(",") if isinstance(start_urls, str) else (start_urls or [])
		self.db_path = db_path
		self.max_pages = int(max_pages)
		self.pages_crawled = 0
		self.keyword_patterns = []
		if keywords:
			for kw in [k.strip() for k in keywords.split(",") if k.strip()]:
				self.keyword_patterns.append(re.compile(re.escape(kw), re.IGNORECASE))
		engine, self.SessionLocal = create_sqlite_engine(self.db_path)
		Base.metadata.create_all(engine)
		# Restrict to seed domains
		self.allowed_domains = [urlparse(u).netloc for u in self.start_urls if u]
		# Extra whitelist domains (comma-separated)
		self.allowed_domains_extra = []
		if allowed_domains_extra:
			self.allowed_domains_extra = [d.strip().lower() for d in allowed_domains_extra.split(",") if d.strip()]
		# Path blacklist (substring match)
		self.path_blocklist = []
		if path_blocklist:
			self.path_blocklist = [p.strip().lower() for p in path_blocklist.split(",") if p.strip()]

	def parse(self, response):
		# Limit total pages
		if self.pages_crawled >= self.max_pages:
			return
		self.pages_crawled += 1

		# Save the landing page as a candidate if keyword-relevant; extract basic HTML metadata
		session = self.SessionLocal()
		try:
			url = response.url
			exists = session.query(Document).filter(Document.source_url == url).first()
			title = response.css("title::text").get() or response.css("h1::text").get()
			abstract = None
			# heuristic: first <p> under main content
			abstract = response.css("main p::text").get() or response.css("p::text").get()
			# keyword filter: require at least one keyword match in title/body if patterns provided
			is_relevant = True
			if self.keyword_patterns:
				# Skip common non-content pages
				skip_titles = {"education", "aci university", "cooperating organizations"}
				if (title or "").strip().lower() in skip_titles:
					return
				full_text = (title or "") + "\n" + (" ".join(response.css("p::text").getall()) or "")
				is_relevant = any(p.search(full_text) for p in self.keyword_patterns)
			if not is_relevant:
				return
			if not exists:
				doc = Document(source_url=url, status="metadata_only", source="scrapy", title=title, abstract=abstract)
				session.add(doc)
				session.commit()
		finally:
			session.close()

		# Extract next links (only same domain, http/https)
		for href in response.css("a::attr(href)").getall():
			if not href or href.startswith("javascript:") or href.startswith("mailto:"):
				continue
			next_url = urljoin(response.url, href)
			parsed = urlparse(next_url)
			if parsed.scheme not in ("http", "https"):
				continue
			domain_ok = (parsed.netloc in self.allowed_domains) or (parsed.netloc.lower() in self.allowed_domains_extra)
			if not domain_ok:
				continue
			# Blocklist path substrings
			path_l = (parsed.path or "").lower()
			if any(b in path_l for b in self.path_blocklist):
				continue
			yield scrapy.Request(next_url, callback=self.parse)
