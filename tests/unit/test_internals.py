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

    def test_collision_loop(self):
        """:return  None:
        
        Create 500 random exceptions and verify none collide with any
        standard exceptions in Python.
        """
        for _ in range(500):
            exc = exceptlib.random_exception()
            self.assertTrue(exc not in exceptlib.std_excs)
            self.assertTrue(len(exc.__name__) == 15)

    def test_name_parameter_variation(self):
        """:return None:
        
        Verify name parameter can be passed inline or with its keyword
        without altering the name of the object itself
        """
        self.assertEqual(
            exceptlib.random_exception("Foo").__name__,
            exceptlib.random_exception(name="Foo").__name__
        )
        self.assertNotEqual(
            exceptlib.random_exception("Foo").__name__,
            exceptlib.random_exception("Bar").__name__
        )


class TestExceptionTypeScraper(unittest.TestCase):
    """test exceptlib.ExceptionTypeScraper"""

    def test_wip(self):
        import secrets, ast, inspect, pathlib
        module_source = pathlib.Path(inspect.getfile(exceptlib)).read_text("utf-8")
        module_ast = ast.parse(module_source)
        s = exceptlib.ExceptionTypeScraper(secrets)
        s.visit(module_ast)
        try:
            self.assertTrue(
                s.raised_exceptions == {
                    NameError, ValueError, TypeError, Exception, Warning
                }
            )
        except:
            raise