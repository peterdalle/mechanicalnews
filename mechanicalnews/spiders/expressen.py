#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class ExpressenSpider(BaseArticleSpider):
    """Web scraper for articles on www.expressen.se."""
    SPIDER_GUID = "83a612b2-7aa8-483e-b73a-9fa9a96f0cd3"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "expressen"
    allowed_domains = ["expressen.se"]
    start_urls = [
        "https://www.expressen.se/",
        "https://www.expressen.se/sport/",
        "https://www.expressen.se/premium/",
        "https://www.expressen.se/tv/",
        "https://www.expressen.se/noje/",
        "https://www.expressen.se/kultur/",
        "https://www.expressen.se/ledare/",
        "https://www.expressen.se/debatt/",
        "https://www.expressen.se/nyheter/klimat/",
    ]

    def parse_article(self, response: scrapy.http.Response) -> ArticleItem:
        """Parse article and extract article information."""
        # Extract all news URLs from page.
        self.response = response
        self.article = ArticleExtractor.from_response(self.response)
        yield self.extract_information(response, ArticleItem({
            "links": self.extract_related_links(),
            "title": response.css("title::text").get(default=""),
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
            "categories": self.extract_categories(),
            "tags": self.extract_tags(),
            "image_urls": self.extract_images()
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract headline."""
        h1 = self.response.css(".article__header h1::text").get(default="")
        if h1:
            return h1
        lead = self.article.headline
        if lead:
            return lead
        return None

    def extract_categories(self) -> list:
        """Extract categories."""
        categories = self.response.css(
            ".ArticleLayout-category a::text").getall()
        if categories:
            return categories
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        tags = self.response.css(".article__meta .tag ::text").getall()
        if tags:
            return tags
        return None

    def extract_lead(self) -> str:
        """Extract lead."""
        lead = "\n".join(self.response.css(
                                   ".rich-text__preamble p::text").getall())
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract body."""
        return " ".join(self.response.css(".article__body-text").getall())

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/tv/") > 0:
            return PageType.VIDEO
        if len(lead) > 0 or len(body) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if self.response.url.lower().find("/debatt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/ledare/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/kronikorer/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/dinapengar/") > 0:
            return ArticleGenre.ECONOMY
        if self.response.url.lower().find("/noje/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/allt-om-resor/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/leva-och-bo/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/halsoliv/") > 0:
            return ArticleGenre.PERSONAL
        if self.response.url.lower().find("/brandstudio/") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("rabattkoder.expressen.se") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("kampanj.expressen.se") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("lanapengar.expressen.se") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("kampanj.expressen.se") > 0:
            return ArticleGenre.ADVERTISEMENT
        return ArticleGenre.NONE

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

    def extract_authors(self) -> list:
        """Extract authors."""
        authors = self.response.css(
            ".article__authors .byline__contact span::text").getall()
        if authors:
            return authors
        authors = self.article.authors
        if authors:
            return authors
        return None

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        if self.response.css(".paywall__login-dialog"):
            return True
        return False
