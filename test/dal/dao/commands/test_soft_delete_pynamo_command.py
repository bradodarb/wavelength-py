
import logging
import unittest

from mock import MagicMock, call

from wavelength_py.dal.dal_config import DalConfig
from wavelength_py.dal.dao.commands.soft_delete_pynamo_command import PynamoSoftDeleteCommand
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestPynamoSoftDeleteCommand(unittest.TestCase):

    def test_execute(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }

        model_mock = get_persitence_model_mock(template, template)

        model_mock.db_model.get = MagicMock(return_value=model_mock.db_model)

        result = command = PynamoSoftDeleteCommand(model_mock)
        command._post_filter = MagicMock(return_value=True)
        command()
        model_mock.db_model.get.assert_called_once()
        self.assertEqual(model_mock.override_protected_field.call_args_list[0],
                         call('table_state', DalConfig.table_state_deleted))
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
