#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class FriaTiderSpider(BaseArticleSpider):
    """Web scraper for articles on friatider.se."""
    SPIDER_GUID = "a8379d8a-ae80-40fe-bb16-81b83af5ad69"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    name = "friatider"
    allowed_domains = ["friatider.se"]
    start_urls = [
        "https://www.friatider.se/",
        "https://www.friatider.se/ekonomi",
        "https://www.friatider.se/vetenskap",
        "https://www.friatider.se/kultur",
        "https://www.friatider.se/inrikes",
        "https://www.friatider.se/utrikes",
        "https://www.friatider.se/opinion",
        "https://www.friatider.se/section/debatt",
        "https://www.friatider.se/section/insandare",
        "https://www.friatider.se/section/replik",
        "https://www.friatider.se/section/ledare"
        "https://www.friatider.se/ledarblogg",
        "https://www.friatider.se/kolumn",
        "https://www.friatider.se/juridik",
        "https://www.friatider.se/eu",
    ]

    # Deny URLs that match these rules.
    rules = [
        Rule(LinkExtractor(deny=r"\.zip"), follow=False),
        Rule(LinkExtractor(deny=r"\.pdf"), follow=False),
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
        """Extract headline."""
        h1 = self.response.css(".content h1::text").get(default="")
        if h1:
            return h1
        h1 = self.article.headline
        if h1:
            return h1
        return None

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = " ".join(self.response.css(".standfirst strong").getall())
        if lead:
            return lead
        lead = self.article.description
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = "\n".join(self.response.css(".bodytext").getall())
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.find("/section/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/ledare/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/kolumn/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("?page=") > 0:
            return PageType.COLLECTION
        if self.response.url.find("/taxonomy/term/") > 0:
            return PageType.COLLECTION
        if self.response.url.find("konto.friatider.se") > 0:
            return PageType.NONE
        if self.response.url.find("/nyhetstips/") > 0:
            return PageType.NONE
        if self.article.find_key("type") == "http://schema.org/NewsArticle":
            return PageType.ARTICLE
        if self.article.find_key("og:type") == "article":
            return PageType.ARTICLE
        if self.response.url.count("-") > 3:
            # Simple hueristic: titles are converted to URL slugs, with
            # hyphens instead of spaces, so we'll guess that hyphens in URL
            # are an indicator of an article.
            return PageType.ARTICLE
        elif len(lead.strip()) > 5 or len(body.strip()) > 5:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        section = self.article.section
        if section == "Kultur":
            return ArticleGenre.ENTERTAINMENT
        if section == "Bok":
            return ArticleGenre.ENTERTAINMENT
        if section == "Essä":
            return ArticleGenre.ENTERTAINMENT
        if section == "Vetenskap":
            return ArticleGenre.TECHNOLOGY
        if section == "Ekonomi":
            return ArticleGenre.ECONOMY
        if section == "EU":
            return ArticleGenre.NEWS
        if section == "Inrikes":
            return ArticleGenre.NEWS
        if section == "Utrikes":
            return ArticleGenre.NEWS
        if section == "Lag & Rätt":
            return ArticleGenre.NEWS
        if section == "Opinion":
            return ArticleGenre.OPINION
        if section == "Debatt":
            return ArticleGenre.OPINION
        if section == "Insändare":
            return ArticleGenre.OPINION
        if section == "Ledare":
            return ArticleGenre.EDITORIAL
        if section == "Kolumn":
            return ArticleGenre.EDITORIAL
        if section == "Porträtt":
            return ArticleGenre.PERSONAL
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
        author_links = self.response.css(
            ".td-post-content p a::attr(href)").getall()
        for author_url in author_links:
            if author_url.find("/author/") > 0:
                author = author_url.replace("https://samnytt.se/", "")
                author = author.replace("/author/", "")
                author = author.replace("/", "")
                if author:
                    return author
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.find_key("og:created")
        if dt:
            try:
                # It seems that the datetime in og:created is
                # in UNIX timestamp format for some reason.
                return datetime.fromtimestamp(int(dt))
            except ValueError:
                pass
        dt = self.article.published_date
        if dt:
            return dt
        return None

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        return self.article.modified_date

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images
