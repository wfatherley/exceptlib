"""unit tests for exceptlib interals"""
import sys
import unittest

import exceptlib


class TestIsHotExcInfo(unittest.TestCase):
    """test exceptlib.is_hot_exc_info"""

    def test_input_variation(self):
        """return None"""

        # raise TypeError with no parameters
        with self.assertRaises(TypeError):
            exceptlib.is_hot_exc_info()

        # false-inducing inputs
        self.assertFalse(exceptlib.is_hot_exc_info(tuple()))
        self.assertFalse(exceptlib.is_hot_exc_info("123"))
        self.assertFalse(exceptlib.is_hot_exc_info(sys.exc_info()))

        # true-inducing input
        exc = Exception()
        #self.assertTrue(exceptlib.is_hot_exc_info((type(exc), exc, exc.__traceback__)))
        try:
            raise KeyError()
        except:
            self.assertTrue(exceptlib.is_hot_exc_info(sys.exc_info()))



class TestGetExceptionChain(unittest.TestCase):
    """test exceptlib.get_exception_chain"""

    def test_input_variation(self):
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

    def test_chain(self):
        """return None"""

        # 1-length
        exc = Exception()
        self.assertEqual(exceptlib.get_exception_chain(exc), (exc,))

        # 2-length
        for exc in (TypeError(),):
            try:
                raise ValueError() from exc
            except Exception as e:

                # default order sequential
                self.assertEqual(
                    exceptlib.get_exception_chain(e), (e.__cause__, e)
                )

                # reversed order reversed
                self.assertEqual(
                    exceptlib.get_exception_chain(e, earliest_first=False),
                    (e, e.__cause__)
                )


class TestGetTracebacks(unittest.TestCase):
    """test exceptlib.get_tracebacks"""

    def test_input_variation(self):
        """return None"""

        # raise TypeError with no parameters
        with self.assertRaises(TypeError):
            exceptlib.get_tracebacks()

        for obj in (1, "a", None, list, {}):
            with self.assertRaises(ValueError):
                exceptlib.get_tracebacks(obj)