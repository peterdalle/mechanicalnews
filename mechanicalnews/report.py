# -*- coding: utf-8 -*-
"""
Module for generating reports about the Mechanical News status, such as
statistics about the crawling, database size, number of articles collected etc.
Can be runned as a command line interface (CLI) or as module you can import.
Most of the summary statistics are fetched from the stats module.
"""
import sys
import argparse
import smtplib
import datetime
from mechanicalnews.core import ArticleFilter, ArticleManager
from mechanicalnews.stats import SummaryStats
from mechanicalnews.settings import AppConfig
from mechanicalnews.utils import TextUtils, FileUtils, WebUtils, PrettyPrint
from mechanicalnews.items import LogAction


class Reports():
    """Show various resports about the crawling and collected articles."""

    @staticmethod
    def print_database_size(projected_size=False):
        """Print total database size, and size of each table."""
        print("Database size:")
        ss = SummaryStats()
        d = ss.get_database_size()
        all_tables = ss.get_database_size(all_tables=True)
        # Total.
        print("  data: {}".format(
            FileUtils.format_bytes(d["database_data_size"])))
        print("  index: {}".format(
            FileUtils.format_bytes(d["database_index_size"])))
        print("  total: {}".format(
            FileUtils.format_bytes(d["database_total_size"])))
        print()
        print("Table size:")
        for table in all_tables:
            print("  {}: {}".format(
                table["table_name"],
                FileUtils.format_bytes(table["total_size"])))
        # Projected total size.
        if projected_size:
            print()
            print("Predicted size:")
            s = ss.get_summary(iso_date=False)
            num_urls = s["num_urls"]
            total_size = d["database_total_size"]
            future_size = (total_size / num_urls) * 1000000
            if num_urls > 0 and total_size > 0:
                print("  {} with 1 million URLs".format(
                    FileUtils.format_bytes(future_size)))

    @staticmethod
    def print_source_counts():
        print("Sources:")
        ss = SummaryStats()
        s = ss.get_source_counts()
        lines = []
        for pair in s:
            lines.append([pair["source"], str(pair["articles"])])
        PrettyPrint.print_columns(lines, headers=["Sources", "Saved articles"],
                                  indent=2)

    @staticmethod
    def print_article_counts():
        print("Article count:")
        ss = SummaryStats()
        s = ss.get_summary()
        map_explanations = {
            "num_log": "Logs",
            "num_errors": "Errors",
            "num_sources": "sources",
            "num_frontpage_articles": "Frontpage articles",
            "num_urls": "URLs",
            "num_images": "Images",
            "num_articles": "Articles",
            "num_article_versions": "Article versions",
            "num_article_links": "Article links",
            "num_article_metadata": "Article metadata",
            "num_article_images": "Article images",
            "num_article_headers": "Article headers",
            "num_unique_pages": "Unique pages",
            "earliest_published_article": "Earliest published article",
            "latest_published_article": "Latest published article",
        }
        PrettyPrint.print_stars_and_bars(s, map_explanations)

    @staticmethod
    def print_log(limit=7):
        """Print the latest entries from the log."""
        print("Log:")
        ss = SummaryStats()
        rows = []
        for row in ss.get_log(limit):
            rows.append((
                Reports._shorten_date(row["added"]),
                str(LogAction(row["action_id"])),
                "#" + str(row["article_id"]) if row["article_id"] else "",
                str(row["latency"]) if row["latency"] else ""
            ))
        PrettyPrint.print_columns(rows, headers=["Date", "Action",
                                  "Article", "Latency (ms)"], indent=2)

    @staticmethod
    def print_article(id_string):
        """Print specific article by aribtrary identifier of article
        (e.g., ID of article, URL of article)."""
        if not id_string:
            print("No ID found.")
            return
        # Try to interpret ID string.
        a = ArticleManager()
        article = None
        id_int = None

        try:
            id_int = int(id_string)
        except ValueError:
            pass
        if id_int and id_int > 0:
            print("Interpreted as article ID")
            article = a.get_article_by_id(id_int)
        elif type(id_string) == str:
            if id_string.startswith(
                   "http://") or id_string.startswith("https://"):
                print("Interpreted as article URL")
                article_id = a.get_article_id_by_url(id_string)
                if article_id:
                    article = a.get_article_by_id(article_id)
            else:
                print("Couldn't interpret input")
                return
        else:
            print("Couldn't interpret input")
            return
        if article:
            PrettyPrint.print_json(article.get_json(include_lists=False))
        else:
            print("Article not found.")

    @staticmethod
    def print_latest_articles(limit=7, query=None):
        """Print list of latest articles."""
        print("Latest articles:")
        filters = ArticleFilter()
        filters.limit = limit
        if query:
            filters.query = query
        rows = []
        a = ArticleManager()
        for article in a.get_articles(filters):
            a = article.get_json(iso_date=False)
            rows.append((
                "#" + str(a["id"]),
                Reports._shorten_date(a["added"]),
                WebUtils.get_domain_name(a["domain"],
                                         include_subdomain=False),
                Reports._sanitize_text(a["title"]),
                Reports._shorten_date(a["published"])))
        PrettyPrint.print_columns(rows, headers=["ID", "Added", "Domain",
                                  "Title", "Published"], indent=2)

    @staticmethod
    def print_spider_crawls(days_back=7):
        print("Crawls:")
        rows = []
        ss = SummaryStats()
        for crawl in ss.get_crawled_articles_per_day(days_back):
            rows.append((crawl["day"], str(crawl["articles"])))
        PrettyPrint.print_columns(rows, headers=["Day", "Saved pages"],
                                  indent=2)

    @staticmethod
    def print_image_count():
        """Show number of downloaded image files and their disk size."""
        print("Image files:")
        directory = AppConfig.ROOT_IMAGES_DIRECTORY
        if not directory:
            print("  No image file directory set")
            return
        size, num_files = FileUtils.get_directory_size(directory)
        print("  {} images including thumbnails ({}) in {}".format(
            num_files, FileUtils.format_bytes(size), directory))

    @staticmethod
    def print_html_file_count():
        """Show number of HTML files and their disk size."""
        print("HTML files:")
        directory = AppConfig.HTML_FILES_DIRECTORY
        if not directory:
            print("  No HTML file directory set")
            return
        size, num_files = FileUtils.get_directory_size(directory)
        print("  {} HTML files ({}) in {}".format(
            num_files, FileUtils.format_bytes(size), directory))

    @staticmethod
    def _sanitize_text(text, limit=50):
        """Sanitize text string & remove things that fuck up printing
        on screen."""
        if not text:
            return ""
        text = PrettyPrint.fubar_unicode(text=text, limit=limit)
        text = text.replace("\n", " ")
        return text

    @staticmethod
    def _shorten_date(date: datetime.datetime, resolution="minute") -> str:
        """Shorten date to a more human-friendly format.

        E.g., `2020-01-01 15:32:20` becomes `2020-01-01 15:32`.

        Change the `resolution` to further strip parts of the date."""
        if resolution not in ["minute", "date", "month", "year"]:
            raise ValueError(
                "Argument 'resolution' must be " +
                "'minute', 'date', 'month', or 'year'.")
        if not date:
            return ""
        if resolution.lower() == "minute":
            return "{0:%Y-%m-%d %H:%M}".format(date)
        elif resolution.lower() == "date":
            return "{0:%Y-%m-%d}".format(date)
        elif resolution.lower() == "month":
            return "{0:%Y-%m}".format(date)
        elif resolution.lower() == "year":
            return "{0:%Y}".format(date)
        return ""


