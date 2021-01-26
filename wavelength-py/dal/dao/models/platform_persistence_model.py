"""
Observable Data Model
"""
from copy import copy
from typing import List, Any, Dict, Optional, Type

from pynamodb.models import Model as PynamoModel
from schematics.types import StringType, IntType

from wavelength_serverless_lib.dal.dal_config import DalConfig
from wavelength_serverless_lib.dal.dao.models.observable_persistence_model import ObservablePersistenceModel
from wavelength_serverless_lib.model.model_base import BaseModel


class BasePersistenceModel(ObservablePersistenceModel):
    """
    Self-persisting base model
    """
    created_at = IntType(default=0)
    modified_at = IntType(default=0)
    version = IntType(default=1)
    table_state = StringType(default=DalConfig.table_state_new)

    def __init__(self, source_model: dict, protected_fields=None, column_mapping: dict = None, **kwargs):

        super().__init__(source_model, protected_fields=protected_fields, **kwargs)
        self._column_mapping = column_mapping if column_mapping else {}
        self.system_fields = ['created_at', 'modified_at', 'version', 'table_state']

    def get_mapped_changes(self):
        """
        Converts the change set to represent underlying schema
        :return: dict
        """
        changes = self._get_changes()
        if not self._column_mapping:
            return changes

        return self._resolve_mapped_changes(changes)

    def _resolve_mapped_changes(self, source: Dict[str, Any]) -> Dict[str, Any]:
        result = {}  # type: Dict[str, Any]
        for key in source:
            result.update(**self._resolve_mapped_change(key, source))
        return result

    def _resolve_mapped_change(self, key: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        mapped_key = self._resolve_mapped_key(key)
        return {mapped_key: changes[key]}

    def _resolve_mapped_key(self, key: str) -> str:
        mapping = self._column_mapping.get(key)
        if mapping:
            mapped_key = mapping() if callable(mapping) else mapping
            return mapped_key
        return key

    def build(self, source_model: Dict[str, Any]) -> 'BasePersistenceModel':
        """
        Creates an instance of this model
        :param source_model:
        :return:
        """
        result = copy(self)
        result.from_json(self._resolve_mapped_changes(source_model))
        return result

    def push(self, source_model: Dict[str, Any]) -> None:
        """
        In-place swap of attribute values based on source model
        :param source_model: dict
        :return: None
        """
        self.from_json(self._resolve_mapped_changes(source_model))


class PynamoPersistenceModel(BasePersistenceModel):
    """
    Base model for developing domain models with a DynamoDB back end
    """

    def __init__(self, source_model: Dict[str, Any], db_model: Type[PynamoModel], **kwargs):
        super().__init__(source_model, **kwargs)
        self.db_model = db_model
        self.db_hash_key = None
        self.db_range_key = None
        self.non_key_db_attributes: List = []
        self._discover_db_attributes()

    def get_key(self) -> List[str]:
        """
        Gets keys for keyed model
        :return: list
        """
        result: List[str] = []
        if self.db_hash_key:
            result.append(getattr(self, self._resolve_mapped_key(self.db_hash_key)))

        if self.db_range_key:
            result.append(getattr(self, self._resolve_mapped_key(self.db_range_key)))

        return result

    def get_creation_actions(self) -> Dict[str, Any]:
        """
        Builds a dict representing non-key attributes from the db_model
         mapped to non-None values from the model
        :return: dict
        """
        result: Dict[str, Any] = {}
        for key in self.non_key_db_attributes:
            action = self._get_creation_action(key)
            if action:
                result.update(**action)

        return result

    def _get_creation_action(self, key: str) -> Optional[Dict[str, Any]]:
        if hasattr(self, key):
            value = getattr(self, key)
            if value is not None and isinstance(value, BaseModel):
                return {key: value.to_dict()}
            if value is not None:
                return {key: value}
        return None

    def _discover_db_attributes(self) -> None:
        """
        Loop through the Pynamodb attributes member and discover available fields
        :return: None
        """
        for prop, val in getattr(self.db_model, '_attributes').items():

            if val.is_hash_key:
                self.db_hash_key = prop
            elif val.is_range_key:
                self.db_range_key = prop
            else:
                self.non_key_db_attributes.append(prop)
