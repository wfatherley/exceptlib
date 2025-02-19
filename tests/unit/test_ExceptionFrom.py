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


class TestApi(unittest.TestCase):
    """test basic characteristics"""

    def test_name(self):
        """:return None:
        
        Verify the name of of the object is ``ExceptionFrom``.
        """
        self.assertEqual(exceptlib.ExceptionFrom.__name__, "ExceptionFrom")

    def test_type(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom`` is of type ``tuple``.
        """
        self.assertTrue(issubclass(exceptlib.ExceptionFrom, tuple))

    def test_member_names(self):
        """:return None:
        
        Verify public API names are bound.
        """
        exception_from_dir = dir(exceptlib.ExceptionFrom)
        self.assertTrue("__new__" in exception_from_dir)


class TestInitializationApi(unittest.TestCase):
    """test behavior of exceptlib.ExceptionFrom.__new__"""

    def test_basic_exception_handler(self):
        """:return None:
        
        Verify that ``exceptlib.ExceptionFrom.__new__`` is called and
        correctly furnishes the interpreter to enter its exception
        handler when that exception handler is the only one provided.
        """

        # unchained exception
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertTrue(caught)

        # chained exception
        caught = False
        try:
            raise_index_error_from_bad_logging_call()
        except exceptlib.ExceptionFrom(logging):
            caught = True
        self.assertTrue(caught)

    def test_skip_basic_exception_handler(self):
        """:return None:
        
        Verify that ``exceptlib.ExceptionFrom.__new__`` is called and
        correctly furnishes the interpreter to skip its exception
        handler because the input module is uninvolved.
        """

        # unchained exception
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(logging):
            caught = True
        except:
            self.assertFalse(caught)

        # chained exception
        caught = False
        try:
            raise_index_error_from_bad_logging_call()
        except exceptlib.ExceptionFrom(re):
            caught = True
        except:
            self.assertFalse(caught)


    def test_basic_exception_handler_without_root_only(self):
        """:return None:
        
        Verify that ``exceptlib.ExceptionFrom.__new__`` is called and
        correctly furnishes the interpreter to enter its exception
        handler when that exception handler is the only one provided.
        Keyword arguement ``root_only`` is set to ``False``.
        """

        # unchained exception
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re, root_only=False):
            caught = True
        self.assertTrue(caught)

        # chained exception
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(re, root_only=False):
            caught = True
        self.assertTrue(caught)

    def test_skip_basic_exception_handler_without_root_only(self):
        """:return None:
        
        Verify that ``exceptlib.ExceptionFrom.__new__`` is called and
        correctly furnishes the interpreter to enter its exception
        handler when that exception handler is the only one provided.
        Keyword arguement ``root_only`` is set to ``False``.
        """

        # unchained exception
        caught = False
        try:
            re.compile(0)
        except exceptlib.ExceptionFrom(logging, root_only=False):
            caught = True
        except:
            self.assertFalse(caught)

        # chained exception
        caught = False
        try:
            raise_index_error_from_bad_logging_call()
        except exceptlib.ExceptionFrom(re, root_only=False):
            caught = True
        except:
            self.assertFalse(caught)

    def test_deprioritized_second_exception_handler(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` in some way
        alters the interpreter's priority mechanism for entering
        exception handlers.
        """

        # unchained exception
        caught = None
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging):
            caught = True
        self.assertIsNotNone(caught)
        self.assertFalse(caught)

        # chained exception
        caught = None
        try:
            raise_index_error_from_bad_logging_call()
        except IndexError:
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

        # unchained exception
        caught = None
        try:
            logging.getLogger(1)
        except TypeError:
            caught = False
        except exceptlib.ExceptionFrom(logging, root_only=False):
            caught = True
        self.assertIsNotNone(caught)
        self.assertFalse(caught)

        # chained exception
        caught = None
        try:
            raise_index_error_from_bad_logging_call()
        except IndexError:
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

        # unchained exception
        caught = None
        try:
            re.compile(2)
        except StopIteration:
            caught = False
        except exceptlib.ExceptionFrom(re):
            caught = True
        self.assertIsNotNone(caught)
        self.assertTrue(caught)

        # chained exception
        caught = None
        try:
            raise_index_error_from_bad_logging_call()
        except StopIteration:
            caught = False
        except exceptlib.ExceptionFrom(logging):
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

        # unchained exception
        caught = None
        try:
            re.compile(2)
        except StopIteration:
            caught = False
        except exceptlib.ExceptionFrom(re, root_only=False):
            caught = True
        self.assertIsNotNone(caught)
        self.assertTrue(caught)

        # chained exception
        caught = None
        try:
            raise_index_error_from_bad_logging_call()
        except StopIteration:
            caught = False
        except exceptlib.ExceptionFrom(logging, root_only=False):
            caught = True
        self.assertIsNotNone(caught)
        self.assertTrue(caught)


    def test_no_input_gives_empty_tuple(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` with no
        parameters results in an empty tuple when there is no current
        exception.
        """
        exc_from = exceptlib.ExceptionFrom()
        self.assertIsInstance(exc_from, tuple)
        self.assertFalse(exc_from)

    def test_no_input_gives_empty_tuple_without_root_only(self):
        """:return None:
        
        Verify calling ``exceptlib.ExceptionFrom.__new__`` with no
        parameters results in an empty tuple when there is no current
        exception. Keyword arugment ``root_only`` is set to ``False``.
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
            exceptlib.ExceptionFrom(sys)

    def test_cohesion_with_exceptlib_get_raised_without_root_only(self):
        """:return None:
        
        Verify ``exceptlib.ExceptionFrom.__new__`` correctly propogates
        ``ValueError`` from ``exceptlib.get_raised`` when a builtin
        module is passed as a parameter. Keyword argument ``root_only``
        is set to ``False``.
        """
        with self.assertRaises(ValueError):
            exceptlib.ExceptionFrom(sys, root_only=False)

    def test_scraping_ability(self):
        """:return None:
        
        Verify initialization's scraping ability.
        """
        self.assertEqual(
            set(exceptlib.ExceptionFrom(exceptlib)),
            {RuntimeError, TypeError, ValueError}
        )
        self.assertEqual(
            set(exceptlib.ExceptionFrom(re)),
            {TypeError, ValueError}
        )

    def test_stdlib_supported_examples(self):
        """:return None:
        
        Additional tests against some standard libarary modules.
        """

        # secrets will call random for RNG service
        import math, random, secrets

        # verify secrets is involved
        try:
            secrets.randbelow(math.inf)
        except exceptlib.ExceptionFrom(secrets, root_only=False):
            self.assertTrue(True)

        # but also verify its not the root cause
        try:
            secrets.randbelow(math.inf)
        except exceptlib.ExceptionFrom(secrets):
            self.assertTrue(False)
        except AttributeError:
            self.assertTrue(True)

        # and that random is the root
        try:
            secrets.randbelow(math.inf)
        except exceptlib.ExceptionFrom(random):
            self.assertTrue(True)

    def test_stdlib_unsupported_examples(self):
        """:return None:
        
        Additional tests against some standard libarary modules.
        """
        import os
        self.assertEqual(
            set(exceptlib.ExceptionFrom(os)),
            {
                ImportError,
                OSError,
                FileNotFoundError,
                NotADirectoryError,
                ValueError,
                KeyError,
                TypeError,
                AttributeError,
                NotImplementedError,
            }
        )