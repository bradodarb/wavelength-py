"""
Observable Data Model
"""
from typing import List, Any, Dict

from wavelength_py.model.model_base import BaseModel


class ObservablePersistenceModel(BaseModel):
    """
    Self-persisting base model
    """

    def __init__(self, source_model: dict = None, protected_fields=None,
                 forced_change_fields: List[str] = None, **kwargs):
        """
        Creates an instance of a change tracking persistence model
        :param source_model: dict to hydrate model from
        :param dao: DaoBase to execute commands against
        :param protected_fields: fields to prevent marking as 'dirty'
        """
        super().__init__(raw_data=source_model, **kwargs)
        self._protected_fields = protected_fields if protected_fields else []
        self._changes = {}  # type: Dict[str, Any]
        self._forced_change_fields = forced_change_fields if forced_change_fields else []

    @property
    def is_dirty(self) -> bool:
        """
        If non-protected changes have been set on this model wil return True
        :return: bool
        """
        return bool(self._changes)

    def _get_changes(self) -> Dict[str, Any]:
        forced_changes = {}  # type: Dict[str, Any]
        for field in self._forced_change_fields:
            forced_changes.update(**{field: getattr(self, field)})
        return {**self._changes, **forced_changes}

    def flush_changes(self) -> 'ObservablePersistenceModel':
        """
        Clears the change set and un flags the model as being dirty
        :return: self
        """
        self._changes.clear()
        return self

    def __setattr__(self, key, value):
        # _fields is attached to the class during the schematics model instance creation process
        # pylint: disable=no-member
        if key in self._fields:
            if key in self._protected_fields:
                return
            self._changes.update(**{key: value})
        super().__setattr__(key, value)

    def override_protected_field(self, field_name, value) -> None:
        """
        Temporarily removes protected field to set value internally
        :param field_name: attribute to set
        :param value: new value
        :return: None
        """

        if not hasattr(self, field_name):
            raise AttributeError(f'No field named {field_name} on current model')
        if not isinstance(self, ObservablePersistenceModel):
            raise TypeError('_override_protected_field method should only be called from a model')
        if field_name not in self._protected_fields:
            setattr(self, field_name, value)
            return
        self._protected_fields.remove(field_name)
        setattr(self, field_name, value)
        self._protected_fields.append(field_name)
