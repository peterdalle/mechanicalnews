# -*- coding: utf-8 -*-
"""
Utils module for text transformations, printing to screen, and handling files.
"""
import datetime
import html.parser
import json
import langdetect
import hashlib
import os
import re
import tldextract
from bs4 import BeautifulSoup


class TextUtils():
    """Various text transformation and extraction utilities."""

    @staticmethod
    def is_number(value: object) -> bool:
        """Get whether or not the value is a number.

        Parameters
        ----------
        value : object
            A value that you want to check if it's a number.

        Returns
        -------
        bool
            Returns `True` if the value is a number, or `False` if it's not
            a number.
        """
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            pass
        try:
            import unicodedata
            unicodedata.numeric(value)
            return True
        except (TypeError, ValueError):
            pass
        return False

    @staticmethod
    def count_words(text: str) -> int:
        """Get number of words in a text string.

        Parameters
        ----------
        text : str
            A text string.

        Returns
        -------
        str
            Returns the number of words. Returns 0 if there are no words, or
            text is empty.
        """
        if text:
            regex = re.compile(r"\w+", re.MULTILINE)
            return len(regex.findall(text))
        return 0

    @staticmethod
    def detect_language(text: str, min_length=5) -> str:
        """Detect language of text string.

        Parameters
        ----------
        text : str
            The text string to detect language from.
        min_length : int
            Minimum number of characters of the text that is needeed
            for automatic detection of language (the longer the better).

        Returns
        -------
        str
            Returns language in ISO 639-1 format (e.g., `en` for English).
        """
        if text and len(text) >= min_length:
            return langdetect.detect(text)
        return ""

    class MLStripper(html.parser.HTMLParser):
        """"Strip HTML tags from a text string."""

        def __init__(self):
            self.reset()
            self.strict = False
            self.convert_charrefs = True
            self.fed = []

        def handle_data(self, d):
            self.fed.append(d)

        def get_data(self) -> str:
            return " ".join(self.fed)

    @staticmethod
    def strip_html_tags(html: str) -> str:
        """Removes HTML tags from a text string.

        E.g., `<b>Hello World</b>` becomes `Hello World`. Note that this
        method does not remove the content within the HTML tags. For example,
        removing `<script>` tags will keep the actual script within those tags.

        Parameters
        ----------
        html : str
            A text string with HTML code.

        Returns
        -------
        str
            A new string without HTML tags. If no HTML is found, an empty
            string is returned.
        """
        if not html:
            return ""
        s = TextUtils.MLStripper()
        html = html.replace("<br>", "\n\n")
        html = html.replace("<BR>", "\n\n")
        html = html.replace("<br/>", "\n\n")
        html = html.replace("<BR/>", "\n\n")
        html = html.replace("<p>", "\n\n")
        html = html.replace("<P>", "\n\n")
        html = html.replace("</p>", "\n\n")
        html = html.replace("</P>", "\n\n")
        s.feed(html)
        return s.get_data()

    @staticmethod
    def remove_tag_and_content(html: str, tag: str) -> str:
        """Remove a specific HTML tag and its inside content

        E.g., by removing the `script` tag, a string like
        `Hello <script>alert(document.title)</script> World` becomes
        `Hello World`.

        Parameters
        ----------
        html : str
            A text string with HTML code.
        tag : str
            An HTML tag such as `script` or `style`.

        Returns
        -------
        str
            A new string without specific HTML tags and its content.
        """
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        for s in soup.select(tag):
            s.extract()
        return str(soup)

    @staticmethod
    def remove_white_space(text: str) -> str:
        """Removes unnecessary white space between words.

        Will leave only 1 space between words, and 2 newlines between
        paragraphs.

        Parameters
        ----------
        text : str
            A text string.

        Returns
        -------
        str
            A new string with extroneuos white space removed.
        """
        if not text:
            return ""
        # Remove leading and trailing white spaces line by line.
        lines = []
        for line in text.split("\n"):
            lines.append(line.strip())
        text = "\n".join(lines)
        # Restrict the number of white space.
        text = re.sub("\n+", "\n\n", text)
        text = re.sub(" +", " ", text)
        return text

    @staticmethod
    def remove_white_space_from_list(lst: list, remove_empty_str=True) -> list:
        """Remove whitespace from strings in a list.

        Parameters
        ----------
        lst : list
            A list with strings.
        remove_empty_str : bool
            Whether or not to remove strings that are empty. This may reduce
            the number of strings in the list.

        Returns
        -------
        list
            A list with strings, where whitespace is removed from strings.
            if `remove_empty_str` is set to True, empty strings are removed
            from list.
        """
        line = []
        for s in lst:
            if type(s) == str:
                s = s.strip()
                if s and s != "":
                    line.append(s)
                elif not s and not remove_empty_str:
                    line.append(s)
        return line

    @staticmethod
    def convert_list_to_string(char_list: list, strip=True, sep="\n",
                               default=None) -> str:
        """Convert a list to a string separated by newline.

        Parameters
        ----------
        char_list : list
            A list with strings that should be converted.
        strip : bool
            Whether strings should be stripped, and empty strings removed.
        sep : str
            String inserted between values, defaults a newline.
        default : object
            Default value to return if the input char_list is None.

        Returns
        -------
        str
            A string with each value separated (by a separator, e.g. newline).
            If the char_list is None, then default value is returned.
        """
        if not char_list:
            return default
        if strip:
            char_list_stripped = (x.strip() for x in char_list)
            char_list = [x for x in char_list_stripped if x]
        if char_list:
            return sep.join(char_list)
        return default

    @staticmethod
    def md5_hash(text: str) -> str:
        """Create an MD5 hash from text.

        Parameters
        ----------
        text : str
            Text string to hash.

        Returns
        -------
        str
            Returns MD5 hash as a string. Returns empty string if no text
            input.
        """
        if not text:
            return ""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    @staticmethod
    def sanitize_str(value: str, default=None, keep_newlines=True,
                     replace_newlines=" ") -> str:
        """
        Sanitize text string for database insertion by setting default
        values and removing newlines.

        Note: This method deos NOT handle SQL injections!

        Parameters
        ----------
        value : str
            Text string to sanitize.
        default : object
            Default value that is returned if the input value is None.
        keep_newlines : bool
            Whether or not to keep new lines in the text string.
        replace_newlines : str
            Text string that newlines should be replaced to. Only applicable
            if keep_newlines is set to False.

        Returns
        -------
        str
            Returns a sanitized string. If the input string is None, then
            the default value is returned.
        """
        if not value:
            return default
        if type(value) != str:
            value = str(value)
        value = value.strip()
        if not keep_newlines:
            value = value.replace("\n", replace_newlines)
        return value

    @staticmethod
    def sanitize_int(value: int, default=None) -> int:
        """Sanitize integer for database insertion by setting default values.

        Note: This method does NOT handle SQL injections!

        Parameters
        ----------
        value : int
            Integer value to sanitize.
        default : object
            Default value that is returned if the input value is None.

        Returns
        -------
        int
            Returns a sanitized integer. If the input string is None, then
            the default value is returned.
        """
        if type(value) in [int, float]:
            return value
        if not value:
            return default
        return default


