# -*- coding: utf-8 -*-
"""
Module for searching and retrieving articles.
"""
import datetime
import json
import hashlib
from mechanicalnews.utils import DateUtils
from mechanicalnews.items import LogAction, ArticleItem, SourceItem
from mechanicalnews.settings import AppConfig
from mechanicalnews.storage import MySqlDatabase


class ArticleFilter():
    """Filter for retrieving list of articles. Used in article search."""

    def __init__(self, args=None):
        """Set filters by values from query string. If no query string, use
        default values."""
        self.args = args
        self.limit = self.get_int("limit", default=500)
        self.offset_id = self.get_int("offset_id", default=0)
        self.id = self.get_int("id", default=0)
        self.query = self.get_str("query")
        self.url = self.get_str("url")
        self.from_date = self.get_str("from_date")
        self.to_date = self.get_str("to_date")
        self.author = self.get_str("author")
        self.source = self.get_str("source")
        self.include_additionals = self.get_bool("include_additionals", default=True)

    def get_str(self, name, default="") -> str:
        """Read string value from query string, or use default value."""
        if self.args:
            if self.args.get(name):
                return str(self.args.get(name))
        return default

    def get_int(self, name, default=0) -> int:
        """Read integer value from query string, or use default value."""
        if self.args:
            if self.args.get(name):
                return int(self.args.get(name))
        return default

    def get_bool(self, name, default=False) -> bool:
        """Read boolean value from query string, or use default value."""
        if self.args:
            if self.args.get(name):
                if self.args.get(name) in [True, "true", 1, "1", "yes"]:
                    return True
                elif self.args.get(name) in [False, "false", 0, "0", "no"]:
                    return False
        return default


