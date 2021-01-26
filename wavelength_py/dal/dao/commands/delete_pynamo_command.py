"""
Module for supporting a hard delete on a pynamo item
"""
from typing import Any

from wavelength_py.dal.dao.commands.post_filter_pynamo_command import PostFilteredPynamoCommand


class PynamoDeleteCommand(PostFilteredPynamoCommand):
    """
    Performs a permanent delete on an an item
    """

    def _execute(self) -> Any:
        """
        Run the command
        :return:Union[List[PynamoPersistenceModel],PynamoPersistenceModel]
        """
        result = super()._execute()
        return result.delete()

    def __call__(self):
        return self._execute()
