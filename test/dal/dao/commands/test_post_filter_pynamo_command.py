import logging
import unittest

from botocore.exceptions import ClientError
from mock import MagicMock
from pynamodb.exceptions import DoesNotExist, PynamoDBConnectionError

from wavelength_py.dal.dal_config import DalConfig
from wavelength_py.dal.dao.commands.post_filter_pynamo_command import PostFilteredPynamoCommand, filter_deleted_items
from wavelength_py.errors.exceptions import Base422Exception, Base404Exception, Base409Exception, Base5xxException
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock, always_filter_out

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestPostFilterPynamoCommand(unittest.TestCase):

    def test_post_filter_pynamo_command(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent.db_model.get = MagicMock(return_value=template)

        command = PostFilteredPynamoCommand(mock_parent)

        result = command._execute()

        self.assertEqual(template, result)

    def test_post_filter_pynamo_command_filters(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent.db_model.get = MagicMock(return_value=template)

        command = PostFilteredPynamoCommand(mock_parent, post_filter=always_filter_out)

        result = command._execute()

        self.assertIsNone(result)

    def test_post_filter_pynamo_command_raises_404(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent._get_keys()

        mock_parent.db_model.get = MagicMock(side_effect=DoesNotExist('No Datas'))

        command = PostFilteredPynamoCommand(mock_parent, post_filter=always_filter_out)

        with self.assertRaises(Base404Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Model does not exist')

    def test_post_filter_pynamo_command_raises_422(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent._get_keys()

        error = PynamoDBConnectionError(cause=ClientError({
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Bad Datas dude'
            }
        }, 'Dynamo Get_Item'))
        mock_parent.db_model.get = MagicMock(side_effect=error)

        command = PostFilteredPynamoCommand(mock_parent, post_filter=always_filter_out)

        with self.assertRaises(Base422Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Bad Datas dude')

    def test_post_filter_pynamo_command_raises_409(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent._get_keys()

        error = PynamoDBConnectionError(cause=ClientError({
            'Error': {
                'Code': 'ConditionalCheckFailedException',
                'Message': 'Usurper was here'
            }
        }, 'Dynamo Get_Item'))
        mock_parent.db_model.get = MagicMock(side_effect=error)

        command = PostFilteredPynamoCommand(mock_parent, post_filter=always_filter_out)

        with self.assertRaises(Base409Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Usurper was here')

    def test_post_filter_pynamo_command_raises_500(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent._get_keys()

        mock_parent.db_model.get = MagicMock(side_effect=PynamoDBConnectionError())

        command = PostFilteredPynamoCommand(mock_parent)

        with self.assertRaises(Base5xxException) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Not Available')

    def test_filter_deleted_items(self):
        record_mock = MagicMock()
        record_mock.table_state = DalConfig.table_state_deleted

        with self.assertRaises(Base404Exception) as err:
            filter_deleted_items(record_mock)

        self.assertEqual(str(err.exception), 'Model does not exist')

    if __name__ == '__main__':
        unittest.main()
