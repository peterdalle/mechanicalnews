# -*- coding: utf-8 -*-
"""
Unit tests of spider.
"""
# Use relative import of module for testing.
import sys, os
testdir = os.path.dirname(__file__)
srcdir = "../mechanicalnews"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import datetime
import unittest
import html_snippets as html_snippets
from datetime import tzinfo
from basespider import BaseArticleSpider
from extractors import ArticleExtractor, ArticleExtractorParserError
from spiders.goteborgsposten import GoteborgspostenSpider


class RunTest_BaseSpider(unittest.TestCase):

    def setUp(self):
        self.spider = BaseArticleSpider(name="test")

    def test_basespider_has_values(self):
        self.assertEqual(self.spider._SOURCE_ID, None)
        self.assertEqual(repr(self.spider), "test (057d97fc-6a80-4c00-8c9f-7a8bc681b592)")
        self.assertEqual(self.spider.USE_SPLASH, False)
        self.assertEqual(self.spider.DEFAULT_LANGUAGE, "en")
        self.assertEqual(self.spider.USE_SPLASH, False)
        self.assertEqual(self.spider.EXCLUDED_META_TAGS, ["viewport", "msapplication-config",
                          "googlebot", "robots", "format-detection", "theme-color", ""])


class RunTest_ExampleSpider(unittest.TestCase):

    def setUp(self):
        self.spider = BaseArticleSpider(name="test")

    def test_base_pider_has_correct_default_values(self):
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

if __name__ == '__main__':
    unittest.main()
