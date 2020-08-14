# -*- coding: utf-8 -*-
"""
Module for database and file storage.
"""
import os
import mysql.connector
from mechanicalnews.settings import AppConfig


class MySqlDatabase():
    """Helper functions for database connection to MySQL, open and close.

    Example usage
    -------------

    ```python
    db = MySqlDatabase.from_settings()
    db.open()
    db.execute("INSERT INTO table VALUES(1, 2, 3)")
    version = db.get_scalar("SELECT field FROM table LIMIT 1")
    db.close()
    ```

    Context manager is also supported:

    ```python
    with MySqlDatabase.from_settings() as db:
        db.execute("INSERT INTO table VALUES(1, 2, 3)")
    ```
    """

    def __init__(self, username: str, password: str, database: str,
                 host="localhost", charset="utf8", auth_plugin=None):
        """Constructor.

        Parameters
        ----------
        username : str
            Username to database.
        password : str
            Password to database.
        database : str
            Name of the database.
        host : str
            Server host address to the database.
        charset : str
            Charset for the connection to the database.
        auth_plugin : str
            Authentication plugin to the database. Should be
            `mysql_native_password` or `None`.
        """
        self.cur = None
        self.conn = None
        self.username = username
        self.password = password
        self.database = database
        self.host = host
        self.charset = charset
        if auth_plugin not in ["mysql_native_password", None]:
            raise ValueError("Parameter 'auth_plugin' must be 'mysql_native_password' or None.")
        self.auth_plugin = auth_plugin

    def __repr__(self):
        """Text represention of object."""
        return "{}(database='{}', host='{}')".format(self.__class__.__name__, self.database, self.host)

    def __enter__(self):
        """Open database connection for context manager."""
        self.open()
        return self

    def __exit__(self, *args):
        """Close database connection for context manager."""
        self.close()

    def __del__(self):
        """Close database connection when destroying the instance."""
        self.close()

    @classmethod
    def from_settings(cls):
        """Create a new instance using the database settings from
        settings file."""
        return cls(database=AppConfig.MYSQL_DB,
                   username=AppConfig.MYSQL_USER,
                   password=AppConfig.MYSQL_PASS,
                   charset=AppConfig.MYSQL_CHARSET,
                   auth_plugin=AppConfig.MYSQL_AUTH_PLUGIN)

    @staticmethod
    def is_installed():
        """Checks whether database exists (i.e., is installed).

        Returns
        -------
        bool
            Returns True if database exists, otherwise False.
        """
        db = MySqlDatabase.from_settings()
        try:
            db.open()
            db.close()
            return True
        except mysql.connector.errors.ProgrammingError:
            pass
        db.close()
        return False

    def open(self):
        """Open database connection."""
        if not self.conn:
            self.conn = self.get_conn()
        if not self.cur:
            self.cur = self.get_cur()

    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
            self.cur = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_conn(self):
        return mysql.connector.connect(database=self.database,
                                       user=self.username,
                                       password=self.password,
                                       auth_plugin=self.auth_plugin,
                                       charset=self.charset)

    def get_cur(self):
        cur = self.conn.cursor(dictionary=True, buffered=True)
        cur.execute("SET NAMES 'utf8mb4';")
        cur.execute("SET CHARACTER SET utf8mb4;")
        return cur

    def execute(self, query: str, params=None):
        """Execute a SQL query that does not return any value.

        Parameteres
        -----------
        query : str
            Query to perform on the database (e.g., INSERT, UPDATE, ALTER).
        params : tuple
            Tuple of values.
        """
        self.cur.execute(operation=query, params=params)
        self.conn.commit()

    def get_rows(self, query: str, params=None) -> list:
        """Execute query and retrieve rows.

        This method is only suitable for small data since no iterator is used.

        Parameteres
        -----------
        query : str
            SELECT query to perform on the database.

        Returns
        -------
        list
            Returns a list of rows.
        """
        self.cur.execute(query, params=params)
        if self.cur:
            rows = []
            for row in self.cur:
                rows.append(row)
            return rows
        else:
            return None

    def get_scalar(self, query: str, params=None, field=None, default=None) -> object:
        """Get scalar value.

        Parameters
        ----------
        query : str
            SELECT query to perform on the database.
        field : str
            Name of the field to retrieve.
        default : object
            Default value to return if no value is found.

        Returns
        -------
        object
            Returns a scalar value.
        """
        self.cur.execute(query, params=params)
        if field:
            value = self.cur.fetchone()[field]
        else:
            # Figure out field name, assuming it's the first one.
            value = self.cur.fetchone()
            if type(value) == dict:
                for key in value.keys():
                    if value[key]:
                        return value[key]
        if value:
            return value
        return default


class StaticFiles():
    """Serve static files and build URL and directory paths."""

    @staticmethod
    def get_html_filename(article_id: int) -> str:
        return str(article_id) + ".html"

    @staticmethod
    def get_html_full_filename(article_id: int) -> str:
        return AppConfig.HTML_FILES_DIRECTORY + "/" + StaticFiles.get_html_filename(article_id)

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
        filename = StaticFiles.get_html_full_filename(article_id)
        if type(html) == bytes:
            html = html.decode("utf-8")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(html)
