"""unit tests for exceptlib.ExceptionFrom"""
import logging
import re
import sys
import unittest

import exceptlib


def raise_index_error_from_bad_logging_call():
    """:return None:"""
    try:
        logging.getLogger(75)
    except:
        raise IndexError





class TestInitializationApi(unittest.TestCase):
    """tests behavior of exceptlib.ExceptionFrom.__new__"""

    def test_sole_exception_handler(self):
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

    def test_sole_exception_handler_without_root_only(self):
        """:return None:
        
        Verify that ``exceptlib.ExceptionFrom.__new__`` is called and
        correctly furnishes the interpreter to enter its exception
        handler when that exception handler is the only one provided.
        Keyword arguement ``root_only`` is set to ``False``.
        """
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re, root_only=False):
            caught = True
        self.assertTrue(caught)

    def test_deprioritized_second_exception_handler(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` in some way
        alters the interpreter's priority mechanism for entering
        exception handlers.
        """
        caught = None
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging):
            caught = True
        self.assertIsNotNone(caught)
        self.assertFalse(caught)

    def test_deprioritized_second_exception_handler_without_root_only(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` in some way
        alters the interpreter's priority mechanism for entering
        exception handlers. Keyword argument ``root_only`` is set to
        ``False``.
        """
        caught = None
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging, root_only=False):
            caught = True
        self.assertIsNotNone(caught)
        self.assertFalse(caught)

    def test_prioritized_second_exception_handler(self):
        """:return None:
        
        Verify the interpreter passes over uninvolved exception
        handlers and enters a later one that calls
        ``exceptlib.ExceptionFrom.__new__`` with an involved module.
        """
        caught = None
        try:
            re.compile(2)
        except StopIteration:
            caught = None
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertIsNotNone(caught)
        self.assertTrue(caught)

    def test_prioritized_second_exception_handler_without_root_only(self):
        """:return None:
        
        Verify the interpreter passes over uninvolved exception
        handlers and enters a later one that calls
        ``exceptlib.ExceptionFrom.__new__`` with an involved module.
        Keyword argument ``root_only`` is set to ``False``.
        """
        caught = None
        try:
            re.compile(2)
        except StopIteration:
            caught = None
        except exceptlib.ExceptionFrom(re, root_only=False):
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

    def test_no_input_gives_empty_tuple_without_root_only(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` with no
        parameters results in an empty tuple. Keyword arugment
        ``root_only`` is set to ``False``.
        """
        exc_from = exceptlib.ExceptionFrom(root_only=False)
        self.assertIsInstance(exc_from, tuple)
        self.assertFalse(exc_from)

    def test_with_wrong_input_raises(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` raises ``TypeError``
        when passed an object not of type ``ModuleType``.
        """
        with self.assertRaises(TypeError):
            exc_from = exceptlib.ExceptionFrom(7)

    def test_with_wrong_input_raises_without_root_only(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` raises ``TypeError``
        when passed an object not of type ``ModuleType``. Keyword
        argument ``root_only`` is set to ``False``.
        """
        with self.assertRaises(TypeError):
            exc_from = exceptlib.ExceptionFrom(7, root_only=False)

    def test_cohesion_with_exceptlib_get_raised(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` correctly propogates
        ``ValueError`` from ``exceptlib.get_raised`` when a builtin
        module is passed as a parameter.
        """
        with self.assertRaises(ValueError):
            exc_from = exceptlib.ExceptionFrom(sys)

    def test_cohesion_with_exceptlib_get_raised_without_root_only(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` correctly propogates
        ``ValueError`` from ``exceptlib.get_raised`` when a builtin
        module is passed as a parameter. Keyword argument ``root_only``
        is set to ``False``.
        """
        with self.assertRaises(ValueError):
            exc_from = exceptlib.ExceptionFrom(sys, root_only=False)
