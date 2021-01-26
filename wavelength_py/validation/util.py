"""
Utils for supporting validating API Gateway events
"""
from functools import wraps

import simplejson
from bravado_core.exception import SwaggerMappingError

from wavelength_py.errors.exceptions import Base422Exception


def validate_event(model, validation_exceptions=(SwaggerMappingError, Exception)):
    """
    Parses a Lambda Event, validates it and adds it to event[model]
    :param model: Callable(<address>,<event>) that the event is passed to for validation and transform.
    :param validation_key: Key address in swagger spec to find validation schema
    :param validation_exceptions: Exceptions to listen for to call 422 exceptions
    :return:
    """

    def package(func):
        """
        Standard decorator
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            Validation wrapper
            """
            event = args[0]
            try:
                event['model'] = model(event)
            except validation_exceptions as vex:
                if any(isinstance(vex, ex) for ex in validation_exceptions):
                    if hasattr(vex, "reason"):
                        reason = vex.reason
                    else:
                        reason = str(vex)

                    raise Base422Exception('Validation Failed', reason=reason)
            try:
                return func(*args, **kwargs)
            finally:
                del event['model']

        return wrapper

    return package


class RequestValidationModel:
    """
    Base Validation model
    """

    def __init__(self, event_data):
        self._data = event_data

    @property
    def profile_id(self) -> str:
        """
        Profile Id
        :return: dict
        """
        # TODO - update to pull from Matt's JWT
        return self.headers.get('profile_id')

    @property
    def headers(self) -> dict:
        """
        Header Parameters
        :return: dict
        """
        return _sanitize_event(self._data.get('headers', {}))

    @property
    def query(self) -> dict:
        """
        Querystring Parameters
        :return: dict
        """
        return _sanitize_event(self._data.get('queryStringParameters', {}))

    @property
    def path(self) -> dict:
        """
        Path Parameters
        :return: dict
        """
        return _sanitize_event(self._data.get('pathParameters', {}))

    @property
    def form(self) -> dict:
        """
        Form Body
        :return: dict
        """
        return _sanitize_event(self._data.get('body', {}))

    @property
    def body(self) -> dict:
        """
        Request Body
        :return: dict
        """
        return _sanitize_event(self._data.get('body', {}))

    def json(self) -> str:
        """
        Request Body as JSON
        :return: dict
        """

        result = self._data.get('body', {})
        if isinstance(result, str):
            try:
                result = simplejson.loads(result)
            except(simplejson.JSONDecodeError, BaseException):
                result = {}

        return result


def _sanitize_event(val):
    """
    Return empty dictionary object here if val is null because Bravado doesn't null check
    """
    if val is None:
        val = {}
    return val


class NoAuthRequestValidationModel(RequestValidationModel):
    """
    Base Validation model with no Auth
    """

    @property
    def profile_id(self) -> str:
        """
        Profile Id
        :return: dict
        """
        return self._data.get('pathParameters', {}).get('profile-id')
