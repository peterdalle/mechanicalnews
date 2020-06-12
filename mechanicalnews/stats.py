# -*- coding: utf-8 -*-
"""
Module for summary statistics of already collected articles.
"""
from utils import DateUtils
from settings import AppConfig
from database import MySqlDatabase


class SummaryStats():
    """Generate summary statistics.

    Number of crawled (or published) articles per day."""

    @staticmethod
    def get_database_size(all_tables=False):
        """
        Get size of data and index of the MySQL database tables (in bytes).
        """
        db = MySqlDatabase.from_settings()
        if all_tables:
            # Show size for each table in database.
            query = """SELECT table_schema 'databasename',
            table_name 'tablename',
            SUM(data_length) 'datasize',
            SUM(index_length) 'indexsize'
            FROM information_schema.tables
            WHERE table_schema = %s
            GROUP BY table_name
            ORDER BY table_schema, table_name"""
            db.open()
            db.cur.execute(query, (AppConfig.MYSQL_DB, ))
            rows = db.cur.fetchall()
            tables = []
            for row in rows:
                tables.append({
                    "table_name": row["tablename"],
                    "data_size": int(row["datasize"]),
                    "index_size": int(row["indexsize"]),
                    "total_size": int(row["datasize"]) + int(row["indexsize"]),
                })
            db.close()
            return tables
        else:
            # Show size for whole database.
            query = """SELECT table_schema 'databasename',
            SUM(data_length) 'datasize',
            SUM(index_length) 'indexsize'
            FROM information_schema.tables
            WHERE table_schema = %s"""
            db.open()
            db.cur.execute(query, (AppConfig.MYSQL_DB, ))
            rows = db.cur.fetchall()
            for row in rows:
                size = {
                    "database_data_size": int(row["datasize"]),
                    "database_index_size": int(row["indexsize"]),
                    "database_total_size": int(
                                   row["datasize"]) + int(row["indexsize"]),
                }
            db.close()
            return size

    @staticmethod
    def get_summary(iso_date=True):
        """Get summary statistics of number of collected articles.

        Number of articles (and its links, versions, images, meta data),
        sources, log."""
        db = MySqlDatabase.from_settings()
        db.open()
        num_sources = db.get_scalar(
            "SELECT COUNT(*) value FROM sources", field="value", default=0)
        num_urls = db.get_scalar(
            "SELECT COUNT(*) value FROM article_urls",
            field="value", default=0)
        num_articles = db.get_scalar(
            "SELECT COUNT(*) value FROM articles WHERE parent_id = 0",
            field="value", default=0)
        num_versions = db.get_scalar(
            "SELECT COUNT(*) value FROM articles WHERE parent_id != 0",
            field="value", default=0)
        """num_links = self._get_scalar(
            "SELECT COUNT(*) value FROM article_links") # TODO: Make faster
        num_images = self._get_scalar(
            "SELECT COUNT(*) value FROM article_images") # TODO: Make faster
        num_metadata = self._get_scalar(
            "SELECT COUNT(*) value FROM article_meta") # TODO: Make faster
        # TODO: What the hell is the diffrence between num_images
        # and num_meta_images? What was I thinking? Just set it as -1 for now.
        num_headers = self._get_scalar(
            "SELECT COUNT(*) value FROM article_headers") # TODO: Make faster
        num_frontpage_articles = self._get_scalar(
            "SELECT COUNT(*) value FROM frontpage_articles") # TODO: Make fast
        num_unique_pages = self._get_scalar(
            "SELECT COUNT(DISTINCT checksum) value " \
            "FROM articles WHERE parent_id = 0") # TODO: Make faster
        num_log = self._get_scalar(
            "SELECT COUNT(*) value FROM log")  # TODO: Make faster"""
        num_images = -1
        num_metadata = -1
        num_headers = -1
        num_frontpage_articles = -1
        num_log = -1
        num_unique_pages = -1
        num_meta_images = -1
        num_links = -1
        num_errors = -1
        earliest_published_article = db.get_scalar(
            "SELECT MIN(published) value " +
            "FROM articles WHERE NOT ISNULL(published)",
            field="value", default=0)
        latest_published_article = db.get_scalar(
            "SELECT MAX(published) value " +
            "FROM articles WHERE NOT ISNULL(published)",
            field="value", default=0)
        db.close()
        data = {
            "num_log": num_log,
            "num_errors": num_errors,
            "num_sources": num_sources,
            "num_frontpage_articles": num_frontpage_articles,
            "num_images": num_images,
            "num_urls": num_urls,
            "num_articles": num_articles,
            "num_article_versions": num_versions,
            "num_article_links": num_links,
            "num_article_metadata": num_metadata,
            "num_article_images": num_meta_images,
            "num_article_headers": num_headers,
            "num_unique_pages": num_unique_pages,
            "earliest_published_article": DateUtils.set_iso_date(
                earliest_published_article, iso_date=iso_date),
            "latest_published_article": DateUtils.set_iso_date(
                latest_published_article, iso_date=iso_date),
        }
        return data

    @staticmethod
    def get_source_counts():
        """Get summary statistics of articles collected per source."""
        sql = """SELECT s.name source, COUNT(*) articles
              FROM articles a
              LEFT JOIN sources s ON s.id=a.source_id
              GROUP BY a.source_id
              ORDER BY COUNT(*) DESC"""
        with MySqlDatabase.from_settings() as db:
            return db.get_rows(sql)

    @staticmethod
    def get_published_articles_per_day():
        """Get number of published articles per day.

        Returns `dict` with fields `day` and `articles`."""
        sql = "SELECT DATE(published) a, COUNT(*) b FROM articles GROUP BY" \
              " DATE(published) ORDER BY published DESC"
        db = MySqlDatabase.from_settings()
        db.open()
        db.cur.execute(sql)
        stats = None
        if db.cur:
            stats = []
            for row in db.cur:
                meta = {
                    "day": str(row["a"]) if row["a"] else None,
                    "articles": row["b"],
                }
                stats.append(meta)
        db.close()
        return stats

    @staticmethod
    def get_crawled_articles_per_day(days_back=None):
        """Get number of crawled articles per day.

        Returns `dict` with fields `day` and `articles`."""
        if days_back:
            sql = """SELECT DATE(added) day, COUNT(*) articles
            FROM articles
            WHERE DATE(added) BETWEEN DATE_ADD(DATE(NOW()), INTERVAL -{} DAY)
                  AND NOW()
            GROUP BY DATE(added)
            ORDER BY added DESC""".format(days_back)
        else:
            sql = """SELECT DATE(added) day, COUNT(*) articles
            FROM articles
            GROUP BY DATE(added)
            ORDER BY added DESC"""
        db = MySqlDatabase.from_settings()
        db.open()
        db.cur = db.conn.cursor(dictionary=True)
        db.cur.execute(sql)
        stats = None
        if db.cur:
            stats = []
            for row in db.cur:
                meta = {
                    "day": str(row["day"]) if row["day"] else None,
                    "articles": row["articles"],
                }
                stats.append(meta)
        db.close()
        return stats

    @staticmethod
    def get_log(limit=20):
        """Get latest values from log."""
        sql = "SELECT * FROM log ORDER BY id DESC"
        if limit > 0:
            sql = sql + " LIMIT {}".format(limit)
        with MySqlDatabase.from_settings() as db:
            return db.get_rows(sql)

    @staticmethod
    def get_missing_values_by_day(days_back=7):
        """Get the missing values from a number of days back in time."""
        sql = """SELECT DATE(added) added, ISNULL(published) missing,
        COUNT(*) articles
        FROM articles
        WHERE (added BETWEEN DATE_ADD(NOW(), INTERVAL -{} DAY) AND NOW())
        GROUP BY DATE(added), ISNULL(published)
        ORDER BY added ASC, missing ASC;""".format(days_back)
        with MySqlDatabase.from_settings() as db:
            return db.get_rows(sql)

    @staticmethod
    def get_missing_values_by_source(days_back=7):
        """Get the missing values from a number of days back in time."""
        sql = """SELECT source_id, ISNULL(published) missing, COUNT(*) articles
        FROM articles
        WHERE (added BETWEEN DATE_ADD(NOW(), INTERVAL -{} DAY) AND NOW())
        GROUP BY source_id, ISNULL(published)
        ORDER BY id DESC""".format(days_back)
        with MySqlDatabase.from_settings() as db:
            return db.get_rows(sql)

    @staticmethod
    def get_missing_text(days_back=7):
        """Get the missing text from a number of days back in time."""
        sql = """SELECT DATE(added), COUNT(*) articles
        FROM articles
        WHERE (ISNULL(published) OR ISNULL(body) OR ISNULL(`lead`))
        AND (added BETWEEN DATE_ADD(NOW(), INTERVAL -{} DAY) AND NOW())
        GROUP BY DATE(added)""".format(days_back)
        with MySqlDatabase.from_settings() as db:
            return db.get_rows(sql)