class FileUtils():
    """Various file utilities for getting file size of directories,
    number of files in directory and formatting file size bytes."""

    @staticmethod
    def get_directory_size(directory: str) -> tuple:
        """Get size (in bytes) of directory, including subdirectories.

        Parameters
        ----------
        directory : str
            Absolute path to the directory.

        Returns
        -------
        tuple
            Returns a tuple `(total_size, num_files)` with the total size
            in bytes (int) and the total number of files (int).
        """
        total_size = 0
        num_files = 0
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                num_files += 1
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size, num_files

    @staticmethod
    def get_directory_file_count(directory: str) -> int:
        """Count number of files in a directory.

        Does not include subdirectories.

        Parameters
        ----------
        directory : str
            Absolute path to the directory.

        Returns
        -------
        int
            Returns the total number of files.
        """
        files = []
        for name in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, name)):
                files.append(name)
        return len(files)

    @staticmethod
    def format_bytes(size: int, decimals=0, dec_sign=".") -> str:
        """Format byte size with appropriate suffix, e.g. `1024` -> `1 KB`.

        Parameters
        ----------
        size : int
            Size in bytes.
        decimals : int
            Number of decimals for rounding.
        dec_sign : str
            Decimal sign.

        Returns
        -------
        str
            A string such as `3.5 GB`.
        """
        if not size:
            return "0 bytes"
        power = 2**10
        n = 0
        power_labels = {0: "bytes", 1: "KB", 2: "MB", 3: "GB", 4: "TB",
                        5: "PB", 6: "EB", 7: "ZB", 8: "YB"}
        while size >= power:
            size /= power
            n += 1
        if decimals == 0:
            size = int(size)
        text = str(round(size, decimals)) + " " + power_labels[n]
        return text.replace(".", dec_sign)


class DateUtils():

    @staticmethod
    def set_iso_date(date, iso_date=True) -> str:
        """Convert string or date into a string in ISO 8601 format.

        Parameters
        ----------
        date: str
            A date as a string or datetime object.
        iso_date: bol
            Whether or not the date should be converted to ISO 8601 format
            (YYYY-MM-DDTHH:MM:SSZ). If False, then an ordinary datetime object
            is returned.

        Returns
        -------
        str
            Returns string with a date. If no date is found, None is returned.
        """
        if date:
            if type(date) == datetime.datetime:
                if iso_date:
                    return date.isoformat()
                else:
                    return date
            try:
                dt = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                return dt.isoformat() if iso_date else dt
            except BaseException:
                return None
        return None


