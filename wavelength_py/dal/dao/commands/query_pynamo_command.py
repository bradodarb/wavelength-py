"""
Module to support updating a single record
"""
from typing import List, Callable, Optional, Iterator

from cachetools import cached, TTLCache
from pynamodb.models import Model as PynamoModel

from wavelength_py.config import CONFIG
from wavelength_py.dal.dal_config import DalConfig
from wavelength_py.dal.dao.commands.post_filter_pynamo_command import PostFilteredPynamoCommand, filter_deleted_items
from wavelength_py.dal.dao.commands.pynamo_command import FilterModel
from wavelength_py.dal.dao.commands.pynamo_query_args import PynamoQueryArguments
from wavelength_py.dal.dao.models.platform_persistence_model import PynamoPersistenceModel
from wavelength_py.dal.dynamodb.util import decode_start_token
from wavelength_py.dal.pynamo_models.util import pynamo_read_handler


class PynamoQueryResult:
    """
    Class to take a raw query result (ResultIterator) and form a typed response for encoded
    start token and domain model
    """

    def __init__(self, query_result: List[Optional[PynamoModel]],
                 parent_model: PynamoPersistenceModel, start_token: str = None) -> None:
        """
        Converts a result set from a pynamoDB query and converts it a collection of domain models
        :param query_result: List[PynamoModel]
        :param parent_model: PynamoPersistenceModel
        """
        self._start_token = start_token

        self._items = [parent_model.build(item.to_json()) for item in query_result]

    @property
    def start_token(self) -> Optional[str]:
        """
        Provides encoded start_token
        :return: str
        """
        return self._start_token

    @property
    def items(self) -> List[PynamoPersistenceModel]:
        """
        List of converted domain items
        :return: List[PynamoPersistenceModel]
        """
        return self._items


class PynamoQueryCommand(PostFilteredPynamoCommand):
    """
    This class encapsulates the updating of a versioned record
    """

    def __init__(self, parent_model: PynamoPersistenceModel,
                 pre_filters: List[FilterModel] = None,
                 post_filter: Callable = filter_deleted_items):
        """
        :param parent_model: PynamoPersistenceModel
        :param pre_filters: pre_filters: List[FilterModel])
        """
        super().__init__(parent_model, post_filter)
        self._next_token = None
        # using `is not None` here so we can clear out the pre_filters with an empty list
        self._pre_filters = pre_filters if pre_filters is not None else [
            FilterModel('table_state', 'is_in', [DalConfig.table_state_new, DalConfig.table_state_modified])]

    @cached(TTLCache(maxsize=32, ttl=CONFIG.DATA_CACHE_TTL))
    def __call__(self, query: PynamoQueryArguments) -> PynamoQueryResult:
        """
        Builds the query object for subsequent execution and returns the result
        :param query: str
        :return: PynamoQueryCommand
        """
        query.append_filters(self._pre_filters)
        return self._execute_query(query)

    def _execute_query(self, query: PynamoQueryArguments) -> PynamoQueryResult:
        """
        Execute command interface
        :return: list[PynamoPersistenceModel]
        """
        query_result = self._gather_query(query)
        post_filter: Callable = self._post_filter

        if query.post_filter:
            self._post_filter = query.post_filter

        result = PynamoQueryResult([self._filter(item) for item in query_result.items if item], self._parent,
                                   self._next_token)

        self._post_filter = post_filter
        self._next_token = None
        return result

    @pynamo_read_handler
    def _gather_query(self, query: PynamoQueryArguments) -> Iterator[PynamoModel]:
        """
        Run query and cast results to domain objects
        :return: QueryResult
        """

        return self._parent.db_model.query(query.hash_key,
                                           index_name=query.index_name,
                                           range_key_condition=self._build_conditionals(query.range_key_filter),
                                           filter_condition=self._build_conditionals(query.filters),
                                           limit=query.limit,
                                           scan_index_forward=query.scan_index_forward,
                                           consistent_read=query.consistent_read,
                                           last_evaluated_key=decode_start_token(query.start_token))
