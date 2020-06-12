#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest, SlotPolicy
from basespider import BaseArticleSpider
from extractors import ArticleExtractor
from items import ArticleItem, PageType, ArticleGenre
from settings import PaywallLogin


class SvenskaDagbladetSpider(BaseArticleSpider):
    """Web scraper for articles on www.dn.se."""
    SPIDER_GUID = "c2a9e4a5-606f-497c-8d2a-0a19d3518ebd"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    USE_SPLASH = True
    name = "svenskadagbladet"
    allowed_domains = ["svd.se"]
    start_urls = [
        "https://www.svd.se/",
        "https://www.svd.se/naringsliv",
        "https://www.svd.se/kultur",
        "https://www.svd.se/ledare",
        "https://www.svd.se/debatt",
        "https://www.svd.se/livet",
    ]

    # Deny URLs that match these rules.
    rules = [
        Rule(LinkExtractor(deny=r"^https?://www.svd.se/i/senaste.*"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://accent.svd.se/.*"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://kundservice.svd.se/.*"),
             follow=False),
    ]

    def login(self):
        username, password = PaywallLogin.get_spider_login(self.name)
        # Load page below because it's lighter than the frontpage.
        url = "https://kundservice.svd.se/"
        script = """
        function main(splash)
            splash.private_mode_enabled = false
            splash.images_enabled = false
            splash:init_cookies(splash.args.cookies)

            assert(splash:go('{{url}}'))
            assert(splash:wait(2))

            local user_btn = splash:select('.CoreNavigation-login-link')
            user_btn:click()
            assert(splash:wait(3))

            local user_input = splash:select('#email')
            user_input:send_text('{{username}}')
            user_input:send_keys('<Enter>')
            assert(splash:wait(1))

            local pass_input = splash:select('#password')
            pass_input:send_text('{{password}}')
            assert(splash:wait(1))

            local login_btn = splash:select('#ActionButton_0')
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

    def after_login(self, response: scrapy.http.Response):
        loggedin = response.css(".logged-in-as").getall(default="")
        if loggedin:
            self.logger.info("✅ Logged in.")
        else:
            self.logger.warn("Not logged in.")

    def get_lua_script(self) -> str:
        pass

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
            "is_deleted": False,
            "published": self.extract_publish_date(),
            "edited": self.extract_modified_date(),
            "authors": self.extract_author(),
            "section": self.article.section,
            "categories": self.extract_categories(),
            "tags": self.extract_tags(),
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract headline."""
        return self.response.css(
            "h1.ArticleHead-heading::text").get(default="")

    def extract_lead(self) -> str:
        """Extract lead."""
        return " ".join(self.response.css(
                                 ".ArticleLayout-subHeader p::text").getall())

    def extract_body(self) -> str:
        """Extract body."""
        return " ".join(self.response.css(".Body").getall())

    def extract_categories(self) -> list:
        """Extract categories."""
        return self.response.css(".ArticleLayout-category a::text").getall()

    def extract_tags(self) -> list:
        """Extract tags."""
        return self.response.css(".ArticleTags a::text").getall()

    def extract_page_type(self) -> PageType:
        """
        Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page).
        """
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/om/") > 0:
            return PageType.COLLECTION
        elif self.response.url.lower().find("/senaste/i") > 0:
            return PageType.COLLECTION
        elif len(lead.strip()) > 0 or len(body.strip()) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if self.response.url.lower().find("/debatt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/ledare/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/ledare-kolumnister/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/sverige/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/varlden/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/sverige/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.css(".Native-marking"):
            return ArticleGenre.ADVERTISEMENT
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "| SvD",
            "- SvD",
            "| SVD",
            "- SVD",
        ]
        title = self.response.css("title::text").get(default="")
        return self._remove_strings(title, parts_to_remove)

    def extract_author(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.response.css(".LinkedAuthor::text").getall()
        if authors:
            return authors
        authors = self.response.css(".Meta-part--author::text").getall()
        if authors:
            return authors
        authors = self.article.authors
        if authors:
            return authors
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.response.css(
           ".Meta-part--published > time::attr(data-datetime)").get(default="")
        return self.parse_date(dt, languages=["sv"],
                               date_formats=["%d %B %Y %H.%M"])

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        dt = self.response.css(
            ".Meta-part--updated > time::attr(data-datetime)").get(default="")
        return self.parse_date(dt)

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        if self.response.css(".paywall-loader"):
            return True
        return False
