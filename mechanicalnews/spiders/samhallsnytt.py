#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class SamhallsnyttSpider(BaseArticleSpider):
    """Web scraper for articles on samhallsnytt.se."""
    SPIDER_GUID = "d1f59f05-0a0d-4ba1-bc7b-f6263c875380"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "samhallsnytt"
    allowed_domains = ["samnytt.se"]
    start_urls = [
        "https://samnytt.se/category/inrikes/",
        "https://samnytt.se/category/utrikes/",
        "https://samnytt.se/category/kultur/",
        "https://samnytt.se/category/vetenskap/",
        "https://samnytt.se/category/opinion/",
        "https://samnytt.se/video/",
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
        h1 = self.response.css("h1::text").get(default="")
        if h1:
            return h1
        h1 = self.article.headline
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = " ".join(self.response.css(
            ".td-post-content > p strong::text").getall())
        if lead:
            return lead
        lead = self.article.description
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = self.response.css(".td-post-content").get(default="")
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
        if self.response.url.find("/author/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/page/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/video/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/om-oss/") > 0:
            return PageType.NONE
        if self.response.url.find("/personuppgiftspolicy/") > 0:
            return PageType.NONE
        if self.response.url.find("/stod-oss/") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        if self.response.url.find("-") > 0:
            # Simple hueristic: titles are converted to URL slugs, with
            # hyphens instead of spaces, so we'll guess that hyphens in URL
            # are an indicator of an article.
            return PageType.ARTICLE
        elif len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        section = self.article.section
        if section == "Kultur":
            return ArticleGenre.ENTERTAINMENT
        if section == "Inrikes":
            return ArticleGenre.NEWS
        if section == "Utrikes":
            return ArticleGenre.NEWS
        if section == "Opinion":
            return ArticleGenre.OPINION
        if section == "Vetenskap":
            return ArticleGenre.TECHNOLOGY
        if self.extract_page_type() == PageType.ARTICLE:
            return ArticleGenre.NEWS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "- Samhällsnytt",
        ]
        title = self.response.css("title::text").get(default="")
        return TextUtils.remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        # There is no CSS indicating who's an author, but there is a link
        # to author pages (e.g. https://samnytt.se/author/egor-putilov/).
        # Therefore, pull author name from the URL.
        authors = self.response.css(
            ".td-post-content p a::attr(href)").getall()
        for author_url in authors:
            if author_url.find("/author/") > 0:
                name = author_url.replace("https://samnytt.se/", "")
                name = name.replace("/author/", "")
                name = name.replace("/", "")
                if name:
                    return [name]
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
