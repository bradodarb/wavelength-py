import unittest

from exos_serverless_lib.logging.util.cast_checks import is_int_like, is_json_serializable


class TestCastings(unittest.TestCase):

    def test_is_json_serializable(self):
        rv = is_json_serializable("object")
        self.assertTrue(rv)

    def test_is_json_serializable_false(self):
        obj = {'set'}
        rv = is_json_serializable(obj)
        self.assertFalse(rv)

    def test_is_int_like(self):
        self.assertTrue(is_int_like(1))
        self.assertTrue(is_int_like("1"))

    def test_is_int_like_false(self):
        self.assertFalse(is_int_like('something'))
