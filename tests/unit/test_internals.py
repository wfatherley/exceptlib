"""unit tests for exceptlib interals"""
import logging
import unittest

import exceptlib


class BaseTestCase(unittest.TestCase):
    """boilerplate"""

    def setUpClass(cls):
        """return None"""
        logging.basicConfig(level=logging.DEBUG)


class TestGetExceptionChain(BaseTestCase):
    """test exceptlib.get_exception_chain"""

    def test_input_behavior(self):
        """return None"""
        pass