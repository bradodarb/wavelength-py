"""
Module supporting soft delete behavior with a DynamoDB backend
"""
from typing import Dict

from pynamodb.expressions.operand import Path as PynamoAction

from wavelength_serverless_lib.dal.dal_config import DalConfig
from wavelength_serverless_lib.dal.dao.commands.base_update_pynamo_command import BaseUpdatePynamoCommand
from wavelength_serverless_lib.dal.dao.commands.post_filter_pynamo_command import filter_deleted_items
from wavelength_serverless_lib.dal.dao.models.platform_persistence_model import PynamoPersistenceModel


class PynamoSoftDeleteCommand(BaseUpdatePynamoCommand):
    """
    Class to encapsulate performing a soft delete command
    """

    def __init__(self, parent_model: PynamoPersistenceModel):
        super().__init__(parent_model, filter_deleted_items)

    def _execute(self):
        self._parent.override_protected_field('table_state', DalConfig.table_state_deleted)
        return super()._execute()

    def _build_model_update_actions(self) -> Dict[str, PynamoAction]:
        """
        Override to set table state == deleted
        :return: dict
        """

        return {
            **super()._build_model_update_actions(),
            **{
                'table_state': self._parent.db_model.table_state.set(DalConfig.table_state_deleted),
            }}

    def __call__(self):
        return self._execute()
