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
        # check constant name length
        for _ in range(500):
            exc = exceptlib.random_exception()
            self.assertTrue(exc not in exceptlib.std_excs)
            self.assertTrue(len(exc.__name__) == 15)
        
        # check equivalance of name parameter variation
        self.assertEqual(
            exceptlib.random_exception("Foo").__name__,
            exceptlib.random_exception(name="Foo").__name__
        )
        self.assertNotEqual(
            exceptlib.random_exception("Foo").__name__,
            exceptlib.random_exception("Bar").__name__
        )
        

class TestStandardExceptions(unittest.TestCase):
    """test exceptlib.standard_exceptions"""

    def test_can_raise_all(self):
        """:return None:"""
        for exc in exceptlib.standard_exceptions:
            with self.assertRaises(exc):
                raise exc