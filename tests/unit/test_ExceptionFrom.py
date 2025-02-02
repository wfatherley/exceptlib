"""unit tests for exceptlib.ExceptionFrom"""
import logging
import re
import sys
import unittest

import exceptlib


class TestInitializationApi(unittest.TestCase):
    """tests behavior of exceptlib.ExceptionFrom.__new__"""

    def test_prioritized_as_sole_exception_handler(self):
        """:return None:
        
        Verify that ``exceptlib.ExceptionFrom.__new__`` is called and
        correctly furnishes the interpreter to enter its exception
        handler when that exception handler is the only one provided.
        """
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertTrue(caught)

    def test_deprioritized_as_second_exception_handler(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` in some way
        alters the interpreter's priority mechanism for entering
        exception handlers.
        """
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging):
            caught = True
        self.assertFalse(caught)

    def test_prioritized_as_second_exception_handler(self):
        """:return None:
        
        Verify the interpreter passes over uninvolved exception
        handlers and enters a later one that calls
        ``exceptlib.ExceptionFrom.__new__`` with an involved module.
        """
        try:
            re.compile(2)
        except StopIteration:
            caught = None
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertIsNotNone(caught)
        self.assertTrue(caught)

    def test_no_input_gives_empty_tuple(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` with no
        parameters results in an empty tuple.
        """
        exc_from = exceptlib.ExceptionFrom()
        self.assertIsInstance(exc_from, tuple)
        self.assertFalse(exc_from)

    def test_with_wrong_input_raises(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` raises ``TypeError``
        when passed an object not of type ``ModuleType``.
        """
        with self.assertRaises(TypeError):
            exc_from = exceptlib.ExceptionFrom(7)

    def test_cohesion_with_exceptlib_get_raised(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` correctly propogates
        ``ValueError`` from ``exceptlib.get_raised`` when a builtin
        module is passed as a parameter.
        """
        with self.assertRaises(ValueError):
            exc_from = exceptlib.ExceptionFrom(sys)
