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
from mechanicalnews.database import MySqlDatabase


class UserManager():
    """Handle users and their API keys."""

    def __init__(self):
        self.db = MySqlDatabase.from_settings()

    def is_valid_api_key(self, api_key: str) -> bool:
        """Check if API key is valid (active and authorized).

        Parameters
        ----------
        api_key : str
            API key for a user who is permitted to use the service.

        Returns
        -------
        bool
            Returns True if the API key is valid and authorized,
            otherwise False.
        """
        user = self.get_user_by_key(api_key)
        if not user:
            return False
        elif not user["active"]:
            return False
        elif user["to_date"] and user["to_date"] < datetime.datetime.today():
            return False
        return True

    def incremenet_api_key_count(self, api_key: str):
        """Increment the number of times an API key was used.

        Parameters
        ----------
        api_key : str
            API key for a user who is permitted to use the service.
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")
        with self.db:
            self.db.execute("UPDATE users SET api_counter=api_counter+1," +
                            " api_last_used = NOW()" +
                            " WHERE api_key = %s LIMIT 1", (api_key, ))

    def is_administrator(self, api_key: str) -> bool:
        """Check if the API key has administrator privileges.

        Parameters
        ----------
        api_key : str
            API key for a user who is permitted to use the service.

        Returns
        -------
        bool
            Returns True if the user is an administrator, otherwise False.
        """
        # TODO: Add API key check.
        return True

    def get_user_by_key(self, api_key: str) -> dict:
        """Get user by API key.

        Parameters
        ----------
        api_key : str
            API key for a user who is permitted to use the service.

        Returns
        -------
        dict
            Returns a dict object of a user.
        """
        user = None
        self.db.open()
        self.db.cur.execute(
            "SELECT * FROM users WHERE api_key = %s LIMIT 1", (api_key, ))
        if self.db.cur:
            for row in self.db.cur:
                user = row
        self.db.close()
        return user
