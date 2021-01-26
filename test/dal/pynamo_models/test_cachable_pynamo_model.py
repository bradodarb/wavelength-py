# -*- coding: utf-8 - *-

import logging
import random
import string
import unittest
from time import sleep

from wavelength_serverless_lib.dal.dal_config import DalConfig
from cachetools import TTLCache
from mock import patch, MagicMock

from wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model import CachingPynamoModel
from wavelength_serverless_lib.dal.pynamo_models.util import QueryResult

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


def random_key():
    return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])


def item_mock(template: dict):
    result = MagicMock()
    for key in template:
        setattr(result, key, template[key])
    result.hash_id = random_key()
    result.range_id = random_key()
    result._get_keys = MagicMock(return_value=[result.hash_id, result.range_id])
    result.toJSON = MagicMock(return_value=template)
    return result


def query_mock():
    result = MagicMock()
    result.last_evaluated_key = None
    result.total_count = MagicMock(return_value=5)
    result.__iter__.return_value = [
        item_mock({
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }),
        item_mock({
            'table_state': DalConfig.table_state_modified,
            'kind': 'abcd'
        })
        ,
        item_mock({
            'table_state': DalConfig.table_state_deleted,
            'kind': 'abcd'
        }),
        item_mock({
            'table_state': DalConfig.table_state_modified,
            'kind': 'wxyz'
        })
    ]
    return MagicMock(return_value=result)


get_mock_result = item_mock({
    'table_state': DalConfig.table_state_new,
    'kind': 'abcd'
})
get_mock = MagicMock(return_value=get_mock_result)


@patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.__init__', MagicMock(return_value=None))
@patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.query', query_mock())
@patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.get', get_mock)
@patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.save', MagicMock(return_value=None))
@patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.update', MagicMock(return_value=None))
@patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.delete', MagicMock(return_value=None))
class TestPynamoCacheModel(unittest.TestCase):

    def test_init(self):
        model = CachingPynamoModel({})
        self.assertIsInstance(model.cache, TTLCache)

    def test_query_cache(self):
        # TODO Stop this test from flapping.
        get_mock.reset_mock()
        model = CachingPynamoModel({})
        CachingPynamoModel.cache = TTLCache(maxsize=128, ttl=0.001)
        result = model.query('1234')

        self.assertIsInstance(result, QueryResult)
        self.assertEqual(len(result.items), 4)
        item = model.get(result.items[0].hash_id, result.items[0].range_id)
        self.assertEqual(item.kind, 'abcd')
        # Should have pulled from cache
        get_mock.assert_not_called()
        self.assertEqual(len(model.cache), 4)
        sleep(.05)
        self.assertEqual(len(model.cache), 0)

        item = model.get(result.items[0].hash_id, result.items[0].range_id)
        self.assertEqual(item, get_mock_result)
        get_mock.assert_called_once()

    def test_get_cache(self):
        get_mock.reset_mock()
        model = CachingPynamoModel({})
        CachingPynamoModel.cache = TTLCache(maxsize=128, ttl=0.001)

        item = model.get(get_mock_result.hash_id, get_mock_result.range_id)

        self.assertEqual(item.kind, 'abcd')

        get_mock.assert_called_once()

        item = model.get(get_mock_result.hash_id, get_mock_result.range_id)

        self.assertEqual(item, get_mock_result)

        # Should have pulled from cache
        get_mock.assert_called_once()

        sleep(.005)

        model.get(get_mock_result.hash_id, get_mock_result.range_id)

        self.assertEqual(get_mock.call_count, 2)

    def test_save_cache(self):
        get_mock.reset_mock()
        model = CachingPynamoModel({})
        CachingPynamoModel.cache = TTLCache(maxsize=128, ttl=0.001)

        key = [random_key(), random_key()]

        model._get_keys = MagicMock(return_value=key)

        model.save()

        item = model.get(*key)

        self.assertEqual(item, model)

        get_mock.assert_not_called()

    def test_update_cache(self):
        get_mock.reset_mock()
        model = CachingPynamoModel({})
        CachingPynamoModel.cache = TTLCache(maxsize=128, ttl=0.001)

        key = [random_key(), random_key()]

        model._get_keys = MagicMock(return_value=key)

        model.update(actions=[])

        item = model.get(*key)

        self.assertEqual(item, model)

        get_mock.assert_not_called()

    def test_delete_cache(self):
        get_mock.reset_mock()
        model = CachingPynamoModel({})
        CachingPynamoModel.cache = TTLCache(maxsize=128, ttl=0.001)

        key = [random_key(), random_key()]

        model._get_keys = MagicMock(return_value=key)

        model.save()

        item = model.get(*key)

        self.assertEqual(item, model)

        get_mock.assert_not_called()

        model.delete()

        item = model.get(*key)

        self.assertEqual(item, get_mock_result)

        get_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
