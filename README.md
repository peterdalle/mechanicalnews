# Mechanical News

Mechanical News is a Python web server application that crawls and saves news articles for research purposes.

- Automatically download and extract information from news articles
- Save structured information into a searchable database
- Get structured news data through an API client library
- Extend with your own news sources and collect custom information

Researchers can use Mechanical News with a client library of their favorite programming language, and thereby minimize the distance from data collection to both data analysis and machine learning.

An R client library for the Mechanical News API is being developed. An equivalent for Python is planned as well.

This project is under development at the [Department of Journalism, Media and Communication (JMG), University of Gothenburg](https://jmg.gu.se/english).

## Requirements

- Python 3+
- Windows, Linux or Mac OS

Mechanical News relies on [Scrapy](https://scrapy.org/) for web scraping.

## Install

```
pip install https://github.com/peterdalle/mechanicalnews
```

Note: This is a development version. The install may fail.

## Documentation

See [documentation wiki](https://github.com/peterdalle/mechanicalnews/wiki).

## Contribute

Read [how to contribute to the software](CONTRIBUTE.md).

## Support

- Report issues or problems by [submitting a new issue](https://github.com/peterdalle/mechanicalnews/issues/new)
- Read how to [get further support](SUPPORT.md)

## Todo

- [x] Application design
- [ ] Build scraper with headless browser that access HTML DOM
- [ ] Build one scraper per news site
- [ ] Build scheduler and que system
- [ ] Add user handling with API keys
- [ ] Add automatic error handling, with e-mail alerts
- [ ] Run unit tests
- [ ] Build R client library
- [ ] Validate method against existing data sources
- [ ] Build Python client library
- [ ] Build web client

## History

- 2019-02-13 Programming started
- 2019-02-08 Design implementation
- 2018-10-22 Design idea started

## License

[GNU General Public License v3.0](LICENSE)