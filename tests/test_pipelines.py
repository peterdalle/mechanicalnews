# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the pipelines module.
"""
# Use relative import of module for testing.
import sys, os
testdir = os.path.dirname(__file__)
srcdir = "../mechanicalnews"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest
from scrapy.spiders import CrawlSpider
from scrapy.crawler import Crawler
from pipelines import MySQLPipeline
from basespider import BaseArticleSpider


class TestSpider(BaseArticleSpider):
    name = "testspider"
    allowed_domains = []
    start_urls = []
    SPIDER_GUID = "test"
    LAST_UPDATED = "2020-06-24"
    DEFAULT_LANGUAGE = "en"

    def parse_article(self):
        pass


class RunTest_MySQLPipeline(unittest.TestCase):

    def test_crawler_default_settings(self):
        pipeline = MySQLPipeline.from_crawler(Crawler(
            spidercls=TestSpider))
        self.assertEqual(pipeline.database, "mechanicalnews")
        del(pipeline)


if __name__ == '__main__':
    unittest.main()
