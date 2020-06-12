# -*- coding: utf-8 -*-
"""
Unit tests of spider.
"""
import datetime
import unittest
import tests.html_snippets as html_snippets
from datetime import tzinfo
from basespider import (BaseArticleSpider, ArticleExtractorParserError,
                        ArticleExtractor)
from spiders.goteborgsposten import GoteborgspostenSpider


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
