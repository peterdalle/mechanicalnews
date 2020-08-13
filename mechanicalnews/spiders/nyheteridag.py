#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
from mechanicalnews.utils import DateUtils, TextUtils


class NyheterIdagSpider(BaseArticleSpider):
    """Web scraper for articles on nyheteridag.se."""
    SPIDER_GUID = "6af48e49-1a8a-4321-83ff-63ac4bec315a"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "nyheteridag"
    allowed_domains = ["nyheteridag.se"]
    start_urls = [
        "https://nyheteridag.se/",
        "https://nyheteridag.se/category/sverige/",
        "https://nyheteridag.se/category/politik/",
        "https://nyheteridag.se/category/ekonomi/",
        "https://nyheteridag.se/category/opinion/",
        "https://nyheteridag.se/category/world/",
        "https://nyheteridag.se/category/kultur/",
        "https://nyheteridag.se/category/kronika/",
        "https://nyheteridag.se/category/sport/",
        "https://nyheteridag.se/category/nyhetspodden/"
    ]

    def parse_article(self, response: scrapy.http.Response) -> ArticleItem:
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
            "is_paywalled": self.extract_is_paywalled(),
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
        h1 = self.article.headline
        if h1:
            return h1
        h1 = self.response.css("article.article h1::text").get(default="")
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css(
            "article.article .content strong::text").get(default="")
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = self.response.css("article .content").get(default="")
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/category/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/om-oss-kontakt/") > 0:
            return PageType.NONE
        if self.response.url.lower().find("/plus-info/") > 0:
            return PageType.NONE
        if self.response.url.lower().find("/integritetspolicy-gdpr/") > 0:
            return PageType.NONE
        if self.response.url.lower().find("/tipsa-oss/") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        elif len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if self.response.url.lower().find("/category/") > 0:
            return ArticleGenre.NONE
        if self.response.url.lower().find("/om-oss-kontakt/") > 0:
            return ArticleGenre.NONE
        if self.response.url.lower().find("/plus-info/") > 0:
            return ArticleGenre.NONE
        if self.response.url.lower().find("/integritetspolicy-gdpr/") > 0:
            return ArticleGenre.NONE
        if self.response.url.lower().find("-") > 0:
            # Since headlines are made into URLs, and spaces are converted to
            # dashes, treat dashes as an indication of an article.
            return ArticleGenre.NEWS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "- Nyheter Idag",
        ]
        title = self.response.css("title::text").get(default="")
        return TextUtils.remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".article-author .h5::text").getall()
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

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        if self.response.url.find("/plus/") > 0:
            return True
        return False
