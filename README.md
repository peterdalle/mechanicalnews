# Mechanical News

Mechanical News is an application framework that scrapes and saves the full text of online news articles to a database for social science research purposes.

Mechanical News it built on top of [Scrapy](https://scrapy.org/) and [Flask](http://flask.pocoo.org/), which lets you write web scrapers that retrieve news articles (using Scrapy), store them in the database, and then connect to a RESTful API to retrieve the articles from the database (using Flask).

You run Mechanical News on your own server. The users (i.e., researchers) instead use an R library or Python package to access the articles in a [tidy data](https://en.wikipedia.org/wiki/Tidy_data) format directly from the API. The researcher doesn't need to know anything about how Mechanical News works.


## Features

- Build your own Scrapy scraper (or use an existing scraper from the library)
- Extract information from news articles
- Store full text news articles to a database
- Run in different modes:
   - Scrape articles from news sites continuously (e.g., every day)
   - Scrape articles from specific URLs

## Extracted information from news articles

News content

- headline
- article lead
- article body text
- links in article body text
- main image

Metadata

- authors
- date of publication
- date of modification
- news section (e.g., World, Sports, Tech)
- tags
- categories
- language
- type of page (e.g., text article, video, sound)
- news genre (e.g., news, sports, opinion, entertainment)
- whether the article is behind a paywall
- HTTP response headers
- metadata tags (e.g., OpenGraph, microformats)
- when the article was present on the frontpage

## Overview of the architecture

![Overview of the architecture of Mechanical News.](architecture.png)

## Install

*Not yet available*

<!--

Install the Mechanical News server application:
```
$ pip install git+https://github.com/peterdalle/mechanicalnews.git@release
```
-->

Requirements:

- Python 3.6+
- MySQL 5.6+
- Docker

Mechanical News have been tested on Windows 10, Red Hat 7.6, and Ubuntu 18.

## Quick start

Scrape all news articles from the news frontpages using all available spiders in the `/spiders` directory by running this from the project path:

```bash 
$ python run.py --crawl
```

Scrape all news articles from the frontpage of a specific site (`bbc` is the name of the spider):

```bash 
$ python run.py --crawl bbc
```

Scrape the news article content from a specific URL:

```bash 
$ python run.py --url https://www.bbc.com/XXX
```

## Available spiders

Show all spiders you have installed:

```bash
$ python run.py --list
```

This will list all spiders in your [`/spiders`](mechanicalnews/spiders/README.md) directory. A spider is responsible for scraping a news site.

## Documentation

See [documentation wiki](https://github.com/peterdalle/mechanicalnews/wiki).

## Contribute

Read [how to contribute to Mechanical News](CONTRIBUTE.md) by writing your own scrapers and share them.

## Support

- Report issues or problems by [submitting a new issue](https://github.com/peterdalle/mechanicalnews/issues/new)
- Read how to [get further support](SUPPORT.md)

## License

[GNU General Public License v3.0](LICENSE)

## Similar projects

- [newspaper](https://github.com/codelucas/newspaper) - library for automatic news article metadata extraction using heuristics. Mainly useful for English speaking content and when you don't want specific metadata.
- [news-please](https://github.com/fhamborg/news-please) - library and system for news article metadata extraction with database and search function, also built on Scrapy and newspaper. However, you cannot specify what information you want to extract.
- [Media Cloud](https://github.com/berkmancenter/mediacloud) - open data platform that allows researchers to answer quantitative questions about the content of online media. Roll your own server or use the cloud service. However, you cannot access full text due to copyright.
