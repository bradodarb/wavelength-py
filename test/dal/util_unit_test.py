import logging
import unittest
from datetime import datetime

from wavelength_py.model.util import get_posix_timestamp, get_posix_date, get_range_key

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestModelUtils(unittest.TestCase):

    def setUp(self):
        log.info("==================================================")
        log.info("======   Test: %s, SetUp", self.id())
        log.info("==================================================")

    def tearDown(self):
        log.info("--------------------------------------------------")
        log.info("------   Test: %s, TearDown", self.id())
        log.info("--------------------------------------------------")

    def test_conversion_is_accurate(self):
        timestamp = datetime.utcnow()
        timestamp_milis = get_posix_timestamp(timestamp)
        milis_timestamp = get_posix_date(timestamp_milis)

        self.assertEqual(round(timestamp.timestamp()), round(milis_timestamp.timestamp()))

    def test_range_key_generation(self):
        key = 'key'
        timestamp = datetime.utcnow()
        timestamp_milis = get_posix_timestamp(timestamp)
        test_key = f'{timestamp_milis}::{key}'
        reverse_test_key = f'{key}::{timestamp_milis}'

        self.assertEqual(test_key, get_range_key(key, timestamp))
        self.assertEqual(reverse_test_key, get_range_key(key, timestamp, reverse=True))


if __name__ == '__main__':
    unittest.main()
