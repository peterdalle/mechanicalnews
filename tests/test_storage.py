# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the pipelines module.
"""
# Use relative import of module for testing.
import sys, os
testdir = os.path.dirname(__file__)
srcdir = "../mechanicalnews"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest
from storage import MySqlDatabase


class RunTest_MySqlDatabase(unittest.TestCase):

    def test_database_default_settings(self):
        db = MySqlDatabase.from_settings()
        self.assertEqual(db.database, "mechanicalnews")


if __name__ == '__main__':
    unittest.main()
