"""unit tests for exceptlib.exc_from_mod"""
import logging
import re
import sys
import unittest

import exceptlib


class SequentialTestCase(unittest.TestCase):
    """line by line unit tests"""

    def setUpClass(cls):
        """return None"""
        logging.basicConfig(level=logging.DEBUG)

    def test_preloop_controlflow(self):
        """return None"""

        # ensure raise runtime error if not exception
        with self.assertRaises(RuntimeError):
            exceptlib.exc_from_mod()

        # ensure raise runtime error if bad modules
        with self.assertRaises(RuntimeError):
            try:
                raise IndexError
            except exceptlib.exc_from_mod("re", sys.modules["abc"]):
                pass

        # ensure no suppress if exception but no modules
        with self.assertRaises(KeyError):
            try:
                raise KeyError
            except exceptlib.exc_from_mod():
                raise

    def test_simple_use(self):
        """return None"""

        # input without root_only
        try:
            re_obj = re.compile(7)
        except exceptlib.exc_from_mod(re) as e:
            self.assertIsInstance(e, TypeError)

        # input with root_only
        try:
            re_obj = re.match(None)
        except exceptlib.exc_from_mod(re, any_traceback=True) as e:
            self.assertIsInstance(e, TypeError)

    