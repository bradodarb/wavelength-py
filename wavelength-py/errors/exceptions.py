"""
Base level errors
"""
from abc import abstractmethod
from enum import Enum
from http import HTTPStatus

from wavelength_serverless_lib.util.standard_response import get_standard_response


class ExceptionLogLevel(Enum):
    """
    Enum representing the expected log level of an Exception.
    """
    EXCEPTION = 1
    WARNING = 2
    DEBUG = 3
    INFO = 4
    CRITICAL = 5
    ERROR = 6


BASE_EXCEPTION_EVENT_TYPE = 'EXCEPTION'


class wavelengthBaseException(Exception):
    """
    Base exception for serverless. Other exceptions inherit from this class in
    order to provide a standard error message response format. Subclasses
    must therefor implemtned the defined abstract method(s) defined herein.
    """

    def __init__(self, error="Not Available", reason="Not Available", code="0"):
        super(wavelengthBaseException, self).__init__(error)
        self.reason = reason
        self.code = code
        self.exception_log_level = ExceptionLogLevel.EXCEPTION
        self.event_type = BASE_EXCEPTION_EVENT_TYPE

    def _get_response(self, status_code, context):
        """
        Builds an error response dict based on the supplied status code and AWS context object.
        :param status_code: int HTTP Status Code (https://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html).
        :param context: Python Lambda Context Object.
        (https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html#python-context-object-props).
        :return: dict
        """
        result = {
            "message": str(self),
            "error": {
                "path": context.invoked_function_arn,
                "reason": self.reason,
                "requestId": context.aws_request_id,
                "code": self.code
            }
        }
        return get_standard_response(result, status_code)

    @abstractmethod
    def get_response(self, context):
        """
        abstract method to required by inheriting classes to override.
        Retrieves the response string for the exception.
        """
        raise NotImplementedError()


class Base401Exception(wavelengthBaseException):
    """
    401 Unauthorized.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.UNAUTHORIZED, context)


class Base404Exception(wavelengthBaseException):
    """
    404 Not found (API route).
    """

    def __init__(self, error="Not Available", reason="Not Available", code="0", object_id=None):
        super(Base404Exception, self).__init__(error)
        self.reason = reason
        self.code = code
        self.object_id = object_id
        if self.object_id is not None:
            self.reason = f'Unable to find a model with ID: {self.object_id}'

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.NOT_FOUND, context)


class Base403Exception(wavelengthBaseException):
    """
    403 Forbidden.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.FORBIDDEN, context)


class Base409Exception(wavelengthBaseException):
    """
    409 Conflict.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.CONFLICT, context)


class Base412Exception(wavelengthBaseException):
    """
    412 Precondition Failed exception.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.PRECONDITION_FAILED, context)


class Base415Exception(wavelengthBaseException):
    """
    415 Invalid Media Type exception.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, context)


class Base422Exception(wavelengthBaseException):
    """
    422 Input validation error.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.UNPROCESSABLE_ENTITY, context)


class Base429Exception(wavelengthBaseException):
    """
    429 Too many request exception.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.TOO_MANY_REQUESTS, context)


class Base5xxException(wavelengthBaseException):
    """
    5xx Server Errors.
    """

    def get_response(self, context=None):
        return self._get_response(HTTPStatus.INTERNAL_SERVER_ERROR, context)


class InvalidParametersException(Base422Exception):
    """
    Derived input validation exception, use when parameters are not valid
    """


class OutputConversionException(Base422Exception):
    """
    Derived input validation exception, use when parameters are not valid
    """


class InvalidEventInputException(Base422Exception):
    """
    Derived input validation exception, use when lambda input event is not valid
    """
