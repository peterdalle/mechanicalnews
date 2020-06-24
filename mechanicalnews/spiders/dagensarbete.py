#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scrapy.http import Response
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
import re
from datetime import datetime


class DagensArbeteSpider(BaseArticleSpider):
    """Web scraper for articles on da.se."""
    SPIDER_GUID = "659cf678-8b26-49ea-aff3-602a83917f45"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "dagensarbete"
    allowed_domains = ["da.se"]
    start_urls = [
        "https://da.se/",
        "https://da.se/da-experter/",
        "https://da.se/opinion/",
        "https://da.se/da-granskar/",
        "https://da.se/lyssna/",
        "https://da.se/arbetsmiljo/",
        "https://da.se/stress-mobbning/"
        "https://da.se/arbetstider/",
        "https://da.se/teknik-och-miljo/",
        "https://da.se/lon/",
        "https://da.se/forsakringar/",
        "https://da.se/inhyrning/",
        "https://da.se/migrationen/",
        "https://da.se/hellekleinsblogg/",
        "https://da.se/forbundskronikor/",
    ]

    def parse_article(self, response: Response) -> ArticleItem:
        """Parse article and extract article information."""
        # Extract all news URLs from page.
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
            "section": self.extract_section(),
            "categories": [],
            "tags": [],
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_section(self) -> str:
        """Extract section."""
        section = self.article.section
        if section:
            return section
        return None

    def extract_headline(self) -> str:
        h1 = self.response.css("main h1::text").get(default="")
        if h1:
            return h1
        h1 = self.article.headline
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css("main p.intro::text").get(default="")
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = self.response.css("main").get(default="")
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/story/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/author/") > 0:
            return PageType.COLLECTION
        if self.response.url.endswith("/ledare/"):
            return PageType.COLLECTION
        if self.response.url.endswith("/debatt/"):
            return PageType.COLLECTION
        if self.response.url.endswith("/kronika/"):
            return PageType.COLLECTION
        if self.response.url.endswith("/opinion/"):
            return PageType.COLLECTION
        if self.response.url.endswith("/prenumerera/"):
            return PageType.NONE
        if self.response.url.endswith("/redaktionen/"):
            return PageType.NONE
        if self.response.url.endswith("tipsa.da.se"):
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        if re.search(r"/\d{4}/\d{1,2}/", self.response.url):
            # Articles have date in URL, e.g. /2020/01.
            return PageType.ARTICLE
        elif len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if re.search(r"/\d{4}/\d{1,2}/", self.response.url):
            # Articles have date in URL, e.g. /2020/01.
            return ArticleGenre.NEWS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "- Dagens Arbete",
        ]
        title = self.response.css("title::text").get(default="")
        return self._remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.response.css("p.author a ::text").getall()
        if authors:
            if type(authors) == list:
                return authors
            else:
                return [authors]
        authors = self.article.find_key("article:author")
        if authors:
            if type(authors) == list:
                return authors
            else:
                return [authors]
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        return self.article.published_date

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        return self.article.modified_date

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images