class Articles():
    """Create, read, update, and delete articles."""

    def __init__(self):
        super().__init__()
        self.last_article_id = 0
        self.db = MySqlDatabase.from_settings()

    def parse_sources_to_id(self, source) -> list:
        """
        Parse a string of source names, and convert them to their
        corresponding ID's. Returns a list of ID's.

        Parameters
        ----------
        source : str
            Source name to search for.

        Returns
        -------
        list
            Returns a list of ID's to the sources.
        """
        sources = None
        sql = "SELECT id FROM sources WHERE name LIKE %s OR url LIKE %s"
        self.db.open()
        self.db.cur.execute(sql, ("%" + source + "%", "%" + source + "%", ))
        if self.db.cur:
            sources = []
            for row in self.db.cur:
                sources.append(row[0])
        self.db.close()
        return sources

    def get_article_count(self, filters=None) -> int:
        """Get article (web page) count.

        Parameters
        ----------
        filters : ArticleFilter
            What articles to search for. If `None`, no restrictions will be
            used for searching.

        Returns
        -------
        int
            Returns the number of articles that match the filter criteria.
        """
        if not filters:
            sql = "SELECT COUNT(*) count FROM articles WHERE parent_id=0"
        else:
            sql = self._build_sql_from_filter(filters=filters, count_only=True)
        self.db.open()
        self.db.cur.execute(sql)
        value = self.db.cur.fetchone()["count"]
        self.db.close()
        if value:
            return value
        return 0

    def get_article_hits_over_time(self, filters=None) -> list:
        """Get list of hits over time, filtered by search criteria.

        Parameters
        ----------
        filters : ArticleFilter
            What articles to search for. If `None`, no restrictions will be
            used for searching.

        Returns
        -------
        list
            Returns a list of dict, with date and the number of matching hits.
        """
        hits = None
        if not filters:
            filters = ArticleFilter(args={"to_date": datetime.datetime.now().date()})
        sql = self._build_sql_from_filter(filters=filters, hits_only=True)
        self.db.open()
        self.db.cur.execute(sql)
        if self.db.cur:
            hits = []
            for row in self.db.cur:
                hits.append({
                    "date": str(row["timeunit"]),
                    "hits": row["count"],
                })
        self.db.close()
        return hits

    def get_article_by_id(self, article_id):
        """Get article by its ID."""
        article = None
        self.db.open()
        self.db.cur.execute("""SELECT a.*, u.url, s.name AS source
        FROM articles a
        INNER JOIN article_urls u ON u.id=a.url_id
        INNER JOIN sources s ON s.id=a.source_id
        WHERE a.id = %s LIMIT 1""", (article_id,))
        for row in self.db.cur:
            article = ArticleItem.from_datarow(row)
            self.db.close()
            return article
        self.db.close()
        return article

    def get_articles(self, filters=None) -> list:
        """Get list of articles, filtered by search criteria."""
        articles = None
        sql = self._build_sql_from_filter(filters=filters)
        self.db.open()
        self.db.cur.execute(sql)
        if self.db.cur:
            articles = []
            for row in self.db.cur:
                articles.append(ArticleItem.from_datarow(row))
        self.db.close()
        return articles

    def append_additionals(self, article: ArticleItem) -> ArticleItem:
        """Append additional data (e.g., images, links) to articles.
        
        Parameters
        ----------
        articles : list
            An article.

        Returns
        -------
        list
            Returns the article with additional metadata added.
        """
        if not article:
            return article
        article_id = article["article_id"]
        article["images"] = self.get_images(article_id)
        article["metadata"] = self.get_metadata(article_id)
        article["links"] = self.get_links(article_id)
        article["log"] = self.get_log(article_id)
        article["response_headers"] = self.get_headers(article_id)
        return article

    def _secure_input(self, text):
        """Secure the input text from SQL injections."""
        # HACK: Only for debugging!!!
        if text:
            text = text.replace("'", "''")
        return text

    def _build_sql_from_filter(self, filters=None, count_only=False,
                               hits_only=False):
        """Build SQL query from filter. Used in get_articles()."""
        if filters and type(filters) != ArticleFilter:
            raise TypeError("Filters should be of type {}, not {}.".format(ArticleFilter, type(filters)))
        sql_where = self._append_where_filters(filters)
        # Append SQL parts into final SQL.
        if count_only:
            # Get total number of articles.
            sql = """SELECT COUNT(*) count
                    FROM articles a
                    FORCE INDEX (id, title, title_2, title_3)
                    {} LIMIT 1"""
            sql = sql.format(sql_where)
        elif hits_only:
            # Get total number of articles by date.
            sql = """SELECT DATE(published) timeunit, COUNT(*) count
                    FROM articles a
                    FORCE INDEX (id, title, title_2, title_3)
                    {}
                    GROUP BY DATE(published)
                    ORDER BY DATE(published) DESC
                    """
            sql = sql.format(sql_where)
        else:
            # Get article content.
            sql = """SELECT a.*, u.url, s.name source
                    FROM articles a
                    FORCE INDEX (id, title, title_2, title_3)
                    INNER JOIN article_urls u ON u.id=a.url_id
                    INNER JOIN sources s ON s.id=a.source_id
                    {} ORDER BY a.id DESC LIMIT {}"""
            sql = sql.format(sql_where, filters.limit)
        return sql

    def _append_where_filters(self, filters: ArticleFilter) -> str:
        """Append WHERE filter for for the SQL query."""
        if not filters:
            return ""
        where = []
        where.append("a.parent_id = 0")  # Don't include versions of articles.
        if filters.offset_id:
            # Offset records by this article ID.
            where.append("a.id < {}".format(filters.offset_id))
        if filters.id:
            # What articles to filter.
            where.append("a.id IN ({})".format(self._secure_input(filters.id)))
        if filters.query != "":
            # Search query using fulltext index.
            where.append("MATCH (a.title, a.lead, a.body)" +
                         " AGAINST ('{}' IN BOOLEAN MODE)".format(self._secure_input(filters.query)))
        if filters.url:
            # Article URL to search for.
            where.append("u.url = '{}'".format(self._secure_input(filters.url)))
        if filters.author:
            # Get articles from author.
            where.append("a.author LIKE '%{}%'".format(self._secure_input(filters.author)))
        if filters.source:
            # Get articles from source.
            # First convert source names to list of source IDs.
            source_ids = self.parse_sources_to_id(filters.source)
            if source_ids:
                where.append("a.source_id IN ({})".format(",".join(str(x) for x in source_ids)))
            else:
                # If source isn't found, don't return articles.
                where.append("1=2")
        if filters.from_date and filters.to_date:
            # Published between these dates.
            where.append("DATE(a.published) BETWEEN '{}' AND '{}'".format(filters.from_date, filters.to_date))
        elif filters.from_date:
            # Published after this date.
            where.append("DATE(a.published) BETWEEN '{}' AND DATE('now')".format(filters.from_date))
        elif filters.to_date:
            # Published before this date.
            where.append("DATE(a.published) <= '{}'".format(filters.to_date))
        if len(where) > 0:
            return "WHERE " + " AND ".join(where)
        return ""

    def get_article_id_by_url(self, url):
        """Get article ID by URL."""
        if not url:
            raise ValueError("url cannot be empty.")
        article_id = None
        url_checksum = hashlib.md5(url.encode("utf-8")).hexdigest()
        self.db.open()
        self.db.cur.execute("SELECT id FROM article_urls WHERE checksum = %s", (url_checksum,))
        for row in self.db.cur.fetchall():
            article_id = row["id"]
        self.db.close()
        return article_id

    def get_versions(self, article_id):
        """Get list of all versions of an article."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        versions = None
        self.db.open()
        self.db.cur.execute("SELECT * FROM articles WHERE parent_id = %s ORDER BY id DESC", (article_id,))
        if self.db.cur:
            versions = []
            for row in self.db.cur:
                versions.append(ArticleItem.from_datarow(row))
        self.db.close()
        return versions

    def get_images(self, article_id):
        """Get list of all images in an article."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        images = None
        self.db.open()
        self.db.cur.execute("SELECT * FROM article_images WHERE article_id = %s", (article_id,))
        if self.db.cur:
            images = []
            for row in self.db.cur:
                image = {
                            "url": row["url"],
                            "path": row["path"],
                            "filename": self._extract_filename(row["path"]),
                            "checksum": row["checksum"]
                        }
                images.append(image)
        self.db.close()
        return images

    def _extract_filename(self, path: str) -> str:
        if not path:
            return ""
        return path.replace("full/", "")

    def get_metadata(self, article_id):
        """Get meta data for a specific article.

        Meta data are collected from the `<meta>` tags of article."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        metadata = None
        self.db.open()
        self.db.cur.execute("SELECT * FROM article_meta WHERE article_id = %s", (article_id,))
        if self.db.cur:
            metadata = []
            for row in self.db.cur:
                meta = {
                            "name": row["name"],
                            "content": row["content"],
                            "is_property": bool(row["is_property"])
                    }
                metadata.append(meta)
        self.db.close()
        return metadata

    def get_metadata_raw(self, article_id):
        """Get raw metadata for a specific article.

        Raw metadata is all metadata collected."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        self.db.open()
        self.db.cur.execute("SELECT metadata FROM article_raw WHERE article_id = %s LIMIT 1", (article_id,))
        json_dict = None
        if self.db.cur:
            json_data = self.db.cur.fetchone()
            if json_data:
                json_data = json_data["metadata"]
            try:
                json_dict = json.loads(json_data)
            except BaseException:
                pass
        self.db.close()
        return json_dict

    def get_log(self, article_id, iso_date=True):
        """Get log for a specific article.

        The log contain articke history: crawl date, update date, etc."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        self.db.open()
        self.db.cur.execute("SELECT * FROM log WHERE article_id = %s", (article_id,))
        logs = None
        if self.db.cur:
            logs = []
            for row in self.db.cur:
                meta = {
                    "id": row["id"],
                    "action_id": row["action_id"],
                    "action_message": str(LogAction(row["action_id"])),
                    "added": DateUtils.set_iso_date(row["added"], iso_date=iso_date),
                }
                logs.append(meta)
        self.db.close()
        return logs

    def get_links(self, article_id):
        """Get all links in an article.

        Refers to all links within the body of the article text."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        self.db.open()
        self.db.cur.execute("""SELECT to_url_id, url FROM article_links l
        LEFT JOIN article_urls u ON u.id=l.to_url_id WHERE l.article_id = %s""", (article_id,))
        links = None
        if self.db.cur:
            links = []
            for row in self.db.cur:
                link = {
                    "to_url_id": row["to_url_id"],
                    "to_url": row["url"],
                }
                links.append(link)
        self.db.close()
        return links

    def get_headers(self, article_id):
        """Get HTTP headers for a specific article."""
        if not article_id:
            raise ValueError("article_id cannot be empty.")
        self.db.open()
        self.db.cur.execute("SELECT * FROM article_headers WHERE article_id = %s", (article_id,))
        headers = None
        if self.db.cur:
            headers = []
            for row in self.db.cur:
                header = {
                    "name": row["name"],
                    "value": row["value"],
                }
                headers.append(header)
        self.db.close() 
        return headers
