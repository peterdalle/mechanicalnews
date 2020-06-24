#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from scrapy_splash import SlotPolicy, SplashRequest
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from mechanicalnews.settings import PaywallLogin
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre


class GoteborgspostenSpider(BaseArticleSpider):
    """Web scraper for articles on www.gp.se."""
    SPIDER_GUID = "e3689284-14a4-4878-8747-47f666febf3e"
    LAST_UPDATED = "2020-05-19"
    AUTHORS = ["Peter M. Dahlgren"]
    AUTHORS_EMAIL = ["peterdalle+github@gmail.com"]
    USE_LOGIN = False
    USE_SPLASH = False
    DEFAULT_LANGUAGE = "sv"
    name = "goteborgsposten"
    allowed_domains = ["gp.se"]
    start_urls = [
        "https://www.gp.se/",
        "https://www.gp.se/ekonomi",
        "https://www.gp.se/kultur",
        "https://www.gp.se/sport",
        "https://www.gp.se/ledare",
        "https://www.gp.se/debatt",
        "https://www.gp.se/fria-ord",
        "https://www.gp.se/video",
    ]

    # Deny URLs that match these rules.
    rules = [
        Rule(LinkExtractor(deny=r"^https?://info.gp.se.*"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://rabattkod.gp.se/.*"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://kundforum.gp.se/.*"),
             follow=False),
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
            "section": self.article.section,
            "categories": self.extract_categories(),
            "tags": self.extract_tags(),
            "image_urls": self.extract_images()
        }))

    def login(self):
        """Login through Paywall."""
        username, password = PaywallLogin.get_spider_login(self.name)
        url = "https://www.gp.se/mina-sidor/f%C3%B6ljer"
        script = """
        function main(splash)
            splash.private_mode_enabled = false
            splash.images_enabled = false
            splash:init_cookies(splash.args.cookies)

            assert(splash:go('{{url}}'))
            assert(splash:wait(2))

            local user_input = splash:select('.c-login__form .email')
            user_input:send_text('{{username}}')
            assert(splash:wait(1))

            local pass_input = splash:select('.c-login__form .password')
            pass_input:send_text('{{password}}')
            assert(splash:wait(1))

            local login_btn = splash:select('.c-login__form .js-login-submit')
            login_btn:click()
            assert(splash:wait(3))

            local entries = splash:history()
            local last_response = entries[#entries].response

            return {
                html = splash:html(),
                cookies = splash:get_cookies(),
                headers = last_response.headers,
                http_status = last_response.status,
                cookies = splash:get_cookies(),
            }
        end
        """
        script = script.replace("{{username}}", username)
        script = script.replace("{{password}}", password)
        script = script.replace("{{url}}", url)
        return SplashRequest(url=self.start_urls[0],
                             callback=self.after_login,
                             args={"lua_source": script},
                             cache_args=['lua_source'],
                             endpoint="execute",
                             # Keeps cookies for session.
                             session_id="foo",
                             slot_policy=SlotPolicy.PER_DOMAIN)

    def after_login(self):
        self.logger.info("after_login")
        pass

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_categories(self) -> list:
        """Extract categories."""
        categories = self.response.css(".c-article__category::text").getall()
        if categories:
            return categories
        return None

    def extract_headline(self) -> str:
        """Extract headline."""
        return self.response.css("h1.c-article__heading::text").get(default="")

    def extract_lead(self) -> str:
        """Extract article lead."""
        lead = " ".join(self.response.css(".c-article__lead::text").getall())
        if lead:
            return lead
        lead = self.response.css(".c-article__lead element::text").getall()
        if lead:
            return lead
        return None

    def extract_body(self) -> str:
        """Extract article body."""
        body = " ".join(self.response.css(
                        ".c-article__body__content").getall())
        if body:
            return body
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/om/") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/artikelserie/") > 0:
            return PageType.COLLECTION
        elif len(lead.strip()) > 0 or len(body.strip()) > 0:
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
        if self.response.url.lower().find("/ekonomi/") > 0:
            return ArticleGenre.ECONOMY
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/familjeannonser/") > 0:
            return ArticleGenre.PERSONAL
        if self.response.url.lower().find("/livsstil/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("/kultur/") > 0:
            return ArticleGenre.ENTERTAINMENT
        if self.response.url.lower().find("rabattkod.gp.se") > 0:
            return ArticleGenre.ADVERTISEMENT
        if self.response.url.lower().find("info.gp.se") > 0:
            return ArticleGenre.NONE
        if self.response.url.lower().find("medlem.gp.se") > 0:
            return ArticleGenre.NONE
        if self.response.url.lower().find("kundforum.gp.se") > 0:
            return ArticleGenre.NONE

        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "| Göteborgs-Posten - Ledare",
            "| Göteborgs-Posten - Sverige",
            "| Göteborgs-Posten - Kultur",
            "| Göteborgs-Posten - Debatt",
        ]
        title = self.response.css("title::text").get(default="")
        return self._remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        return None

    def extract_tags(self) -> list:
        """Extract article tags."""
        tags = self.article.tags
        if tags:
            return tags
        tags = self.response.css(".c-article__tags__item span::text").getall()
        if tags:
            return tags
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
        if self.response.css(".c-premium-lockscreen"):
            return True
        return False
