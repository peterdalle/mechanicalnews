#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from mechanicalnews.settings import PaywallLogin
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
import scrapy
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest, SlotPolicy


class DagensNyheterSpider(BaseArticleSpider):
    """Web scraper for articles on www.dn.se."""
    SPIDER_GUID = "565ee7ce-ff93-4c14-b03c-a60d76b6cc97"
    DEFAULT_LANGUAGE = "sv"
    LAST_UPDATED = "2020-05-19"
    USE_SPLASH = False
    USE_LOGIN = False
    name = "dagensnyheter"
    allowed_domains = ["dn.se"]
    start_urls = [
        "https://www.dn.se/",
        "https://www.dn.se/ekonomi/",
        "https://www.dn.se/kultur-noje/",
        "https://www.dn.se/sthlm/",
        "https://www.dn.se/gbg/",
        "https://www.dn.se/sport/",
        "https://www.dn.se/ledare/",
        "https://www.dn.se/debatt/",
        "https://www.dn.se/asikt/",
        "https://www.dn.se/nyheter/sverige/",
        "https://www.dn.se/nyheter/varlden/",
        "https://www.dn.se/nyheter/vetenskap/",
    ]

    # Deny URLs that match these rules.
    rules = [
        Rule(LinkExtractor(deny=r"^https?://www.dn.se/(.*?)\?channel=tablet"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.dn.se/(.*?)\?channel=mobile"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.dn.se/(.*?)\?site=tablet"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://www.dn.se/(.*?)\?site=mobile"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://annons.dn.se/(.*?)"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://faq.dn.se/(.*?)"),
             follow=False),
        Rule(LinkExtractor(deny=r"^https?://jobb.dn.se/(.*?)"),
             follow=False),
    ]

    def login(self) -> scrapy.Request:
        """Login through paywall first."""
        username, password = PaywallLogin.get_spider_login(self.name)
        url = "https://account.bonnier.news/bip/login?appId=dagensnyheter.se"
        script = """
        function main(splash)
            splash.private_mode_enabled = false
            splash.images_enabled = false
            splash:init_cookies(splash.args.cookies)

            assert(splash:go('{{url}}'))
            assert(splash:wait(2))

            local user_input = splash:select('#form_username')
            user_input:send_text('{{username}}')
            assert(splash:wait(1))

            local pass_input = splash:select('#form_password')
            pass_input:send_text('{{password}}')
            assert(splash:wait(1))

            local login_btn = splash:select('#dn-login-button')
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

    def get_lua_script(self) -> str:
        """Get Lua script used for the scrapy-splash.

        This method is called from `ArticleBaseSpider.start_requests()` when
        `USE_SPLASH` is set to `True`."""
        return """
        function main(splash)
            splash.private_mode_enabled = false
            splash.images_enabled = false
            splash:init_cookies(splash.args.cookies)

            assert(splash:go(splash.args.url))
            assert(splash:wait(5))

            local entries = splash:history()
            local last_response = entries[#entries].response

            return {
                html = splash:html(),
                cookies = splash:get_cookies(),
                headers = last_response.headers,
                http_status = last_response.status,
                cookies = splash:get_cookies(),
            }
        end"""

    def after_login(self, response: scrapy.http.Response):
        """Actions taken after login."""
        username = response.css(".user-info__name::text").get(default="")
        if username:
            self.logger.info("✅ Logged in as: {}".format(username))
        else:
            self.logger.warn("Not logged in.")

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
            "categories": [],
            "tags": self.extract_tags(),
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract related links from body HTML."""
        return self.article.get_links(self.extract_body(), self.response.url)

    def extract_headline(self) -> str:
        """Extract headline (<h1>)."""
        return self.response.css("h1.article__title::text").get(default="")

    def extract_lead(self) -> str:
        """Extract lead."""
        return " ".join(self.response.css(".article__lead *::text").getall())

    def extract_body(self) -> str:
        """Extract body."""
        body = self.response.css(".article__body").get(default="")
        if body:
            return body
        return None

    def extract_section(self) -> str:
        """Extract section."""
        section = self.response.css(".article__vignette::text").get(default="")
        if section:
            return section
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        tags = self.article.tags
        if tags:
            return tags
        tags = self.response.css(".tags__tag a::text").getall()
        if tags:
            return tags
        return None

    def extract_page_type(self) -> PageType:
        """Try to determine if the webpage is an article or a collection of
        some sort (e.g., list of articles, search results, category page)."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if self.response.url.lower().find("/om/") > 0:
            return PageType.COLLECTION
        elif len(lead) > 0 or len(body) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Try to determine type of article (e.g., news, opinion, sports)."""
        if self.response.url.lower().find("/opinion/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/asikt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/debatt/") > 0:
            return ArticleGenre.OPINION
        if self.response.url.lower().find("/ledare/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/kolumner/") > 0:
            return ArticleGenre.EDITORIAL
        if self.response.url.lower().find("/nyheter/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/sthlm/") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("/ekonomi/") > 0:
            return ArticleGenre.ECONOMY
        if self.response.url.lower().find("/sport/") > 0:
            return ArticleGenre.SPORTS
        if self.response.url.lower().find("/kultur-noje/") > 0:
            return ArticleGenre.ENTERTAINMENT
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Remove unnecessary characters from <title>."""
        parts_to_remove = [
            "| DN.SE",
            "- DN.SE",
            "- DN.se",
            "| DN.se",
            "- Dagens Nyheter",
            "| Dagens Nyheter",
        ]
        title = self.response.css("title::text").get(default="")
        return self._remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors and turn it into a comma-separated list."""
        authors = self.article.authors
        if authors:
            return authors
        authors = self.response.css(".author__name::text").getall()
        if authors:
            return authors
        authors = self.response.css(".author-box__name::text").getall()
        if authors:
            return authors
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.article.published_date
        if dt:
            return dt
        dt = self.response.css(
            "time.time--published::attr(datetime)").get(default="")
        dt = self.parse_date(dt, languages=["sv"],
                             date_formats=["%d %B %Y %H.%M"])
        return dt

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        dt = self.article.modified_date
        if dt:
            return dt
        dt = self.response.css(
            "time.time--updated::attr(datetime)").get(default="")
        return self.parse_date(dt)

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images

    def extract_is_paywalled(self) -> bool:
        """Extract whether the article is behind a paywall."""
        paywall = " ".join(self.response.css(".paywall").getall())
        if paywall.find("Detta är en låst artikel") > 0:
            return True
        return False
