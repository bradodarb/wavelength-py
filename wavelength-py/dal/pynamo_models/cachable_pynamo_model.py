"""
Base mode for cache enabled pynamo model access
"""
from cachetools import TTLCache
from pynamodb.models import Model as PynamoModel

from wavelength_serverless_lib.config import CONFIG
from wavelength_serverless_lib.dal.pynamo_models.util import QueryResult


class CachingPynamoModel(PynamoModel):
    """
    Overrides a few methods on the Model class to enable selective caching
    """

    cache = TTLCache(maxsize=128, ttl=CONFIG.DATA_CACHE_TTL)

    @classmethod
    def query(cls, *args, **kwargs) -> QueryResult:  # type: ignore  # pylint: disable=arguments-differ
        """
        Override base for caching behavior
        :param hash_key: str
        :param range_key_condition: str
        :param filter_condition:  Condition
        :param consistent_read: bool
        :param index_name: str
        :param scan_index_forward: bool
        :param conditional_operator: List
        :param limit: int
        :param last_evaluated_key: Union[str, dict, None]
        :param attributes_to_get: List
        :param page_size: int
        :param rate_limit: int
        :param filters: List
        :return: QueryResult
        """
        result = QueryResult(super().query(*args, **kwargs))
        for item in result.items:
            cls._put_model_cache(item)
        return result

    @classmethod
    def get(cls,
            hash_key,
            range_key=None,
            consistent_read=False,
            attributes_to_get=None):
        """
        Returns a single object using the provided keys
        :param hash_key: str
        :param range_key: str
        :param consistent_read: bool
        :param attributes_to_get: List
        :return: PynamoModel
        """
        key = cls.get_cache_key(hash_key, range_key)
        result = cls.cache.get(key)

        if not result:
            result = super().get(hash_key, range_key, consistent_read, attributes_to_get)
            cls.cache[key] = result

        return result

    def save(self, condition=None, conditional_operator=None, **expected_values):
        """
        Save this object to dynamodb
        :param condition: Condition
        :param conditional_operator: List
        :param expected_values: List
        :return: dict
        """
        result = super().save(condition, conditional_operator, **expected_values)
        self._put_model_cache(self)
        return result

    def update(self, attributes=None, actions=None, condition=None, conditional_operator=None, **expected_values):
        """
        Updates an item using the UpdateItem operation.
        :param attributes: List
        :param actions: List
        :param condition: Condition
        :param conditional_operator: List
        :param expected_values: List
        :return: dict
        """
        result = super().update(attributes, actions, condition, conditional_operator, **expected_values)
        self._put_model_cache(self)
        return result

    def delete(self, condition=None, conditional_operator=None, **expected_values):
        """
        Deletes this object from dynamodb
        :param condition: Condition
        :param conditional_operator: List
        :param expected_values: List
        :return: dict
        """
        result = super().delete(condition, conditional_operator, **expected_values)
        self._delete_model_cache(self)
        return result

    @classmethod
    def get_cache_key(cls, hash_key, range_key=None):
        """
        Builds hash key from parameters
        :param args: positionals
        :param kwargs: keywords
        :return: str
        """
        result = hash_key
        if range_key:
            result = f'{hash_key}:::{range_key}'

        return result

    @classmethod
    def _put_model_cache(cls, model: PynamoModel):
        """
        Replaces an item in the cache based on its own keys
        :param model: PynamoModel
        :return: None
        """
        key = cls.get_cache_key(*getattr(model, '_get_keys')())
        cls.cache[key] = model

    @classmethod
    def _delete_model_cache(cls, model: PynamoModel):
        """
        Replaces an item in the cache based on its own keys
        :param model: PynamoModel
        :return: None
        """
        key = cls.get_cache_key(*getattr(model, '_get_keys')())
        cls.cache.pop(key)
