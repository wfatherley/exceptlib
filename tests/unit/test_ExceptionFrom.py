"""unit tests for exceptlib.ExceptionFrom"""
import logging
import re
import unittest

import exceptlib


class TestInitializationApi(unittest.TestCase):
    """test exceptlib.ExceptionFrom"""

    def test_exception_handling_priority(self):
        """"""
        
        # verify simplest entry
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertTrue(caught)

        # verify no entry by priority
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging):
            caught = True
        self.assertFalse(caught)

        # verify entry by priority
        try:
            re.compile(2)
        except StopIteration:
            caught = None
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertIsNotNone(caught)
        self.assertTrue(caught)

    def test_input_variation(self):
        """"""
        pass
