# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the pipelines module.
"""
import unittest
from pipelines import MySQLPipeline
from spiders.aftonbladet import AftonbladetSpider
from scrapy.crawler import Crawler


class RunTest_MySQLPipeline(unittest.TestCase):

    def test_crawler_default_settings(self):
        pipeline = MySQLPipeline.from_crawler(Crawler(
            spidercls=AftonbladetSpider))
        self.assertEqual(pipeline.database, "mechanicalnews")


if __name__ == '__main__':
    unittest.main()
