"""
Observable Data Model with CRUD OPs and DynamoDB back end
"""

from typing import Type

from pynamodb.models import Model as PynamoModel

from exos_serverless_lib.dal.dao.commands.create_pynamo_command import PynamoCreateCommand
from exos_serverless_lib.dal.dao.commands.get_by_key_pynamo_command import PynamoGetByIdCommand
from exos_serverless_lib.dal.dao.commands.query_pynamo_command import PynamoQueryCommand
from exos_serverless_lib.dal.dao.commands.soft_delete_pynamo_command import PynamoSoftDeleteCommand
from exos_serverless_lib.dal.dao.commands.update_pynamo_command import PynamoUpdateCommand
from exos_serverless_lib.dal.dao.models.platform_persistence_model import PynamoPersistenceModel


class PynamoCrudModel(PynamoPersistenceModel):
    """
    Base model for developing domain models with a DynamoDB back end
    """

    def __init__(self, source_model: dict, db_model: Type[PynamoModel], **kwargs):
        super().__init__(source_model, db_model, **kwargs)

        self.query = PynamoQueryCommand(self)
        self.create = PynamoCreateCommand(self)
        self.read = PynamoGetByIdCommand(self)
        self.update = PynamoUpdateCommand(self)
        self.delete = PynamoSoftDeleteCommand(self)

    def __repr__(self):
        return f'{type(self).__name__}({self.to_json()})'
