import logging
import unittest

from mock import patch, MagicMock
from schematics.types import StringType

from wavelength_serverless_lib.dal.dao.models.observable_persistence_model import ObservablePersistenceModel
from wavelength_serverless_lib.dal.dao.models.pynamo_crud_model import PynamoCrudModel

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class ModelTestMock(ObservablePersistenceModel):
    """
    Self-persisting base model
    """
    account_id = StringType()
    kind = StringType()


class TestPynamoCrudModel(unittest.TestCase):

    @patch('wavelength_serverless_lib.dal.dao.models.pynamo_crud_model.PynamoCreateCommand')
    @patch('wavelength_serverless_lib.dal.dao.models.pynamo_crud_model.PynamoGetByIdCommand')
    @patch('wavelength_serverless_lib.dal.dao.models.pynamo_crud_model.PynamoQueryCommand')
    @patch('wavelength_serverless_lib.dal.dao.models.pynamo_crud_model.PynamoSoftDeleteCommand')
    @patch('wavelength_serverless_lib.dal.dao.models.pynamo_crud_model.PynamoUpdateCommand')
    def test_init(self, mock_PynamoCreateCommand, mock_PynamoGetByIdCommand, mock_PynamoQueryCommand,
                  mock_PynamoSoftDeleteCommand, mock_PynamoUpdateCommand):
        model = PynamoCrudModel({}, MagicMock())
        model.create()
        mock_PynamoCreateCommand.assert_called_once()
        model.read()
        mock_PynamoGetByIdCommand.assert_called_once()
        model.update()
        mock_PynamoUpdateCommand.assert_called_once()
        model.delete()
        mock_PynamoSoftDeleteCommand.assert_called_once()
        model.query(MagicMock())
        mock_PynamoQueryCommand.assert_called_once()


if __name__ == '__main__':
    unittest.main()