class EmailReport():
    """Create and send email reports with summary statistics about
    the crawling."""

    def __init__(self, from_email, from_name, to_email, to_name="",
                 smtp_host="localhost", smtp_port=587,
                 content_type="text/plain"):
        """Constructor.

        Parameters
        ----------
        from_email : str
            Sender email address.
        from_name : str
            Sender name.
        to_email : str
            Recipient email address.
        to_name : str
            Recipient name.
        smtp_host : str
            SMTP host.
        smtp_port : int
            SMTP port.
        content_type : str
            Content type of the email message, e.g. `text/plain` or
            `text/html`.
        """
        self.from_name = from_name
        self.from_email = from_email
        self.to_name = to_name
        self.to_email = to_email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.content_type = content_type

    @classmethod
    def from_config(cls):
        """Constructor."""
        return cls(from_name=AppConfig.EMAIL_FROM_NAME,
                   from_email=AppConfig.EMAIL_FROM_ADDRESS,
                   to_email=AppConfig.EMAIL_TO_ADDRESS,
                   smtp_host=AppConfig.EMAIL_SMTP_SERVER,
                   smtp_port=AppConfig.EMAIL_SMTP_PORT)

    def send_email_report(self):
        """Send email report with summary of crawling."""
        self.send_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        self.subject = "Crawling report {}".format(self.send_date)
        self.message_body = f"""From: {self.from_name} <{self.from_email}>
To: {self.to_name} <{self.to_email}>
MIME-Version: 1.0
Content-type: {self.content_type}
Subject: {self.subject}

{self.build_message()}
"""
        try:
            smtpObj = smtplib.SMTP(self.smtp_host, self.smtp_port)
            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.sendmail(self.from_email,
                             self.to_email,
                             self.message_body.encode("utf8"))
            smtpObj.quit()
        except BaseException as err:
            print(err)

    def build_message(self, days_back=7) -> str:
        """Build email report message."""
        message = """Email report of Mechanical News crawling progress.

Totals:

- {num_articles} articles
- {num_article_versions} versions
- {num_article_images} images
- {num_urls} URLs
- {num_frontpage_articles} frontpage articles

Log:

- {num_errors} errors
- {num_log} log entries

Crawling and missing values last {days_back} days:

{missing}
"""

        ss = SummaryStats()
        s = ss.get_summary()
        missing = ss.get_missing_values_by_day(days_back)
        missing = self.build_missing_values_message(missing)
        values = {
                    "num_articles": s["num_articles"],
                    "num_article_versions": s["num_article_versions"],
                    "num_article_images": s["num_article_images"],
                    "num_urls": s["num_urls"],
                    "num_frontpage_articles": s["num_frontpage_articles"],
                    "num_errors": s["num_errors"],
                    "num_log": s["num_log"],
                    "days_back": days_back,
                    "missing": missing,
                }
        return self._replace_key_values(message, values)

    def _replace_key_values(self, text: str, values: dict) -> str:
        """Replace a bunch of values in a text string.

        Parameters
        ----------
        text : str
            Text string with `{variable}` names to replace. The variable
            name is the same as the key name of the `values` dict.
        values : dict
            Dictionary with the keys as variable names and values to replace.

        Returns
        -------
        str
            Returns a text string with the replaced values.
        """
        if not text:
            return ""
        if values and not type(values) == dict:
            raise ValueError("Parameter 'values' must be a dict.")
        for key in values.keys():
            text = text.replace("{" + key + "}", str(values[key]))
        return text

    def build_missing_values_message(self, missing_data) -> str:
        """Build collected articles and missing values message."""
        message = "Day".ljust(12)
        message += "Missing pub*".rjust(12)
        message += "Collected".rjust(12)
        message += "% missing".rjust(12)
        message += "\n" + ("-" * 55) + "\n"
        miss = 0
        found = 0
        for na in missing_data:
            if int(na["missing"]) == 1:
                # Get missing articles.
                message += str(na["added"]).ljust(12)
                message += str(na["articles"]).rjust(12)
                miss = int(na["articles"])
                for not_na in missing_data:
                    is_same_date = not_na["added"] == na["added"]
                    is_missing = int(not_na["missing"]) == 0
                    if is_missing and is_same_date:
                        # Get total articles.
                        found = int(not_na["articles"]) + miss
                        message += str(format(found, ",d")).rjust(12)
                # Percent missing.
                percent = int((miss / found) * 100)
                message += f"{percent}%".rjust(12)
                message += "\n"
        message += "\n\n*Missing article publish date"
        return message


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Shows information about collected Mechanical News" +
                    " articles.")
    parser.add_argument("--all", dest="all", action="store_true",
                        required=False, help="show all information")
    parser.add_argument("--articles", dest="articles", action="store_true",
                        required=False, help="show info about articles")
    parser.add_argument("--sources", dest="sources", action="store_true",
                        required=False, help="show info about sources")
    parser.add_argument("--size", dest="metadata", action="store_true",
                        required=False,
                        help="show info about database and file size")
    parser.add_argument("--history", dest="history", action="store_true",
                        required=False, help="show crawls, logged info")
    parser.add_argument("--search", metavar="query", dest="search", type=str,
                        default="", required=False,
                        help="search by article ID/URL (requires --articles)")
    parser.add_argument("--n", metavar="limit", dest="n", type=int,
                        default=7, required=False,
                        help="max number of results to return")
    parser.add_argument("--sendmail", dest="send_email", action="store_true",
                        required=False, help="send email report")
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if args.all:
            Reports.print_database_size()
            print()
            Reports.print_article_counts()
            print()
            Reports.print_source_counts()
            print()
            Reports.print_latest_articles(limit=args.n)
            print()
            Reports.print_log(limit=args.n)
            print()
            Reports.print_spider_crawls(days_back=args.n)
            print()
            Reports.print_image_count()
            print()
            Reports.print_html_file_count()
        elif args.articles:
            if TextUtils.is_number(args.search):
                # Show specific article.
                Reports.print_article(id_string=args.search)
            else:
                # Show list of articles.
                Reports.print_latest_articles(limit=args.n, query=args.search)
                print()
                Reports.print_article_counts()
        elif args.sources:
            Reports.print_source_counts()
        elif args.metadata:
            Reports.print_database_size()
            print()
            Reports.print_image_count()
            print()
            Reports.print_html_file_count()
        elif args.history:
            Reports.print_spider_crawls(days_back=args.n)
            print()
            Reports.print_log(limit=args.n)
        elif args.send_email:
            if AppConfig.EMAIL_ENABLE:
                report = EmailReport.from_config()
                report.send_email_report()
            else:
                print("Cannot send email, email is turned off." +
                      " Change behavior in settings.py" +
                      " (AppConfig.EMAIL_ENABLE).")
        else:
            parser.print_help()
    else:
        parser.print_help()
