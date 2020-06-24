#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import dateparser
import re
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class ArbetetSpider(BaseArticleSpider):
    """Web scraper for articles on arbetet.se."""
    SPIDER_GUID = "0dc78ed4-dc45-477f-9c6d-23a2bd56e21f"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "arbetet"
    allowed_domains = ["arbetet.se"]
    start_urls = [
        "https://arbetet.se/arbetsmiljo/",
        "https://arbetet.se/arbetsratt/",
        "https://arbetet.se/ledare/",
        "https://arbetet.se/kultur/",
        "https://arbetet.se/global/",
        "https://arbetet.se/debatt/",
        "https://arbetet.se/reportage/",
        "https://arbetet.se/nyheter/",
        "https://arbetet.se/politik/",
        "https://arbetet.se/kronikor/",
        "https://arbetet.se/chefredaktoren/",
        "https://arbetet.se/arbetet-forklarar/",
        "https://arbetet.se/arbetsdagen/",
    ]

    def parse_article(self, response: scrapy.http.Response) -> ArticleItem:
        """Parse article and extract article information."""
        self.response = response
        self.article = ArticleExtractor.from_response(self.response)
        yield self.extract_information(response, ArticleItem({
            "links": self.extract_related_links(),
            "title": self.extract_title(),
            "h1": self.extract_heading(),
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
            "tags": self.extract_tags(),
            "images": self.extract_images()
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_heading(self) -> str:
        h1 = self.article.headline
        if h1:
            return h1
        h1 = self.response.css("h1::text").get(default="")
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.response.css(".Lead * ::text").get(default="")
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = "\n".join(self.response.css(".ContentBody").getall())
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/page/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/av/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/kontakt/") > 0:
            return PageType.NONE
        if self.response.url.find("/annonsera/") > 0:
            return PageType.NONE
        if self.response.url.find("/prenumerera/") > 0:
            return PageType.NONE
        if self.response.url.find("/tipsa-oss/") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if re.search(r"/\d{4}/\d{1,2}/\d{1,2}", self.response.url):
            # Articles have date in URL, e.g. /2020/01/30/.
            return PageType.ARTICLE
        if len(lead.strip()) > 0 or len(body.strip()) > 0:
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
        if section.find("kultur") > -1:
            return ArticleGenre.ENTERTAINMENT
        if section.find("krönikor") > -1:
            return ArticleGenre.EDITORIAL
        if section.find("opinion") > -1:
            return ArticleGenre.EDITORIAL
        if section.find("ledare") > -1:
            return ArticleGenre.EDITORIAL
        if section.find("insändare") > -1:
            return ArticleGenre.OPINION
        if section.find("debatt") > -1:
            return ArticleGenre.OPINION
        if section.find("global") > -1:
            return ArticleGenre.NEWS
        if section.find("arbetsrätt") > -1:
            return ArticleGenre.NEWS
        if section.find("arbetsmiljö") > -1:
            return ArticleGenre.NEWS
        if section.find("politik") > -1:
            return ArticleGenre.NEWS
        if section.find("reportage") > -1:
            return ArticleGenre.NEWS
        if section.find("nyheter") > -1:
            return ArticleGenre.NEWS
        if section.find("löner & avtal") > -1:
            return ArticleGenre.NEWS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        return self.response.css("title::text").get(default="")

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".Byline-name::text").getall()
        if authors:
            return authors
        return None

    def extract_section(self) -> str:
        """Extract section."""
        section = self.article.section
        if section:
            return section
        section = self.response.css(
            ".ContentHead-context span a ::text").get(default="")
        if section:
            return section
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        return self.response.css(".ContentHead-context > a::text").getall()

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.published_date
        if dt:
            return dt
        dt = self.response.css(
            ".ContentMeta-group--timestamp time::attr(datetime)").get(
                default="")
        if dt:
            return dateparser.parse(dt)
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
            ".FeaturedMedia-content img::attr(src)").getall()
        if img:
            return img
        return None
