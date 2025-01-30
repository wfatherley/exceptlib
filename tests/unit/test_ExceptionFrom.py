"""unit tests for exceptlib.ExceptionFrom"""
import logging
import re
import sys
import unittest

import exceptlib


class TestExceptionFromInitializationApi(unittest.TestCase):
    """test exceptlib.ExceptionFrom"""

    def test_exception_handling_priority(self):
        """"""
        
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertTrue(caught)

        #
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging):
            caught = True
        self.assertFalse(caught)

        # 
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
