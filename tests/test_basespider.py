# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the basespider module.
"""
# Use relative import of module for testing.
import sys, os
testdir = os.path.dirname(__file__)
srcdir = "../mechanicalnews"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import datetime
from datetime import tzinfo
import unittest
import html_snippets as html_snippets
from basespider import BaseArticleSpider
from extractors import ArticleExtractor, ArticleExtractorParserError


class RunTest_BaseSpider(unittest.TestCase):

    def setUp(self):
        self.spider = BaseArticleSpider(name="test")

    def test_basespider_has_values(self):
        self.assertEqual(self.spider._SOURCE_ID, None)
        self.assertEqual(repr(self.spider),
                         "test (057d97fc-6a80-4c00-8c9f-7a8bc681b592)")
        self.assertEqual(self.spider.USE_SPLASH, False)
        self.assertEqual(self.spider.DEFAULT_LANGUAGE, "en")
        self.assertEqual(self.spider.USE_SPLASH, False)
        self.assertEqual(self.spider.EXCLUDED_META_TAGS,
                         ["viewport", "msapplication-config",
                          "googlebot", "robots", "format-detection",
                          "theme-color", ""])


class TZ(datetime.tzinfo):

    def utcoffset(self, _):
        return datetime.timedelta(hours=1)

    def dst(self, _):
        return datetime.timedelta(0)

    def tzname(self, _):
        return "UTC\+01:00"


class RunTest_ArticleExtractor(unittest.TestCase):

    def setUp(self):
        self.article = ArticleExtractor.from_html(html_snippets.bbc_article())

    def tearDown(self):
        self.article = None

    def test_return_keys_that_should_exist_in_output_dict(self):
        dict_keys_that_should_exist = [
            "authors",
            "body",
            "description",
            "headline",
            "images",
            "modified_date",
            "pagetype",
            "published_date",
            # "publisher",
            "section",
            "sitename",
            "tags",
            "title",
            "url",
            "language",
        ]
        article_dict = self.article.to_dict()
        for key in dict_keys_that_should_exist:
            self.assertIn(key, article_dict)

    def test_return_values_from_dict(self):
        d = self.article.to_dict()
        self.assertEqual(d["url"], "https://www.bbc.com/news/business-52273988")
        self.assertEqual(d["title"], "Coronavirus: 'World faces worst recession since Great Depression' - BBC News")
        self.assertEqual(d["authors"], ["https://www.facebook.com/bbcnews"])
        self.assertEqual(d["body"], None)
        self.assertEqual(d["description"], 'The IMF says the coronavirus pandemic has plunged the world into a "crisis like no other".')
        self.assertEqual(d["headline"], "'World faces worst decline since 1930s depression'")
        self.assertEqual(d["images"], ["https://ichef.bbci.co.uk/news/1024/branded_news/1250A/production/_111781057_gettyimages-1209841621.jpg"])
        self.assertEqual(d["modified_date"], datetime.datetime(2020, 4, 14, 14, 26, 59, tzinfo=TZ()))
        self.assertEqual(d["pagetype"], "article")
        self.assertEqual(d["published_date"], datetime.datetime(2020, 4, 14, 14, 26, 59, tzinfo=TZ()))
        # self.assertEqual(d["publisher"], "BBC News")
        self.assertEqual(d["section"], "Business")
        self.assertEqual(d["sitename"], "BBC News")
        self.assertEqual(d["tags"], [])
        self.assertEqual(d["language"], "en_GB")

    def test_return_values_from_properties(self):
        self.assertEqual(self.article.url,  "https://www.bbc.com/news/business-52273988")
        self.assertEqual(self.article.title, "Coronavirus: 'World faces worst recession since Great Depression' - BBC News")
        self.assertEqual(self.article.authors, ["https://www.facebook.com/bbcnews"])
        self.assertEqual(self.article.body, None)
        self.assertEqual(self.article.description, 'The IMF says the coronavirus pandemic has plunged the world into a "crisis like no other".')
        self.assertEqual(self.article.headline, "'World faces worst decline since 1930s depression'")
        self.assertEqual(self.article.images, ["https://ichef.bbci.co.uk/news/1024/branded_news/1250A/production/_111781057_gettyimages-1209841621.jpg"])
        self.assertEqual(self.article.modified_date, datetime.datetime(2020, 4, 14, 14, 26, 59, tzinfo=TZ()))
        self.assertEqual(self.article.pagetype, "article")
        self.assertEqual(self.article.published_date, datetime.datetime(2020, 4, 14, 14, 26, 59, tzinfo=TZ()))
        # self.assertEqual(self.article.publisher, "BBC News")
        self.assertEqual(self.article.section, "Business")
        self.assertEqual(self.article.sitename, "BBC News")
        self.assertEqual(self.article.tags, [])
        self.assertEqual(self.article.language, "en_GB")

    def test_make_absolute_urls(self):
        links = [
            "/aioreg.html",
            "/hello/world",
            "/news/business.com",
            "/news/business-52273988",
            "#",
            "javascript:",
            "tel:",
        ]
        absolute_links = [
            "https://bbc.com/aioreg.html",
            "https://bbc.com/hello/world",
            "https://bbc.com/news/business.com",
            "https://bbc.com/news/business-52273988",
            "https://bbc.com",
            "javascript:",
            "tel:",
        ]
        new_links = self.article.make_absolute_urls(base="https://bbc.com", href_list=links)
        self.assertEqual(new_links, absolute_links)
        self.assertEqual(self.article.make_absolute_urls(base="", href_list=[]), [])
        self.assertRaises(TypeError, self.article.make_absolute_urls(base="", href_list=None))

    def test_has_errors(self):
        self.assertFalse(self.article.has_errors)
        self.assertEqual(self.article.errors, [])

    # def test_raise_error(self):
    #     article = ArticleExtractor.from_html(html=html_snippets.bbc_article(),
    #                                          raise_exceptions=True,
    #                                          parse=False)
    #     self.assertRaises(ArticleExtractorParserError, article.parse)

    def test_has_dunder_methods(self):
        self.assertTrue(bool(self.article))
        self.assertEqual(len(self.article), 190775)
        self.assertEqual(len(self.article.html), 190775)
        self.assertEqual(str(self.article), "Coronavirus: 'World faces worst recession since Great Depression' - BBC News <https://www.bbc.com/news/business-52273988>")
        self.assertEqual(repr(self.article), "Coronavirus: 'World faces worst recession since Great Depression' - BBC News <https://www.bbc.com/news/business-52273988>")


if __name__ == '__main__':
    unittest.main()
