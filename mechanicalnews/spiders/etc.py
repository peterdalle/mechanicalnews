#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from basespider import BaseArticleSpider
from extractors import ArticleExtractor
from items import ArticleItem, PageType, ArticleGenre


class EtcSpider(BaseArticleSpider):
    """Web scraper for articles on etc.se."""
    SPIDER_GUID = "535172ed-51ff-4317-8e52-ff039752f122"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "etc"
    allowed_domains = ["etc.se"]
    start_urls = [
        "https://www.etc.se/",
        "https://www.etc.se/inrikes",
        "https://www.etc.se/utrikes",
        "https://www.etc.se/ekonomi",
        "https://www.etc.se/ledare",
        "https://www.etc.se/debatt",
        "https://www.etc.se/kronika",
        "https://www.etc.se/kultur-noje",
        "https://www.etc.se/klimat",
        "https://goteborg.etc.se/"
    ]

    # Deny URLs that match these rules.
    rules = [
        Rule(LinkExtractor(deny=r"^https?://varuhuset.etc.se*"), follow=False),
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
            "is_paywalled": self.extract_is_paywalled(),
            "published": self.extract_publish_date(),
            "edited": self.extract_modified_date(),
            "authors": self.extract_authors(),
            "section": self.extract_section(),
            "categories": [],
            "tags": self.extract_tags(),
            "images": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract headline."""
        h1 = self.article.headline
        if h1:
            return h1
        h1 = self.response.css("h1::text").get(default="")
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = "\n".join(self.response.css(
            ".field-name-field-preamble p::text").getall())
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = "\n".join(self.response.css(
            ".field-name-mkts-body-preamble-free * ::text").getall())
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("play.etc.se") > 0:
            return PageType.VIDEO
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.response.url.find("etc.se/inrikes?page="):
            return PageType.COLLECTION
        if len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if self.response.url.find("/nyheter/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.find("/inrikes/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.find("/utrikes/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.find("/ekonomi/") > 0:
            return ArticleGenre.ECONOMY
        if self.response.url.find("/klimat/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.find("/debatt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.find("/kronika/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.find("/ledare/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.find("/kultur-noje/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.find("/sport/") > 0:
            return ArticleGenre.SPORTS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        return self.response.css("title::text").get(default="")

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(
            ".field-name-mkts-field-article-byline * ::text").getall()
        if authors:
            return authors
        return None

    def extract_section(self) -> str:
        """Extract section."""
        section = self.article.section
        if section:
            return section
        section = self.response.css(
            ".field-name-mkts-field-article-header * ::text").get(default="")
        if section:
            if section.endswith("."):
                section = section[:-1]
            return section
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        return []

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.published_date
        if dt:
            return dt
        return None

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        dt = self.article.modified_date
        if dt:
            return dt
        return None

    def extract_images(self) -> list:
        """Extract images."""
        img = self.article.images
        if img:
            return img
        img = self.response.css(
            ".field-name-mkts-scald-mega img::attr(src)").getall()
        if img:
            return img
        return None

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        block = self.response.css("h1.locked-article__heading").get(default="")
        if block:
            return True
        return False
