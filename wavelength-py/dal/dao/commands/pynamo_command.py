"""
Module for abstracting commands on a pynamo item
"""
from operator import and_, or_
from typing import Any, List, Callable, Dict

import simplejson as json
from pynamodb.expressions.condition import Comparison
from pynamodb.expressions.operand import Path as PynamoAction
from schematics.types import StringType, ListType, BaseType

from wavelength_serverless_lib.dal.dao.models.platform_persistence_model import PynamoPersistenceModel
from wavelength_serverless_lib.errors.exceptions import Base422Exception
from wavelength_serverless_lib.model.model_base import BaseModel

OPERATOR_LOOKUP = {
    'eq': '__eq__',
    'ne': '__ne__',
    'lt': '__lt__',
    'gt': '__gt__',
    'lte': '__le__',
    'gte': '__ge__',
    'begins_with': 'startswith',
    'between': 'between',
    'is_in': 'is_in',
    'contains': 'contains'
}


def always_pass(record):
    """
    Pass-through filter
    :param record:
    :return:
    """
    return record


class FilterModel(BaseModel):
    """
    Class to encapsulate a filter condition
    """
    model_attribute = StringType()
    operator = StringType()
    combinator = StringType(default='and', choices=['and', 'or'])
    parameters = ListType(BaseType())

    def __init__(self, model_attribute: str, operator: str, parameters: Any):
        """
        Build a filter operation from args
        :param model_attribute: str
        :param operator: str
        :param parameters: Any
        """
        super().__init__()
        self.model_attribute = model_attribute
        self.operator = operator
        self.parameters = parameters

    def __call__(self) -> dict:
        """
        Build and return DAL struct for creating filtered expressions
        primarily used for backwards-compatibility
        :return: dict
        """
        return {
            'key': self.model_attribute,
            'operator': self.operator,
            'combinator': self.combinator,
            'args': self.parameters
        }

    def __str__(self):
        return json.dumps(self())


class BasePynamoCommand:
    """
    Base Command Interface
    """

    def __init__(self, parent_model: PynamoPersistenceModel):
        """
        :param parent_model: PynamoPersistenceModel (domain model object)
        """
        self._parent = parent_model

    def _execute(self) -> Any:
        """
        Call the command and optionally return a result
        :return:
        """
        raise NotImplementedError('Must override this in a child command class')

    def _build_model_update_actions(self) -> Dict[str, PynamoAction]:
        """
        Takes a dict representing changes from the parent model and converts them to
        Pynamodb update actions
        :return: list[PynamoAction]
        :raise: Base422Exception if model doesn't contain requested attribute
        """
        result = {}
        changes = {k: v for k, v in self._parent.get_mapped_changes().items() if v is not None}
        keys = changes.keys()
        for key in keys:
            prop = getattr(self._parent.db_model, key, None)
            if prop is None:
                raise Base422Exception(f'Model has no property named "{key}""')
            val = changes[key]
            if isinstance(val, list):
                val.sort()
            result.update({key: prop.set(val)})
        return result

    def _build_conditionals(self, filters: List[FilterModel]) -> Comparison:
        """
        Parses a generic DSL (key, operator, args) and converts it to pynamodb Conditions(conditional)
        :param filters: List[FilterModel]
        :return: Comparison
        """
        conditions = None

        for filter_ in filters:
            combinator = or_ if filter_.combinator == 'or' else and_
            key = getattr(self._parent.db_model, filter_.model_attribute, None)
            self._validate_filter_key(filter_, key)
            condition_operator = getattr(key, OPERATOR_LOOKUP.get(filter_.operator, filter_.operator), None)
            self._validate_filter_operator(filter_, condition_operator)
            args = filter_.parameters
            result = self._build_conditional(condition_operator, args)
            conditions = combinator(conditions, result) if conditions is not None else result

        return conditions

    @classmethod
    def _validate_filter_key(cls, filter_model, key):
        if key:
            return
        msg = f'Model has no property named "{filter_model.model_attribute}"'
        raise Base422Exception(msg)

    @classmethod
    def _validate_filter_operator(cls, filter_model, operator):
        if operator:
            return
        msg = f'Attribute {filter_model.model_attribute} does not support the operator "{filter_model.operator}"'
        raise Base422Exception(msg)

    @classmethod
    def _build_conditional(cls, operator: Callable, args):
        if isinstance(args, list):
            return operator(*args)
        return operator(args)

    def __repr__(self):
        return f'{type(self).__name__}({self.__dict__})'

    def __str__(self):
        return json.dumps(self.__dict__)
