#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from basespider import BaseArticleSpider
from extractors import ArticleExtractor
from items import ArticleItem, PageType, ArticleGenre


class DagensIndustriSpider(BaseArticleSpider):
    """Web scraper for articles on www.gp.se."""
    SPIDER_GUID = "056515ae-47af-4a26-861d-4b46f746bb04"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "dagensindustri"
    allowed_domains = ["di.se"]
    start_urls = [
        "https://www.di.se/",
        "https://www.di.se/amnen/ledare/",
        "https://www.di.se/bil/",
        "https://www.di.se/amnen/di-gasell/",
        "https://weekend.di.se/",
        "https://digital.di.se/",
    ]

    def parse_article(self, response: scrapy.http.Response) -> ArticleItem:
        """Parse article and extract article information."""
        self.response = response
        self.article = ArticleExtractor.from_response(self.response,
                                                      parse=False)
        self.article.parse()
        yield self.extract_information(response, ArticleItem({
            "links": self.extract_related_links(),
            "title": self.extract_title(),
            "h1": self.extract_heading(),
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

    def extract_tags(self) -> list:
        tags = self.article.tags
        if tags:
            return tags
        tags = self.response.css(
                        ".di_watchlist-article-tags__value::text").getall()
        if tags:
            return tags
        return None

    def extract_heading(self) -> str:
        h1 = self.article.headline
        if h1:
            return h1
        # di.se
        h1 = self.response.css(
            "h1.di_font--heading1 di_article-top__heading::text").get(
                default="")
        if h1:
            return h1
        # digital.di.se
        h1 = self.response.css("h1.article__headline::text").get(default="")
        if h1:
            return h1
        # general fallback
        h1 = self.response.css("h1::text").get(default="")
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = self.article.description
        if lead:
            return lead
        # di.se
        lead = "\n".join(self.response.css(
            ".di_article-lead p::text").getall())
        if lead:
            return lead
        # digital.di.se
        lead = self.response.css(".article__lead::text").get(default="")
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body, but only without paywall."""
        if self.extract_is_paywalled():
            # digital.di.se
            body = self.article.find_key("articleBody")
            if body:
                return body
            body = "\n".join(self.response.css(
                ".article__main_column article__body").getall())
            if body:
                return body
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/amnen/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/kategori/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/ditv/") > 0:
            return PageType.VIDEO
        if self.response.url.lower().find("/video/") > 0:
            return PageType.VIDEO
        if self.response.url.lower().find("/artikel/") > 0:
            return PageType.ARTICLE
        if self.response.url.lower().find("/intervjuer/") > 0:
            return PageType.ARTICLE
        if self.response.url.lower().find("/analys/") > 0:
            return PageType.ARTICLE
        if self.response.url.lower().find("/nyheter/") > 0:
            return PageType.ARTICLE
        if self.response.url.lower().find("/reportage/") > 0:
            return PageType.ARTICLE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if self.response.url.lower().find("/debatt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/fria-ord/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/ledare/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/sverige/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/varlden/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/nyheter/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/pressreleaser/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/live/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/vin/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/bil/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/bors/") > 0:
            return ArticleGenre.ECONOMY
        if self.response.url.lower().find("kampanj.di.se") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("/brandstudio/") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("/jamfar-bolan/") > 0:
            return ArticleGenre.ADVERTISEMENT
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        return self.response.css("title::text").get(default="")

    def extract_authors(self) -> list:
        """Extract authors into list."""
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
        """Extract whether the article is behind a paywall."""
        block = self.response.css(".di_article_text-block").get(default="")
        if block and block.find("Artikeln du läser är låst"):
            return True
        return False