class PrettyPrint():
    """Various utils for printing data to screen in a way that doesn't
    look horrific."""

    @staticmethod
    def fubar_unicode(text: str, limit=50, remove_unicode=True) -> str:
        """Remove all unicode characters that fuck up printing to screen.

        Parameters
        ----------
        text : str
            Text to remove unicode characters from.
        limit : int
            Limit the number of characters. Set to `None` to disable.
        remove_unicode : bool
            Whether to remove unicode characters.

        Returns
        -------
        str
            Returns a string without unicode characters.
        """
        if not text:
            return ""
        if remove_unicode:
            # Remove diacritic marks for some common words.
            text = text.replace("å", "a")
            text = text.replace("Å", "A")
            text = text.replace("ä", "a")
            text = text.replace("Ä", "A")
            text = text.replace("ö", "o")
            text = text.replace("Ö", "O")
            text = text.replace("Ü", "U")
            text = text.replace("ü", "u")
            text = text.replace("ü", "u")
            text = text.encode("ascii", "ignore").decode("ascii")
            # We could use "unidecode.unidecode(text)" instead but
            # it does more than removing diacritic marks...
        else:
            text = text.encode("utf-8")
        if limit and limit > 0:
            text = text[:limit]
        return text.strip()

    @staticmethod
    def print_columns(rows: list, headers=None, padding=2, indent=0):
        """Print data in columns.

        The column width is based on the max length of the text
        (per column).

        Parameters
        ----------
        rows : list
            A list with rows to print.
        headers : list
            A list with header names for the rows. Should be of the same
            length as the columns of `rows`.
        padding : int
            Number of spaces between each column.
        indent : int
            Numnber of spaces to indent each row.
        """
        if headers:
            # Add column headers and divider.
            rows.insert(0, headers)
            divider = []
            for col in headers:
                divider.append("-" * len(str(col)))
            rows.insert(1, divider)
        widths = [max(map(len, col)) for col in zip(*rows)]
        for row in rows:
            print((" " * indent) + (" " * padding).join(
                (str(val).ljust(width) for val, width in zip(row, widths))))

    @staticmethod
    def print_json(json_data: dict, indent=2, sort_keys=False):
        """Print JSON data formatted and indented.

        Parameters
        ----------
        json_data : dict
            Dictionary to print.
        indent : int
            Numnber of spaces to indent each row.
        sort_keys : bool
            Whether or not to sort the keys in alphabetical order.
        """
        print(json.dumps(json_data, indent=indent, sort_keys=sort_keys))

    @staticmethod
    def print_stars_and_bars(data: dict, explanations=None):
        """Create ASCII bar graph.

        A simple way to visualize the largest numbers by printing horizontal
        bars from dict data with integer values.

        Parameters
        ----------
        data : dict
            A dictionary with a key and an integer.
        explanations : dict
            A dictionary that maps each key to an arbitrary explanation.

        Example usage
        -------------
        ```python
        data = {
            "one": 34534,
            "two": 73633,
            "three": 3731
        }

        explanations = {
            "one": "Explanation for number one",
            "two": "Explanation for number two",
            "three": "Explanation for number three"
        }

        print_stars_and_bars(data, explanations)
        ```
        """
        if type(data) != dict:
            raise ValueError(
                "Argument 'data' mus be of type dict, not {}.".format(
                    type(data).__name__))
        line = []
        for key, value in data.items():
            # Ignore all but integers.
            if type(value) == int:
                if explanations:
                    line.append((explanations[key], value))
                else:
                    line.append((key, value))
        PrettyPrint._print_tuple_bars(line)

    @staticmethod
    def _print_tuple_bars(data: list, pad_length=2, width=45):
        """Print ASCII bar chart of list of tuples,
        e.g. `[("a", 10), ("b", 20)]`.

        Parameters
        ----------
        data : list
            A dictionary with a tuple (label, integer) of type (str, int).
        pad_length : int
            Number of spaces between labels and stars.
        width : int
            The max width of the stars.
        """
        max_value = max(count for _, count in data)
        increment = max_value / width
        longest_label_len = max(len(label) for label, _ in data) + pad_length
        for label, count in data:
            bar_chunks, remainder = divmod(int(count * 8 / increment), 8)
            bar = "*" * bar_chunks
            if remainder > 0:
                bar += ""
            bar = bar or ""
            print(f"{label.rjust(longest_label_len)}: {count:#10d} {bar}")


class WebUtils():
    """Various web and URL utilities for extracing domain names."""

    @staticmethod
    def get_domain_name(url: str, include_subdomain=True) -> str:
        """Get domain name from a given URL (e.g., `example.org`).

        E.g., `https://www.example.org/subdir/image.jpg` will be returned as
        `www.example.org`.

        Parameters
        ----------
        url : str
            A URL to extract domain name from.
        include_subdomain : bool
            Whether or not to include subdomain. If set to `True`,
            `https://www.example.org/` will be returned as `www.example.org`.
            If set to `False`, it will be returned as `example.org`. If the
            subdomain is lacking, it will be returned as `example.org`.

        Returns
        -------
        str
            Returns a domain name and its top-level domain (with or without
            subdomain).
        """
        if not url:
            return None
        d = tldextract.extract(url)
        if include_subdomain and d.subdomain:
            return "{}.{}.{}".format(d.subdomain, d.domain, d.suffix)
        elif d and d.suffix:
            return "{}.{}".format(d.domain, d.suffix)
        elif d:
            return d.domain
        return None
