"""unit tests for exceptlib interals"""
import ast
import unittest

import exceptlib


dummy_module_source = """
raise

raise Exception
raise BaseException("bork")

try:
    list(map)
except TypeError:
    raise

try:
    list()[0]
except IndexError:
    raise ImportError

try:
    dict()[0]
except KeyError as e:
    raise e

my_exc = ZeroDivisionError
raise my_exc
my_other_exc = my_exc
raise my_other_exc

""".strip()
dummy_module_node = ast.parse(dummy_module_source)
dummy_module_raise_nodes = [
    n for n in ast.walk(dummy_module_node) if isinstance(n, ast.Raise)
]


class TestRaiseNodeFromModuleNode(unittest.TestCase):
    """test exceptlib.raise_nodes_from_module_node"""

    def test_dummy_module_parity(self):
        """:return None:
        
        Verify parity between raise nodes from a unspecialized walk and
        nodes from the scraping walk."""
        for node in exceptlib.raise_nodes_from_module_node(dummy_module_node):
            self.assertTrue(
                [n for n in dummy_module_raise_nodes if n.lineno == node.lineno]
            )

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
