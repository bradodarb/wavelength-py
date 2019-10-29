import difflib
import io
import json
import logging
import unittest

import pytest
from mock import MagicMock, patch
from mock.mock import call

import exos_serverless_lib.logging.log_lambda_base as slog_base
import exos_serverless_lib.logging.slog as slog
from exos_serverless_lib.errors.exceptions import EXOSBaseException, Base422Exception, Base5xxException, ExceptionLogLevel
from exos_serverless_lib.logging.logging_util import (MAX_LOG_APPEND, fit_log_msg, BufferStreamHandler)

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class ContextMock(object):

    def __init__(self):
        self.function_name = 'stage-func_name'
        self.aws_request_id = 'TEST-123ID'  # context.requestId
        self.invoked_function_arn = 'all your base are belong to us'
        self.path = '/dev/v1/endpoint'  # context.path


ctx = ContextMock()


class TestSlog(unittest.TestCase):

    def test_fit_message(self):

        too_long_msg = 'A' * (slog.LogLambda._max_log_msg_length + 5)
        ok_length_msg = 'A' * (slog.LogLambda._max_log_msg_length - 5)
        expectd_msg = too_long_msg[0:slog.LogLambda._max_log_msg_length] + MAX_LOG_APPEND
        trimmed_msg = fit_log_msg(too_long_msg, True, slog.LogLambda._max_log_msg_length)
        self.assertTrue(trimmed_msg == expectd_msg,
                        ''.join(difflib.ndiff(too_long_msg, expectd_msg)))
        non_trimmed_msg = fit_log_msg(too_long_msg, False, slog.LogLambda._max_log_msg_length)
        self.assertTrue(non_trimmed_msg == too_long_msg,
                        ''.join(difflib.ndiff(non_trimmed_msg, too_long_msg)))
        trimmed_msg = fit_log_msg(ok_length_msg, True, slog.LogLambda._max_log_msg_length)
        self.assertTrue(trimmed_msg == ok_length_msg,
                        ''.join(difflib.ndiff(trimmed_msg, ok_length_msg)))

    def test_slog(self):
        log_mock = MagicMock()
        bind_mock = log_mock.bind()
        slog_base.LogLambdaBase._structured_logger = log_mock
        test_log = slog.StructLog()
        test_log.info('test_event', 'test_msg')
        test_log.debug('test_event', 'test_msg')
        test_log.exception(Base5xxException('test', 'test_reason'))
        test_log.error('test_event', 'test_msg')
        test_log.warn('test_event', 'test_msg')
        bind_mock.info.assert_called_once_with(
            'test_event',
            interim_desc='test_msg')
        bind_mock.debug.assert_called_once_with(
            'test_event',
            interim_desc='test_msg')
        bind_mock.warning.assert_called_once_with(
            'test_event',
            interim_desc='test_msg')
        bind_mock.error.assert_has_calls([
            call('EXCEPTION', error_type='Base5xxException', exc_info=True, interim_desc='test', reason='test_reason'),
            call('test_event', interim_desc='test_msg')])

    def test_slog_fluent(self):
        log_mock = MagicMock()
        bind_mock = log_mock.bind()
        slog_base.LogLambdaBase._structured_logger = log_mock
        test_log = slog.StructLog()
        test_log.info(
            'test_event',
            'test_msg',
            base_output='base output').debug(
            more_output='debug output')
        exception = Exception('test')
        test_log.exception(exception).warn(more_output='warning output')
        bind_mock.info.assert_called_once_with('test_event',
                                               base_output='base output',
                                               interim_desc='test_msg')
        bind_mock.debug.assert_called_once_with(
            'test_event',
            interim_desc='test_msg',
            base_output='base output',
            more_output='debug output')
        bind_mock.error.assert_has_calls([
            call('EXCEPTION', error_type='Exception', exc_info=True, interim_desc='test', reason='unknown')])
        bind_mock.warning.assert_called_once_with(
            'EXCEPTION',
            error_type='Exception',
            interim_desc='test',
            reason='unknown',
            more_output='warning output')

    # The following tests need a lot of work to actually test code paths
    def test_log_lambda_default(self):
        slog.get_stage = MagicMock(return_value='test')
        wrap_log_mock = MagicMock()
        slog_base.wrap_logger = wrap_log_mock
        slog.LogLambda('test_service', event=MagicMock(), context=MagicMock())
        wrap_log_mock.assert_called_once()

    def test_log_lambda_logger_name(self):
        log_lambda = slog.LogLambda('test_service', logger_name='test', event=MagicMock(), context=MagicMock())
        self.assertEqual(logging.INFO, log_lambda._log_level)

    def test_log_lambda_call(self):
        mock_lambda = MagicMock(side_effect=[0, EXOSBaseException, Exception])
        mock_lambda.__name__ = 'test-lambda'
        event_mock = MagicMock()
        context_mock = MagicMock()
        log_lambda = slog.LogLambda('test_service', event=MagicMock(), context=MagicMock())
        decorator = log_lambda(mock_lambda)
        decorator(event_mock, context_mock)
        self.assertEqual(log_lambda._get_structured_logger(), None)

    def test_filter_pii_info(self):
        event_mock = {
            'interim_desc': {
                'requestContext': {
                    'authorizer': {
                        'claims': {
                            'persisted:': "persisted val",
                            'cognito:username:': "usernam val",
                            'email': "email val",
                            'sub': 'some persisted value'
                        }
                    },
                },
            },
        }
        returnval = slog.LogLambda._filter_pii_info(None, None, event_mock)
        self.assertEqual(
            returnval, {
                'interim_desc': {
                    'requestContext': {
                        'authorizer': {
                            'claims': {
                                'persisted:': '*', 'cognito:username:': '*', 'email': '*', 'sub': 'some persisted value'
                            }
                        }
                    }
                }
            })

    def test_filter_pii_info_empty_dictionary(self):
        event_mock = {}
        returnval = slog.LogLambda._filter_pii_info(None, None, event_mock)
        self.assertEqual(
            returnval, {})

    def test_log_lambda_does_not_raise_4xx(self):

        message = 'Your input could be better'

        @slog.LogLambda('vhs_tracker')
        def func(event, context):
            raise Base422Exception(message)

        event = MagicMock()
        context = ctx
        result = func(event, context)  # pylint: disable=assignment-from-no-return
        body = json.loads(result['body'])
        self.assertEqual(body['message'], message)

    def test_log_lambda_raises_5xx(self):

        message = 'Your input could be better'

        @slog.LogLambda('vhs_tracker')
        def func(event, context):
            raise Base5xxException(message)

        event = MagicMock()
        context = MagicMock()
        with self.assertRaises(Base5xxException):
            func(event, context)

    def test_log_lambda_does_not_raise_Exception(self):

        @slog.LogLambda('vhs_tracker')
        def func(event, context):
            val = {'this': 'that'}
            return val['invalid_key']['ref']

        event = MagicMock()
        context = MagicMock()

        with self.assertRaises(Base5xxException):
            func(event, context)

    def _execute_log_lamda_fucntion_which_raises(self, exception_log_level=None, event_type=None):
        message = 'Your input could be better'
        base_422_exception = Base422Exception(message)

        if exception_log_level:
            base_422_exception.exception_log_level = exception_log_level

        if event_type:
            base_422_exception.event_type = event_type

        @slog.LogLambda('vhs_tracker')
        def func(event, context):
            raise base_422_exception

        event = MagicMock()
        context = ctx
        result = func(event, context)  # pylint: disable=assignment-from-no-return
        body = json.loads(result['body'])

        self.assertEqual(body['message'], message)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.error")
    def test_log_lambda_logs_bod_exception(self, mock_error):
        self._execute_log_lamda_fucntion_which_raises()

        mock_error.assert_called_once_with(
            'EXCEPTION',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.error")
    def test_log_lambda_logs_bod_exception_invalid_type(self, mock_error):
        self._execute_log_lamda_fucntion_which_raises("Bad_VALUE")

        mock_error.assert_called_once_with(
            'EXCEPTION',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.error")
    def test_log_lambda_logs_bod_exception_error_level(self, mock_error):
        self._execute_log_lamda_fucntion_which_raises(ExceptionLogLevel.ERROR)

        mock_error.assert_called_once_with(
            'EXCEPTION',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.critical")
    def test_log_lambda_logs_bod_exception_critical_level(self, mock_critical):
        self._execute_log_lamda_fucntion_which_raises(ExceptionLogLevel.CRITICAL)

        mock_critical.assert_called_once_with(
            'EXCEPTION',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.warn")
    def test_log_lambda_logs_bod_exception_warn_level(self, mock_warn):
        self._execute_log_lamda_fucntion_which_raises(ExceptionLogLevel.WARNING)

        mock_warn.assert_called_once_with(
            'EXCEPTION',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.info")
    def test_log_lambda_logs_bod_exception_info_level(self, mock_info):
        self._execute_log_lamda_fucntion_which_raises(ExceptionLogLevel.INFO)

        mock_info.assert_has_calls(
            [
                call(
                    'EXCEPTION',
                    'Your input could be better',
                    exc_info=True,
                    exception_type='Base422Exception',
                    fluent_logger=None)
            ])

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.debug")
    def test_log_lambda_logs_bod_exception_debug_level(self, mock_debug):
        self._execute_log_lamda_fucntion_which_raises(ExceptionLogLevel.DEBUG)

        mock_debug.assert_called_once_with(
            'EXCEPTION',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)

    @patch("exos_serverless_lib.logging.log_lambda_base.LogLambdaBase.debug")
    def test_log_lambda_logs_bod_exception_with_configured_event_name(self, mock_debug):
        self._execute_log_lamda_fucntion_which_raises(ExceptionLogLevel.DEBUG, event_type="TEST_EVENT_NAME")

        mock_debug.assert_called_once_with(
            'TEST_EVENT_NAME',
            'Your input could be better',
            exc_info=True,
            exception_type='Base422Exception',
            fluent_logger=None)


class TestBufferStreamHandler(unittest.TestCase):

    def test_emit(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        rec = logging.LogRecord('test_name', logging.INFO,
                                'pathname', 123, '{"key": "test message"}', (), None)
        # setting to empty, seems something else is writing to it somehow
        bsh.emit(rec)

        self.assertEqual(len(bsh.message_buffer['items']), 1)
        self.assertEqual(stream.getvalue().strip(), '')

    def test_emit_string(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        rec = logging.LogRecord('test_name', logging.INFO,
                                'pathname', 123, 'string', (), None)
        # setting to empty, seems something else is writing to it somehow
        bsh.emit(rec)

        self.assertEqual(len(bsh.message_buffer['items']), 1)
        self.assertEqual(stream.getvalue().strip(), '')

    def test_emit_different_error_level_writes_immeditely(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        rec = logging.LogRecord('test_name', logging.ERROR,
                                'pathname', 123, '{"key": "error message"}', (), None)
        bsh.emit(rec)

        self.assertEqual(len(bsh.message_buffer['items']), 1)
        self.assertEqual(stream.getvalue().strip(), '{"key": "error message"}')

    def test_emit_different_error_level_writes_immeditely_string(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        rec = logging.LogRecord('test_name', logging.ERROR,
                                'pathname', 123, 'error message', (), None)
        bsh.emit(rec)

        self.assertEqual(len(bsh.message_buffer['items']), 1)
        self.assertEqual(stream.getvalue().strip(), 'error message')

    def test_write_to_stream(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        teststring = 'string'
        bsh.write_to_stream(teststring)

        self.assertEqual(stream.getvalue().strip(), teststring)

    def test_flush_buffer_to_stream(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        messages = {'items': ['msg1', 'msg2', 'msg3']}
        bsh.message_buffer = messages
        bsh.flush_buffer_to_stream()

        # what is returned is the string representation of the buffer, which
        # should always be an array of strings. Opted to hard code the expected
        # value to higlight clearly what is expected rather than str(messages)
        self.assertEqual(stream.getvalue().strip(), '{"items": ["msg1", "msg2", "msg3"]}')

        try:
            json.loads(stream.getvalue().strip())
        except Exception:  # pylint: disable=broad-except
            self.fail("the outputted object is not valid json")

    def test_flush_buffer_to_stream_empty_object(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        messages = {'items': [{}]}
        bsh.message_buffer = messages
        bsh.flush_buffer_to_stream()

        # what is returned is the string representation of the buffer, which
        # should always be an array of strings. Opted to hard code the expected
        # value to higlight clearly what is expected rather than str(messages)
        self.assertEqual(stream.getvalue().strip(),
                         '{"items": [{}]}')

        try:
            json.loads(stream.getvalue().strip())
        except Exception:  # pylint: disable=broad-except
            self.fail("the outputted object is not valid json")

    def test_flush_buffer_to_stream_empty_items_key(self):
        stream = io.StringIO()
        bsh = BufferStreamHandler(stream)
        messages = {'items': []}
        bsh.message_buffer = messages
        bsh.flush_buffer_to_stream()

        # what is returned is the string representation of the buffer, which
        # should always be an array of strings. Opted to hard code the expected
        # value to higlight clearly what is expected rather than str(messages)
        self.assertEqual(stream.getvalue().strip(), '')


if __name__ == '__main__':
    unittest.main()
