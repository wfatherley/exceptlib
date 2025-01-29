"""unit tests for exceptlib interals"""
import sys
import unittest

import exceptlib


class TestExcInfos(unittest.TestCase):
    """test exceptlib.exc_infos"""
    pass


class TestIsHotExcInfo(unittest.TestCase):
    """test exceptlib.is_hot_exc_info"""
    pass


class TestGetTracebackModules(unittest.TestCase):
    """test exceptlib.get_modules"""
    pass


class TestGetRaised(unittest.TestCase):
    """test exceptlib.get_modules"""
    pass


class TestRandomException(unittest.TestCase):
    """test exceptlib.random_exception"""

    def test_input_variation(self):
        """:return  None:"""

        # poll for collision with no input parameters
        for _ in range(500):
            self.assertTrue(
                exceptlib.random_exception() not in exceptlib.std_excs
            )
        
        # check equivalance of name parameter variation
        self.assertEqual(
            exceptlib.random_exception("Foo").__name__,
            exceptlib.random_exception(name="Foo").__name__
        )
        self.assertNotEqual(
            exceptlib.random_exception("Foo").__name__,
            exceptlib.random_exception("Bar").__name__
        )
        