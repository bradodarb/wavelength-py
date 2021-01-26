"""
Module for supporting a hard delete on a pynamo item
"""
from wavelength_py.dal.dao.commands.pynamo_command import BasePynamoCommand
from wavelength_py.dal.pynamo_models.util import pynamo_write_handler
from wavelength_py.errors.exceptions import Base422Exception
from wavelength_py.model.util import get_posix_timestamp


class PynamoCreateCommand(BasePynamoCommand):
    """
    Creates a new record based on the parent model
    """

    def _execute(self):
        """
        Creates using retryable method
        :return: None
        """
        model = self._create_record()

        return self._parent.build(model.to_json())

    @pynamo_write_handler
    def _create_record(self):
        """
        Create record
        :return:None
        """
        try:
            now = get_posix_timestamp()
            self._parent.override_protected_field('created_at', now)
            self._parent.override_protected_field('modified_at', now)

            record = self._parent.db_model(*self._parent.get_key(),
                                           **self._parent.get_creation_actions())
            # TODO consider supporting conditions
            record.save()
            return record
        except ValueError as verr:
            raise Base422Exception('Model creation failed', reason=str(verr))

    def __call__(self):
        return self._execute()
