#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
from mechanicalnews.utils import DateUtils, TextUtils


class NyaTiderSpider(BaseArticleSpider):
    """Web scraper for articles on nyatider.nu."""
    SPIDER_GUID = "68e2d9aa-957c-4fca-a1b4-d8f38258b536"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "nyatider"
    allowed_domains = ["nyatider.nu"]
    start_urls = [
        "https://www.nyatider.nu/",
        "https://www.nyatider.nu/kategori/brott-och-straff/",
        "https://www.nyatider.nu/kategori/ekonomi/",
        "https://www.nyatider.nu/kategori/halsa/",
        "https://www.nyatider.nu/kategori/inrikes/",
        "https://www.nyatider.nu/kategori/kultur/",
        "https://www.nyatider.nu/kategori/miljo/",
        "https://www.nyatider.nu/kategori/notiser/",
        "https://www.nyatider.nu/kategori/opinion/",
        "https://www.nyatider.nu/kategori/utrikes/",
        "https://www.nyatider.nu/kategori/vetenskap/",
        "http://www.nyatider.nu/arkiv/",
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
            "tags": self.article.tags,
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract article headline."""
        h1 = self.response.css("#content h1::text").get(default="")
        if h1:
            return h1
        h1 = self.article.headline
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css(".ingress::text").get(default="")
        if lead:
            return lead
        lead = self.article.description
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = "\n".join(self.response.css(
            ".mepr-unauthorized-excerpt").getall())
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/arkiv/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/kategori/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/video/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/om-nya-tider/") > 0:
            return PageType.NONE
        if self.response.url.find("/titta/") > 0:
            return PageType.NONE
        if self.response.url.find("/kontakta/") > 0:
            return PageType.NONE
        if self.response.url.find("/produkter/prenumeration/") > 0:
            return PageType.NONE
        if self.response.url.find("/login/") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        if self.response.url.count("-") > 2:
            # Headlines are made into URLs, and spaces are replaced with
            # hyphens, so we'll assume hyphens in URL are articles.
            return PageType.ARTICLE
        elif len(lead) > 5 or len(body) > 5:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        section = self.extract_section() if self.extract_section() else ""
        section = section.lower()
        if self.extract_page_type() == PageType.ARTICLE:
            return ArticleGenre.NEWS
        if section == "utrikes":
            return ArticleGenre.NEWS
        if section == "inrikes":
            return ArticleGenre.NEWS
        if section != "":
            return ArticleGenre.NEWS
        return ArticleGenre.NONE

    def extract_section(self) -> str:
        section = self.article.section
        if section:
            return section
        section = self.response.css("#content .topic::text").get()
        if section:
            return section
        return None

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "| Nya Tider",
        ]
        title = self.response.css("title::text").get(default="")
        return TextUtils.remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".skrib-namn a::text").get(default="")
        if authors:
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
