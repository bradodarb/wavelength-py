import logging
import unittest

from botocore.exceptions import ClientError
from mock import MagicMock
from pynamodb.exceptions import DoesNotExist, PynamoDBConnectionError

from exos_serverless_lib.dal.dal_config import DalConfig
from exos_serverless_lib.dal.dao.commands.base_update_pynamo_command import BaseUpdatePynamoCommand
from exos_serverless_lib.errors.exceptions import Base422Exception, Base404Exception, Base409Exception, Base5xxException
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock, always_filter_out

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestPostFilterPynamoCommand(unittest.TestCase):

    def test_base_update_pynamo_command_raises_404(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent._get_keys()

        mock_parent.db_model.get = MagicMock(side_effect=DoesNotExist('No Datas'))

        command = BaseUpdatePynamoCommand(mock_parent, post_filter=always_filter_out)

        with self.assertRaises(Base404Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Model does not exist')

    def test_base_update_pynamo_command_raises_422(self):
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

        command = BaseUpdatePynamoCommand(mock_parent, post_filter=always_filter_out)

        with self.assertRaises(Base422Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Bad Datas dude')

    def test_base_update_pynamo_command_raises_409(self):
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

        command = BaseUpdatePynamoCommand(mock_parent, post_filter=always_filter_out)

        with self.assertRaises(Base409Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Usurper was here')

    def test_base_update_pynamo_command_raises_500(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        mock_parent._get_keys()

        mock_parent.db_model.get = MagicMock(side_effect=PynamoDBConnectionError())

        command = BaseUpdatePynamoCommand(mock_parent)

        with self.assertRaises(Base5xxException) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Not Available')

    if __name__ == '__main__':
        unittest.main()
