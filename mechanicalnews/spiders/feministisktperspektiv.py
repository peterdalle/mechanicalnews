#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import dateparser
from datetime import datetime
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
import scrapy


class FeministisktPerspektivSpider(BaseArticleSpider):
    """Web scraper for articles on feministisktperspektiv.se."""
    SPIDER_GUID = "692cfcf4-cbee-4a44-9651-44e9cbb6393e"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "feministisktperspektiv"
    allowed_domains = ["feministisktperspektiv.se"]
    start_urls = [
        "https://feministisktperspektiv.se/",
        "https://feministisktperspektiv.se/avdelning/inrikes",
        "https://feministisktperspektiv.se/avdelning/utrikes",
        "https://feministisktperspektiv.se/avdelning/opinion",
        "https://feministisktperspektiv.se/avdelning/ekonomi",
        "https://feministisktperspektiv.se/avdelning/kultur",
        "https://feministisktperspektiv.se/avdelning/sport",
        "https://feministisktperspektiv.se/international",
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
            "body": self.extract_body(),
            "body_html": self.extract_body(),
            "page_type": self.extract_page_type(),
            "article_genre": self.extract_article_genre(),
            "is_paywalled": self.extract_is_paywalled(),
            "published": self.extract_publish_date(),
            "edited": self.extract_modified_date(),
            "authors": self.extract_authors(),
            "section": self.extract_section(),
            "categories": self.extract_categories(),
            "tags": self.extract_tags(),
            "images": self.extract_images()
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
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = "\n".join(self.response.css(".lede * ::text").getall())
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = self.article.body
        if body:
            return body
        body = self.response.css("#body").get(default="")
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/avdelning/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/international/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/nummer/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/om/") > 0:
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
        section = self.extract_section() if self.extract_section() else []
        if "INTERNATIONAL" in section:
            return ArticleGenre.NEWS
        if "OPINION/INTERNATIONAL" in section:
            return ArticleGenre.OPINION
        if "CULTURE/INTERNATIONAL" in section:
            return ArticleGenre.ENTERTAINMENT
        if "CULTURE/INTERNATIONAL" in section:
            return ArticleGenre.ENTERTAINMENT
        if "SPORTS/INTERNATIONAL" in section:
            return ArticleGenre.SPORTS
        if "KRÖNIKA/KULTUR" in section:
            return ArticleGenre.ENTERTAINMENT
        if "KRÖNIKA/OPINION" in section:
            return ArticleGenre.OPINION
        if "KRÖNIKA/UTRIKES" in section:
            return ArticleGenre.OPINION
        if "EU-KRÖNIKAN/OPINION" in section:
            return ArticleGenre.OPINION
        if "OPINION" in section:
            return ArticleGenre.OPINION
        if "INRIKES" in section:
            return ArticleGenre.NEWS
        if "UTRIKES" in section:
            return ArticleGenre.NEWS
        if "EKONOMI" in section:
            return ArticleGenre.NEWS
        if "KULTUR" in section:
            return ArticleGenre.ENTERTAINMENT
        if "FEMINISM" in section:
            return ArticleGenre.NEWS
        if "SPORTS" in section:
            return ArticleGenre.SPORTS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        title = self.article.title
        if title:
            return title
        title = self.response.css("title::text").get(default="")
        if title:
            return title
        return None

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".date_and_author::text").get(
            default="").split("|")
        if len(authors) > 0:
            authors = authors[-1]
        if authors:
            return [str(authors).strip()]
        return None

    def extract_section(self) -> str:
        """Extract section."""
        section = self.response.css(".category::text").get(default="")
        if section:
            return str(section).strip()
        section = self.article.section
        if section:
            return section
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        return None

    def extract_categories(self) -> list:
        """Extract categories."""
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.published_date
        if dt:
            return dt
        dt = self.response.css(".date_and_author::text").get(
            default="").split("|")
        if len(dt) > 0:
            dt = dt[0]
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
        img = self.response.css("img.primary_image::attr(src)").getall()
        if img:
            return img
        return None

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        if self.response.url.find("/konton/loggain/") > 0:
            return True
        if self.response.css("#main_content h1::text").get(
                             default="") == "Inloggning":
            return True
        return False
