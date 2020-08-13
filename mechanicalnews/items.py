# -*- coding: utf-8 -*-
"""
Module for article items used by Scrapy, and different types of enums used
to classify the article content.
"""
import scrapy
from enum import IntEnum
from mechanicalnews.utils import DateUtils, WebUtils, TextUtils


class PageType(IntEnum):
    """Type of web page.

    `NONE` = generic web page.
    `ARTICLE` = specific article.
    `COLLECTION` = collection of articles (e.g., frontpage, subsection,
    categories, topics).

    Primarily used by each spider to classify the content, and the value is
    stored in the MySQL table field `articles.page_type`.
    """
    NONE = 0
    ARTICLE = 1
    COLLECTION = 2
    SOUND = 3
    VIDEO = 4


class ArticleGenre(IntEnum):
    """Genre of article.

    `NONE` = generic web page.
    `NEWS` = news article.
    `EDITORIAL` = news editorial, news columnist, chronical.
    `OPINION` = opinion piece, debate article, letter to the editor.
    `SPORTS` = any sport.
    `ADVERTISEMENT` = advertisement, native ad.
    `ENTERTAINMENT` = culture, movies, books, events, life style.
    `TECHNOLOGY` = cars, boats, machines, digital, science, tech.
    `PERSONAL` = human interest, family, relationships, portraits, health.
    `ECONOMY` = world/national economy, business, industry, personal finance.

    Primarily used by each spider to classify the content, and the value is
    stored in the MySQL table field `articles.article_genre`.
    """
    NONE = 0
    NEWS = 1
    EDITORIAL = 2
    OPINION = 3
    SPORTS = 4
    ADVERTISEMENT = 5
    ENTERTAINMENT = 6
    TECHNOLOGY = 7
    PERSONAL = 8
    ECONOMY = 9


class LogAction(IntEnum):
    """Type of action that was performed.

    Used for logging purposes. Used for field `action_id` in the `log` database
    table.
    """
    NONE = 0             # No specific category.
    OPEN_SPIDER = 1      # The spider opened for crawling.
    CLOSE_SPIDER = 2     # The spider closed for crawling.
    ADD_ARTICLE = 3      # An article (web page) was added to the database.
    ADD_VERSION = 4      # A version of an existing article was added.
    NO_CHANGE_SKIP = 5   # No article changes were detected, no version added.

    def __repr__(self) -> str:
        """Convert to human-readable message.

        Returns
        -------
        str
            Returns a human-readable message of the object.
        """
        if self == LogAction.ADD_ARTICLE:
            return "Added new article"
        elif self == LogAction.ADD_VERSION:
            return "Added new version to existing article"
        elif self == LogAction.NO_CHANGE_SKIP:
            return "No article changes detected, skipped"
        elif self == LogAction.OPEN_SPIDER:
            return "Spider started crawling"
        elif self == LogAction.CLOSE_SPIDER:
            return "Spider stopped crawling"
        elif self == LogAction.NONE:
            return "No action category set"
        else:
            return "Unknown action"

    def __str__(self) -> str:
        """Convert object to a string.

        Returns
        -------
        str
            Returns a human-readable message of the object.
        """
        return self.__repr__()


class FrontpageItem(scrapy.Item):
    """Item for a scraped news frontpage, or section,
    that contain a collection of news articles.

    Primarily used by `BaseArticleSpider.parse_frontpage()`.
    """
    source = scrapy.Field()
    source_id = scrapy.Field()
    from_url = scrapy.Field()
    links = scrapy.Field()
    added = scrapy.Field()
    parent_id = scrapy.Field()

    def __repr__(self) -> str:
        """Get string representation of object.

        Returns
        -------
        str
            Returns a human-readable message of the object.
        """
        return "FrontPageItem() {} (#{})".format(self.get("source"), self.get("source_id"))

    def __str__(self) -> str:
        """Get string representation of object.

        Returns
        -------
        str
            Returns a human-readable message of the object.
        """
        return self.__repr__()


