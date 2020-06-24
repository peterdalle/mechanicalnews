# -*- coding: utf-8 -*-
"""
Module for initialization of Mechanical News that is responsible for finding
spiders in the "spiders" directory, as well as running them.
"""
import sys
import os
import importlib
import pkgutil
import requests
import inspect
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from functools import lru_cache
import mechanicalnews.settings
from mechanicalnews.utils import WebUtils, PrettyPrint
from mechanicalnews.basespider import BaseArticleSpider

if sys.version_info[0] < 3:
    raise Exception("Mechanical News requires Python 3 or higher.")


class MechanicalNewsError(Exception):
    """General class for Mechanical News related errors."""
    pass


class MechanicalNews(object):
    """Start spiders and crawl URLs.

    This is the main high-level interface you should use."""

    @staticmethod
    def get_spider_directories() -> list:
        """Get list of directories where spiders are located.

        Returns
        -------
        list
            Returns a list of directory paths (strings). If no paths are found,
            an empty list is returned.
        """
        dirs = []
        path = os.path.dirname(os.path.abspath(__file__)) + "/spiders"
        dirs.append(path)
        for subdir, _, _ in os.walk(path):
            if subdir:
                dirs.append(subdir)
        return list(set(dirs))

    @staticmethod
    def register_spiders_module_dirs():
        """Append spider directories to system path.

        Make sure we can read in package modules from the spider directory and
        its subdirectories."""
        for directory in MechanicalNews.get_spider_directories():
            if directory != "__pycache__":
                sys.path.append(directory)

    @staticmethod
    @lru_cache(maxsize=32)
    def get_all_spiders() -> list:
        """Get a list of all spiders in the `spiders` directory.

        A spider must inherit the `BaseArticleSpider` class.

        Returns
        -------
        list
            Returns a list of dictionaries with information about each spider.
            If no spider is found, an empty list is returned.
        """
        spiders = []
        spider_dirs = MechanicalNews.get_spider_directories()
        for path, module_name, _ in pkgutil.iter_modules(spider_dirs):
            module = importlib.import_module(module_name)
            excluded_classes = [BaseArticleSpider.__name__]
            class_names = list(filter(lambda x: x not in [
                            excluded_classes] and not
                            x.startswith('__'), dir(module)))
            for class_name in set(class_names):
                spider_class = getattr(module, class_name)
                is_sub_class = inspect.isclass(spider_class) and issubclass(
                               spider_class, BaseArticleSpider)
                if is_sub_class and class_name not in excluded_classes:
                    spider = spider_class()
                    spiders.append({
                        "class": spider_class,
                        "class_name": class_name,
                        "spider_name": spider.name,
                        "spider_guid": spider.SPIDER_GUID,
                        "start_urls": spider.start_urls,
                        "allowed_domains": spider.allowed_domains,
                        "path": path.path,
                        "filename": module_name + ".py",
                        "last_updated": spider.LAST_UPDATED,
                        "use_splash": spider.USE_SPLASH,
                        })
        return spiders

    @staticmethod
    def get_spider_by_url(url: str) -> BaseArticleSpider:
        """Find a matching spider for a given URL.

        Parameters
        ----------
        url : str
            An URL you want to scrape.

        Returns
        -------
        BaseArticleSpider
            Returns a spider that can scrape the URL. Returns `None` if no
            matching spider is found.
        """
        for spider in MechanicalNews.get_all_spiders():
            match_urls = spider["start_urls"] + spider["allowed_domains"]
            if MechanicalNews.is_domain_match(url, match_urls):
                return spider
        return None

    @staticmethod
    def get_spider_by_name(spider_name: str) -> BaseArticleSpider:
        """Find a matching spider for a given spider name.

        The spider name is found in the `name` variable of each spider class.

        Parameters
        ----------
        spider_name : str
            The name of the spider you want to get.

        Returns
        -------
        BaseArticleSpider
            Returns a spider. Returns `None` if no matching spider is found.
        """
        if not spider_name:
            raise ValueError("Argument 'spider_name' cannot be empty.")
        for spider in MechanicalNews.get_all_spiders():
            if spider["spider_name"].lower() == spider_name.lower():
                return spider
        return None

    @staticmethod
    def print_spider_list(verbose=True):
        """Print a list of all spiders.

        Parameters
        ----------
        verbose : bool
            Whether or not to show extended information about each spider
            (e.g., update date, file, GUID).
        """
        spiders = MechanicalNews.get_all_spiders()
        rows = []
        if verbose:
            # Show a lot of information about spiders.
            headers = ["File", "Spider name", "Domain", "Updated"]
            for spider in spiders:
                rows.append([
                    spider["filename"],
                    spider["spider_name"],
                    spider["allowed_domains"][0],
                    spider["last_updated"],
                    ])
        else:
            # Show less information about spiders.
            headers = ["Spider name", "Domain(s)"]
            for spider in spiders:
                rows.append([
                    spider["spider_name"],
                    ", ".join(spider["allowed_domains"]),
                    ])
        PrettyPrint.print_columns(rows, headers)
        print()
        print("Total of {} spider(s)".format(len(spiders)))

    @staticmethod
    def print_settings(mask_passwords=True, debug=False):
        """Print Scrapy settings.

        Parameters
        ----------
        mask_passwords : bool
            Whether or not to mask password fields.
        debug : bool
            Whether or not to get debug settings.
        """
        settings = MechanicalNews.get_crawler_settings(debug=debug)
        for i, key in enumerate(settings.keys()):
            if key in ["FTP_PASSWORD", "MAIL_PASS", "TELNETCONSOLE_PASSWORD"]:
                print(key, ": ", ("*" * 30), " [Password masked]", sep="")
            else:
                print(key, ": ", settings.get(key), sep="")

    @staticmethod
    def is_domain_match(url: str, url_list: list) -> bool:
        """Whether or not the given domain from a URL match any of the
        listed domains.

        Note that the domains are matched (e.g., `example.com`), not the full
        URL (e.g., `https://www.example.com/`).

        Parameters
        ----------
        url : str
            A given URL you want to find.
        url_list : str
            A list of URLs you want to your URL to match.

        Returns
        -------
        bool
            Returns a `True` if `url` match any of the domains in `url_list`,
            otherwise `False`.
        """
        url = url.lower() if url else ""
        url = WebUtils.get_domain_name(url, include_subdomain=False)
        for current_url in url_list:
            current_url = current_url.lower() if current_url else ""
            current_url = WebUtils.get_domain_name(current_url,
                                                   include_subdomain=False)
            if current_url == url:
                return True
        return False

    @staticmethod
    def is_splash_running() -> bool:
        """Check whether or not Scrapy Splash Docker container is running.

        It simply calls the Splash HTTP endpoint to see if it responds.

        Returns
        -------
        bool
            Returns `True` is Splash is running, otherwise `False`.
        """
        status_code = -1
        try:
            response = requests.post(settings.SPLASH_URL + "run", json={
                "lua_source": "return 1",
                "url": "http://example.com/"
                })
            status_code = response.status_code
        except BaseException:
            pass
        if status_code == 200:
            return True
        return False

    @staticmethod
    def get_crawler_settings(debug=False) -> scrapy.settings.Settings:
        """Get default crawler settings for news article web sites.

        These settings are stored in the default Scrapy settings file
        `settings.py`.

        Parameters
        ----------
        debug : bool
            Whether or not to use debug settings.

        Returns
        -------
        scrapy.settings.Settings
            Returns Scrapy project settings.
        """
        settings = scrapy.settings.Settings(get_project_settings())
        if debug:
            settings["LOG_LEVEL"] = "DEBUG"
        return settings

    @staticmethod
    def run_spiders(spider_names=None, debug=False, ignore_errors=False):
        """Start and run the specified spiders. They will crawl simultaneously
        in parallel.

        Raises a `MechanicalNewsError` if spider is not found,
        or when Scrapy Splash is required but not running.

        Parameters
        ----------
        spider_names : list
            A list of spider names (strings). If `None`, all installed spiders
            will run and crawl simultaneously.
        debug : bool
            Whether or not to perform the crawling in debug mode. If `True`,
            the crawling will be done in debug mode, otherwise use `False`.
        ignore_errors : bool
            Whether or not to ignore errors before starting the crawl process,
            such as checks whether Splash is running.
        """
        if not spider_names:
            # Get all spiders.
            spiders = MechanicalNews.get_all_spiders()
        else:
            # Get spiders by name.
            spiders = []
            for name in spider_names:
                spider = MechanicalNews.get_spider_by_name(name)
                if spider:
                    spiders.append(spider)
                else:
                    raise MechanicalNewsError(
                            "Spider with name '{}' not found.".format(name))
        is_splash_running = MechanicalNews.is_splash_running()
        # Extract only references to the classes.
        spider_classes = []
        for spider in spiders:
            spider_classes.append(spider["class"])
            use_splash = spider["use_splash"]
            # Make sure Splash is running for spiders that need it.
            if use_splash and not is_splash_running and not ignore_errors:
                raise MechanicalNewsError(
                    ("Spider '{}' requires Splash, but it's not" +
                     " running. Please start Splash first, or use --force" +
                     " to ignore this error.").format(spider["spider_name"]))
        MechanicalNews._run_spiders_by_class(spiders=spider_classes,
                                             debug=debug)

    @staticmethod
    def _run_spiders_by_class(spiders, debug=False):
        """Internal method for starting and running specified spiders.
        They will crawl simultaneously.

        This method assumes that all input parameters are valid.

        Parameters
        ----------
        spider_names : list
            A list of spider classes that inherits `BaseArticleSpider`.
        debug : bool
            Whether or not to perform the crawling in debug mode. If `True`,
            the crawling will be done in debug mode, otherwise use `False`.
        """
        process = CrawlerProcess(
                settings=MechanicalNews.get_crawler_settings(debug))
        for spider in spiders:
            is_spider = inspect.isclass(spider)
            is_subclassed = issubclass(spider, BaseArticleSpider)
            if not (is_spider and is_subclassed):
                raise AttributeError(
                    "Spider {} must inherit BaseArticleSpider.".format(spider))
            crawler = process.create_crawler(spider)
            process.crawl(crawler)
            # process.crawl(spider)
        process.start()
        process.stop()

    @staticmethod
    def crawl_urls(urls: list, debug=False, ignore_errors=False):
        """Run corresponding spiders from a list of URLs.

        Parameters
        ----------
        urls : list
            A list of URLs (as strings) that you want to crawl and scrape.
        debug : bool
            Whether or not to use debug settings.
        ignore_errors : bool
            Whether or not to ignore errors before starting the crawl process,
            such as checks whether Splash is running.
        """
        if not urls:
            return
        urls_spiders = MechanicalNews.find_spiders(urls)
        if urls_spiders:
            for url, spider in urls_spiders:
                print("{} --> {}()".format(url, spider["class_name"]))
        raise NotImplementedError("Crawling by URL is not implemented yet.")
        # TODO: Finish this.
        # process = CrawlerProcess(
        #         settings = MechanicalNews.get_crawler_settings(debug))
        # process.crawl(spiders.aftonbladet.AftonbladetSpider,
        #             input='inputargument', start_urls = urls)
        # process.start()
        # process.stop()

    @staticmethod
    def find_spiders(urls: list) -> list:
        """Find corresponding spiders from a list of URLs.

        Parameters
        ----------
        spider_names : list
            A list of spider classes that inherits `BaseArticleSpider`.
        debug : bool
            Whether or not to perform the crawling in debug mode. If `True`,
            the crawling will be done in debug mode, otherwise use `False`.

        Returns
        -------
        list
            Returns a list with tuples. The tuple contain URL (`str`) and
            spider class (`BaseArticleClass`). If no spider is found, an
            empty list is returned.
        """
        if not urls:
            return []
        url_spider_map = []
        for url in urls:
            spider = MechanicalNews.get_spider_by_url(url)
            if spider:
                url_spider_map.append((url, spider))
        return url_spider_map

    @staticmethod
    def check_spiders_for_errors() -> int:
        """Check spiders for errors and incorrect implementations.

        This method is helpful when developing spiders and to make sure spiders
        inherit the correct methods, and correct values are set.

        - Raises `ValueError` for incorrect values.
        - Raises `AttributeError` for missing methods.

        Returns
        -------
        int
            Returns the number of spiders checked.
        """
        # Note: O(n^2) comparisons, which should be OK in these scenarios.
        spiders = MechanicalNews.get_all_spiders()
        for spider in spiders:
            print("Checking {}...".format(spider["spider_name"]))
            for compare in spiders:
                # Unique GUID from basespider.
                if spider["spider_guid"] == BaseArticleSpider.SPIDER_GUID:
                    raise ValueError(
                        ("{} cannot have same GUID as" +
                         "BaseArticleSpider().").format(spider["class_name"]))
                # Unique GUID across spiders.
                same_guid = spider["spider_guid"] == compare["spider_guid"]
                same_name = spider["spider_name"] == compare["spider_name"]
                same_file = spider["filename"] == compare["filename"]
                if same_guid and not same_file:
                    raise ValueError(
                        ("{}() has the same GUID as {}()." +
                         " They must have unique GUID's.").format(
                         spider["class_name"], compare["class_name"]))
                # Unique name.
                if same_name and not same_file:
                    raise ValueError(
                        ("{}() has the same name as {}(): {}." +
                         " They should have unique names.").format(
                         spider["class_name"], compare["class_name"],
                         compare["spider_name"]))
                # If USE_SPLASH is set, get_lua_script() must also be set.
                class_ = spider["class"]
                if class_.USE_SPLASH:
                    if not hasattr(class_, "get_lua_script"):
                        raise AttributeError(
                               ("{}() has USE_SPLASH set to True," +
                                " but get_lua_script() is missing.").format(
                                spider["class_name"]))
        return len(spiders)


# Make sure spiders can be located in the "spiders" directory at init.
MechanicalNews.register_spiders_module_dirs()
