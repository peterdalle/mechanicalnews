# -*- coding: utf-8 -*-
"""
Extractors module helps extract article information from HTML, such as title
and author, as well as other structured metadata.
"""
import datetime
import urllib
import dateparser
import lxml
import extruct
import parsel
from scrapy.http import Response
from mechanicalnews.utils import TextUtils


class ArticleExtractorParserError(BaseException):
    """Parser error while extracting information from HTML."""
    pass


class ArticleExtractor():
    """Extract structured metadata from news article HTML.

    Extracts metadata from `<title>`, `<meta>` and `<script>` tags, as well
    as microformats with a focus on news article metadata.

    If `raise_exceptions = True`, an `ArticleExtractorParserError` will
    be raised when a parsering error is caught. Otherwise, they are silently
    logged and accessible via the `errors` property.

    Compared to newspaper3k (https://newspaper.readthedocs.io/),
    ArticleExtractor does not guess.

    Example usage
    -------------
    ```python
    html = "<html><head><title>...</title></head><body></body></html>"
    article = ArticleExtractor.from_html(html)
    print(article.title)
    ```
    """

    def __init__(self, url=None, html=None, parse=True, raise_exceptions=False):
        """Initialize and set default values.

        Parameters
        ----------
        url : str
            The URL of the article.
        html : str
            A string with HTML to extract information from.
        parse : bool
            Whether or not the HTML content should be parsed (i.e., extract
            metadata from the HTML). If `True`, the HTML will be parsed during
            init. If `False`, the metadata will not be parsed during init.
            You can then parse the HTML with the `parse()` method.
        raise_exceptions : bool
            Whether or not to raise `ArticleExtractorParserError` during
            parsing. If `True`, all exceptions are raised. If `False`,
            exceptions are silently logged and accessible through the
            `errors` property.
        """
        self.html = html
        self.microdata = None
        self._metatags = []
        self._url = url
        self._errors = []
        self._raise_exceptions = raise_exceptions
        self._authors = None
        self._body = None
        self._description = None
        self._headline = None
        self._images = None
        self._modified_date = None
        self._pagetype = None
        self._published_date = None
        #self._publisher = None
        self._section = None
        self._sitename = None
        self._tags = None
        self._title = None
        self._language = None
        if parse:
            self.parse()
        if self.html:
            self.selector = parsel.Selector(text=self.html)
            if not self._url:
                self._url = self.url

    @classmethod
    def from_response(cls, response: Response, parse=True, raise_exceptions=False):
        """Create an instance from a Scrapy response object.

        Parameters
        ----------
        response : scrapy.http.Response
            A Scrapy response object.
        url : str
            The URL of the article.
        parse : bool
            Whether or not the HTML content should be parsed (i.e., extract
            metadata from the HTML).
        raise_exceptions : bool
            Whether or not to raise exceptions during parsing. If `True`, all
            exceptions are raised. If `False`, exceptions are silently logged
            and accessible through the `errors` property.

        Returns
        -------
        ArticleExtractor
            Returns a new ArticleExtractor obejct.
        """
        return cls(url=response.url, html=str(response.body, encoding="utf8"),
                   parse=parse, raise_exceptions=raise_exceptions)

    @classmethod
    def from_html(cls, html: str, url=None, parse=True,
                  raise_exceptions=False):
        """Create an instance from HTML string.

        Parameters
        ----------
        html : str
            A string with HTML to extract information from.
        url : str
            The URL of the article.
        parse : bool
            Whether or not the HTML content should be parsed (i.e., extract
            metadata from the HTML).
        raise_exceptions : bool
            Whether or not to raise exceptions during parsing. If `True`, all
            exceptions are raised. If `False`, exceptions are silently logged
            and accessible through the `errors` property.

        Returns
        -------
        ArticleExtractor
            Returns a new ArticleExtractor obejct.
        """
        return cls(url=url, html=html, parse=parse, raise_exceptions=raise_exceptions)

    def __bool__(self):
        """Returns whether HTML exists."""
        return True if self.html else False

    def __len__(self):
        """Returns the length of the HTML."""
        return len(self.html)

    # def __getattr__(self, key) -> object:
    #     return self.to_dict()[key]

    def __repr__(self) -> str:
        """Get string representation.

        Returns
        -------
        str
            Returns a string representation of the object.
        """
        if self.url:
            return "{} <{}>".format(self.title, self.url).strip()
        else:
            return "{}".format(self.title).strip()

    def __str__(self) -> str:
        """Get string representation.

        Returns
        -------
        str
            Returns a string representation of the object.
        """
        return self.__repr__()

    def to_dict(self) -> dict:
        """Get extracted values as a dict.

        Returns
        -------
        dict
            Returns extracted values as a dict.
        """
        if not self.microdata:
            return {}
        return {
            "authors": self.authors,
            "body": self.body,
            "description": self.description,
            "headline": self.headline,
            "images": self.images,
            "modified_date": self.modified_date,
            "pagetype": self.pagetype,
            "published_date": self.published_date,
            # "publisher": self.publisher,
            "section": self.section,
            "sitename": self.sitename,
            "tags": self.tags,
            "title": self.title,
            "url": self.url,
            "language": self.language,
            }

    def parse(self):
        """Parse HTML and extract metadata from HTML.

        The metadata is then available via parameter `microdata`.
        """
        if not self.html:
            return
        try:
            self.microdata = extruct.extract(self.html)
        except BaseException as err:
            if self._raise_exceptions:
                raise ArticleExtractorParserError("parse(): {}".format(err))
            else:
                self._errors.append("parse() error: {}".format(err))

    @property
    def errors(self) -> list:
        """Get errors that occured while parsing the HTML.

        Returns
        -------
        list
            Returns list with each error message in the order they were
            encountered. Returns an empty list if there are no errors.
        """
        return self._errors

    @property
    def has_errors(self) -> bool:
        """Get whether or not errors occured during parsing.

        Returns
        -------
        bool
            Returns True if errors were found, False if no errors were found.
        """
        return len(self._errors) > 0

    @staticmethod
    def make_absolute_urls(base: str, href_list: list) -> list:
        """Make relative URLs to absolute URLs.

        Parameters
        ----------
        base : str
            The base of the URL (e.g., https://example.net).
        href_list : list
            A list with relative URLs as text strings
            (e.g., ['/dir1/', '/dir2/']).

        Returns
        -------
        list
            Returns a new list with the absolute URLs. If no URLs are found,
            an empty list is returned.
        """
        if not href_list:
            return []
        if type(href_list) != list:
            return TypeError("'href_list' must be a list.")
        absolute_urls = []
        for href in href_list:
            absolute_urls.append(urllib.parse.urljoin(base, href))
        return absolute_urls

    @staticmethod
    def get_links(html: str, base: str, to_absolute_urls=True) -> list:
        """Extract URLs from HTML snippet.

        Parameters
        ----------
        html : str
            A snippet of HTML from which URLs should be extracted.
        base : str
            The base of the URL (e.g., https://example.net).
        to_absolute_urls : bool
            Whether or not relative URLs should be
            converted to absolute URLs.

        Returns
        -------
        list
            Returns a list of string URLs. If no URLs are found,
            an empty list is returned.
        """
        if not html:
            return []
        selector = parsel.Selector(text=html)
        urls = selector.css("a::attr(href)").getall()
        if not urls:
            return []
        if to_absolute_urls:
            return ArticleExtractor.make_absolute_urls(base, urls)
        return urls

    def get_metatags(self, exclude_metatags: list) -> list:
        """Get all <meta> tags from web page.

        Returns
        -------
        list
            Returns a list of dicts with metadata, with `name`, 
            `content`, and `is_property`.
        """
        if self._metatags:
            return self._metatags
        if not self.html:
            return []
        selector = parsel.Selector(text=self.html)
        tags = []
        for meta in selector.css("meta"):
            name = meta.css("::attr(name)").get(default="")
            prop = meta.css("::attr(property)").get(default="")
            content = meta.css("::attr(content)").get(default="")
            name = name if name != "" else prop
            is_prop = 0 if prop == "" else 1
            if not self._is_excluded_metatag(name, exclude_metatags):
                tags.append({
                    "name": name,
                    "content": content,
                    "is_property": is_prop,
                })
        self._metatags = tags
        return tags

    def _is_excluded_metatag(self, metatag: str, exclude_metatags: list) -> bool:
        """Should <meta> tag be excluded?

        Checks both meta name and meta property HTML tags.

        Parameters
        ----------
        meta_name : str
            Name of the HTML meta tag.

        Returns
        -------
        bool
            Returns True if the meta tag should be excluded, otherwise False.
        """
        if metatag.lower() in exclude_metatags:
            return True
        else:
            return False

    @property
    def pagetype(self) -> str:
        """Extracts type of web page (`og:type`).

        Returns
        -------
        str
            Returns type of web page. If no type is found, `None` is returned.
        """
        if self._pagetype:
            return self._pagetype
        self._pagetype = self.find_key("og:type")
        return self._pagetype

    @property
    def url(self) -> str:
        """Extract web page URL (`og:url`, `canonical`).

        Returns
        -------
        str
            Returns web page URL. If no URL is found, `None` is returned.
        """
        if self._url:
            return self._url
        url = self.find_key("og:url")
        if url:
            self._url = url
            return url
        url = self.find_key("canonical")
        if url:
            self._url = url
            return url
        return None

    @property
    def sitename(self) -> str:
        """Extract site name.

        Returns
        -------
        str
            Returns name of web site. If no name is found, `None` is returned.
        """
        if self._sitename:
            return self._sitename
        site = self.find_key("name")
        if site:
            if type(site) in [list, dict]:
                site = site[0] if site and len(site) > 1 else site
        if site:
            self._sitename = site
            return site
        return None

    @property
    def title(self) -> str:
        """Extract document title from `<title>`.

        Returns
        -------
        str
            Returns title of web page. If no title is found,
            `None` is returned.
        """
        if self._title:
            return self._title
        try:
            self._title = self.selector.css(
                "title::text").get(default="").strip()
            return self._title
        except BaseException as err:
            if self._raise_exceptions:
                raise ArticleExtractorParserError("title(): {}".format(err))
            else:
                self._errors.append("title() error: {}".format(err))
        return None

    @property
    def description(self) -> str:
        """Extract description of web page (`description` meta tag or
        `og:description`).

        Returns
        -------
        str
            Returns meta description of web page. If no description is found,
            `None` is returned.
        """
        if self._description:
            return self._description
        self._description = self.find_key("og:description")
        return self._description

    @property
    def headline(self) -> str:
        """Extract headline (`<h1>` or `headline` meta tag).

        Returns
        -------
        str
            Returns headline of web page. If no headline is found,
            `None` is returned.
        """
        if self._headline:
            return self._headline
        headline = self.find_key("headline")
        if not headline:
            headline = self.selector.css("h1::text").get(default="").strip()
        if headline:
            self._headline = headline
            return headline
        return None

    @property
    def body(self) -> str:
        """Extract body text (`articleBody` meta tag).

        Returns
        -------
        str
            Returns article body of web page. If no body is found,
            `None` is returned.
        """
        if self._body:
            return self._body
        body = self.find_key("articleBody")
        if body:
            self._body = body
            return body
        return None

    @property
    def language(self) -> str:
        """Extract language of the web page from meta tag `og:locale`
        or `<html lang>` attribute.

        Returns
        -------
        str
            The language of the web page.
        """
        if self._language:
            return self._language
        lang = self.find_key("og:locale")
        if lang:
            self._language = lang
            return lang
        lang = self.selector.css("html::attr(lang)").get(default="")
        if lang:
            self._language = lang
            return lang
        return None

    @property
    def section(self) -> str:
        """Extract article section (`article:section` or `lp:section` meta tag).

        Returns
        -------
        str
            Returns article section of web page. If no section is found,
            `None` is returned.
        """
        if self._section:
            return self._section
        section = self.find_key("article:section")
        if section:
            if type(section) == list:
                section = "\n".join(section)
            elif type(section) == tuple:
                section = section[1] if len(section) > 1 else ""
            self._section = section
            return section
        section = self.find_key("lp:section")
        if section:
            if type(section) == list:
                section = "\n".join(section)
            elif type(section) == tuple:
                section = section[1] if len(section) > 1 else ""
            self._section = section
            return section
        return None

    @property
    def tags(self) -> list:
        """Extract article tags (`article:tags` meta tag).

        Returns
        -------
        list
            Returns list of article tags. If no tags are found, an empty list
            is returned.
        """
        if self._tags:
            return self._tags
        found_tags = [tag for tag in self.find_dict_keys(
            self.microdata, "article:tag")]
        tags = []
        if found_tags and type(found_tags) == list:
            for tag in found_tags:
                if type(tag) == str:
                    tags.append(tag)
        if tags:
            self._tags = list(set(tags))
            return self._tags
        self._tags = []
        return self._tags

    @property
    def published_date(self) -> datetime.datetime:
        """Extract date article was published (`article:published_time` or
        `datePublished` meta tags).

        Returns
        -------
        datetime
            Returns datetime when article was published. If no datetime was
            found, None is returned.
        """
        if self._published_date:
            return self._published_date
        dt = self.find_key("article:published_time")
        if dt:
            if type(dt) == list and len(dt) > 1:
                dt = dt[1]
                if dt:
                    self._published_date = dateparser.parse(dt)
                    return self._published_date
            else:
                try:
                    self._published_date = dateparser.parse(dt)
                    return self._published_date
                except BaseException as err:
                    if self._raise_exceptions:
                        raise ArticleExtractorParserError(
                                        "published_date(): {}".format(err))
                    else:
                        self._errors.append(
                                 "published_date() error: {}".format(err))
        dt = self.find_key("datePublished")
        if dt:
            if dt is list and len(dt) > 1:
                dt = dt[1]
                if dt:
                    self._published_date = dateparser.parse(dt)
                    return self._published_date
            else:
                try:
                    self._published_date = dateparser.parse(dt)
                    return self._published_date
                except BaseException as err:
                    if self._raise_exceptions:
                        raise ArticleExtractorParserError(
                                            "published_date(): {}".format(err))
                    else:
                        self._errors.append(
                                 "published_date() error: {}".format(err))
        dt = self.find_key("og:created")
        if dt:
            try:
                self._published_date = dateparser.parse(dt)
                return self._published_date
            except BaseException as err:
                if self._raise_exceptions:
                    raise ArticleExtractorParserError(
                                            "published_date(): {}".format(err))
                else:
                    self._errors.append(
                                "published_date() error: {}".format(err))
        return None

    @property
    def modified_date(self) -> datetime.datetime:
        """Extract date article was modified (`article:modified_time` or
        `dateModified` meta tags).

        Returns
        -------
        datetime
            Returns datetime when article was last modified. If no datetime
            was found, None is returned.
        """
        if self._modified_date:
            return self._modified_date
        dt = self.find_key("article:modified_time")
        if dt:
            if type(dt) == list and len(dt) > 1:
                dt = dt[1]
                if dt:
                    self._modified_date = dateparser.parse(dt)
                    return self._modified_date
            else:
                try:
                    self._modified_date = dateparser.parse(dt)
                    return self._modified_date
                except BaseException as err:
                    if self._raise_exceptions:
                        raise ArticleExtractorParserError(
                                            "modified_date(): {}".format(err))
                    else:
                        self._errors.append(
                                 "modified_date() error: {}".format(err))
        dt = self.find_key("dateModified")
        if dt:
            if type(dt) == list and len(dt) > 1:
                dt = dt[1]
                if dt:
                    self._modified_date = dateparser.parse(dt)
                    return self._modified_date
            else:
                try:
                    self._modified_date = dateparser.parse(dt)
                    return self._modified_date
                except BaseException as err:
                    if self._raise_exceptions:
                        raise ArticleExtractorParserError(
                                            "modified_date(): {}".format(err))
                    else:
                        self._errors.append(
                                  "modified_date() error: {}".format(err))
        elif dt:
            self._modified_date = dateparser.parse(dt)
            return self._modified_date
        return None

    @property
    def authors(self) -> list:
        """Extract name of authors (`article:author` or `author` meta tags).

        Returns
        -------
        list
            Returns a list of author names as strings. If no author is found,
            an empty list is returned.
        """
        if self._authors:
            return self._authors
        found_authors = self.find_key("article:author")
        if found_authors:
            if type(found_authors) == list:
                self._authors = "\n".join(found_authors)
                return self._authors
            elif type(found_authors) == dict:
                try:
                    self._authors = found_authors["properties"]["name"]
                    return self._authors
                except KeyError as err:
                    if self._raise_exceptions:
                        raise ArticleExtractorParserError(
                                                   "authors(): {}".format(err))
                    else:
                        self._errors.append(
                                        "authors() error: {}".format(err))
            else:
                self._authors = [found_authors]
                return self._authors
        found_authors = self.find_key("author")
        authors = []
        if found_authors:
            if type(found_authors) == list:
                for author in found_authors:
                    if "name" in author:
                        authors.append(author["name"])
            elif type(found_authors) == str:
                self._authors = authors.append(found_authors)
                return self._authors
        self._authors = list(set(authors))
        return self._authors

    @property
    def images(self) -> list:
        """Extract unique image URLs from article.

        Returns
        -------
        list
            Returns a list of URLs to images. If no image is found, an empty
            list is returned.
        """
        if self._images:
            return self._images
        images = []
        image = self.find_key("og:image")
        if image:
            images.append(image)
        image = self.find_key("twitter:image")
        if image:
            images.append(image)
        image = self.find_key("image")
        if image:
            try:
                image = image["properties"]["url"]
                images.append(image)
            except (KeyError, TypeError) as err:
                if self._raise_exceptions:
                    raise ArticleExtractorParserError(
                                                    "images(): {}".format(err))
                else:
                    self._errors.append("images() error: {}".format(err))
        if images:
            # Turn /image.jpg into http://absolute-url.com/image.jpg.
            images = ArticleExtractor.make_absolute_urls(self.url, images)
        self._images = list(set(images))
        return self._images

    # @property
    # def publisher(self) -> str:
    #     """Extract publisher name (`publisher` meta tag).

    #     Returns
    #     -------
    #     str
    #         Returns name of the web page publisher. If there is no name,
    #         `None` is returned.
    #     """
    #     if self._publisher:
    #         return self._publisher
    #     publisher = self.find_key("publisher")
    #     if publisher:
    #         if type(publisher) == list:
    #             for name in publisher:
    #                 if "NewsMediaOrganization" in name[0]:
    #                     self._publisher = name["name"]
    #                 elif "name" in name:
    #                     self._publisher = name[1]
    #                 else:
    #                     self._publisher = name[1]
    #                 return self._publisher
    #         else:
    #             self._publisher = publisher
    #             return self._publisher
    #     return None

    def find_key(self, kv) -> object:
        """Find a specific key in a node, and return its value.

        Returns
        -------
        object
            Returns a value of any type. Returns `None` if key is not found.
        """
        for value in self.find_dict_keys(self.microdata, kv):
            if value:
                return value
        return None

    def find_dict_keys(self, node, kv) -> object:
        """Find a specific key in a dict node resursively, and return its
        value.

        Returns
        -------
        object
            Returns a value of any type. Returns `None` if key is not found.
        """
        if isinstance(node, list):
            for i in node:
                for x in self.find_dict_keys(i, kv):
                    yield x
        elif isinstance(node, dict):
            if kv in node:
                yield node[kv]
            for j in node.values():
                for x in self.find_dict_keys(j, kv):
                    if isinstance(x, list):
                        for value in x:
                            if "@value" in value:
                                yield value["@value"]
                    else:
                        yield x
        elif isinstance(node, tuple):
            if node[0] == kv:
                yield node[1]
        return None