class ArticleItem(scrapy.Item):
    """Item for a single scraped news article.

    The primary item for dealing with article content, and used heavily in
    the modules `basespider` and `pipelines`.
    """
    article_id = scrapy.Field()
    url_id = scrapy.Field()
    checksum = scrapy.Field()
    domain = scrapy.Field()
    source = scrapy.Field()
    source_id = scrapy.Field()
    referer_url = scrapy.Field()
    parent_id = scrapy.Field()
    added = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    title_raw = scrapy.Field()
    h1 = scrapy.Field()
    lead = scrapy.Field()
    body = scrapy.Field()
    body_html = scrapy.Field()
    authors = scrapy.Field()
    language = scrapy.Field()
    section = scrapy.Field()
    tags = scrapy.Field()
    categories = scrapy.Field()
    published = scrapy.Field(serializer=str)
    edited = scrapy.Field(serializer=str)
    is_deleted = scrapy.Field(serializer=bool)
    is_paywalled = scrapy.Field(serializer=bool)
    num_videos = scrapy.Field()
    num_images = scrapy.Field()
    lead_length = scrapy.Field()
    lead_words = scrapy.Field()
    body_length = scrapy.Field()
    body_words = scrapy.Field()
    article_genre = scrapy.Field(serializer=int)
    page_type = scrapy.Field(serializer=int)
    metadata = scrapy.Field()
    metadata_raw = scrapy.Field()
    links = scrapy.Field()
    response_headers = scrapy.Field()
    response_meta = scrapy.Field()
    response_html = scrapy.Field()
    images = scrapy.Field()        # Used by Scrapy:s ImagesPipeline.
    image_urls = scrapy.Field()    # Used by Scrapy:s ImagesPipeline.
    log = scrapy.Field()

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)
        self.populate_default_values()

    def __repr__(self) -> str:
        """Get string representation of object.

        Returns
        -------
        str
            Returns a human-readable message of the object.
        """
        return "ArticleItem(url='{}')".format(self.get("url"))

    def __str__(self) -> str:
        """Get string representation of object.

        Returns
        -------
        str
            Returns a human-readable message of the object.
        """
        return self.__repr__()

    def populate_default_values(self):
        """Set a standard value for all attributes."""
        self.setdefault("article_id", None)
        self.setdefault("url_id", None)
        self.setdefault("checksum", None)
        self.setdefault("domain", None)
        self.setdefault("source_id", 0)
        self.setdefault("referer_url", None)
        self.setdefault("parent_id", 0)
        self.setdefault("added", None)
        self.setdefault("url", None)
        self.setdefault("title", None)
        self.setdefault("title_raw", None)
        self.setdefault("h1", None)
        self.setdefault("lead", None)
        self.setdefault("body", None)
        self.setdefault("body_html", None)
        self.setdefault("authors", [])
        self.setdefault("language", None)
        self.setdefault("section", None)
        self.setdefault("tags", [])
        self.setdefault("categories", [])
        self.setdefault("published", None)
        self.setdefault("edited", None)
        self.setdefault("is_deleted", False)
        self.setdefault("is_paywalled", False)
        self.setdefault("num_videos", 0)
        self.setdefault("num_images", 0)
        self.setdefault("lead_length", 0)
        self.setdefault("lead_words", 0)
        self.setdefault("body_length", 0)
        self.setdefault("body_words", 0)
        self.setdefault("article_genre", ArticleGenre.NONE)
        self.setdefault("page_type", PageType.NONE)
        self.setdefault("metadata", None)
        self.setdefault("metadata_raw", None)
        self.setdefault("links", [])
        self.setdefault("response_headers", None)
        self.setdefault("response_meta", None)
        self.setdefault("response_html", None)
        self.setdefault("images", [])
        self.setdefault("image_urls", [])

    @classmethod
    def from_datarow(cls, row: dict):
        """Create a new instance of ArticleItem from a MySQL data row.

        Parameters
        ----------
        row : dict
            A database row from MySQL.

        Returns
        -------
        ArticleItem
            Returns a new instance of ArticleItem.
        """
        cls = ArticleItem({
            "article_id": int(row["id"]),
            "parent_id": int(row["parent_id"]),
            "source_id": int(row["source_id"]),
            "source": row["source"],
            "domain": WebUtils.get_domain_name(row["url"]),
            "url_id": int(row["url_id"]),
            "url": row["url"],
            "title": row["title"],
            "lead": row["lead"],
            "added": row["added"],
            "published": row["published"],
            "edited": row["edited"],
            "body": row["body"],
            "section": row["section"],
            "categories": row["categories"],
            "tags": row["tags"],
            "authors": row["author"],
            "language": row["language"],
            "is_deleted": bool(row["is_deleted"]),
            "is_paywalled": bool(row["is_paywalled"]),
            "checksum": row["checksum"],
            "num_images": int(row["num_images"]),
            "num_videos": int(row["num_videos"]),
            "page_type": row["page_type"],
            "article_genre": row["article_genre"],
        })
        return cls

    def get_json(self, include_lists=True, iso_date=True) -> dict:
        """Get article as a dict optimized for JSON API.

        Parameters
        ----------
        include_lists : bool
            Whether or not to include lists in the JSON.
        iso_date : bool
            Whether or note to use ISO dates instead of Python dates.

        Returns
        -------
        dict
            Returns a dict optimized for JSON output.
        """
        data = {
            "id": self.get("article_id"),
            "parent_id": self.get("parent_id"),
            "source": self.get("source"),
            "source_id": self.get("source_id"),
            "domain": self.get("domain"),
            "url": self.get("url"),
            "url_id": self.get("url_id"),
            "title": self.get("title"),
            "h1": self.get("h1"),
            "lead": self.get("lead"),
            "body": self.get("body"),
            "authors": self.get("authors"),
            "language": self.get("language"),
            "section": self.get("section"),
            "categories": self.get("categories"),
            "tags": self.get("tags"),
            "checksum": self.get("checksum"),
            "num_images": self.get("num_images"),
            "num_videos": self.get("num_videos"),
            "page_type": self.get("page_type"),
            "article_genre": self.get("article_genre"),
            "is_paywalled": self.get("is_paywalled"),
            "is_deleted": self.get("is_deleted"),
            "added": DateUtils.set_iso_date(self.get("added"), iso_date=iso_date),
            "published": DateUtils.set_iso_date(self.get("published"), iso_date=iso_date),
            "edited": DateUtils.set_iso_date(self.get("edited"), iso_date=iso_date),
        }
        if include_lists:
            lists = {
                "images": self.get("images"),
                "versions": self.get("versions"),
                "links": self.get("links"),
                "metadata": self.get("metadata"),
                "log": self.get("log"),
                "headers": self.get("headers"),
            }
            data = {**data, **lists}
        return data

    def compute_checksum(self) -> str:
        """Get hash of article content.

        Useful for fast and easy detection of  content changes by comparing
        MD5 hashes of an old and new article.

        Returns
        -------
        str
            An MD5 hash of the news article information.
        """
        data = str(self.get("title")) + str(self.get("h1")) + \
               str(self.get("lead")) + str(self.get("body")) + \
               str(self.get("published")) + str(self.get("edited")) +  \
               str(self.get("authors")) + str(self.get("section")) + \
               str(self.get("tags")) + str(self.get("categories"))
        return TextUtils.md5_hash(data)


