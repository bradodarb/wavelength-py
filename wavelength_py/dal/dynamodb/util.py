"""
Common utils for Dynamo interop
"""
import base64
import binascii
import json

from botocore.exceptions import ClientError
from retrying import retry

from wavelength_py.aws.boto_helper import is_a_boto3_throttle_error
from wavelength_py.errors.exceptions import Base409Exception, Base422Exception, Base429Exception
from wavelength_py.logging.slog import StructLog as log


class BotoThrottleConfig:
    """
    Class to set throttle retry values
    """
    max_retries = 5
    dynamo_db_timeout = 3.1
    max_write_backoff = 2500
    max_read_backoff = 2500
    wait_exponential_multiplier = 500


class OnThrottleError:
    """
    Boto3 Throttle handler for retry
    """

    def __init__(self, client_name):
        self._client_name = client_name

    def __call__(self, exception):
        """Return True if we should retry (in this case when it's an IOError), False otherwise"""
        if exception:
            throttle_error = is_a_boto3_throttle_error(exception)
            if throttle_error:
                log.warn(f'{self._client_name}_Operation',
                         'A throttle error was triggered',
                         operation='on_throttle_error',
                         data={'exception': str(exception)},
                         obj="exception",
                         exc_info=True)
            return throttle_error
        return False


def dynamo_read_handler(func):
    """ Retry dynamodb read wrapper, returns value from function or passes the exception upward """

    @retry(wait_exponential_multiplier=BotoThrottleConfig.wait_exponential_multiplier,
           wait_exponential_max=BotoThrottleConfig.max_read_backoff,
           stop_max_attempt_number=BotoThrottleConfig.max_retries,
           retry_on_exception=OnThrottleError('DynamonDB'))
    def wrapper(*args, **kwargs):
        """ Standard function wrapper """
        return func(*args, **kwargs)

    return wrapper


def dynamo_write_handler(func):
    """ Retry dynamodb write wrapper, returns value from function,
        true if there are concurrency issues or write fails, false if successful
        Non Client Error exception are not processed
        returns:
            True if a concurrency issues occurred
            False if process is successful
    """

    @retry(wait_exponential_multiplier=1000,
           wait_exponential_max=BotoThrottleConfig.max_write_backoff,
           stop_max_attempt_number=BotoThrottleConfig.max_retries,
           retry_on_exception=OnThrottleError('DynamonDB'))
    def wrapper(*args, **kwargs):
        """ Standard function wrapper """
        try:
            return func(*args, **kwargs)
        except ClientError as err:
            if err.response['Error']['Code'] == "ConditionalCheckFailedException":
                log.warn('CONDITIONAL_CHECK_FAILURE',
                         'Failed to update item due to conditional check failure',
                         operation=func.__name__, data={'exception': str(err)},
                         obj="exception", exc_info=True)
                raise Base409Exception(err)
            raise err

    return wrapper


class OnThrottleOrConditionalCheckError:
    """
    Boto3 Throttle handler for conditional check
    """

    def __init__(self, client_name):
        self._client_name = client_name

    def __call__(self, exception):
        """Return True if we should retry (in this case when it's an IOError), False otherwise"""
        if exception:
            throttle_error = OnThrottleError(self._client_name)
            if throttle_error(exception):
                return throttle_error
            if (isinstance(exception, ClientError) and
                    exception.response['Error']['Code'] == "ConditionalCheckFailedException"):
                log.warn('CONDITIONAL_CHECK_FAILURE',
                         'Failed to update item due to conditional check failure',
                         operation='_set_deleted', data={'exception': str(exception)},
                         obj="exception", exc_info=True)
                return True
        return False


def encode_start_token(token: dict) -> str:
    """
    Converts dict into base-64 encoded serialized JSON
    :param token: dict
    :return: str
    """
    if token is not None:
        return base64.b64encode(
            json.dumps(token).encode('utf-8')).decode('utf-8')
    return token


def decode_start_token(token: str = None):
    """
    Deserialize token back to dict
    :param token: str
    :return: dict
    """
    if token:
        try:
            return json.loads(base64.b64decode(token))
        except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError) as berr:
            raise Base422Exception('Invalid startToken', reason=str(berr))

    return None


def validate_start_token(token: dict, keys: list):
    """
    Ensures that certain keys provided reside in the provided dictionary
    :param token: dict (representing decoded token)
    :param token: list (representing list of keys that should be in token)
    :return: None
    """
    if not isinstance(token, dict):
        raise Base422Exception('Invalid startToken', reason='start token is in an invalid format')

    for k in keys:
        if k not in token:
            reason = f"{k} is a required attribute that is not present in the provided start token"
            raise Base422Exception('Invalid startToken', reason=reason)


def decode_and_validate_start_token(token: str, keys: list):
    """
    Will attempt to decode the provided token. Which should be a dictionary. It will then attempt to ensure that the
    decoded dictionary matches the expected strucuture.
    :param token: str (representing an encoded token)
    :param token: list (representing list of keys that should be in token, once decoded)
    :return: None
    """
    decoded = decode_start_token(token)
    if decoded is None:
        raise Base422Exception('Invalid startToken', reason='Invalid format')

    validate_start_token(decoded, keys)
    return decoded


def handle_dynamodb_client_error(error):
    """
    Return correct application error from boto Client Error
    :param error: Exception
    :return: BODBaseException
    """
    error_map = {
        'ValidationException': Base422Exception,
        'ConditionalCheckFailedException': Base409Exception
    }
    if isinstance(error.cause, ClientError):
        code = error.cause.response['Error'].get('Code')
        message = error.cause.response['Error'].get('Message')
        exception = error_map.get(code)
        if exception:
            raise exception(error=message, reason=code)
        if is_a_boto3_throttle_error(error.cause):
            log.warn('EXCEPTION', error, error_code=code)
            raise Base429Exception(error.cause)


def check_version(arg1, arg2):
    """
    Version Equality Outcome, keeps code more concise and aides in testing
    :param arg1: Any
    :param arg2: Any
    :return: bool
    """
    if arg1 != arg2:
        raise Base409Exception('Model version conflict',
                               reason='Try getting the latest model and re-apply updates')
