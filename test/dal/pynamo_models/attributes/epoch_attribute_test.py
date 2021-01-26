import logging
import unittest
from decimal import Decimal

from wavelength_serverless_lib.dal.pynamo_models.attributes.epoch_attribute import serialize_epoch_str, serialize_epoch, EpochAttribute, \
    serialize_epoch_numeric, serialize_epoch_int

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestEpochAttribute(unittest.TestCase):

    def setUp(self):
        log.info("==================================================")
        log.info("======   Test: %s, SetUp", self.id())
        log.info("==================================================")

    def tearDown(self):
        log.info("--------------------------------------------------")
        log.info("------   Test: %s, TearDown", self.id())
        log.info("--------------------------------------------------")

    def test_serialize_epoch(self):
        self.assertIsNone(serialize_epoch({'test_dict': 123}))

        test_value = 1576421280000000.123
        self.assertEqual(serialize_epoch(test_value), 1576421280000000)
        test_value = Decimal('1576421280000000.123')
        self.assertEqual(serialize_epoch(test_value), 1576421280000000)

    def test_serialize_epoch_str(self):
        result = serialize_epoch_str('2019-12-15T14:48:00.000Z')
        self.assertEqual(result, 1576421280000000)

    def test_serialize_epoch_str_fails_with_invalid_datetime_format(self):
        with self.assertRaises(ValueError) as err:
            serialize_epoch_str('1576421280000000')

        self.assertEqual(str(err.exception), 'Unable to parse string as a datetime')

    def test_serialize_epoch_int(self):
        result = serialize_epoch_int(1576421280000000)
        self.assertEqual(result, 1576421280000000)
        self.assertIsInstance(result, int)

    def test_EpochAttribute_serialize_numeric(self):
        result = serialize_epoch_numeric(1576421280000000.0123456)
        self.assertEqual(result, 1576421280000000)

    def test_EpochAttribute_serialize_string(self):
        epoch_attribute = EpochAttribute()
        result = epoch_attribute.serialize('2019-12-15T14:48:00.000Z')
        self.assertEqual(result, '1576421280000000')

    def test_EpochAttribute_serialize_returns_None_when_unsuported_type(self):
        epoch_attribute = EpochAttribute()

        result = epoch_attribute.serialize({'datetime': '2019-12-15T14:48:00.000Z'})
        self.assertEqual(result, 'null')

        with self.assertRaises(ValueError) as err:
            epoch_attribute.serialize(True)

            self.assertEqual(str(err.exception), 'Boolean not supported for Epoch')


if __name__ == '__main__':
    unittest.main()
