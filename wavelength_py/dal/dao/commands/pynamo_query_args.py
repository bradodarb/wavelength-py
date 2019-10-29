"""
Query args for gathering a single record and filtering it on the client side
"""
from typing import List, Any, Callable

from exos_serverless_lib.dal.dao.commands.post_filter_pynamo_command import filter_deleted_items
from exos_serverless_lib.dal.dao.commands.pynamo_command import FilterModel
from exos_serverless_lib.dal.dynamodb.util import decode_start_token


class PynamoQueryArguments:
    """
    Class to represent *args and **kwargs for a query method
    """

    def __init__(self, hash_key: str, **kwargs):
        """
        Represents input to the query command
        :param hash_key: str
        :param range_key_filter: str
        :param filters: List[FilterModel]
        :param scan_index_forward: bool
        :param limit: int
        :param start_token: str
        :param consistent_read: str
        """
        self.hash_key = hash_key
        self.index_name = kwargs.get('index_name')
        self.range_key_filter = kwargs.get('range_key_filter', [])
        self.filters = kwargs.get('filters', [])
        self.scan_index_forward = kwargs.get('scan_index_forward', False)
        self.limit = kwargs.get('limit', 30)
        start_token = kwargs.get('start_token')
        self.start_token = decode_start_token(start_token) if start_token else None
        self._consistent_read = kwargs.get('consistent_read', False)
        self._frozen = kwargs.get('frozen', False)
        self._post_filter: Callable = kwargs.get('post_filter', filter_deleted_items)

    @property
    def consistent_read(self) -> bool:
        """
        Property to enable / disable consistent reads bypassing the dal cache.
        """
        return self._consistent_read

    @consistent_read.setter
    def consistent_read(self, value: bool) -> None:
        """
        Setter for consistent_read property to enable / disable consistent reads bypassing the dal cache.
        """
        self._consistent_read = value

    @property
    def post_filter(self) -> Callable:
        """
        Query result filter function
        :return:
        """
        return self._post_filter

    def append_filters(self, filters: List[FilterModel]) -> None:
        """
        Adds filters to the list of filters
        :param filters: List[FilterModel]
        :return: None
        """
        if not self._frozen and filters:
            self.filters.extend(filters)

    def __hash__(self) -> Any:
        filters = '::'.join([str(filter_) for filter_ in self.range_key_filter + self.filters])

        return hash((self.hash_key, self.start_token or '', self.limit, self.scan_index_forward, filters))
