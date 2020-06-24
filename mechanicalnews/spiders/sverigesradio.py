#!/usr/bin/env python
# -*- coding: utf-8 -*-
import scrapy
from mechanicalnews.basespider import BaseArticleSpider
from mechanicalnews.extractors import ArticleExtractor
from mechanicalnews.items import ArticleItem, PageType, ArticleGenre
from datetime import datetime
import re


class SverigesRadioSpider(BaseArticleSpider):
    """Web scraper for articles on www.sverigesradio.se."""
    SPIDER_GUID = "05b2cbe8-8606-4bc9-9165-57f0c7a5d8ad"
    LAST_UPDATED = "2020-05-19"
    DEFAULT_LANGUAGE = "sv"
    name = "sverigesradio"
    allowed_domains = ["sverigesradio.se"]
    start_urls = [
        "https://sverigesradio.se/",
        "https://sverigesradio.se/ekot",
        "https://sverigesradio.se/studioett",
        "https://sverigesradio.se/p3nyheterpaenminut",
        # Nyheter på lätt svenska:
        "https://sverigesradio.se/sida/avsnitt?programid=5307",
        # Regionala nyheter:
        "https://sverigesradio.se/blekinge/",
        "https://sverigesradio.se/dalarna/",
        "https://sverigesradio.se/gotland/",
        "https://sverigesradio.se/gavleborg/",
        "https://sverigesradio.se/goteborg/",
        "https://sverigesradio.se/halland/",
        "https://sverigesradio.se/jamtland/",
        "https://sverigesradio.se/jonkoping/",
        "https://sverigesradio.se/kalmar/",
        "https://sverigesradio.se/kristianstad/",
        "https://sverigesradio.se/kronoberg/",
        "https://sverigesradio.se/malmo/",
        "https://sverigesradio.se/norrbotten/",
        "https://sverigesradio.se/sjuharad/",
        "https://sverigesradio.se/skaraborg/",
        "https://sverigesradio.se/stockholm/",
        "https://sverigesradio.se/sormland/",
        "https://sverigesradio.se/uppland/",
        "https://sverigesradio.se/varmland/",
        "https://sverigesradio.se/vast/",
        "https://sverigesradio.se/vasterbotten/",
        "https://sverigesradio.se/vasternorrland/",
        "https://sverigesradio.se/vastmanland/",
        "https://sverigesradio.se/orebro/",
        "https://sverigesradio.se/ostergotland/",
        "https://sverigesradio.se/sodertalje/",
        ]

    def parse_article(self, response: scrapy.http.Response) -> ArticleItem:
        """Parse article and extract information."""
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
            "section": self.extract_section(),
            "categories": self.extract_categories(),
            "tags": self.extract_tags(),
            "image_urls": self.extract_images(),
        }))

    def extract_related_links(self) -> list:
        """Extract list of realted links."""
        links = self.response.css(".sr-page__content::attr(href)").getall()
        return self.article.make_absolute_urls(self.response.url, links)

    def extract_headline(self) -> str:
        """Extract headlne."""
        h1 = self.response.css("h1.heading::text").get(default="")
        if h1:
            return h1
        return None

    def extract_section(self) -> str:
        """Extract section."""
        return self.response.css(".ribbon__title--text::text").get(default="")

    def extract_categories(self) -> list:
        """Extract categories."""
        categories = self.response.css(
                                ".publication-theme::text").get(default="")
        if categories:
            return [categories]
        return None

    def extract_tags(self) -> list:
        """Extract tags."""
        return self.response.css(".ArticleTags a::text").getall()

    def extract_lead(self) -> str:
        """Extract lead."""
        return " ".join(self.response.css(
                "div.publication-preamble *::text").getall())

    def extract_body(self) -> str:
        """Extract body."""
        return self.response.css(".publication-text").get(default="")

    def extract_page_type(self) -> PageType:
        """Determine if webpage is an article or collection."""
        lead = self.extract_lead() if self.extract_lead() else ""
        body = self.extract_body() if self.extract_body() else ""
        if len(self.response.css("article.article-details")):
            return PageType.ARTICLE
        if self.response.url.lower().find("/artikel/") > 0:
            return PageType.ARTICLE
        if self.response.url.lower().find("/sida/artikel.aspx") > 0:
            return PageType.ARTICLE
        if self.response.url.lower().find("/avsnitt/") > 0:
            return PageType.SOUND
        if self.response.url.lower().find("programid=") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/sida/default.aspx") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/sida/tabla.aspx") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/sida/latlista.aspx") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/sida/gruppsida.aspx") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/sida/kanalprogramlista.aspx") > 0:
            return PageType.COLLECTION
        if self.response.url.lower().find("/sida/textarkiv.aspx") > 0:
            return PageType.COLLECTION
        if len(lead) > 0 or len(body) > 0:
            return PageType.ARTICLE
        return PageType.NONE

    def extract_article_genre(self) -> ArticleGenre:
        """Determine type of article (news, opinion, sports etc)."""
        if self.response.url.lower().find("artikel") > 0:
            return ArticleGenre.NEWS
        if self.response.url.lower().find("programid=179") > 0:
            return ArticleGenre.SPORTS
        return ArticleGenre.NONE

    def extract_title(self) -> str:
        """Extract <title>."""
        # Remove unnecessary characters
        parts_to_remove = [
            "| Sveriges Radio",
            "- Nyheter (Ekot) | Sveriges Radio",
            "- P4 Blekinge | Sveriges Radio",
            "- P4 Dalarna | Sveriges Radio",
            "- P4 Gotland | Sveriges Radio",
            "- P4 Gävleborg | Sveriges Radio",
            "- P4 Göteborg | Sveriges Radio",
            "- P4 Halland | Sveriges Radio",
            "- P4 Jämtland | Sveriges Radio",
            "- P4 Jönköping | Sveriges Radio",
            "- P4 Kalmar | Sveriges Radio",
            "- P4 Kristianstad | Sveriges Radio",
            "- P4 Kronoberg | Sveriges Radio",
            "- P4 Malmöhus | Sveriges Radio",
            "- P4 Norrbotten | Sveriges Radio",
            "- P4 Sjuhärad | Sveriges Radio",
            "- P4 Skaraborg | Sveriges Radio",
            "- P4 Stockholm | Sveriges Radio",
            "- P4 Sörmland | Sveriges Radio",
            "- P4 Uppland | Sveriges Radio",
            "- P4 Värmland | Sveriges Radio",
            "- P4 Väst | Sveriges Radio",
            "- P4 Västerbotten | Sveriges Radio",
            "- P4 Västernorrland | Sveriges Radio",
            "- P4 Västmanland | Sveriges Radio",
            "- P4 Örebro | Sveriges Radio",
            "- P4 Östergötland | Sveriges Radio",
            "- P4 Södertälje | Sveriges Radio",
            ]
        title = self.response.css("title::text").get(default="")
        return self._remove_strings(title, parts_to_remove)

    def extract_authors(self) -> list:
        """Extract authors."""
        authors = self.response.css(".byline::text").getall()
        if authors:
            return authors
        return None

    def extract_publish_date(self) -> datetime:
        """Extract publish date."""
        dt = self.response.css(
            ".publication-metadata__item::text").get(default="").strip()
        if "Publicerat" in dt:
            dt = dt[dt.find("Publicerat"):]
            try:
                parsed_dt = self._parse_date_from_textstring(dt)
                self.logger.debug(
                    "Parsed '{}' as publish date '{}'".format(dt, parsed_dt))
                return parsed_dt
            except BaseException as e:
                self.logger.debug(
                    "Error parsing '{}' as modified date: '{}'".format(dt, e))
        return None

    def extract_modified_date(self) -> datetime:
        """Extract modified date."""
        dt = self.response.css(
            ".nyh_article__date-timestamp::attr(datetime)").getall()
        if "Uppdaterat" in dt:
            dt = dt[:dt.find("Publicerat")]
            try:
                parsed_dt = self._parse_date_from_textstring(dt)
                self.logger.debug(
                    "Parsed '{}' as modified date '{}'".format(dt, parsed_dt))
                return parsed_dt
            except BaseException as e:
                self.logger.debug(
                    "Error parsing '{}' as modified date: '{}'".format(dt, e))
        return None

    def extract_images(self) -> list:
        """Extract images."""
        return self.article.images

    def _parse_date_from_textstring(self, text) -> datetime:
        """Extract date parts."""
        # Date formats:
        #   Uppdaterat kl 17.14 Publicerat kl 09.49
        #   Publicerat kl 21.10
        #   Publicerat söndag 22 mars kl 21.10
        #   Publicerat tisdag 29 november 2005 kl 11.05
        year = re.search(r"([1-3][0-9]{3})", text)
        month = self._get_month_in_string(text)
        day = re.search(r"\s(\d{1,2})\s", text)
        time = re.search(r"([0-9]|0[0-9]|1[0-9]|2[0-3])\.[0-5][0-9]", text)
        # Make sure parts are valid.
        day = day.group().strip() if day else datetime.now().day
        year = year.group() if year else datetime.now().year
        time = time.group().replace(".", ":") if time else "00:00"
        # Construct full date.
        d = "{}-{}-{} {}".format(year, month, day, time)
        date = datetime.strptime(d, "%Y-%m-%d %H:%M")
        if date:
            return date
        return None

    def _get_month_in_string(self, text) -> int:
        """Get month as integer from text string with a month."""
        if not text:
            return None
        months = ["januari", "februari", "mars", "april",
                  "maj", "juni", "juli", "augusti",
                  "september", "oktober", "november", "december"]
        for i, month in enumerate(months):
            if month in text.lower():
                return i
        return datetime.now().month
