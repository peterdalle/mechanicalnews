# -*- coding: utf-8 -*-
"""
Module for generating alerts about too many missing values.
"""
from mechanicalnews.stats import SummaryStats
from mechanicalnews.storage import MySqlDatabase


class Alert():
    """Show various resports."""

    @staticmethod
    def get_missing_values(self, days_back=7) -> dict:
        s = SummaryStats.get_summary()
        missing = SummaryStats.get_missing_values_by_day(days_back)
        missing = self.build_missing_values_message(missing)
        return {
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

    @staticmethod
    def build_missing_values_message(self, missing_data) -> str:
        """Build collected articles and missing values message."""
        miss = 0
        found = 0
        for na in missing_data:
            if int(na["missing"]) == 1:
                # Get missing articles.
                miss = int(na["articles"])
                for not_na in missing_data:
                    is_same_date = not_na["added"] == na["added"]
                    is_missing = int(not_na["missing"]) == 0
                    if is_missing and is_same_date:
                        # Get total articles.
                        found = int(not_na["articles"]) + miss
                # Percent missing.
                percent = int((miss / found) * 100)
        print(miss)
        print(found)
        print(percent)
        return ""


# missings = SummaryStats.get_missing_values_by_source(days_back=14)

# sources = [int(x["source_id"]) for x in missings]

# for source in sorted(sources):
#     for na in [x for x in missings if x["source_id"] == source]:
#         percent_missing = (na["missing"] / na["articles"]) * 100
#         print(na["source_id"], na["missing"], na["articles"], percent_missing)


# sql = """SELECT
# DATE(added) day,
# IF(`lead`, 0, 1) na_lead,
# IF(body, 0, 1) na_body,
# IF(published, 0, 1) na_published,
# COUNT(*) articles
# FROM articles
# WHERE (added BETWEEN DATE_ADD(NOW(), INTERVAL -{} DAY) AND NOW())
# GROUP BY DATE(added)""".format(days_back)
# with MySqlDatabase.from_settings() as db:
#     missings_per_day = db.get_rows(sql)

# for na in missings_per_day:
#     day = na["day"]
#     pct_na_lead = (na["na_lead"] / na["articles"]) * 100
#     pct_na_body = (na["na_body"] / na["articles"]) * 100
#     pct_na_publ = (na["na_published"] / na["articles"]) * 100
#     print(day, round(pct_na_lead), round(pct_na_body), round(pct_na_publ))


def get(days_back, field="published"):
    # Counting Missing Values
    # https://www.oreilly.com/library/view/mysql-cookbook/0596001452/ch13s05.html
    sql = f"""SELECT
    COUNT(*) AS 'n_total',
    COUNT({field}) AS 'n_nonmissing',
    COUNT(*) - COUNT({field}) AS 'n_missing',
    ((COUNT(*) - COUNT({field})) * 100) / COUNT(*) AS 'pct_missing'
    FROM articles
    WHERE (added BETWEEN DATE_ADD(NOW(), INTERVAL -{days_back} DAY) AND NOW())
    GROUP BY source_id
    """
    with MySqlDatabase.from_settings() as db:
        return {
            "field": field,
            "days_back": days_back,
            "data": db.get_rows(sql),
    }

print(get(days_back=14, field="published"))
