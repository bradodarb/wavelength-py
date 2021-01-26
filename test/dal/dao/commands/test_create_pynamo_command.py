import logging
import unittest

from botocore.exceptions import ClientError
from mock import MagicMock
from pynamodb.exceptions import PynamoDBConnectionError

from wavelength_py.dal.dao.commands.create_pynamo_command import PynamoCreateCommand
from wavelength_py.errors.exceptions import Base5xxException, Base409Exception, Base422Exception
from test.dal.dao.commands.test_pynamo_command import get_persitence_model_mock

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestPynamoCreateCommand(unittest.TestCase):

    def test_execute(self):
        mock_parent = get_persitence_model_mock({}, {})

        command = PynamoCreateCommand(mock_parent)

        command()
        mock_parent.db_model.assert_called_once()
        mock_parent.db_model.save.assert_called_once()

    def test_execute_raises_500(self):
        mock_parent = get_persitence_model_mock({}, {})

        mock_parent.db_model.save = MagicMock(side_effect=PynamoDBConnectionError())
        command = PynamoCreateCommand(mock_parent)

        with self.assertRaises(Base5xxException) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Not Available')

    def test_execute_raises_422(self):
        mock_parent = get_persitence_model_mock({}, {})

        error = PynamoDBConnectionError(cause=ClientError({
            'Error': {
                'Code': 'ValidationException',
                'Message': 'Bad Datas dude'
            }
        }, 'Dynamo Get_Item'))
        mock_parent.db_model.save = MagicMock(side_effect=error)

        command = PynamoCreateCommand(mock_parent)

        with self.assertRaises(Base422Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Bad Datas dude')

    def test_execute_raises_409(self):
        mock_parent = get_persitence_model_mock({}, {})

        error = PynamoDBConnectionError(cause=ClientError({
            'Error': {
                'Code': 'ConditionalCheckFailedException',
                'Message': 'Usurper was here'
            }
        }, 'Dynamo Get_Item'))
        mock_parent.db_model.save = MagicMock(side_effect=error)

        command = PynamoCreateCommand(mock_parent)

        with self.assertRaises(Base409Exception) as err:
            command._execute()

        self.assertEqual(str(err.exception), 'Usurper was here')


if __name__ == '__main__':
    unittest.main()
