"""
Base pynamo command for gathering a single record and filtering it on the client side
"""
from typing import Callable, Optional, List, Union

from pynamodb.exceptions import DoesNotExist
from pynamodb.models import Model as PynamoModel

from wavelength_serverless_lib.dal.dal_config import DalConfig
from wavelength_serverless_lib.dal.dao.commands.pynamo_command import BasePynamoCommand, always_pass
from wavelength_serverless_lib.dal.dao.models.platform_persistence_model import PynamoPersistenceModel
from wavelength_serverless_lib.dal.pynamo_models.util import pynamo_read_handler
from wavelength_serverless_lib.errors.exceptions import Base404Exception


class PostFilteredPynamoCommand(BasePynamoCommand):
    """
    Base Pynamo Command with post-operation filtering
    """

    def __init__(self, parent_model: PynamoPersistenceModel, post_filter: Callable = always_pass):
        """

        :param parent_model: PynamoPersistenceModel (domain model object)
        :param post_filter: callable->bool function to run retrieved items against
        """
        super().__init__(parent_model)
        self._post_filter: Callable = post_filter

    def _execute(self) -> Union[List[PynamoPersistenceModel], PynamoPersistenceModel]:
        """
        Run the command
        :return:Union[List[PynamoPersistenceModel],PynamoPersistenceModel]
        """
        return self._filter(self._gather(self._get_key()))

    def _get_key(self) -> List[str]:
        return self._parent.get_key()

    @pynamo_read_handler
    def _gather(self, key=None) -> Optional[PynamoModel]:
        """
        Pulls the most recent model from DB based on the parent model's keys
        :return: PynamoModel
        """
        try:
            if not key:
                key = self._parent.get_key()
            item = self._parent.db_model.get(*key, consistent_read=True)
            return item
        except DoesNotExist as err:
            raise Base404Exception('Model does not exist', object_id=key) from err

    def _filter(self, item: PynamoModel) -> Optional[PynamoModel]:
        """
        Perform post-result filtering
        :param item: PynamoModel
        :return: all items that yield a 'truthy' result from the _post_filter
        """

        if self._post_filter(item):
            return item
        return None


def filter_deleted_items(record) -> bool:
    """
    filter_item is a method that handles the filtering of items. It
    raises an exception depending on the state of the object defined
    in the function implementation.
    @return: True
    :raise Base404Exception if model is already deleted
    """
    if hasattr(record, 'table_state') and record.table_state == DalConfig.table_state_deleted:
        raise Base404Exception(
            'Model does not exist', object_id=record.to_json())
    return True
