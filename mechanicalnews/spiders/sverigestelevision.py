#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class SverigesTelevisionSpider(BaseArticleSpider):
    """Web scraper for articles on www.svt.se."""
    SPIDER_GUID = "bbd7cd8b-d9af-441d-89ae-1c212b0fb644"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "sverigestelevision"
    allowed_domains = ["svt.se"]
    start_urls = [
        "https://www.svt.se/",
        "https://www.svt.se/nyheter/lokalt/blekinge/",
        "https://www.svt.se/nyheter/lokalt/blekinge/",
        "https://www.svt.se/nyheter/lokalt/dalarna/",
        "https://www.svt.se/nyheter/lokalt/gavleborg/",
        "https://www.svt.se/nyheter/lokalt/halland/",
        "https://www.svt.se/nyheter/lokalt/helsingborg/",
        "https://www.svt.se/nyheter/lokalt/jamtland/",
        "https://www.svt.se/nyheter/lokalt/jonkoping/",
        "https://www.svt.se/nyheter/lokalt/norrbotten/",
        "https://www.svt.se/nyheter/lokalt/skane/",
        "https://www.svt.se/nyheter/lokalt/smaland/",
        "https://www.svt.se/nyheter/lokalt/stockholm/",
        "https://www.svt.se/nyheter/lokalt/sodertalje/",
        "https://www.svt.se/nyheter/lokalt/sormland/",
        "https://www.svt.se/nyheter/lokalt/uppsala/",
        "https://www.svt.se/nyheter/lokalt/varmland/",
        "https://www.svt.se/nyheter/lokalt/vast/",
        "https://www.svt.se/nyheter/lokalt/vasterbotten/",
        "https://www.svt.se/nyheter/lokalt/vasternorrland/",
        "https://www.svt.se/nyheter/lokalt/vastmanland/",
        "https://www.svt.se/nyheter/lokalt/orebro/",
        "https://www.svt.se/nyheter/lokalt/ost/",
        "https://www.svt.se/sport/",
        "https://www.svt.se/opinion/",
        "https://www.svt.se/vader/",
        ]

    # Deny URLs that match these rules.
    rules = [
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?sida="),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?autosida="),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?lokalmeny="),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?mobilmeny="),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?nyhetsmeny="),
             follow=False),
        Rule(LinkExtractor(
             deny=r"^https?://www.svt.se/(.*?)\?showalllatestnews="),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?showmodal="),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.svt.se/(.*?)\?sportmeny="),
             follow=False),
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
            "categories": self.extract_categories(),
            "tags": [],
        }))

    def extract_related_links(self) -> list:
        """Extract list of realted links."""
        links = self.response.css("article.nyh_article a::attr(href)").getall()
        return self.article.make_absolute_urls(self.response.url, links)

    def extract_categories(self) -> list:
        """Extract categories."""
        return self.response.css(
                ".nyh_section-header__title a::text").getall()

    def extract_headline(self) -> str:
        """Extract headline."""
        return self.response.css(
                "h1.nyh_article__heading::text").get(default="")

    def extract_lead(self) -> str:
        """Extract lead."""
        return " ".join(self.response.css(
                "p.nyh_article__lead *::text").getall())

    def extract_body(self) -> str:
        """Extract body."""
        return self.response.css(".nyh_article-body").get(default="")

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.css(".nyh_timeline").getall():
            return PageType.COLLECTION
        if self.response.url.lower().find("/nyheter/amne/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/lokalt/") > 0:
            return PageType.ARTICLE
        if len(lead) > 10 or len(body) > 25:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        cats = self.extract_categories()
        cats = [x.lower() for x in cats]
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/svtsport/") > 0:
            return ArticleGenre.SPORTS
        if "opinion" in cats:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/opinion/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/nyheter/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/kultur/") > 0:
            return ArticleGenre.ENTERTAINMENT
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "| SVT Nyheter",
            "| SVT Sport",
            "| SVT Recept",
            "- SVT Nyheter",
            "- SVT Sport",
            ]
        title = self.response.css("title::text").get(default="")
        return TextUtils.remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.response.css(".nyh_article__author ::text").getall()
        if authors:
            return authors

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.response.css(
            ".nyh_article__date-timestamp::attr(datetime)").get(default="")
        dt = DateUtils.parse_date(dt, languages=["sv"],
                             date_formats=["%d %B %Y %H.%M"])
        if dt:
            return dt
        dt = self.article.published_date
        if dt:
            return dt
        return None

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        dt = self.response.css(
            ".nyh_article__date-timestamp::attr(datetime)").getall()
        if len(dt) == 2:
            edited = DateUtils.parse_date(dt[-1])
            if edited:
                return edited
            else:
                edited = DateUtils.parse_date(dt, languages=["sv"],
                                         date_formats=["%d %B %Y %H.%M"])
                if edited:
                    return edited
        dt = self.article.modified_date
        if dt:
            return dt
        return None
