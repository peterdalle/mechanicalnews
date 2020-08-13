# -*- coding: utf-8 -*-
"""
Module that handles static files (e.g., images, HTML files).
"""
import os
from mechanicalnews.settings import AppConfig


class StaticFiles():
    """Serve static files and build URLs and directories."""

    @staticmethod
    def get_html_filename(article_id: int) -> str:
        return str(article_id) + ".html"

    @staticmethod
    def get_html_full_filename(article_id: int) -> str:
        return AppConfig.HTML_FILES_DIRECTORY + "/" + get_html_filename(article_id)

    @staticmethod
    def save_html_file(html: str, article_id: int):
        """Save HTML to a file.

        Parameters
        ----------
        content : str
            Content of the HTML file.
        article_id : int
            ID to an existing article.
        """
        if not html:
            return
        if not AppConfig.HTML_FILES_DIRECTORY:
            return
        with open(get_html_full_filename(article_id), "w", encoding="utf8") as file:
            file.write(html)

    @staticmethod
    def read_html_file(article_id) -> str:
        raise NotImplementedError()  # TODO
