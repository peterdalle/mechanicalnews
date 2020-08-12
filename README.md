# Mechanical News

Mechanical News is a web server framework built on top of [Scrapy](https://scrapy.org/) that scrapes and saves online news articles (full text) to a database for social science research.

The articles in the database are then accessible via a RESTful API built with [Flask](http://flask.pocoo.org/), easily retrieved with a R library or Python package in [tidy data](https://en.wikipedia.org/wiki/Tidy_data) format.

## Features

- Extract information from news articles using an existing scraper (or build your own)
- Store full text news articles to a database
- Two modes:
   - Scrape articles from news sites continuously (e.g., every day)
   - Scrape articles from specific URLs
- Retrieve articles via an API using an API key (for students or collaborators)

## Extracted information from news articles

News content

- headline
- article lead
- article body text
- links in article body text
- main image

Metadata

- author(s)
- date of publication
- date of modification
- news section (e.g., Economy, Sports, Tech)
- tags
- categories
- language
- content type (e.g., text, video, sound)
- news genre (e.g., news, opinion, entertainment)
- paywall
- optional:
   - HTTP response headers
   - metadata tags (e.g., OpenGraph, microformats)
   - when the article was present on the frontpage

## Architecture

<img src="architecture.png" width="70%" alt="Overview of the architecture of Mechanical News">

## Install

```
Not yet available
```

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

## Quick start

Scrape all news articles from the news frontpages using all available spiders in the [`spiders` directory](mechanicalnews/spiders/README.md) by running this from the project path:

```bash 
$ python run.py --crawl
```

Scrape all news articles from the frontpage of a specific site (`aftonbladet` is the name of the spider):

```bash 
$ python run.py --crawl aftonbladet
```

Scrape the news article content from a specific URL:

```bash 
$ python run.py --url https://www.aftonbladet.se/kultur/a/BRoWvQ/sa-kan-putin-bli-kvar-vid-makten
```

## Available spiders

Show all spiders you have installed:

```bash
$ python run.py --list
```

This will list all spiders in your [`spiders` directory](mechanicalnews/spiders/README.md). A spider is responsible for scraping a news site.

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
