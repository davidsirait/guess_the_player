BOT_NAME = 'transfermarkt_scraper'

SPIDER_MODULES = ['transfermarkt_scraper.spiders']
NEWSPIDER_MODULE = 'transfermarkt_scraper.spiders'

# Crawl responsibly by identifying yourself
USER_AGENT = 'guess-the-player/1.0 (https://github.com/davidsirait/guess-the-player)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Configure a delay for requests (in seconds)
# Respect the Crawl-delay: 2 from robots.txt
DOWNLOAD_DELAY = 3

# Enable AutoThrottle for adaptive delays
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Enable retry middleware
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Configure item pipelines
ITEM_PIPELINES = {
    'transfermarkt_scraper.json_pipeline.JsonWriterPipeline': 300,
    'transfermarkt_scraper.db_pipeline.DuckDBPipeline': 400,
}

# Set log level
LOG_LEVEL = 'INFO'

# Enable HTTP caching (helps with development and reduces load)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [404, 500, 502, 503]

# Disable cookies unless needed
COOKIES_ENABLED = False

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
}

# DuckDB database path
DUCKDB_DATABASE = 'transfermarkt.db'

# Output file paths
PLAYER_OUTPUT_FILE = 'output/players.json'
TRANSFER_OUTPUT_FILE = 'output/transfers.json'