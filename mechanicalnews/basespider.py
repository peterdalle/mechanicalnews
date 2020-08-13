# -*- coding: utf-8 -*-
"""
Basespider module contain the the base spider that all spiders must inherit.
There is also a class for article information extraction.
"""
import datetime
import json
from abc import abstractmethod
from mechanicalnews.items import FrontpageItem, ArticleItem, PageType, ArticleGenre
from mechanicalnews.settings import AppConfig
from mechanicalnews.utils import TextUtils
from mechanicalnews.extractors import ArticleExtractor
from scrapy.http import Request, Response
from scrapy.spiders import CrawlSpider
from scrapy_splash import SplashRequest, SlotPolicy
from scrapy_selenium import SeleniumRequest
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from twisted.python.failure import Failure


class BaseArticleSpider(CrawlSpider):
    """Base spider that all news article spiders must inherit.

    Spiders that sublcass this superclass will be part of the Mechanical News
    framework and automatically detected and started during a crawl. Just make
    sure that the spider is put in the `spiders` directory.

    You must always override the method `parse_article()`.

    - If `USE_LOGIN = True`, you must override `login()`
      and `after_login()`.
    - If `USE_SPLASH = True``, you must override `get_lua_script()`.

    This class performs automatic checks on the spider itself, as well as the
    content.
    """

    # Unique GUID of the spider. Each spider must have its own GUID.
    # You can generate a GUID with https://www.uuidgenerator.net/guid.
    # Do not touch the GUID below, though.
    SPIDER_GUID = "057d97fc-6a80-4c00-8c9f-7a8bc681b592"

    # Local ID of the spider. Created dynamically by the database ID (instead
    # of the GUID) to save space. Should not be set by the user.
    _SOURCE_ID = None

    # Fallback language. Used if the spider cannot automatically detect the
    # right language of the web page. Use ISO 639-1 format (two letters).
    # https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    DEFAULT_LANGUAGE = "en"

    # Use Scrapy Splash for scraping? Set to True to scrape dynamically
    # loaded JavaScript content via Scrapy-splash. Set to False to scrape
    # static HTML pages (recommended).
    USE_SPLASH = False

    # Use Selenium for scraping?
    USE_SELENIUM = False

    # Login before scraping? Set to True to login before scraping.
    USE_LOGIN = False

    # HTML <meta> tags that should not be saved. They do not contain any
    # useful information about the article.
    EXCLUDED_META_TAGS = ["viewport", "msapplication-config", "googlebot", "robots",
                          "format-detection", "theme-color", ""]

    @classmethod
    def __init_subclass__(subcls, **kwargs):
        """Runs when the child spider is initialized, and checks for bad
        implementations in the child spider.

        - Raises `NotImplementedError` for methods that have not been
          implemented by the child spider.
        - Raises `AttributeError` for methods that are mistakenly overriden
          by the child spider.
        - Raises `ValueError` if the child spider has the same `SPIDER_GUID`
          as `BaseArticleSpider`.
        """
        # Must implement.
        required_child_attributes = ["parse_article", "LAST_UPDATED", "DEFAULT_LANGUAGE",
                                     "SPIDER_GUID", "name", "allowed_domains", "start_urls"]
        for method in required_child_attributes:
            if method not in subcls.__dict__:
                raise NotImplementedError("{}() must implement {}.".format(subcls.__name__, method))
        # Cannot implement.
        disallowed_child_attributes = [
            "extract_information",
            "SOURCE_ID"
        ]
        for method in disallowed_child_attributes:
            if method in subcls.__dict__:
                raise AttributeError(("{} cannot implement {}. It's reserved" +
                    " for BaseArticleSpider.").format(subcls.__name__, method))
        # Spider GUID cannot be same as BaseArticleSpider GUID.
        if subcls.SPIDER_GUID == BaseArticleSpider.SPIDER_GUID:
            raise ValueError(("{} cannot have same GUID as BaseArticleSpider.").format(subcls.__name__))
        # Required combinations of attributes.
        if subcls.USE_SPLASH:
            if not hasattr(subcls, "get_lua_script") and not callable(subcls.get_lua_script):
                raise AttributeError(("{} is missing get_lua_script(), which" +
                                      " is required when USE_SPLASH is set" +
                                      " to True.").format(subcls.__name__))
        # Required combinations of attributes.
        if subcls.USE_LOGIN:
            if not hasattr(subcls, "login") and not callable(subcls.login):
                raise AttributeError(("{} is missing login(), which is required when USE_LOGIN" +
                                      " is set to True.").format(subcls.__name__))
            if not hasattr(subcls, "after_login") and not callable(subcls.after_login):
                raise AttributeError(("{} is missing after_login(), which is required when" +
                                      " USE_LOGIN is set to True.").format(subcls.__name__))

    def __repr__(self) -> str:
        """Get string representation of spider.

        Returns
        -------
        str
            Returns spider name and spider GUID.
        """
        return "{} ({})".format(self.name, self.SPIDER_GUID)

    def __str__(self) -> str:
        """Get string representation of spider.

        Returns
        -------
        str
            Returns spider name and spider GUID.
        """
        return self.__repr__()

    def start_requests(self) -> Request:
        """Start Scrapy spider request.

        Returns
        -------
        scrapy.http.Request
            For static web pages, an ordinary Scrapy Request() is returned.
            For dynamic web pages, a SplashRequest() is returned.
        """
        # Login. The login function will make a callback to the after_login()
        # method in the spider.
        if self.USE_LOGIN:
            self.logger.info("Paywall login...")
            yield self.login()
        # Request start URLs.
        for url in self.start_urls:
            self.logger.info("Requesting <{}>".format(url))
            yield self._get_request(url=url, callback=self.parse_frontpage)

    def closed(self, reason: str):
        """Runs when spider has closed.

        Parameters
        ----------
        reason: str
            Reason why the spider closed (e.g., 'finished', 'shutdown').
            Automatically passed on from the Scrapy spider.
        """
        self.logger.info("Spider {} closed (reason: {})".format(self.name, reason))

    def _get_request(self, url: str, callback=None) -> Request:
        """Make request to scrape webpage.

        Parameters
        ----------
        url: str
            URL to scrape.
        callback : object
            The function that will be called with the response of the
            request (once it's downloaded) as its first parameter.

        Returns
        -------
        scrapy.http.Request
            For static web pages, an ordinary Scrapy Request() is returned.
            For dynamic web pages, a SplashRequest() is returned.
        """
        if self._is_allowed_url(url):
            if self.USE_SPLASH:
                # For dynamic web pages, with JavaScript. Note that
                # Srapy-splash must be started separately.
                return SplashRequest(url=url,
                                     callback=callback,
                                     errback=self.handle_errors,
                                     args={ "lua_source": self.get_lua_script() },
                                     cache_args=['lua_source'],
                                     endpoint="execute",
                                     # Keeps cookies for session.
                                     session_id="foo",
                                     slot_policy=SlotPolicy.PER_DOMAIN)
            elif self.USE_SELENIUM:
                # For dynamic web pages, with JavaScript. Note that
                # a webdriver (e.g. Firefox) must be started separately.
                return SeleniumRequest(url=url, callback=callback, errback=self.handle_errors)
            else:
                # For static web pages, with plain HTML, using Scrapy.
                return Request(url=url, callback=callback, errback=self.handle_errors)
        else:
            self.logger.debug("Skipping, not allowed <{}>".format(url))

    def parse_frontpage(self, response: Response) -> FrontpageItem:
        """Parse and get article links on frontpage.

        Each link is later passed on to the `parse_article()` method.
        By default, all links are followed. This may be too many, and
        you can override this method in your child spider and specify a
        more specific set of links to follow if you prefer.

        Parameters
        ----------
        response : scrapy.http.Response
            Scrapy response object.

        Returns
        -------
        items.FrontpageItem
            Links from the frontpage and what URL/source the link came from.
        """
        frontpage_links = response.css("a::attr(href)").getall()
        absolute_urls = ArticleExtractor.make_absolute_urls(response.url, frontpage_links)
        self.logger.info("Found {} links <{}>".format(len(frontpage_links), response.url))
        yield FrontpageItem({
            "source_id": self._SOURCE_ID,
            "from_url": response.url,
            "links": absolute_urls,
        })
        for url in absolute_urls:
            yield self._get_request(url=url, callback=self.parse_article)

    def handle_errors(self, failure: Failure):
        """Log scraping failures from Scrapy requests.

        Parameters
        ----------
        failure : twisted.python.failure.Failure
            Contains connection establishment timeouts, DNS errors etc.
        """
        self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error("HttpError <{}>".format(response.url))
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error("DNSLookupError <{}>".format(request.url))
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error("TimeoutError <{}>".format(request.url))

    def _is_allowed_url(self, url: str) -> bool:
        """Make sure the URL is allowed (and therefore should be crawled).

        This is to ensure that only relevant pages are crawled and saved.

        Parameters
        ----------
        url : str
            URL to check.

        Returns
        -------
        bool
            Returns True if the URL is allowed, otherwise False.
        """
        for prefix in AppConfig.DISALLOWED_URL_PREFIXES:
            if url.lower().startswith(prefix):
                return False
        return True

    @abstractmethod
    def get_lua_script(self) -> str:
        """Get Lua script used by Scrapy Splash for scraping a single URL.

        This method is called from `ArticleBaseSpider.start_requests()` when
        `USE_SPLASH = True`.

        Example method content:

        ```python
        return '''
            function main(splash)
                splash.private_mode_enabled = false
                splash.images_enabled = false
                splash:init_cookies(splash.args.cookies)

                assert(splash:go(splash.args.url))
                assert(splash:wait(5))

                local entries = splash:history()
                local last_response = entries[#entries].response

                return {
                    html = splash:html(),
                    cookies = splash:get_cookies(),
                    headers = last_response.headers,
                    http_status = last_response.status,
                    cookies = splash:get_cookies(),
                }
            end'''
        ```
        Returns
        -------
        str
            Returns Lua script that will be used by Scrapy-splash.
        """
        raise NotImplementedError("Spider '{}' must implement get_lua_script().".format(self.name))

    @abstractmethod
    def login(self) -> Response:
        """Login through paywall.

        Scrapers with `USE_LOGIN = True` most override this method.

        Example
        -------
        ```python
        def login(self):
            return ScrapyRequest( ... )
        ```

        Returns
        -------
        scrapy.http.Response
            A Scrapy response object.
        """
        raise NotImplementedError("Spider '{}' must implement login().".format(self.name))

    @abstractmethod
    def after_login(self, response: Response):
        """What to do after login through paywall.

        Scrapers with `USE_LOGIN = True` most override this method.

        Parameters
        ----------
        response : scrapy.http.Response
            A Scrapy response object.
        """
        raise NotImplementedError("Spider '{}' must implement after_login().".format(self.name))

    @abstractmethod
    def parse_article(self, response: Response) -> ArticleItem:
        """Parse each scraped article.

        Called from `parse_frontpage()` and should yield
        an `ArticleItem`. See the example spiders for how-to.
        Each scraper must override this method.

        Parameters
        ----------
        response : scrapy.http.Response
            A Scrapy response object.

        Returns
        -------
        items.ArticleItem
            Should return an ArticleItem.
        """
        raise NotImplementedError("Spider '{}' must implement parse_article().".format(self.name))

    def extract_information(self, response: Response, item: ArticleItem) -> ArticleItem:
        """Adds additional metadata to an `ArticleItem` object.

        This method adds response headers, metadata, HTML, URL, <title>, text
        language, makes relative image URLs to absolute URLs, and counts length
        of lead and body. The method can be runned just before the child spider
        returns an `ArticleItem` in the `parse_article()` method.

        Parameters
        ----------
        response : scrapy.http.Response
            A Scrapy response object.
        item : items.ArticleItem
            An ArticleItem object from the child spider.

        Returns
        -------
        items.ArticleItem
            Return an ArticleItem with additional metadata.
        """
        self.item = item
        self.response = response
        self.meta_dict = None
        self._check_item_for_errors(self.item)
        self.extractor = ArticleExtractor.from_response(response)
        if self.extractor.microdata:
            self.item["metadata_raw"] = json.dumps(self.extractor.microdata)
        self.item["metadata"] = self.extractor.get_metatags(exclude_metatags=self.EXCLUDED_META_TAGS)
        self.item["source_id"] = self._SOURCE_ID
        self.item["url"] = response.url
        self.item["response_headers"] = response.headers
        self.item["response_meta"] = response.meta
        self.item["response_html"] = str(response.body)
        self.item["referer_url"] = response.request.url
        self.item["title_raw"] = response.css("title::text").get(default="")
        if self.item["body_html"]:
            self.item["body"] = TextUtils.html_to_text(self.item["body_html"])
        if not self.item["language"]:
            self.item["language"] = TextUtils.detect_language(text = self.item["body"], fallback=self.DEFAULT_LANGUAGE)
        self._set_text_counts()
        return self.item

    def _check_item_for_errors(self, item: ArticleItem):
        """Check ArticleItem for errors.

        Will rase a TypeError if `item` is not an ArticleItem, or if any of
        the items in the dictionary are of the wrong type.

        This method helps ensure that the data is of high quality before
        saving it.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem object from the child spider.
        """
        # Make sure item is the right data type.
        if not item:
            raise TypeError("Parameter 'item' cannot be empty.")
        if not isinstance(item, ArticleItem):
            raise TypeError("Parameter 'item' must be an ArticleItem.")
        # Make sure these are of correct data type.
        self._check_item_data_type(item, str, ["title", "title_raw", "h1", "lead", "body", "section"])
        self._check_item_data_type(item, list, ["images", "image_urls", "tags", "categories", "authors", "links"])
        self._check_item_data_type(item, int, ["source_id"])
        self._check_item_data_type(item, bool, ["is_deleted", "is_paywalled"])
        self._check_item_data_type(item, datetime.datetime, ["published", "edited"])
        self._check_item_data_type(item, PageType, ["page_type"])
        self._check_item_data_type(item, ArticleGenre, ["article_genre"])
        if item["body"]:
            ValueError("Item with key 'body' should not be set by spider. Set 'body_html' instead.")
        if item["title_raw"]:
            ValueError("Item with key 'title_raw' should not be set by spider. It's set automatically.")

    def _check_item_data_type(self, item: ArticleItem, data_type: object, fields: list):
        """Check that the article content have the right data types.

        Raises a `TypeError` if incorrect data type is found, otherwise it
        continues silently.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem object from the child spider.
        data_type : object
            Data type of the fields (bool, str, int, list etc).
        fields : list
            A list of names for which fields to check.
        """
        for key in fields:
            if item[key] and type(item[key]) != data_type:
                raise TypeError(("Key '{}' in 'item' must be of type '{}'.").format(key, data_type))

    def _set_text_counts(self):
        """Count the character length and word length of lead and body, as well
        as number of images and videos.

        Updates `self.item["body_length"]`, `self.item["body_words"]`,
        `self.item["lead_length"]`, and `self.item["lead_words"]`,"""
        if self.item["body"]:
            self.item["body_length"] = len(self.item["body"])
            self.item["body_words"] = TextUtils.count_words(self.item["body"])
        if self.item["lead"]:
            self.item["lead_length"] = len(self.item["lead"])
            self.item["lead_words"] = TextUtils.count_words(self.item["lead"])
        if self.item["image_urls"]:
            self.item["num_images"] = len(self.item["image_urls"])
