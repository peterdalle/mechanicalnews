# -*- coding: utf-8 -*-
"""
Pipelines module responsible for saving articles and its related metadata
to the database and file system.
"""
import datetime
import mysql.connector
from scrapy.crawler import Crawler
from scrapy.spiders import Spider
from mechanicalnews.items import FrontpageItem, ArticleItem, LogAction
from mechanicalnews.sources import SourceManager
from mechanicalnews.utils import TextUtils, WebUtils
from mechanicalnews.settings import AppConfig
from mechanicalnews.storage import StaticFiles

class MySQLPipeline(object):
    """Pipeline to save scraped items to MySQL/MariaDB."""

    def __init__(self, database: str, username: str, password: str, charset: str, auth_plugin: str):
        """Default constructor.

        Parameters
        ----------
        database : str
            Name of MySQL database.
        username : str
            Username to the database server.
        password : str
            Password to the database server.
        charset : str
            Character encoding set.
        auth_plugin : str
            MySQL database authentication. Either 'mysql_native_password' for
            the traditional method of authentication (hash of password) or
            '' (empty string) for the newer and more secure authentication.
        """
        self.database = database
        self.username = username
        self.password = password
        self.charset = charset
        self.auth_plugin = auth_plugin

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        """Return new instance of this pipeline.

        Parameters
        ----------
        crawler : scrapy.crawler.Crawler
            Scrapy crawler object.

        Returns
        -------
        MySQLPipeline
            Returns a new MySQLPipeline object.
        """
        return cls(database=AppConfig.MYSQL_DB,
                   username=AppConfig.MYSQL_USER,
                   password=AppConfig.MYSQL_PASS,
                   charset=AppConfig.MYSQL_CHARSET,
                   auth_plugin=AppConfig.MYSQL_AUTH_PLUGIN)

    def open_spider(self, spider: Spider):
        """Runs when spider opens. Opens database connection.

        Parameters
        ----------
        spider : scrapy.spiders.Spider
            A Scrapy spider object.
        """
        self._register_spider(spider)
        SourceManager.set_spider_last_run(guid=spider.SPIDER_GUID)
        self.spider_name = spider.name
        self.conn = mysql.connector.connect(database=self.database,
                                            user=self.username,
                                            password=self.password,
                                            auth_plugin=self.auth_plugin,
                                            charset=self.charset)
        self.cur = self.conn.cursor(buffered=True)
        self.cur.execute("SET NAMES 'utf8mb4';")
        self.cur.execute("SET CHARACTER SET utf8mb4;")
        self.save_log_action(LogAction.OPEN_SPIDER,
                             source_id=spider._SOURCE_ID)

    def _register_spider(self, spider: Spider):
        """Register spider using the GUID.

        Registering the spider means that the spider GUID is saved in the
        database table `sources`, and a local ID is used because it's shorter
        and saves space.

        Parameters
        ----------
        spider : scrapy.spiders.Spider
            A Scrapy spider object.
        """
        spider._SOURCE_ID = SourceManager.register_spider(name=spider.name, guid=spider.SPIDER_GUID)
        if spider._SOURCE_ID:
            spider.logger.info("Spider registered as #{}".format(spider._SOURCE_ID))
        else:
            spider.logger.warn("Couldn't register ID for '{}' (GUID {})".format(
                               spider.name, spider.SPIDER_GUID))

    def close_spider(self, spider: Spider):
        """Runs when spider closes. Closes database connection.

        Parameters
        ----------
        spider : scrapy.spiders.Spider
            A Scrapy spider object.
        """
        self.save_log_action(LogAction.CLOSE_SPIDER, source_id=spider._SOURCE_ID)
        self.save_scraping_stats(spider)
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def process_item(self, item: ArticleItem, spider: Spider):
        """Process scraped item, save to database.

        If it's an item that has been scraped from the frontpage of a news
        site, then call `_process_frontpage()`. If it's a specific news
        article, then call `_process_article()`.

        Parameters
        ----------
        item : object
            An items.ArticleItem or items.FrontpageItem with the extracted
            information from the news article, or the frontpage.
        spider : scrapy.spiders.Spider
            A Scrapy spider object.
        """
        # Add standard meta data fields.
        self.spider = spider
        item["added"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Process frontpage or article.
        if type(item) == FrontpageItem:
            self._process_frontpage(item)
        if type(item) == ArticleItem:
            self._process_article(item)
        return item

    def _process_frontpage(self, item: FrontpageItem):
        """Process scraped frontpage item, save to database.

        Parameters
        ----------
        item : items.FrontpageItem
            An FrontpageItem with the extracted information from the frontpage
            of a news site.
        """
        if item["links"]:
            # Insert frontpage links into database.
            from_url_id, _ = self._create_or_get_url_id_from_url(item["from_url"])
            for link in item["links"]:
                to_url_id, _ = self._create_or_get_url_id_from_url(link)
                sql_query = "INSERT INTO frontpage_articles (source_id, from_url_id, to_url_id, added)" + \
                            " VALUES (%s, %s, %s, %s)"
                self.cur.execute(sql_query, (
                    TextUtils.sanitize_int(item["source_id"], default=0),
                    TextUtils.sanitize_int(from_url_id, default=0),
                    TextUtils.sanitize_int(to_url_id, default=0),
                    TextUtils.sanitize_str(item["added"], default=None),
                ))
                self.conn.commit()

    def _process_article(self, item: ArticleItem):
        """Process scraped article item and save to database.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        """
        # Get ID of the URL (create URL if it doesn't exists).
        url_id, is_new = self._create_or_get_url_id_from_url(item["url"])
        if is_new:
            # Save completely new article.
            article_id = self._insert_article(item, url_id)
            self.save_log_action(LogAction.ADD_ARTICLE, article_id=article_id, item=item)
            self.spider.logger.info("Saved #{} <{}>".format(article_id, item["url"]))
        else:
            # Existing article found: has it changed since previous scraping?
            is_changed, parent_id = self._detect_article_changes(item, url_id)          
            if is_changed:
                # Changes found: save new version.
                article_id = self._insert_article(item, url_id)
                self.save_log_action(LogAction.ADD_VERSION, article_id=parent_id, item=item)
                self.spider.logger.info("Saved changes #{} <{}>".format(article_id, item["url"]))
            else:
                # No changes found, don't save.
                self.save_log_action(LogAction.NO_CHANGE_SKIP, article_id=parent_id, item=item)

    def _detect_article_changes(self, item: ArticleItem, url_id: int) -> tuple:
        """Check whether the content of an existing has changed.

        The comparison is done against the last saved version.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        url_id : int
            ID to an existing URL.

        Returns
        -------
        tuple
            Returns a tuple (bool, int) that indicates whether the content
            has changed (bool), and the ID of the previous article (int).
            If no article is found, the article ID of `None` is returned.
        """
        new_checksum = item.compute_checksum()
        old_article = self._get_article_checksum_by_url_id(url_id)
        old_checksum = old_article["checksum"] if old_article else None
        has_changed = (new_checksum != old_checksum)
        parent_id = old_article["article_id"] if old_article else None
        return has_changed, parent_id

    def _insert_article(self, item: ArticleItem, url_id: int) -> int:
        """Insert article to database, plus related metadata.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        url_id : int
            ID to an existing URL.
        """
        article_id = self.save_article_and_get_id(item, url_id)
        self.save_article_images(item, article_id)
        self.save_article_links(item, article_id)
        self.save_article_metadata(item, article_id)
        self.save_article_http_headers(item, article_id)
        self.save_article_html(item, article_id)
        StaticFiles.save_html_file(item["response_html"], article_id)
        return article_id

    def _create_or_get_url_id_from_url(self, url: str) -> tuple:
        """Get URL ID by URL.

        Parameters
        ----------
        url : str
            A URL to a web page that should be created.

        Returns
        -------
        tuple
            Returns a tuple (int, bool), with an ID (int) of the URL and
            a flag indicating whether it was Inserted (bool) or not. If URL
            could not be inserted, the tuple (0, False) is returned.
        """
        # Find ID of URL.
        url_id = self._get_url_id_from_url(url, use_checksum=True)
        if url_id:
            return url_id, False
        # Couldn't find ID: Create URL and get its ID.
        try:
            domain = WebUtils.get_domain_name(url)
            url_checksum = TextUtils.md5_hash(url)
            sql_query = "INSERT INTO article_urls (url, domain, checksum) VALUES(%s, %s, %s)"
            self.cur.execute(sql_query, (
                TextUtils.sanitize_str(url, default="", keep_newlines=False),
                TextUtils.sanitize_str(domain, default=None),
                TextUtils.sanitize_str(url_checksum, default="")))
            return self.cur.lastrowid, True
        except mysql.connector.OperationalError:
            # Couldn't insert. Likely "duplicate key". Get ID slow way.
            url_id = self._get_url_id_from_url(url, use_checksum=False)
            if url_id:
                return url_id, False
        except mysql.connector.IntegrityError:
            # Couldn't insert. Likely "duplicate key". Get ID slow way.
            url_id = self._get_url_id_from_url(url, use_checksum=False)
            if url_id:
                return url_id, False
        # If everything fails, use 0.
        return 0, False

    def _get_url_id_from_url(self, url: str, use_checksum=True) -> int:
        """Get ID from a URL. Returns `None` if it doesn't exist.

        Parameters
        ----------
        url : str
            A URL to a web page.
        use_checksum : bool
            Whether to lookup by checksum (faster, but the URL has to exist
            already) or by looking for the specific URL (slower, but the URL
            does not need to exist already).

        Returns
        -------
        int
            Returns the ID for the URL. If URL is not found, None is returned.
        """
        if use_checksum:
            # Fast URL lookup using MD5 checksums (by index).
            url_checksum = TextUtils.md5_hash(url)
            self.cur.execute("SELECT id FROM article_urls WHERE checksum = %s", (url_checksum, ))
            for row in self.cur.fetchall():
                return row[0]
        else:
            # Slow URL lookup using string comparison.
            self.cur.execute("SELECT id FROM article_urls WHERE url = %s", (url, ))
            for row in self.cur.fetchall():
                return row[0]
        return None

    def _get_article_checksum_by_url_id(self, url_id: int) -> dict:
        """Get article checksum by article URL ID.

        Gets the checksum for the last saved version of the article.

        Parameters
        ----------
        url_id : int
            ID to an existing URL.

        Returns
        -------
        dict
            Returns a dict with the keys "article_id" and "checksum". Returns
            None if no article is found.
        """
        self.cur.execute("SELECT id, checksum FROM articles" +
                         " WHERE url_id = %s ORDER BY id DESC LIMIT 1", (url_id, ))
        if self.cur:
            for row in self.cur:
                return {"article_id": row[0], "checksum": row[1]}
        return None

    def save_article_and_get_id(self, item: ArticleItem, url_id: int) -> int:
        """Save article information to database, and return ID of article.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        url_id : int
            ID to an existing URL.

        Returns
        -------
        int
            Returns the ID of the created article.
        """
        if not item:
            raise AttributeError("Cannot save article: 'item' is missing.")
        if not item["source_id"]:
            raise AttributeError("Cannot save article: 'source_id' is missing from item.")
        if not url_id > 0:
            raise AttributeError("Cannot save article: 'url_id' is missing.")
        try:
            sql_query = """INSERT INTO articles
                        (parent_id, source_id, url_id, added, page_type,
                        article_genre, is_paywalled, is_deleted, checksum,
                        title, h1, `lead`, body, published, edited, author,
                        language, section, tags, categories, num_videos,
                        num_images, lead_length, lead_words, body_length,
                        body_words) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s)"""
            self.cur.execute(sql_query, (
                item["parent_id"],
                item["source_id"],
                url_id,
                item["added"],
                int(item["page_type"]),
                int(item["article_genre"]),
                int(item["is_paywalled"]),
                int(item["is_deleted"]),
                item.compute_checksum(),
                TextUtils.sanitize_str(item["title"], default="",
                                       keep_newlines=False),
                TextUtils.sanitize_str(item["h1"], default="",
                                       keep_newlines=False),
                TextUtils.sanitize_str(item["lead"], default=""),
                TextUtils.sanitize_str(item["body"], default=""),
                TextUtils.sanitize_str(item["published"], default=None),
                TextUtils.sanitize_str(item["edited"], default=None),
                TextUtils.convert_list_to_string(item["authors"], sep="\n",
                                                 strip=True, default=""),
                TextUtils.sanitize_str(item["language"], default=""),
                TextUtils.sanitize_str(item["section"], default=""),
                TextUtils.convert_list_to_string(item["tags"], sep="\n",
                                                 strip=True, default=""),
                TextUtils.convert_list_to_string(item["categories"], sep="\n",
                                                 strip=True, default=""),
                TextUtils.sanitize_int(item["num_videos"], default=0),
                TextUtils.sanitize_int(item["num_images"], default=0),
                TextUtils.sanitize_int(item["lead_length"], default=0),
                TextUtils.sanitize_int(item["lead_words"], default=0),
                TextUtils.sanitize_int(item["body_length"], default=0),
                TextUtils.sanitize_int(item["body_words"], default=0)
            ))
            article_id = self.cur.lastrowid
            self.conn.commit()
            return article_id
        except mysql.connector.Error as err:
            self.spider.logger.error(
                "Couldn't save: {} <{}>".format(err, item["url"]))
        return None

    def save_article_links(self, item: ArticleItem, article_id: int):
        """Save article links to database.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        article_id : int
            ID to an existing article.
        """
        if item["links"] and article_id:
            for link in item["links"]:
                if link:
                    to_url_id, _ = self._create_or_get_url_id_from_url(link)
                    if to_url_id > 0:
                        sql_query = "INSERT INTO article_links" + \
                                    " (article_id, to_url_id) VALUES (%s, %s)"
                        self.cur.execute(sql_query, (article_id, to_url_id, ))
                        self.conn.commit()

    def save_article_images(self, item: ArticleItem, article_id: int):
        """Save article images to database.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        article_id : int
            ID to an existing article.
        """
        if item["images"] and article_id:
            for image in item["images"]:
                sql_query = "INSERT INTO article_images (article_id, url, path, checksum)" + \
                            " VALUES (%s, %s, %s, %s)"
                self.cur.execute(sql_query, (article_id, image["url"],
                                             image["path"],
                                             image["checksum"], ))
                self.conn.commit()

    def save_article_http_headers(self, item: ArticleItem, article_id: int):
        """Save article HTTP headers to database.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        article_id : int
            ID to an existing article.
        """
        if item["response_headers"] and article_id:
            for header in item["response_headers"]:
                sql_query = "INSERT INTO article_headers (article_id, name, value) VALUES (%s, %s, %s)"
                self.cur.execute(sql_query,
                                 (article_id,
                                  header,
                                  item["response_headers"][header], ))
                self.conn.commit()

    def save_article_metadata(self, item: ArticleItem, article_id: int):
        """Save article <meta> tags to database.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        article_id : int
            ID to an existing article.
        """
        if item["metadata"] and article_id:
            for meta in item["metadata"]:
                if meta["content"] != "":
                    sql_query = "INSERT INTO article_meta (article_id, name, content, is_property)" + \
                                " VALUES (%s, %s, %s, %s)"
                    self.cur.execute(sql_query, (
                      article_id,
                      TextUtils.sanitize_str(meta["name"],
                                             keep_newlines=False),
                      TextUtils.sanitize_str(meta["content"]),
                      TextUtils.sanitize_int(meta["is_property"], default=0),
                    ))
                    self.conn.commit()

    def save_article_html(self, item: ArticleItem, article_id: int):
        """Save raw title, body HTML, and metadata to database.

        Parameters
        ----------
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        article_id : int
            ID to an existing article.
        """
        if not article_id:
            return
        if AppConfig.SAVE_RAW_METADATA_IN_DATABASE:
            # Save copy of metadata in database.
            sql_query = "INSERT INTO article_raw (article_id, title, body, metadata)" + \
                        " VALUES (%s, %s, %s, %s)"
            try:
                self.cur.execute(sql_query,
                                 (article_id,
                                     str(item["title_raw"]).strip(),
                                     item["body_html"],
                                     str(item["metadata_raw"]).strip()))
                self.conn.commit()
            except mysql.connector.errors.DataError as err:
                self.spider.logger.warn("save_article_html(): {}".format(err))

    def save_log_action(self, action: LogAction, user="",
                        source_id=0, article_id=0, item=None):
        """Save log action that describe what was done.

        Parameters
        ----------
        action : LogAction
            An action describing the activity.
        user : str
            The API user responsible for creating the event.
        source : str
            The spider responsible for creating the event.
        article_id : int
            ID of the article the event is about.
        item : items.ArticleItem
            An ArticleItem with the extracted information from a news article.
        """
        latency = None
        if item:
            source_id = TextUtils.sanitize_int(item["source_id"], default=0)
            try:
                latency = item["response_meta"]["download_latency"]
                latency = round(latency * 1000) if latency else None
            except KeyError:
                latency = None
        sql_query = "INSERT INTO log" + \
                    " (action_id, added, source_id, article_id, latency)" + \
                    " VALUES (%s, %s, %s, %s, %s)"
        added = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cur.execute(sql_query, (int(action), added, source_id,
                                     article_id, latency))
        self.conn.commit()

    def save_scraping_stats(self, spider: Spider):
        """Save Scrapy crawler statistics.

        Parameters
        ----------
        spider : scrapy.spiders.Spider
            A Scrapy spider object.
        """
        return
        # TODO: stats object is empty. Figure out why.
        stats = spider.crawler.stats.get_stats()
        sql = """INSERT INTO scrapy_stats
                (source_id,
                downloader_request_count,
                downloader_response_bytes,
                downloader_response_count,
                downloader_response_status_count_200,
                downloader_response_status_count_301,
                downloader_response_status_count_302,
                downloader_response_status_count_404,
                log_count_error,
                response_received_count,
                item_scraped_count,
                start_time,
                finish_time,
                finish_reason,
                elapsed_time_seconds)
                VALUES (%s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s)"""
        params = (spider._SOURCE_ID,
                  int(stats["downloader_request_count"]),
                  int(stats["downloader_response_bytes"]),
                  int(stats["downloader_response_count"]),
                  int(stats["downloader_response_status_count_200"]),
                  int(stats["downloader_response_status_count_301"]),
                  int(stats["downloader_response_status_count_302"]),
                  int(stats["downloader_response_status_count_404"]),
                  int(stats["log_count_error"]),
                  int(stats["response_received_count"]),
                  int(stats["item_scraped_count"]),
                  stats["start_time"],
                  stats["finish_time"],
                  str(stats["finish_reason"]),
                  int(stats["elapsed_time_seconds"]))
        self.cur.execute(sql, params)
        self.conn.commit()
