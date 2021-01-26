"""
Module to support loading a single record by key
"""
from typing import Any

from wavelength_serverless_lib.dal.dao.commands.post_filter_pynamo_command import filter_deleted_items, PostFilteredPynamoCommand
from wavelength_serverless_lib.dal.dao.models.platform_persistence_model import PynamoPersistenceModel


class PynamoGetByIdCommand(PostFilteredPynamoCommand):
    """
    This class encapsulates the updating of a versioned record
    """

    def __init__(self, parent_model: PynamoPersistenceModel, **kwargs):
        """

        :param parent_model: PynamoPersistenceModel (domain model object)
        :param post_filter: callable->bool function to run retrieved items against
        """
        filter_function = kwargs.get('post_filter', filter_deleted_items)

        super().__init__(parent_model, filter_function)
        self.keys = None

    def _execute(self) -> Any:
        """
        Run the command
        :return:Union[List[PynamoPersistenceModel],PynamoPersistenceModel]
        """
        result = super()._execute()
        self.keys = None

        return self._parent.build(result.to_json())

    def _get_key(self):
        return self.keys if self.keys else self._parent.get_key()

    def __call__(self, *keys):
        self.keys = keys
        return self._execute()
