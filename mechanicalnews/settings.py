# -*- coding: utf-8 -*-
"""
Settings module for Scrapy as well as Mechanical News (AppConfig and
PaywalLogin).
"""
import json
from shutil import which

# Selenium options (see https://github.com/clemfromspace/scrapy-selenium)
SELENIUM_DRIVER_NAME = 'firefox'
SELENIUM_DRIVER_EXECUTABLE_PATH = "/mechanicalnews/webdriver/geckodriver.exe"
SELENIUM_DRIVER_ARGUMENTS = ['-headless']

# Name of crawler.
BOT_NAME = 'mechnewsbot'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# Crawler user-agent.
# USER_AGENT = 'mechnewsbot (+https://github.com/peterdalle/mechanicalnews)'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'

# Obey robots.txt rules.
ROBOTSTXT_OBEY = True

# Encoding for exporting files.
FEED_EXPORT_ENCODING = 'utf-8'

# Override the default request headers.
DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Language': 'sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Do not store duplicate Splash arguments in queue.
SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

# Enable downloader middlewares.
DOWNLOADER_MIDDLEWARES = {
    'scrapy_splash.SplashCookiesMiddleware': 720,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy_selenium.SeleniumMiddleware': 800,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Configure item pipelines.
ITEM_PIPELINES = {
    'scrapy.pipelines.images.ImagesPipeline': 100,
    'pipelines.MySQLPipeline': 200,
}

# Scrapy-splash to handle JavaScript web pages. End URL with /.
SPLASH_URL = 'http://127.0.0.1:8050/'
DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'

# Show cookies sent/retrieved from Splash.
SPLASH_COOKIES_DEBUG = False

# Maximum concurrent requests performed by Scrapy. Limit to 1 while debugging.
CONCURRENT_REQUESTS = 1

# Delay for requests for the same website.
DOWNLOAD_DELAY = 3
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# Enable AutoThrottle extension.
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Cache all HTTP requests. Set to True during development, False on production.
HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
# HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

# Only log information.
LOG_LEVEL = 'INFO'

# Where to store article images.
IMAGES_STORE = '/mechanicalnews/data/images'

# Generate image thumbnails of news article images.
# Thumbnails are saved in <IMAGES_STORE>/thumbs/<size_name>/<image_id>.jpg
# where <size_name> is the one specified in the IMAGES_THUMBS dictionary keys
# (small, big, etc) and <image_id> is the SHA1 hash of the image url.
IMAGES_THUMBS = {
    'medium': (270, 270),
}

# Minimum size of images. Do not include images that are smaller
# than this. This does not affect thumbnail generation.
IMAGES_MIN_WIDTH = 110
IMAGES_MIN_HEIGHT = 110

# Follow images that are redirected to another URL.
MEDIA_ALLOW_REDIRECTS = True

# Don't download article images again for at least this number of days.
IMAGES_EXPIRES = 30

# Crawl in breadth-first order (pages near frontpage first).
# DEPTH_PRIORITY = 1
# SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
# SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'


class AppConfig():
    """Settings that a specific to Mechanical News are placed here."""

    # MySQL/MariaDB database settings (required).
    MYSQL_HOST = 'localhost'
    MYSQL_DB = 'mechanicalnews'
    MYSQL_USER = 'root'
    MYSQL_PASS = 'root'
    MYSQL_CHARSET = "utf8"
    MYSQL_AUTH_PLUGIN = 'mysql_native_password'

    # E-mail settings.
    EMAIL_ENABLE = False
    EMAIL_FROM_NAME = "Mechanical News"
    EMAIL_FROM_ADDRESS = "mechanicalnews@mechanicalnews.com"
    EMAIL_TO_ADDRESS = ""
    EMAIL_SMTP_SERVER = ""
    EMAIL_SMTP_PORT = None

    # Mechanical News Flask Restful API settings.
    WWW_URL = 'http://127.0.0.1:5000'
    API_URL = 'http://127.0.0.1:5000/api/v1'

    # Directories and URLs for downloaded images.
    ROOT_IMAGES_DIRECTORY = IMAGES_STORE
    FULL_IMAGES_DIRECTORY = IMAGES_STORE + "/full"
    THUMB_IMAGES_DIRECTORY = IMAGES_STORE + "/thumbs/medium"
    FULL_IMAGES_URL = WWW_URL + "/full"
    THUMB_IMAGES_URL = WWW_URL + "/thumbs/medium"

    # Directory to store full HTML copies of web pages in file system.
    # Leave empty to not store.
    HTML_FILES_DIRECTORY = "/mechanicalnews/data/full_html"

    # Whether or not to save all metadata (JSON-LD, Microdata, Microformat,
    # OpenGraph, and RDFa) into database. This data is also accessible via the
    # API.
    SAVE_RAW_METADATA_IN_DATABASE = True

    # URLs that starts with these characters should be excluded from
    # the crawling, as well as links that are saved in articles.
    DISALLOWED_URL_PREFIXES = ["tel:", "mailto:", "javascript:",
                               "ftp:", "sftp:", "settings:", "sms:",
                               "fb-messenger:", "settings:", "#"]


class PaywallLogin():
    """Get paywall logins (username and password) for spiders.

    The JSON file with paywall logins should look like this:

    ```json
    {
        "spiders": {
            "bbc": {
                "username": "root@example.com",
                "password": "secret"
            },
            "newyorktimes": {
                "username": "root@example.com",
                "password": "secret"
            }
        }
    }
    ```
    """
    # Filename (relative to settings.py) to the JSON file with paywall logins.
    FILENAME = "paywall_login.json"

    @staticmethod
    def get_json() -> dict:
        """Get dictionary of paywall logins.

        Returns
        -------
        dict
            Returns a dictionary with all the file contents.
        """
        with open(PaywallLogin.FILENAME) as file:
            data = json.load(file)
        return data

    @staticmethod
    def get_spider_login(spider_name: str) -> tuple:
        """Get login tuple `(username, password)` for a particular spider.

        Parameters
        ----------
        spider_name : str
            Name of spider.

        Returns
        -------
        tuple
            Returns a tuple as `(username, password)`. If no login is found,
            a `KeyError` is raised.
        """
        paywalls = PaywallLogin.get_json()
        try:
            spiders = paywalls["spiders"]
            return (spiders[spider_name]["username"],
                    spiders[spider_name]["password"])
        except KeyError:
            raise KeyError(
               "Paywall login keys not found for spider '{}'.".format(
                   spider_name))
