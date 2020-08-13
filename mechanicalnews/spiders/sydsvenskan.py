#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
import dateparser
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
from mechanicalnews.utils import DateUtils, TextUtils
import re


class SydsvenskanSpider(BaseArticleSpider):
    """Web scraper for articles on sydsvenskan.se."""
    SPIDER_GUID = "95afc522-91a8-475b-a216-683e31895040"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "sydsvenskan"
    allowed_domains = ["sydsvenskan.se"]
    start_urls = [
        "https://www.sydsvenskan.se/",
        "https://www.sydsvenskan.se/sverige/",
        "https://www.sydsvenskan.se/malmo",
        "https://www.sydsvenskan.se/lund",
        "https://www.sydsvenskan.se/kultur",
        "https://www.sydsvenskan.se/opinion",
        "https://www.sydsvenskan.se/sport",
        "https://www.sydsvenskan.se/naringsliv",
        "https://www.sydsvenskan.se/dygnet-runt",
        "https://www.sydsvenskan.se/ekonomi",
        "https://www.sydsvenskan.se/varlden",
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
            "tags": self.extract_tags(),
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        h1 = self.article.headline
        if h1:
            return h1
        h1 = self.response.css("h1::text").get(default="")
        if h1:
            return h1
        h1 = self.response.css("h2.article-heading span::text").get("")
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css(".article-preamble::text").get(default="")
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body, but only without paywall."""
        body = " ".join(self.response.css(".article-content").getall())
        if body:
            return body
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        tags = self.response.css(".tag__title::text").getall()
        if tags:
            return tags
        tags = self.article.tags
        if tags:
            return tags
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/story/") > 0:
            return PageType.COLLECTION
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if re.search(r"\d{4}-\d{1,2}-\d{1,2}", self.response.url):
            # Articles have date in URL, e.g. 2020-01-30.
            return PageType.ARTICLE
        if len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        tags = self.extract_tags() if self.extract_tags() else []
        if "Debatt" in tags:
            return ArticleGenre.OPINION
        if "Åsikter" in tags:
            return ArticleGenre.OPINION
        if "Opinion" in tags:
            return ArticleGenre.OPINION
        if "Ledare" in tags:
            return ArticleGenre.EDITORIAL
        if "Signerat" in tags:
            return ArticleGenre.EDITORIAL
        if "Huvudledare" in tags:
            return ArticleGenre.EDITORIAL
        if "Världen" in tags:
            return ArticleGenre.NEWS
        if "Ekonomi" in tags:
            return ArticleGenre.ECONOMY
        if "Näringsliv" in tags:
            return ArticleGenre.ECONOMY
        if "Lund" in tags:
            return ArticleGenre.NEWS
        if "Malmö" in tags:
            return ArticleGenre.NEWS
        if "Vellinge" in tags:
            return ArticleGenre.NEWS
        if "Lomma" in tags:
            return ArticleGenre.NEWS
        if "Sknåne" in tags:
            return ArticleGenre.NEWS
        if "Sverige" in tags:
            return ArticleGenre.NEWS
        if "Viktigaste idag" in tags:
            return ArticleGenre.NEWS
        if "Sport" in tags:
            return ArticleGenre.SPORTS
        if "Fotboll" in tags:
            return ArticleGenre.SPORTS
        if "Ishockey" in tags:
            return ArticleGenre.SPORTS
        if "Handboll" in tags:
            return ArticleGenre.SPORTS
        if "Nöje" in tags:
            return ArticleGenre.ENTERTAINMENT
        if "Kultur" in tags:
            return ArticleGenre.ENTERTAINMENT
        if "Böcker" in tags:
            return ArticleGenre.ENTERTAINMENT
        if "Mat & Dryck" in tags:
            return ArticleGenre.ENTERTAINMENT
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        return self.response.css("title::text").get(default="")

    def extract_authors(self) -> str:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".author__name::text").getall()
        if authors:
            return authors
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.published_date
        if dt:
            return dt
        dt = self.response.css("time.article-pubdate::attr(datetime)").get("")
        if dt:
            try:
                dt = dateparser.parse(dt)
                if dt:
                    return dt
            except ValueError:
                pass
        return None

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        return self.article.modified_date

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        block = self.response.css(".article__premium-box").get(default="")
        if block:
            return True
        return False