class SourceItem():
    """Item for a single source (e.g., news site) that has been scraped."""

    def __init__(self, source_id=0, parent_id=0, name="", url="", added=None, guid=None):
        """Constructor.

        Parameters
        ----------
        source_id : int
            The ID of the source, as set by the database.
        parent_id : int
            Parent ID of the souce, as set by the database.
        nane : str
            Name of the source (i.e., name of web site).
        url : str
            URL to the source (news site home page).
        added : datetime
            When the source was added.
        guid : str
            A GUID of the source, as set by the spider.
        """
        self.source_id = source_id
        self.parent_id = parent_id
        self.name = name
        self.url = url
        self.added = added
        self.guid = guid

    @classmethod
    def from_datarow(cls, row: dict):
        """Create a new instance of SourceItem from a MySQL data row.

        Parameters
        ----------
        row : dict
            A database row from MySQL.

        Returns
        -------
        SourceItem
            Returns a new instance of SourceItem.
        """
        cls = SourceItem(source_id=row["id"], parent_id=row["parent_id"], name=row["name"],
                         url=row["url"], added=row["added"], guid=row["guid"])
        return cls

    def get_json(self, iso_date=True) -> dict:
        """Get source as a dict optimized for JSON API.

        Parameters
        ----------
        iso_date : bool
            Whether or note to use ISO dates (instead of Python date objects).

        Returns
        -------
        dict
            Returns a dict optimized for JSON output.
        """
        data = {
                "source_id": self.source_id,
                "parent_id": self.parent_id,
                "name": self.name,
                "url": self.url,
                "added": DateUtils.set_iso_date(self.added, iso_date=iso_date),
                "guid": self.guid,
                }
        return data

    def __repr__(self) -> str:
        """Return representation of source."""
        return "{} (#{} <{}>)".format(self.name, self.source_id, self.url)

    def __str__(self) -> str:
        """Return source as a JSON string."""
        return self.get_json()
