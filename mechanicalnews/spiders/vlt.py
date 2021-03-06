#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from basespider import BaseArticleSpider
from extractors import ArticleExtractor
from items import ArticleItem, PageType, ArticleGenre


class VltSpider(BaseArticleSpider):
    """Web scraper for articles on nyatider.nu."""
    SPIDER_GUID = "c12283cc-1865-4948-adc9-f5434020abd1"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "vlt"
    allowed_domains = ["vlt.se"]
    start_urls = [
        "https://www.vlt.se/",
        "https://www.vlt.se/alla",
        "https://www.vlt.se/sport",
        "https://www.vlt.se/blaljus",
        "https://www.vlt.se/opinion",
        "https://www.vlt.se/kronikor"
        "https://www.vlt.se/debatt",
        "https://www.vlt.se/insandare",
        "https://www.vlt.se/ledare-lib",
        "https://www.vlt.se/naringsliv",
        "https://www.vlt.se/all-noje-och-kultur",
        "https://www.vlt.se/hallstahammar",
        "https://www.vlt.se/surahammar",
        "https://www.vlt.se/sala",
        "https://www.vlt.se/vasteras",
        "https://www.vlt.se/koping",
        "https://www.vlt.se/kungsor",
        "https://www.vlt.se/arboga",
        "https://www.vlt.se/fagersta",
        "https://www.vlt.se/familj",
        "https://www.vlt.se/bostadspuls",
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
            "section": self.article.section,
            "categories": [],
            "tags": self.article.tags,
            "image_urls": self.extract_images()
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract article headline."""
        h1 = self.response.css("h1.headline::text").get(default="")
        if h1:
            return h1
        h1 = self.article.headline
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css(".leadin p::text").get(default="")
        if lead:
            return lead
        lead = self.article.description
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = self.article.body
        if body:
            return body
        body = "\n".join(self.response.css(".body").get(default=""))
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/artikel/") > 0:
            return PageType.ARTICLE
        if self.response.url.find("/artikelserie/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/info/") > 0:
            return PageType.NONE
        if self.response.url.find("/skicka-in-insandare") > 0:
            return PageType.NONE
        if self.response.url.find("/skicka-in-debattartikel") > 0:
            return PageType.NONE
        if self.response.url.find("/skickain-foreningsnytt") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        elif len(lead) > 5 or len(body) > 5:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        section = self.article.section
        section = section.lower() if section else ""
        if section.find("inrikes") > -1:
            return ArticleGenre.NEWS
        if section.find("sport") > -1:
            return ArticleGenre.SPORTS
        if section.find("superettan") > -1:
            return ArticleGenre.SPORTS
        if section.find("elitserien") > -1:
            return ArticleGenre.SPORTS
        if section.find("folkrace") > -1:
            return ArticleGenre.SPORTS
        if section.find("friidrott") > -1:
            return ArticleGenre.SPORTS
        if section.find("hockey") > -1:
            return ArticleGenre.SPORTS
        if section.find("fotboll") > -1:
            return ArticleGenre.SPORTS
        if section.find("ridsport") > -1:
            return ArticleGenre.SPORTS
        if section.find("bandy") > -1:
            return ArticleGenre.SPORTS
        if section.find("cykling") > -1:
            return ArticleGenre.SPORTS
        if section.find("kultur") > -1:
            return ArticleGenre.ENTERTAINMENT
        if section.find("recension") > -1:
            return ArticleGenre.ENTERTAINMENT
        if section.find("kommun") > -1:
            return ArticleGenre.NEWS
        if section.find("krönika") > -1:
            return ArticleGenre.EDITORIAL
        if section.find("opinion") > -1:
            return ArticleGenre.EDITORIAL
        if section.find("ledare") > -1:
            return ArticleGenre.EDITORIAL
        if section.find("insändare") > -1:
            return ArticleGenre.OPINION
        if section.find("kommun") > -1:
            return ArticleGenre.NEWS
        if self.extract_page_type() == PageType.ARTICLE:
            return ArticleGenre.NEWS
        return ArticleGenre.NONE

    def extract_section(self) -> str:
        section = self.response.css(".article-story-header-name::text").get()
        if section:
            return section
        section = self.article.section
        if section:
            return section
        return None

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        return self.response.css("title::text").get(default="")

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.response.css(".byline.first div.name::text").getall()
        if authors:
            return authors
        authors = self.article.authors
        if authors:
            return authors
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
        """Extract whether article is behind paywall."""
        paywall = self.response.css(".paywall").get(default="")
        if paywall:
            return True
        return False
