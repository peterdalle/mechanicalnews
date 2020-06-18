# -*- coding: utf-8 -*-
"""
Unit tests of the classes in the api module.
"""
# Use relative import of module for testing.
import sys, os
testdir = os.path.dirname(__file__)
srcdir = "../mechanicalnews"
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import unittest
import api


class RunTest_Api(unittest.TestCase):

    def setUp(self):
        self.app = api.app

    def test_api_config_values(self):
        self.assertEqual(self.app.debug, True)


if __name__ == '__main__':
    unittest.main()
