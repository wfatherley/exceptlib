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
        exc = Exception()
        self.assertFalse(exceptlib.is_hot_exc_info((type(exc), exc, exc.__traceback__)))

        # true-inducing input
        try:
            raise KeyError()
        except:
            self.assertTrue(exceptlib.is_hot_exc_info(sys.exc_info()))


class TestGetTracebackModules(unittest.TestCase):
    """test exceptlib.get_modules"""
    pass


class TestGetRaised(unittest.TestCase):
    """test exceptlib.get_modules"""
    pass