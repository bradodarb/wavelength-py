import logging
import unittest

from mock import MagicMock, ANY

from wavelength_py.dal.dal_config import DalConfig
from wavelength_py.dal.dao.commands.pynamo_command import always_pass
from wavelength_py.dal.dao.commands.pynamo_query_args import PynamoQueryArguments
from wavelength_py.dal.dao.commands.query_pynamo_command import PynamoQueryCommand, PynamoQueryResult
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


def get_model_mock(json_dict=None):
    if not json_dict:
        json_dict = {
            'account_id': '12345',
            'range_id': 'abcde',
        }
    mock_db_model_instance = MagicMock()
    mock_db_model_instance.to_json = MagicMock(return_value=json_dict)

    return mock_db_model_instance


def build_pynamo_mock_query_interface(mock, instance):
    mock.return_value = instance
    mock_query_result = MagicMock()
    mock_query_result.items = [instance]
    mock_query_result.last_evaluated_key = None
    mock.query = MagicMock(return_value=mock_query_result)


class TestPynamoQueryCommand(unittest.TestCase):

    def test_pynamo_query_arguments(self):
        query_kwargs = {
            'index_name': 'test-index-name',
            'range_key_filter': ['filter1', 'filter2'],
            'filters': ['filter3', 'filter4'],
            'scan_index_forward': False,
            'limit': 30
        }

        pynamo_query_arguments = PynamoQueryArguments('test-hash-key', **query_kwargs)

        self.assertEqual(pynamo_query_arguments.hash_key, 'test-hash-key')
        self.assertEqual(pynamo_query_arguments.index_name, query_kwargs.get('index_name'))
        self.assertEqual(pynamo_query_arguments.range_key_filter, query_kwargs.get('range_key_filter', []))
        self.assertEqual(pynamo_query_arguments.filters, query_kwargs.get('filters', []))
        self.assertEqual(pynamo_query_arguments.scan_index_forward, query_kwargs.get('scan_index_forward', False))
        self.assertEqual(pynamo_query_arguments.limit, query_kwargs.get('limit', 30))
        self.assertEqual(pynamo_query_arguments._consistent_read, query_kwargs.get('consistent_read', False))

        self.assertEqual(pynamo_query_arguments.consistent_read, False)

        pynamo_query_arguments.consistent_read = True

        self.assertEqual(pynamo_query_arguments.consistent_read, True)

    def test_query_pynamo_command(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        build_pynamo_mock_query_interface(mock_parent.db_model, get_model_mock(template))

        command = PynamoQueryCommand(mock_parent, post_filter=always_pass)

        query_kwargs = {
            'index_name': 'test-index-name',
            'scan_index_forward': False,
            'limit': 30
        }
        query = PynamoQueryArguments('1234', **query_kwargs)

        result = command(query)

        self.assertIsInstance(result, PynamoQueryResult)
        self.assertEqual(len(result.items), 1)

        command._parent.db_model.query.assert_called_with(
            '1234',
            index_name='test-index-name',
            range_key_condition=ANY,
            filter_condition=ANY,
            limit=30,
            scan_index_forward=False,
            consistent_read=False,
            last_evaluated_key=None)

        query_kwargs = {
            'index_name': 'test-index-name',
            'scan_index_forward': False,
            'limit': 30,
            'consistent_read': True
        }

        query = PynamoQueryArguments('1234', **query_kwargs)

        result = command(query)

        self.assertIsInstance(result, PynamoQueryResult)
        self.assertEqual(len(result.items), 1)

        command._parent.db_model.query.assert_called_with(
            '1234',
            index_name='test-index-name',
            range_key_condition=ANY,
            filter_condition=ANY,
            limit=30,
            scan_index_forward=False,
            consistent_read=True,
            last_evaluated_key=None)


if __name__ == '__main__':
    unittest.main()
