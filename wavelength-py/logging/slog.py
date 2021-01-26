"""
Lambda log wrapper
"""
import functools

from wavelength_serverless_lib.aws.aws_args import convert_response, convert_body
from wavelength_serverless_lib.errors.exceptions import (Base5xxException,
                                                   wavelengthBaseException)
from wavelength_serverless_lib.logging.log_lambda_base import LogLambdaBase
from wavelength_serverless_lib.logging.log_lambda_metrics import LogLambdaMetrics
from wavelength_serverless_lib.logging.logging_util import FluentLogger
from wavelength_serverless_lib.logging.util.cast_checks import is_json_serializable


class LogLambda(LogLambdaBase):
    """
    This is a decorator that will record the invoking of a lambda handler
    and its input event.

    Also, it will wrap the handler to record the exceptions in a structured
    format for ingestion into the log monitor es cluster.

    the decorator should be initialized with the logger returned
    from _get_structured_logger()
    """

    @staticmethod
    def _flush_buffer(**kwargs):
        return_status = kwargs.get('return_status')

        if return_status:
            if is_json_serializable(return_status):
                LogLambda.info('LogLambda#return_status', 'return_status', data=return_status)
            else:
                LogLambda.warn('LogLambda#_flush_buffer', 'provided return state is not json serializable')

        LogLambda.info('LogLambda#metrics', 'metrics', data=LogLambdaMetrics.sanitized())
        LogLambdaMetrics.reset_metrics()

    def __call__(self, lambda_func):
        """
        If there are decorator arguments, __call__() is only called
        once, as part of the decoration process! You can only give
        it a single argument, which is the function object.
        """
        LogLambdaMetrics.reset_metrics()

        @functools.wraps(lambda_func)
        def log_decorator(*args, **kwargs):
            """
            Decorator function call to setup structured logger
            """
            event = kwargs.get('event', args[0])
            if event:
                event['body'] = convert_body(event.get('body'))

            # Setting the context here, it is safe to assume a 'global'
            # context setting will have no conflict since this is lambda
            # runtime specific
            context = kwargs.get('context', args[1])
            # context.structured_logger = self._set_structured_logger(context, lambda_func.__name__)
            context.structured_logger = self._set_structured_logger(
                context, logger_name=lambda_func.__name__, service_tag=self.service_tag)

            # TODO we can evaluate the entry point for an api gateway context and limit length based on its presence.
            # Currently using simplest path of removing log limit on lambda entry point to reduce overhead of
            # processing input event
            if event and event.get('source') == 'serverless-plugin-warmup':
                # Skipping serverless plugin logging
                self.debug('TRACE',
                           'serverless plugin warmup invocation, skipping processing',
                           state='Skip', **kwargs)
                self._clear_structured_logger()
                return None

            self.info('TRACE', event, state='Invoked', **kwargs)
            try:
                # Capture code for serverless warmup plugin
                ret = lambda_func(*args, **kwargs)
            except Base5xxException as error:
                self.exception(error)
                ret = error.get_response(context)
                raise error
            except wavelengthBaseException as error:
                self.log_wavelength_exception(error)
                ret = error.get_response(context)
            except Exception as error:
                self.exception(error)
                ret = str(error)
                raise Base5xxException(str(error)) from error
            finally:
                self.info('TRACE', ret, state='Completed', **kwargs)
                self._flush_buffer(return_status=ret)
                self._clear_structured_logger()
            return convert_response(ret)

        return log_decorator


class StructLog:
    """
    Structured logger wrapper, emulates log type functionality
    """

    def __init__(self, **value):
        """
        Initializer allows for extra binds
        """
        self.bind(**value)

    @classmethod
    def bind(cls, **value):
        """
        add binding arguments to structured logger
        """
        LogLambda.bind(**value)

    @staticmethod
    def start_timer(name):
        """
        Wrapper to LogLambdaMetrics.start_timer
        """
        LogLambdaMetrics.start_timer(name)

    @staticmethod
    def stop_timer(name):
        """
        Wrapper to LogLambdaMetrics.stop_timer
        """
        LogLambdaMetrics.stop_timer(name)

    @staticmethod
    def counter(name: str, increment: int) -> None:
        """
        Wrapper to LogLambdaMetrics.counter
        """
        LogLambdaMetrics.counter(name, increment)

    @staticmethod
    def gauge(name: str, item) -> None:
        """
        Wrapper to LogLambdaMetrics.gauge
        """
        LogLambdaMetrics.gauge(name, item)

    @staticmethod
    def sets(name: str, item) -> None:
        """
        Wrapper to LogLambdaMetrics.sets
        """
        LogLambdaMetrics.sets(name, item)

    @classmethod
    def exception(cls, error, limit_output=False, **kwargs):
        """
        log exception to structure logger
        """
        if 'reason' not in kwargs:
            if isinstance(error, wavelengthBaseException):
                reason = error.reason
            else:
                reason = 'unknown'
        else:
            reason = kwargs.pop('reason')

        return cls.error('EXCEPTION',
                         str(error),
                         error_type=type(error).__name__,
                         exc_info=True,
                         limit_output=limit_output,
                         reason=reason,
                         **kwargs)

    @classmethod
    def critical(cls, event, msg, limit_output=True, **kwargs):
        """log critical to structure logger - wrapper to _log classmethod"""
        return cls._process_log("critical", event, msg,
                                limit_output=limit_output,
                                **kwargs)

    @classmethod
    def error(cls, event, msg, limit_output=False, **kwargs):
        """log error to structure logger - wrapper to _log classmethod"""
        return cls._process_log("error", event, msg,
                                limit_output=limit_output,
                                **kwargs)

    @classmethod
    def info(cls, event, msg, limit_output=True, **kwargs):
        """log info to structure logger - wrapper to _log classmethod"""
        return cls._process_log("info", event, msg,
                                limit_output=limit_output,
                                **kwargs)

    @classmethod
    def debug(cls, event, msg, limit_output=True, **kwargs):
        """log debug to structure logger - wrapper to _log classmethod"""
        return cls._process_log("debug", event, msg,
                                limit_output=limit_output,
                                **kwargs)

    @classmethod
    def warn(cls, event, msg, limit_output=True, **kwargs):
        """log warn to structure logger - wrapper to _log classmethod"""
        return cls._process_log("warning", event, msg,
                                limit_output=limit_output,
                                **kwargs)

    @classmethod
    def _process_log(cls, log_type, event, msg, **kwargs):
        """
        General log processor, calls the structured log process
        """
        fluent_logger = kwargs.get('fluent_logger')
        LogLambda.process_log(log_type, event, msg, **kwargs)
        if not fluent_logger:
            return FluentLogger(cls, event, msg, **kwargs)
        return None
