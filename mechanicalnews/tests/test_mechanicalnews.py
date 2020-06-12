# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the __init__ module.
"""
import unittest
from __init__ import MechanicalNews


class RunTest_MechanicalNews(unittest.TestCase):

    def test_find_spider_from_url(self):
        pairs = [
            (None, "foo"),
            (None, None),
            (None, ""),
            (None, "Foo:Bar"),
            (None, "ftp://thisdoesntwork@404.com"),
            (None, "tel:12345"),
            (None, "javascript:alert('hello');"),
            (None, "mailto:none@example.com"),
            (None, "http://notfound.com"),
            ("DagensNyheterSpider", "https://www.dn.se/hej/hallå/där"),
            ("DagensNyheterSpider", "https://dn.se/nyhet/eopgj/"),
            ("DagensNyheterSpider", "http://dn.se/nyhet/eopgj/"),
            ("DagensNyheterSpider", "https://www.dn.se/nyhet/eopgj/"),
            ("AftonbladetSpider", "http://www.aftonbladet.se/"),
            ("AftonbladetSpider", "https://www.aftonbladet.se/"),
            ("AftonbladetSpider", "http://aftonbladet.se/"),
            ("AftonbladetSpider", "https://aftonbladet.se/"),
            ("AftonbladetSpider",
             "https://www.aftonbladet.se/nyheter/a/50QnnK/ambulans-och-personbil-i-krock-med-hjortflock"),
            ("AftonbladetSpider", "https://viktklubb.aftonbladet.se/"),
            ("AftonbladetSpider", "https://live.aftonbladet.se/"),
        ]
        for spider_name, url in pairs:
            found_spider = MechanicalNews.get_spider_by_url(url)
            if found_spider:
                found_spider = found_spider["class_name"]
            self.assertEqual(spider_name, found_spider)

    def test_get_spider_by_name_works(self):
        pairs = [
            ("dagensnyheter", "DagensNyheterSpider"),
            ("aftonbladet", "AftonbladetSpider"),
            ("xxxxxxxxxxxxxx", None),
        ]
        for spider_name, spider_class in pairs:
            found_spider = MechanicalNews.get_spider_by_name(spider_name)
            if found_spider:
                found_spider = found_spider["class_name"]
            self.assertEqual(spider_class, found_spider)

    def test_all_spiders_have_unique_guid(self):
        spiders = MechanicalNews.get_all_spiders()
        for spider in spiders:
            self.assertNotEqual(
                spider["spider_guid"],
                "057d97fc-6a80-4c00-8c9f-7a8bc681b592")


if __name__ == '__main__':
    unittest.main()
