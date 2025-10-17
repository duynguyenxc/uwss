BOT_NAME = "uwss_scraper"
SPIDER_MODULES = ["src.uwss.crawl.scrapy_project.spiders"]
NEWSPIDER_MODULE = "src.uwss.crawl.scrapy_project.spiders"
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DEFAULT_REQUEST_HEADERS = {
	"User-Agent": "uwss/0.1 (+contact email in config)",
}
ITEM_PIPELINES = {
}
