#!/usr/bin/env python
# -*- coding: utf-8 -*-
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
from datetime import datetime
import re


class SamtidenSpider(BaseArticleSpider):
    """Web scraper for articles on samtiden.nu."""
    SPIDER_GUID = "6a3e15ab-f634-40f6-b08b-22704e632ae8"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "samtiden"
    allowed_domains = ["samtiden.nu"]
    start_urls = [
        "https://samtiden.nu/",
        "https://samtiden.nu/category/inrikes/",
        "https://samtiden.nu/category/utrikes/",
        "https://samtiden.nu/category/ekonomi/",
        "https://samtiden.nu/category/kultur/",
        "https://samtiden.nu/opinion/",
        "https://samtiden.nu/category/poddradio/",
        "https://samtiden.nu/category/ledare/",
        "https://samtiden.nu/category/debatt/"
        "https://samtiden.nu/category/kronika/",
    ]

    def parse_article(self, response: scrapy.http.Response) -> ArticleItem:
        """Parse article and extract article information."""
        self.response = response
        self.article = ArticleExtractor.from_response(self.response)
        yield self.extract_information(response, ArticleItem({
            "links": self.extract_related_links(),
            "title": self.extract_title(),
            "h1": self.extract_headline(),
            "lead": self.extract_lead(),
            "body_html": self.extract_body(),
            "page_type": self.extract_page_type(),
            "article_genre": self.extract_article_genre(),
            "is_paywalled": False,
            "published": self.extract_publish_date(),
            "edited": self.extract_modified_date(),
            "authors": self.extract_authors(),
            "section": self.article.section,
            "categories": [],
            "tags": [],
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract headline."""
        h1 = self.response.css("h1.entry-title::text").get(default="")
        if h1:
            return h1
        h1 = self.article.headline
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css(".cb-itemprop p strong::text").get(default="")
        if lead:
            return lead
        lead = self.article.description
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = self.response.css(".cb-itemprop").get(default="")
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/category/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/opinion/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/page/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/om-oss/") > 0:
            return PageType.NONE
        if self.response.url.find("/feed/") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        if self.article.section == "Poddradio":
            return PageType.SOUND
        if re.search(r"/\d{4}/\d{1,2}", self.response.url):
            # Articles have date in URL, e.g. /2020/01/.
            return PageType.ARTICLE
        elif len(lead) > 5 or len(body) > 5:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        section = self.article.section
        if section == "Kultur":
            return ArticleGenre.ENTERTAINMENT
        if section == "Ekonomi":
            return ArticleGenre.ECONOMY
        if section == "Inrikes":
            return ArticleGenre.NEWS
        if section == "Utrikes":
            return ArticleGenre.NEWS
        if section == "Opinion":
            return ArticleGenre.OPINION
        if section == "Debatt":
            return ArticleGenre.OPINION
        if section == "Ledare":
            return ArticleGenre.EDITORIAL
        if section == "Kolumn":
            return ArticleGenre.EDITORIAL
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "- Samtiden",
        ]
        title = self.response.css("title::text").get(default="")
        return self._remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".cb-meta .fn::text").get(default="")
        if authors:
            return [authors]
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        return self.article.published_date

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        return self.article.modified_date

    def extract_images(self) -> bool:
        """Extract images."""
        return self.article.images
