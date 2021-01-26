"""
Base update command and utils
"""
from typing import Any

from pynamodb.models import Model as PynamoModel

from wavelength_serverless_lib.dal.dal_config import DalConfig
from wavelength_serverless_lib.dal.dao.commands.post_filter_pynamo_command import PostFilteredPynamoCommand
from wavelength_serverless_lib.dal.pynamo_models.util import pynamo_write_handler
from wavelength_serverless_lib.errors.exceptions import Base404Exception
from wavelength_serverless_lib.model.util import get_posix_timestamp


class BaseUpdatePynamoCommand(PostFilteredPynamoCommand):
    """
    Base functionality for updating a pynamo record
    """

    def _execute(self) -> Any:
        """
        Run the command
        :return:Union[List[PynamoPersistenceModel],PynamoPersistenceModel]
        """
        result = super()._execute()
        if result is None:
            raise Base404Exception(
                'Model does not exist', 'Unable to perform update on None')
        return self._update_record(result)

    @pynamo_write_handler
    def _update_record(self, record: PynamoModel):
        """
        Updates the validated record based on the parent model's change set
        :param record: PynamoModel
        :return: None
        """
        next_version = record.version + 1
        model_actions = self._build_model_update_actions()
        default_actions = {
            'table_state': self._parent.db_model.table_state.set(DalConfig.table_state_modified),
        }
        system_actions = {
            'version': self._parent.db_model.version.set(next_version),
            'modified_at': self._parent.db_model.modified_at.set(get_posix_timestamp())
        }
        actions = list({**default_actions, **model_actions, **system_actions}.values())  # allow overrides

        record.update(
            actions=actions,
            condition=(self._parent.db_model.version == record.version)
        )
        self._parent.override_protected_field('version', next_version)
        self._parent.flush_changes()
