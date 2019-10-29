"""
Logging utils
"""
import json
import logging

MAX_LOG_OUTPUT = 20000
MAX_LOG_DEBUG_OUTPUT = 200000
MAX_LOG_APPEND = ' ...'
FORMAT = '%(message)s'

ENV_LOG_VAR_KEY = 'LOG_LEVEL'
DEFAULT_LOGGING_NAME = 'INFO'
DEFAULT_LOGGING = logging.INFO
LOG_NAME_VS_VAL = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG}
DEBUG_LOGGING = logging.DEBUG
# Limiting the log output, max for an AWS cloudwatch event is 256K we are
# limiting log events to ~20K for non debug and ~200K for debug.

WHITELISTPATH = ['interim_desc', 'requestContext', 'authorizer', 'claims']
WHITELISTATTRS = ['token_use', 'sub', 'locale', 'iat', 'email_verified', 'auth_time', 'aud']


class FluentLogger():
    """
    Structured logger wrapper, for fluent
    """

    def __init__(self, log_class, event=None, msg=None, **kwargs):
        """
        Standard constructor
        """
        self._event = event
        self._msg = msg
        self._limit_output = kwargs.pop('limit_output')
        self._previous_args = dict()
        self.append_previous(kwargs)
        self._log_class = log_class

    def exception(self, error=None, **kwargs):
        """
        log exception to structure logger
        """
        self._log('exception', error if error else self._event,
                  fluent_logger=self, **kwargs)
        return self

    def critical(self, event=None, msg=None, **kwargs):
        """log critical to structure logger - wrapper to _log method"""
        return self._log("critical", event=event, msg=msg, **kwargs)

    def error(self, event=None, msg=None, **kwargs):
        """log error to structure logger - wrapper to _log method"""
        return self._log("error", event=event, msg=msg, **kwargs)

    def info(self, event=None, msg=None, **kwargs):
        """log info to structure logger - wrapper to _log method"""
        return self._log("info", event=event, msg=msg, **kwargs)

    def debug(self, event=None, msg=None, **kwargs):
        """log debug to structure logger - wrapper to _log method"""
        return self._log("debug", event=event, msg=msg, **kwargs)

    def warn(self, event=None, msg=None, **kwargs):
        """log warn to structure logger - wrapper to _log method"""
        return self._log("warn", event=event, msg=msg, **kwargs)

    def append_previous(self, previous_args):
        """
        Helper to update previous args
        """
        if previous_args:
            self._previous_args.update(previous_args)
            if 'exc_info' in self._previous_args:
                self._previous_args.pop('exc_info')
        return self._previous_args

    def _log(self, cmd, event=None, msg=None, **kwargs):
        """
        log critical to structure logger
        """
        limit_output = kwargs.get('limit_output', True)
        kwargs['fluent_logger'] = self

        self.append_previous(kwargs)
        limit_output = self._limit_output if not limit_output else limit_output
        getattr(self._log_class, cmd)(
            event=event if event else self._event,
            msg=msg if msg else self._msg,
            **self._previous_args)
        return self


class BufferStreamHandler(logging.StreamHandler):
    """
        BufferStreamHandler is a subclass to logging.StreamHandler that is
        used to buffer messages to then be flushed at once.
    """

    LOGGABLE_RECORDS = set([logging.ERROR, logging.CRITICAL])

    def __init__(self, stream=None):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        super().__init__(stream)
        self.message_buffer = {'items': []}

    def add(self, key, value):
        """
        Appends and item by namespace it to a different key.
        """
        self.message_buffer[key] = value

    def emit(self, record):
        """
        Emit a record.
        """

        try:
            msg = self.format(record)
            try:
                dmsg = json.loads(msg)
                self.message_buffer['items'].append(dmsg)
            except json.JSONDecodeError:
                self.message_buffer['items'].append(msg)
            finally:
                if record.levelno in BufferStreamHandler.LOGGABLE_RECORDS:
                    self.write_to_stream(msg)
        # pylint: disable=W0703
        except Exception:
            self.handleError(record)

    def write_to_stream(self, msg):  # msg is a string
        """
        writes message to a buffer.
        """
        stream = self.stream
        stream.write(msg)
        stream.write(self.terminator)
        self.flush()

    def flush_buffer_to_stream(self):
        """
        Flushes buffer by writing to stream.
        """
        if self.message_buffer['items']:
            jmsg = json.dumps(self.message_buffer)
            self.write_to_stream(jmsg)
            self.message_buffer = {'items': []}


def fit_log_msg(msg, limit_output, max_log_msg_length):
    """
    Trims the log based on maximum length declared for debug or regular messages
    """
    if not limit_output:
        return msg
    msg_str = str(msg)
    return (msg_str[:max_log_msg_length] +
            MAX_LOG_APPEND) if len(msg_str) > max_log_msg_length else msg
