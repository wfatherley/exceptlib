"""unit tests for exceptlib interals"""
import logging
import sys
import unittest

import exceptlib


class BaseTestCase(unittest.TestCase):
    """boilerplate"""

    def setUpClass(cls):
        """return None"""
        logging.basicConfig(level=logging.DEBUG)


class TestGetExceptionChain(BaseTestCase):
    """test exceptlib.get_exception_chain"""

    def test_bad_inputs(self):
        """return None"""

        # raise TypeError with no parameters
        with self.assertRaises(TypeError):
            exceptlib.get_exception_chain()

        # raise ValueError for bad parameters
        for obj in ("abc", 7, [], None, unittest, sys.exc_info):
            with self.assertRaises(ValueError):
                exceptlib.get_exception_chain(obj)
        with self.assertRaises(ValueError):
            exceptlib.get_exception_chain(sys.exc_info())

    def test_shallow_chain(self):
        """return None"""

        # 1-length
        self.assertEqual(
            exceptlib.get_exception_chain(Exception()), (Exception(),)
        )

        # 2-length, pattern 1
        for exc in (TypeError(), None):
            try:
                raise ValueError() from exc
            except Exception as e:

                # default order sequential
                self.assertEqual(
                    exceptlib.get_exception_chain(e),
                    (TypeError(), ValueError())
                )

                # reversed order reversed
                self.assertEqual(
                    exceptlib.get_exception_chain(e, earliest_first=False),
                    (ValueError(), TypeError())
                )

        # 2-length, pattern two
        try:
            raise KeyError()
        except KeyError as e:
            try:
