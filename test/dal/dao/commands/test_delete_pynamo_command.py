import logging
import unittest

from mock import MagicMock

from wavelength_serverless_lib.dal.dao.commands.delete_pynamo_command import PynamoDeleteCommand
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestPynamoDeleteCommand(unittest.TestCase):

    def test_execute(self):
        model_mock = get_persitence_model_mock({}, {})
        model_mock.db_model.delete = MagicMock()
        model_mock.db_model.get = MagicMock(return_value=model_mock.db_model)
        command = PynamoDeleteCommand(model_mock)

        command()
        model_mock.db_model.get.assert_called_once()
        model_mock.db_model.delete.assert_called_once()


if __name__ == '__main__':
    unittest.main()
