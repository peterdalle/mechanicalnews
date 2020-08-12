#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from bs4 import BeautifulSoup
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class AftonbladetSpider(BaseArticleSpider):
    """Web scraper for articles on www.aftonbladet.se."""
    SPIDER_GUID = "e7aa4c96-71b8-4044-a749-5c1c152e5d7d"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "aftonbladet"
    allowed_domains = ["aftonbladet.se"]
    start_urls = [
        "https://www.aftonbladet.se/",
        "https://www.aftonbladet.se/sportbladet",
        "https://www.aftonbladet.se/plus",
        "https://tv.aftonbladet.se/abtv/",
        "https://www.aftonbladet.se/a-o",
        "https://www.aftonbladet.se/nojesbladet",
        "https://www.aftonbladet.se/matdryck",
        "https://www.aftonbladet.se/kultur",
        "https://www.aftonbladet.se/ledare",
        "https://www.aftonbladet.se/debatt",
        "https://www.aftonbladet.se/nyheter/kolumnister",
        "https://www.aftonbladet.se/family"
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
            "section": self.extract_section(),
            "categories": self.extract_categories(),
            "tags": self.extract_tags(),
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_section(self) -> str:
        """Extract article section."""
        return self.article.section

    def extract_categories(self) -> list:
        """Extract categories."""
        return self.response.css("._2945r a::text").getall()

    def extract_tags(self) -> list:
        """Extract tags."""
        tags = self.response.css(
            "div[data-test-id='article-tags'] h3::text").getall()
        if tags:
            return tags
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/tagg/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/story/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/amnen/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/tv/") > 0:
            return PageType.VIDEO
        if self.response.url.lower().find("/abtv/programs/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/abtv/") > 0:
            return PageType.VIDEO
        if self.response.url.lower().find("podcast.aftonbladet.se") > 0:
            return PageType.SOUND
        if self.response.url.lower().find("/supernytt/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/a/") > 0:
            return PageType.ARTICLE
        elif len(lead) > 0 or len(body) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)"""
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/sportbladet/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/debatt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/ledare/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/kolumnister/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/nyheter/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/kultur/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/nojesbladet/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/matdryck/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/bil/") > 0:
            return ArticleGenre.TECHNOLOGY
        if self.response.url.lower().find("/family/") > 0:
            return ArticleGenre.PERSONAL
        if self.response.url.lower().find("/relationer/") > 0:
            return ArticleGenre.PERSONAL
        if self.response.url.lower().find("/minekonomi/") > 0:
            return ArticleGenre.ECONOMY
        if self.response.url.lower().find("/kampanj/") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("/rabattkod/") > 0:
            return ArticleGenre.ADVERTISEMENT
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "| Aftonbladet",
            "| Aftonbladet.se",
            "- Aftonbladet",
            "- Aftonbladet.se",
        ]
        title = self.response.css("title::text").get(default="")
        title = TextUtils.remove_strings(title, parts_to_remove)
        return title

    def extract_headline(self) -> str:
        """Extract headline."""
        h1 = self.response.css("h1::text").get()
        if h1:
            return h1
        lead = self.article.headline
        if lead:
            return lead
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = " ".join(
            self.response.css("p.c-Cz1 *::text").getall())
        if lead:
            return lead
        lead = self.response.css("h2::text").get(default="")
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body HTML."""
        soup = BeautifulSoup(self.response.text, "html.parser")
        if soup:
            soup = soup.find("div", {"class": "_3p4DP"})
            if soup:
                body = soup.find_all(["p", "h2"])
                if body:
                    return "\n".join([str(p) for p in body])
        return None

    def extract_authors(self) -> list:
        """Extract authors."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css("._3kA47 ::text").getall()
        if authors:
            return authors
        return None

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.published_date
        if dt:
            return dt
        dt = self.response.xpath(
            "//*[contains(concat(' ', @class, ' '), ' _3aoyk ')]" +
            "//time[@itemprop='datePublished']//@datetime").get()
        if dt:
            return DateUtils.parse_date(dt)
        dt = self.response.css("._2j7q7 time::attr(datetime)").getall()
        if dt and len(dt) > 2:
            pub = dt[0]
            if pub:
                return DateUtils.parse_date(pub)
        if dt:
            return DateUtils.parse_date(dt)
        return None

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        dt = self.article.modified_date
        if dt:
            return dt
        dt = self.response.xpath(
            "//*[contains(concat(' ', @class, ' ')," +
            " ' _3aoyk ')]//time[@itemprop='dateModified']//@datetime").get()
        if dt:
            return DateUtils.parse_date(dt)
        dt = self.response.css("._2j7q7 time::attr(datetime)").getall()
        if dt and len(dt) > 2:
            mod = dt[1]
            if mod:
                return DateUtils.parse_date(mod)
            else:
                return DateUtils.parse_date(dt)
        return None

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        if str(self.response.body).find("teaser-service.aftonbladet.se") > 0:
            return True
        return False
