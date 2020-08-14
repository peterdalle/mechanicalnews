# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the utils module.

Tested classes
--------------
- TextUtils
- DateUtils
- FileUtils
- WebUtils

Don't care about testing PrettyPrint class, which isn't particularly important.
"""
import unittest
from datetime import datetime
from utils import TextUtils, FileUtils, DateUtils, WebUtils


class RunTest_TextUtils(unittest.TestCase):

    def setUp(self):
        # Swedish = sv:
        self.text_sv = """Detta är en svensk text och kan du läsa det här så
            grattis till dig. Visst är det kul med lite svenska bland all
            jävla engelska? Ja, det tycker jag också. Tack och hej. Kom ihåg
            att rösta på Robotpartiet eller Satanistiskt initiativ om du vill
            ha ond bråd död i samhället!
            """
        # English = en:
        self.text_en = """And here we have some enligsh text that hopefully
            should be detected as such even if we havve some tyhpos here.
            """

    def test_is_number(self):
        self.assertEqual(TextUtils.is_number(0), True)
        self.assertEqual(TextUtils.is_number(141), True)
        self.assertEqual(TextUtils.is_number(-141), True)
        self.assertEqual(TextUtils.is_number(3455), True)
        self.assertEqual(TextUtils.is_number(100_000_000), True)
        self.assertEqual(TextUtils.is_number("0"), True)
        self.assertEqual(TextUtils.is_number("452"), True)
        self.assertEqual(TextUtils.is_number("No text"), False)
        self.assertEqual(TextUtils.is_number(TextUtils()), False)

    def test_count_words(self):
        self.assertEqual(TextUtils.count_words(self.text_sv), 52)
        self.assertEqual(TextUtils.count_words(self.text_en), 21)

    def test_detect_language(self):
        self.assertEqual(TextUtils.detect_language(self.text_sv), "sv")
        self.assertEqual(TextUtils.detect_language(self.text_en), "en")
        self.assertEqual(TextUtils.detect_language("No"), "")
        self.assertEqual(TextUtils.detect_language("No", fallback="en"), "en")

    def test_strip_html_tags(self):
        before = "<html><body><p>This is a text</p></body></html>"
        after = "\n\nThis is a text\n\n"
        self.assertEqual(TextUtils.strip_html_tags(html=before), after)

        before = "<html><body>Yet another broken<br>text</body></html>"
        after = "Yet another broken\n\ntext"
        self.assertEqual(TextUtils.strip_html_tags(html=before), after)

    def test_remove_tags_and_content(self):
        before = "<html><body><p>This is a <b>bold</b> text <script>without scripts</script></p></body></html>"
        after = "<html><body><p>This is a <b>bold</b> text </p></body></html>"
        self.assertEqual(TextUtils.remove_tag_and_content(html=before, tag="script"), after)

        before = "<html><body>We should not tolerate inline <style text='text/css'>* {color:red}</style></body></html>"
        after = "<html><body>We should not tolerate inline </body></html>"
        self.assertEqual(TextUtils.remove_tag_and_content(html=before, tag="style"), after)

    def test_remove_white_space(self):
        before = "This is    perhaps best understood  as a removal of   shite."
        after = "This is perhaps best understood as a removal of shite."
        self.assertEqual(TextUtils.remove_white_space(before), after)

        before = "This is    perhaps best understood\n  as a removal of   shite."
        after = "This is perhaps best understood\n\nas a removal of shite."
        self.assertEqual(TextUtils.remove_white_space(before), after)

    def test_remove_white_space_from_list(self):
        before = ["Hello World", "\n", " This is a new", " "]

        after = ["Hello World", "", "This is a new", ""]
        self.assertEqual(TextUtils.remove_white_space_from_list(lst=before,
                         remove_empty_str=False), after)

        after = ["Hello World", "This is a new"]
        self.assertEqual(TextUtils.remove_white_space_from_list(lst=before,
                         remove_empty_str=True), after)

    def test_convert_list_to_string(self):
        before = ["Hello World", "\n", " This is a new", " ", "line."]

        after = "Hello World\nThis is a new\nline."
        self.assertEqual(TextUtils.convert_list_to_string(
                         char_list=before, strip=True), after)

        after = "Hello World This is a new line."
        self.assertEqual(TextUtils.convert_list_to_string(
                         char_list=before, strip=True, sep=" "), after)

        after = "Hello World, \n,  This is a new,  , line."
        self.assertEqual(TextUtils.convert_list_to_string(
                         char_list=before, strip=False, sep=", "), after)

    def test_md5_hash(self):
        self.assertEqual(TextUtils.md5_hash(self.text_sv),
                         "a8e169c715aaba3a32fa57be2f2b58ee")
        self.assertEqual(TextUtils.md5_hash(self.text_en),
                         "be37963c477c0b37d9d4366b3b2cbba6")
        self.assertEqual(TextUtils.md5_hash(None), "")
        self.assertEqual(TextUtils.md5_hash(""), "")
        self.assertRaises(AttributeError, TextUtils.md5_hash, text=400000)

    def test_sanitize_str(self):
        before = "This dirty string should be left untouched."
        after = "This dirty string should be left untouched."
        self.assertEqual(TextUtils.sanitize_str(before), after)

        before = "This dirty string\nshould be left untouched."
        after = "This dirty string\nshould be left untouched."
        self.assertEqual(TextUtils.sanitize_str(before), after)

        before = "This dirty string\nshould be clean afterwards."
        after = "This dirty string should be clean afterwards."
        self.assertEqual(TextUtils.sanitize_str(before,
                                                keep_newlines=False), after)

        before = "This dirty string\nshould be clean afterwards."
        after = "This dirty string-should be clean afterwards."
        self.assertEqual(TextUtils.sanitize_str(before,
                                                keep_newlines=False,
                                                replace_newlines="-"), after)

        before = ""
        after = "Use default"
        self.assertEqual(TextUtils.sanitize_str(before,
                                                keep_newlines=False,
                                                replace_newlines="-",
                                                default="Use default"), after)

    def test_sanitize_int(self):
        self.assertEqual(TextUtils.sanitize_int(0), 0)
        self.assertEqual(TextUtils.sanitize_int(-1), -1)
        self.assertEqual(TextUtils.sanitize_int(1), 1)
        self.assertEqual(TextUtils.sanitize_int(2621), 2621)
        self.assertEqual(TextUtils.sanitize_int("1"), None)
        self.assertEqual(TextUtils.sanitize_int("1", default=0), 0)
        self.assertEqual(TextUtils.sanitize_int(None, default=0), 0)


class RunTest_FileUtils(unittest.TestCase):

    def test_format_bytes(self):
        self.assertEqual(FileUtils.format_bytes(None), "0 bytes")
        self.assertEqual(FileUtils.format_bytes(0), "0 bytes")
        self.assertEqual(FileUtils.format_bytes(1023), "1023 bytes")
        self.assertEqual(FileUtils.format_bytes(1024**1), "1 KB")
        self.assertEqual(FileUtils.format_bytes(1024**2), "1 MB")
        self.assertEqual(FileUtils.format_bytes(1024**3), "1 GB")
        self.assertEqual(FileUtils.format_bytes(1024**4), "1 TB")
        self.assertEqual(FileUtils.format_bytes(1024**5), "1 PB")
        self.assertEqual(FileUtils.format_bytes(1024**6), "1 EB")
        self.assertEqual(FileUtils.format_bytes(1024**7), "1 ZB")
        self.assertEqual(FileUtils.format_bytes(1024**8), "1 YB")
        self.assertEqual(FileUtils.format_bytes(6359834), "6 MB")
        self.assertEqual(FileUtils.format_bytes(6359834, decimals=1), "6.1 MB")
        self.assertEqual(FileUtils.format_bytes(6359834, decimals=1,
                                                dec_sign=","), "6,1 MB")


class RunTest_DateUtils(unittest.TestCase):

    def test_set_iso_date(self):
        dt = datetime.now()
        self.assertEqual(DateUtils.set_iso_date(dt, iso_date=False), dt)

        before = datetime(2020, 5, 18, 12, 27, 42, 359942)
        after = "2020-05-18T12:27:42.359942"
        self.assertEqual(DateUtils.set_iso_date(before, iso_date=True), after)

        before = datetime(2020, 5, 18, 12, 27, 42, 0)
        after = "2020-05-18T12:27:42"
        self.assertEqual(DateUtils.set_iso_date(before, iso_date=True), after)


class RunTest_WebUtils(unittest.TestCase):

    def test_get_domain_name(self):
        with_subdomains = [
            ("https://www.bbc.com/news/business-52273988", "www.bbc.com"),
            ("https://www.BBC.com/news/business-52273988", "www.BBC.com"),
            ("https://twitter.com/home", "twitter.com"),
            ("https://sverigesradio.se/sida/avsnitt/1482239?programid=406",
             "sverigesradio.se"),
            ("http://localhost", "localhost"),
            ("mailto:hello@world.com", "world.com"),
            ("Strange behavior but this works",
             "Strange behavior but this works"),
            (None, None),
        ]
        for url, true_domain in with_subdomains:
            test_domain = WebUtils.get_domain_name(url)
            self.assertEqual(test_domain, true_domain)

        without_subdomains = [
            ("https://www.bbc.com/news/business-52273988", "bbc.com"),
            ("https://www.BBC.com/news/business-52273988", "BBC.com"),
            ("https://twitter.com/home", "twitter.com"),
            ("https://sverigesradio.se/sida/avsnitt/1482239?programid=406",
             "sverigesradio.se"),
            ("http://localhost", "localhost"),
            ("mailto:hello@world.com", "world.com"),
            ("Strange behavior but this works",
             "Strange behavior but this works"),
            (None, None),
        ]
        for url, true_domain in without_subdomains:
            test_domain = WebUtils.get_domain_name(url, include_subdomain=False)
            self.assertEqual(test_domain, true_domain)


if __name__ == '__main__':
    unittest.main()
