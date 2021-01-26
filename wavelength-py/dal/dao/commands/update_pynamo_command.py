"""
Module to support updating a single record
"""

from wavelength_serverless_lib.dal.dao.commands.base_update_pynamo_command import BaseUpdatePynamoCommand
from wavelength_serverless_lib.dal.dao.commands.post_filter_pynamo_command import filter_deleted_items
from wavelength_serverless_lib.dal.dao.models.platform_persistence_model import PynamoPersistenceModel


class PynamoUpdateCommand(BaseUpdatePynamoCommand):
    """
    This class encapsulates the updating of a versioned record
    """

    def __init__(self, parent_model: PynamoPersistenceModel):
        super().__init__(parent_model, filter_deleted_items)

    def __call__(self):
        return self._execute()
