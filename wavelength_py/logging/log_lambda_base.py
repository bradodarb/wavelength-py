"""
Base logger
"""
import logging
import os
import sys

from structlog._config import wrap_logger
from structlog.processors import (TimeStamper,
                                  StackInfoRenderer,
                                  format_exc_info,
                                  JSONRenderer)
from structlog.stdlib import add_logger_name, add_log_level

from wavelength_py.aws.aws_args import get_stage
from wavelength_py.errors.exceptions import ExceptionLogLevel, wavelengthBaseException
from wavelength_py.logging.filter import NestedFilter, whitelist
from wavelength_py.logging.logging_util import (LOG_NAME_VS_VAL,
                                                      ENV_LOG_VAR_KEY, DEFAULT_LOGGING_NAME,
                                                      DEFAULT_LOGGING, MAX_LOG_DEBUG_OUTPUT,
                                                      DEBUG_LOGGING, MAX_LOG_OUTPUT,
                                                      FORMAT,
                                                      WHITELISTATTRS, WHITELISTPATH,
                                                      fit_log_msg)


class LogLambdaBase:
    """
    This is a decorator that will record the invoking of a lambda handler
    and its input event.

    Also, it will wrap the handler to record the exceptions in a structured
    format for ingestion into the log monitor es cluster.

    the decorator should be initialized with the logger returned
    from _get_structured_logger()
    """
    _log_handler = None
    _structured_logger = None
    _do_convert_body = None
    _max_log_msg_length = MAX_LOG_DEBUG_OUTPUT
    _log_level = logging.INFO

    # pylint: disable=too-many-arguments

    def __init__(self, service, logger_name=None, event=None, context=None, do_convert_body=True):
        """
        we will create the structured logger internally
        """
        LogLambdaBase._do_convert_body = do_convert_body
        self.service_tag = service

        # TODO should we use string values to represent log levels via env
        # variables?
        LogLambdaBase._log_level = LOG_NAME_VS_VAL.get(os.getenv(ENV_LOG_VAR_KEY,
                                                                 os.getenv(ENV_LOG_VAR_KEY.lower(),
                                                                           DEFAULT_LOGGING_NAME)),
                                                       DEFAULT_LOGGING)
        LogLambdaBase._max_log_msg_length = MAX_LOG_DEBUG_OUTPUT if self._log_level == DEBUG_LOGGING else MAX_LOG_OUTPUT

        if event is not None and context is not None:
            # Special constructor, if we want to do bindings before calling
            # the method A fully qualified call may be used construct logger
            # instead of implicitly constructor it during the call method
            context.structured_logger = self._set_structured_logger(
                context, logger_name=logger_name, service_tag=self.service_tag)

    @staticmethod
    def _set_structured_logger(context, logger_name=None, service_tag=None):
        """
            use this function to get a structured logger and can use
            this to pass into the LogLambda decorator

            context - aws lambda context
            service - name of the service that this lambda belongs to
            logger_name - logger's name
            log_level - one of the levels in logging module
        """
        if LogLambdaBase._structured_logger:
            return LogLambdaBase._structured_logger

        stage_tag = get_stage(context)

        if logger_name:
            logger = logging.getLogger(str(logger_name))
        else:
            logger = logging.getLogger()

        # Python logger in AWS Lambda has a preset format.
        # To change the format of
        # the logging statement, remove the logging handler
        # and add a new handler with the required format
        for handler in logger.handlers:
            logger.removeHandler(handler)

        LogLambdaBase._log_handler = LogLambdaBase._get_handler()

        LogLambdaBase._log_handler.setFormatter(logging.Formatter(FORMAT))
        logger.addHandler(LogLambdaBase._log_handler)
        logger.setLevel(LogLambdaBase._log_level)
        logger.propagate = False

        wlogger = wrap_logger(
            logger,
            processors=[
                LogLambdaBase._filter_pii_info,
                add_logger_name,
                add_log_level,
                TimeStamper(fmt="iso"),
                StackInfoRenderer(),
                format_exc_info,
                JSONRenderer(separators=(',', ':'), sort_keys=True)])

        inferred_lambda_tag = context.function_name
        if stage_tag is not None:
            inferred_lambda_tag = inferred_lambda_tag.replace('{0}_'.format(stage_tag), '', 1)

        LogLambdaBase._structured_logger = wlogger.bind(
            aws_lambda_name=context.function_name,
            aws_lambda_request_id=context.aws_request_id,
            internal_service_tag=service_tag,
            inferred_stage_tag=stage_tag,
            inferred_lambda_tag=inferred_lambda_tag
        )
        return LogLambdaBase._structured_logger

    @staticmethod
    def bind(**value):
        """
        add binding arguments to structured logger
        """
        if LogLambdaBase._structured_logger:
            LogLambdaBase._structured_logger = LogLambdaBase._structured_logger.bind(**value)

    @staticmethod
    def log_wavelength_exception(wavelength_exception: wavelengthBaseException, fluent_logger=None, **kwargs):
        """
        log wavelengthBaseException to the configured log level.
        """
        log_func = LogLambdaBase._get_wavelength_exception_log_function(wavelength_exception.exception_log_level)

        return log_func(wavelength_exception.event_type,
                        str(wavelength_exception),
                        exception_type=type(wavelength_exception).__name__,
                        exc_info=True,
                        fluent_logger=fluent_logger,
                        **kwargs)

    @staticmethod
    def _get_wavelength_exception_log_function(exception_log_level: ExceptionLogLevel):
        """
        Return the log function appropriate for the ExceptionLogLevel
        """
        _wavelength_exception_log_level_funcs = {
            # EXCEPTION type is deliberately logged as error
            ExceptionLogLevel.EXCEPTION: LogLambdaBase.error,
            ExceptionLogLevel.WARNING: LogLambdaBase.warn,
            ExceptionLogLevel.DEBUG: LogLambdaBase.debug,
            ExceptionLogLevel.INFO: LogLambdaBase.info,
            ExceptionLogLevel.CRITICAL: LogLambdaBase.critical,
            ExceptionLogLevel.ERROR: LogLambdaBase.error
        }

        return _wavelength_exception_log_level_funcs.get(exception_log_level, LogLambdaBase.error)

    @staticmethod
    def exception(error, fluent_logger=None, **kwargs):
        """
        log exception to structure logger
        """
        return LogLambdaBase.error('EXCEPTION',
                                   str(error),
                                   exception_type=type(error).__name__,
                                   exc_info=True,
                                   fluent_logger=fluent_logger,
                                   **kwargs)

    @staticmethod
    def critical(event, msg, limit_output=True, fluent_logger=None, **kwargs):
        """log critical to structure logger - wrapper to _log classmethod"""
        return LogLambdaBase.process_log("critical", event, msg,
                                         limit_output=limit_output,
                                         fluent_logger=fluent_logger, **kwargs)

    @staticmethod
    def error(event, msg, limit_output=True, fluent_logger=None, **kwargs):
        """log error to structure logger - wrapper to _log classmethod"""
        return LogLambdaBase.process_log("error", event, msg,
                                         limit_output=limit_output,
                                         fluent_logger=fluent_logger, **kwargs)

    @staticmethod
    def info(event, msg, limit_output=True, fluent_logger=None, **kwargs):
        """log info to structure logger - wrapper to _log classmethod"""
        return LogLambdaBase.process_log("info", event, msg,
                                         limit_output=limit_output,
                                         fluent_logger=fluent_logger, **kwargs)

    @staticmethod
    def debug(event, msg, limit_output=True, fluent_logger=None, **kwargs):
        """log debug to structure logger - wrapper to _log classmethod"""
        return LogLambdaBase.process_log("debug", event, msg,
                                         limit_output=limit_output,
                                         fluent_logger=fluent_logger, **kwargs)

    @staticmethod
    def warn(event, msg, limit_output=True, fluent_logger=None, **kwargs):
        """log warn to structure logger - wrapper to _log classmethod"""
        return LogLambdaBase.process_log("warning", event, msg,
                                         limit_output=limit_output,
                                         fluent_logger=fluent_logger, **kwargs)

    @staticmethod
    def _get_structured_logger():
        return LogLambdaBase._structured_logger

    @staticmethod
    def _clear_structured_logger():
        LogLambdaBase._structured_logger = None

    @staticmethod
    def _get_handler():
        return logging.StreamHandler(sys.stdout)

    @staticmethod
    def _filter_pii_info(_logger, _method_name, event_dict):
        whitelist_filter = NestedFilter(WHITELISTPATH, WHITELISTATTRS)
        return whitelist(event_dict, whitelist_filter)

    @staticmethod
    def _flush_buffer(**kwargs):
        LogLambdaBase._log_handler.flush_buffer_to_stream()

    @staticmethod
    def process_log(cmd, event, msg, **kwargs):
        """
        Standard base logger
        """
        if 'fluent_logger' in kwargs:
            kwargs.pop('fluent_logger')
        limit_output = kwargs.pop('limit_output', True)
        if LogLambdaBase._get_structured_logger():
            message = fit_log_msg(event, limit_output, LogLambdaBase._max_log_msg_length)
            desc = fit_log_msg(msg, limit_output, LogLambdaBase._max_log_msg_length)
            getattr(LogLambdaBase._get_structured_logger(), cmd)(message, interim_desc=desc, **kwargs)
            # a bit of meta programming here in order to remove duplication
            # in that each logging method basically has the same params with a
            # different message name. Using getattr is just as good.
