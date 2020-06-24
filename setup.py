# -*- coding: utf-8 -*-
"""
Module for the setup of Mechanical News.
"""
import setuptools
import os

with open("README.md", "r", encoding="utf8") as file:
     long_description = file.read()

setuptools.setup(
    name = "mechanicalnews",
    version = "0.0.X",
    author = "Peter M. Dahlgren",
    py_modules = ["mechanicalnews"],
    author_email = "peterdalle@gmail.com",
    description = "Open source web crawler and news article extractor for researchers.",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    keywords = "crawler crawling scraper scraping spider extractor news articles information retrieval",
    url = "https://github.com/peterdalle/mechanicalnews",
    download_url = "https://github.com/peterdalle/mechanicalnews",
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires = ">=3.6",
    install_requires = [
        "dateparser>=0.7.1",
        "extruct>=0.7.3",
        "flask_restful>=0.3.7",
        "Flask>=1.0.2",
        "langdetect>=1.0.7",
        "mysql-connector-python>=2.1.6",
        "pillow>=5.0.0",
        "scrapy-selenium>=0.0.7",
        "scrapy-splash>=0.7.2",
        "scrapy>=1.6.0",
        "tldextract>=2.2.1",
    ],
    extras_require = {
        ':sys_platform == "win32"': [
            'pywin32>=220'
        ]
    },
)
