"""
Utilities for pynamo models
"""
from typing import List, Union

from pynamodb.exceptions import PynamoDBConnectionError
from pynamodb.indexes import Projection
from pynamodb.models import Model as PynamoModel
from pynamodb.pagination import ResultIterator
from retrying import retry

from wavelength_serverless_lib.config import CONFIG
from wavelength_serverless_lib.dal.dynamodb.util import encode_start_token, handle_dynamodb_client_error
from wavelength_serverless_lib.errors.exceptions import Base429Exception, Base5xxException

PLATFORM_DB_PROPS = [
    'hash_id',
    'range_id',
    'kind',
]
COMMON_DB_PROPS = [

    'created_at',
    'modified_at',
    'table_state',
    'version'
]


class QueryResult:
    """
    Translates ResultIterator into a typed model and unwinds the internal generator
    """

    def __init__(self, result: ResultIterator):
        self._items = list(result)
        self._last_evaluated_key = encode_start_token(
            result.last_evaluated_key) if result.last_evaluated_key else None
        self._total_count = result.total_count

    @property
    def items(self) -> List[PynamoModel]:
        """
        Items returned from query
        :return: List[PynamoModel]
        """
        return self._items

    @property
    def last_evaluated_key(self) -> Union[str, dict, None]:
        """
        Next key token
        :return: Union[str, dict, None]
        """
        return self._last_evaluated_key

    @property
    def total_count(self) -> int:
        """
        Count from query
        :return: int
        """
        return self._total_count


class On429ThrottleError:
    """
    Boto3 Throttle handler for retry
    """

    def __init__(self, client_name):
        self._client_name = client_name

    def __call__(self, exception):
        """Return True if we should retry (in this case when it's an IOError), False otherwise"""
        return isinstance(exception, Base429Exception)


def pynamo_read_handler(func):
    """ Retry dynamodb read wrapper, returns value from function or passes the exception upward """

    @retry(wait_exponential_multiplier=CONFIG.CLIENT_RETRY_WAIT_EXPONENTIAL_MULTIPLIER,
           wait_exponential_max=CONFIG.CLIENT_RETRY_WAIT_EXPONENTIAL_MAX,
           stop_max_attempt_number=CONFIG.MAX_NUMBER_OF_CLIENT_RETRIES,
           retry_on_exception=On429ThrottleError('DynamonDB'))
    def wrapper(*args, **kwargs):
        """ Standard function wrapper """
        try:
            return func(*args, **kwargs)
        except PynamoDBConnectionError as err:
            handle_dynamodb_client_error(err)
            raise Base5xxException() from err

    return wrapper


def pynamo_write_handler(func):
    """ Retry dynamodb write wrapper, returns value from function or passes the exception upward """

    @retry(wait_exponential_multiplier=CONFIG.CLIENT_RETRY_WAIT_EXPONENTIAL_MULTIPLIER,
           wait_exponential_max=CONFIG.CLIENT_RETRY_WAIT_EXPONENTIAL_MAX,
           stop_max_attempt_number=CONFIG.MAX_NUMBER_OF_CLIENT_RETRIES,
           retry_on_exception=On429ThrottleError('DynamonDB'))
    def wrapper(*args, **kwargs):
        """ Standard function wrapper """
        try:
            return func(*args, **kwargs)
        except PynamoDBConnectionError as err:
            handle_dynamodb_client_error(err)
            raise Base5xxException() from err

    return wrapper


def get_pynamo_model_keys(db_model: PynamoModel):
    """
    Scan model attributes and pluck the keys
    :param db_model: PynamoModel
    :return: list
    """
    result = []
    for prop, val in getattr(db_model, '_attributes').items():

        if val.is_hash_key or val.is_range_key:
            result.append(prop)
    return result


class IndexBaseMeta:
    """
    Base Meta (useless, really as the actual props are set in serverless.yml but Pynamo needs them...)
    """
    projection = Projection()
    read_capacity_units = -1
    write_capacity_units = -1


class ModelBaseMeta:
    """
    Base Meta (useless, really as the actual props are set in serverless.yml but Pynamo needs them...)
    """
    region = CONFIG.AWS_REGION
