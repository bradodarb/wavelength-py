import logging
import unittest

from mock import MagicMock

from exos_serverless_lib.dal.dal_config import DalConfig
from exos_serverless_lib.dal.dao.commands.get_by_key_pynamo_command import PynamoGetByIdCommand
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestPynamoGetByIdCommand(unittest.TestCase):

    def test_execute(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }

        model_mock = get_persitence_model_mock(template, template)

        model_mock.db_model.get = MagicMock(return_value=model_mock.db_model)

        result = command = PynamoGetByIdCommand(model_mock)
        command._post_filter = MagicMock(return_value=True)
        command()
        model_mock.db_model.get.assert_called_once()
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
