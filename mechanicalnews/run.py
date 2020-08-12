# -*- coding: utf-8 -*-
"""
Module for the main command line interface (CLI) that starts crawling with
all spiders or just some specific spiders.
"""
from mechanicalnews.__init__ import MechanicalNews, MechanicalNewsError
import sys
import argparse

__version__ = "0.1.0"
__author__ = "Peter M. Dahlgren"
__copyright__ = "(C) Peter M. Dahlgren"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        epilog="",
        description="List, run and check Mechanical News web spiders.")
    parser.add_argument(
        "--list", dest="list_spiders", action="store_true", required=False,
        help="show list of spiders and info about them")
    parser.add_argument(
        "--crawl", dest="spider", nargs="*", required=False,
        help="run specific spiders (leave empty to run all)")
    parser.add_argument(
        "--domain", dest="domain", nargs="+",
        help="crawl specific domain(s)")
    parser.add_argument(
        "--url", dest="url", nargs="+",
        help="crawl specific URL(s)")
    parser.add_argument(
        "--check", dest="check_spiders", action="store_true",
        required=False, help="check all spiders for errors")
    parser.add_argument(
        "--debug", dest="debug_mode", action="store_true", required=False,
        help="use debug mode (requires --crawl, --url or --settings)")
    parser.add_argument(
        "--settings", dest="info", action="store_true", default=False,
        required=False, help="show Scrapy settings")
    parser.add_argument(
        "--splash", dest="splash", action="store_true",
        help="show whether Scrapy Splash is running")
    parser.add_argument(
        "--force", dest="force", action="store_true",
        help="ignore errors before starting crawling (requires --crawl)")
    parser.add_argument(
        "--version", dest="version", action="store_true", default=False,
        required=False, help="show version")
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.list_spiders:
            MechanicalNews.print_spider_list()
        elif args.check_spiders:
            try:
                spider_count = MechanicalNews.check_spiders_for_errors()
                print("No errors found in {} spider(s).".format(spider_count))
            except ValueError as err:
                print("Error found in spider: {}".format(err))
        elif args.domain:
            print("Crawling {} domain(s)...".format(len(args.domain)))
            try:
                MechanicalNews.crawl_domains(domains=args.domain,
                                             debug=args.debug_mode,
                                             ignore_errors=args.force)
            except MechanicalNewsError as err:
                print("Error:", err)
        elif args.spider or args.spider == []:
            if len(args.spider) == 0:
                print("Starting all spiders...")
            else:
                print("Starting {0} spider(s)...".format(len(args.spider)))
            try:
                MechanicalNews.run_spiders(spider_names=args.spider,
                                           debug=args.debug_mode,
                                           ignore_errors=args.force)
            except MechanicalNewsError as err:
                print("Error:", err)
        elif args.url:
            print("Crawling {} URL(s)...".format(len(args.url)))
            try:
                MechanicalNews.crawl_urls(urls=args.url,
                                          debug=args.debug_mode,
                                          ignore_errors=args.force)
            except MechanicalNewsError as err:
                print("Error:", err)
        elif args.splash:
            settings = MechanicalNews.get_crawler_settings()
            if MechanicalNews.is_splash_running():
                print("Scrapy Splash found at {}".format(
                                                       settings["SPLASH_URL"]))
            else:
                print("Can't find Scrapy Splash at {}".format(
                                                       settings["SPLASH_URL"]))
        elif args.info:
            MechanicalNews.print_settings(debug=args.debug_mode)
        elif args.version:
            print("{} {} {}".format("Mechanical News",
                                    __version__, __copyright__))
        else:
            parser.print_help()
    else:
        parser.print_help()
