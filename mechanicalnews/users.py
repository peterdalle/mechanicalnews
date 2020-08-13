# -*- coding: utf-8 -*-
"""
Module that handles API users.
"""
import datetime
import os
import sys
import time
import string
from mechanicalnews.settings import AppConfig
from mechanicalnews.storage import MySqlDatabase


class User():
    """Handle users and their API keys."""

    def __init__(self, api_key: str):
        """Create new instance of user.

        Parameters
        ----------
        api_key : str
            API key for user.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")
        self.db = MySqlDatabase.from_settings()
        self.api_key = api_key
        self.user = None

    def is_active(self) -> bool:
        """Check if API key is active.

        Returns
        -------
        bool
            Returns True if the API key exists and is active, otherwise False.
        """
        if not self.user:
            self.user = self.get_user()
        if not self.user:
            return False
        elif not self.user["active"]:
            return False
        elif self.user["to_date"] and self.user["to_date"] < datetime.datetime.today():
            return False
        return True

    def incremenet_api_key_count(self):
        """Increment the number of times an API key was used.

        Parameters
        ----------
        api_key : str
            API key for a user who is permitted to use the service.
        """
        with self.db:
            self.db.execute("UPDATE users SET api_counter=api_counter+1," +
                            " api_last_used = NOW() WHERE api_key = %s LIMIT 1", (self.api_key, ))

    def is_administrator(self) -> bool:
        """Check if the user has administrator privileges.

        Returns
        -------
        bool
            Returns True if the user is an administrator, otherwise False.
        """
        # TODO: Add API key check.
        return True

    def get_user(self) -> dict:
        """Get user (by API key).

        Returns
        -------
        dict
            Returns a dict object of a user.
        """
        user = None
        self.db.open()
        self.db.cur.execute("SELECT * FROM users WHERE api_key = %s LIMIT 1", (self.api_key, ))
        if self.db.cur:
            for row in self.db.cur:
                user = row
        self.db.close()
        return user
