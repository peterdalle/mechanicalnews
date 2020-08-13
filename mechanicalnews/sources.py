# -*- coding: utf-8 -*-
"""
Module for handling sources (i.e., web sites to scrape).
"""
import datetime
import json
import hashlib
from mechanicalnews.utils import DateUtils
from mechanicalnews.items import LogAction, ArticleItem, SourceItem
from mechanicalnews.settings import AppConfig
from mechanicalnews.storage import MySqlDatabase


class Sources():
    """Handles sources: create, read, update, and delete."""

    @staticmethod
    def get_sources(source_id=None) -> list:
        """Get list of all sources from database."""
        db = MySqlDatabase.from_settings()
        db.open()
        db.cur.execute("SELECT * FROM sources ORDER BY name ASC")
        if db.cur:
            sources = []
            for row in db.cur:
                sources.append(SourceItem.from_datarow(row))
            db.close()
            return sources
        db.close()
        return None

    @staticmethod
    def get_source_by_id(source_id) -> dict:
        """Get source by its ID from database."""
        source = None
        db = MySqlDatabase.from_settings()
        db.open()
        db.cur.execute("SELECT * FROM sources WHERE id = %s LIMIT 1", (source_id, ))
        if db.cur:
            for row in db.cur:
                source = SourceItem.from_datarow(row)
        db.close()
        return source

    @staticmethod
    def get_id_by_guid(guid, raise_keyerror=False) -> int:
        """Get source ID by GUID from database."""
        source_id = None
        db = MySqlDatabase.from_settings()
        db.open()
        db.cur.execute("SELECT id FROM sources WHERE guid=%s LIMIT 1", (guid, ))
        if db.cur:
            source_dict = db.cur.fetchone()
            if source_dict:
                source_id = source_dict["id"]
        db.close()
        if not source_id and raise_keyerror:
            raise KeyError("Source GUID {} not found.".format(guid))
        return source_id

    @staticmethod
    def register_spider(name, guid) -> int:
        """Register source GUID in database and return source ID."""
        spider_id = Sources.get_id_by_guid(guid)
        if spider_id:
            return spider_id
        if not spider_id:
            with MySqlDatabase.from_settings() as db:
                sql = "INSERT INTO sources (name, guid) VALUES (%s, %s)"
                db.execute(sql, (name, guid))
                spider_id = db.cur.lastrowid
            return spider_id
        return None

    @staticmethod
    def set_spider_last_run(guid):
        """Set the datetime in database when the spider started.

        Parameters
        ----------
        guid : str
            GUID of the spider.
        """
        if not guid:
            return
        with MySqlDatabase.from_settings() as db:
            sql = "UPDATE sources SET spider_last_run=NOW() WHERE guid=%s"
            db.execute(sql, (guid, ))
