import logging
import unittest

from mock import MagicMock, PropertyMock, patch

from wavelength_serverless_lib.dal.dal_config import DalConfig
from wavelength_serverless_lib.dal.dao.commands.pynamo_command import BasePynamoCommand, FilterModel
from wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model import CachingPynamoModel
from wavelength_serverless_lib.errors.exceptions import Base422Exception

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class CommandTestMock(BasePynamoCommand):
    """ Fake class """
    pass


class CommandTest2Mock(BasePynamoCommand):
    """ Fake class with execute """

    def _execute(self):
        return True


def always_filter_out(_record):
    """
    Pass-through filter
    :param _record:
    :return:
    """
    return None


def get_persitence_model_mock(model_template: dict, db_template: dict, changes: dict = None):
    result = MagicMock()
    result.db_model = MagicMock()
    result.get_mapped_changes = MagicMock(return_value=changes if changes else model_template)
    for key in model_template:
        setattr(result, key, model_template[key])

    for key in db_template:
        prop = PropertyMock(return_value=db_template[key])
        prop.set = MagicMock()
        setattr(result.db_model, key, prop)

    result.db_model.return_value = result.db_model
    return result


class TestPynamoCommand(unittest.TestCase):

    def test_filter_model(self):
        model = FilterModel('my_key', 'my_operator', 'my_params')

        model_dict = model()

        self.assertEqual(model.model_attribute, model_dict['key'])
        self.assertEqual(model.operator, model_dict['operator'])
        self.assertEqual(model.parameters, model_dict['args'])

    def test_base_command_requires_subclassing_to_execute(self):
        with self.assertRaises(NotImplementedError) as err:
            command = CommandTestMock(MagicMock())
            command._execute()
        self.assertEqual(str(err.exception), 'Must override this in a child command class')

        command = CommandTest2Mock(MagicMock())
        self.assertTrue(command._execute())

    def test_builds_model_update_actions(self):
        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }
        mock_parent = get_persitence_model_mock(template, template)
        command = CommandTest2Mock(mock_parent)

        changes = command._build_model_update_actions()
        self.assertIsNotNone(changes)
        self.assertEqual(len(changes), 2)

        mock_parent.db_model.table_state.set.assert_called_once()
        mock_parent.db_model.kind.set.assert_called_once()

    def test_builds_conditionals(self):
        states = ['s1', 's2']
        filters = [FilterModel('table_state', 'my_operator', states),
                   FilterModel('kind', 'other_operator', 'my_param')]

        template = {
            'table_state': DalConfig.table_state_new,
            'kind': 'abcd'
        }

        mock_parent = get_persitence_model_mock(template, template)
        command = CommandTest2Mock(mock_parent)

        conditions = command._build_conditionals(filters)
        self.assertIsNotNone(conditions)

        mock_parent.db_model.table_state.my_operator.assert_called_once()
        mock_parent.db_model.table_state.my_operator.assert_called_with(*states)

        mock_parent.db_model.kind.other_operator.assert_called_once()
        mock_parent.db_model.kind.other_operator.assert_called_with('my_param')

    @patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.__init__', MagicMock(return_value=None))
    def test_builds_conditional_prop_exeption(self):
        model = MagicMock()
        model.db_model = CachingPynamoModel({})

        command = CommandTest2Mock(model)
        filters = [FilterModel('kind', 'my_operator', 'my_param')]

        with self.assertRaises(Base422Exception) as err:
            conditions = command._build_conditionals(filters)
        self.assertEqual(str(err.exception), 'Model has no property named "kind"')

    @patch('wavelength_serverless_lib.dal.pynamo_models.cachable_pynamo_model.PynamoModel.__init__', MagicMock(return_value=None))
    def test_builds_conditional_operator_exeption(self):
        model = MagicMock()
        model.db_model = CachingPynamoModel({})
        setattr(model.db_model, 'kind', {'prop': 'no operators'})
        command = CommandTest2Mock(model)
        filters = [FilterModel('kind', 'my_operator', 'my_param')]

        with self.assertRaises(Base422Exception) as err:
            conditions = command._build_conditionals(filters)
        self.assertEqual(str(err.exception), 'Attribute kind does not support the operator "my_operator"')

    if __name__ == '__main__':
        unittest.main()
