BOT_NAME = 'scraper'

SPIDER_MODULES = ['app.scraper']
NEWSPIDER_MODULE = 'app.scraper'

ROBOTSTXT_OBEY = False

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000

CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 1

LOG_LEVEL = 'INFO'
