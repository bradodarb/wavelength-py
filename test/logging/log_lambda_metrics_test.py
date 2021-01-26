import datetime
import unittest

from wavelength_py.logging.log_lambda_metrics import LogLambdaMetrics


class TestLogLambdaMetrics(unittest.TestCase):

    def test_reset_metrics(self):
        LogLambdaMetrics.reset_metrics()
        self.assertEqual(LogLambdaMetrics.metrics, {'counters': {}, 'gauges': {}, 'sets': {}, 'timers': {}})

    def test_start_timer(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.start_timer('name')

        self.assertTrue(isinstance(LogLambdaMetrics.metrics['timers']['name'], datetime.datetime))

    def test_stop_timer(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.metrics['timers']['name'] = datetime.datetime.now()
        LogLambdaMetrics.stop_timer('name')

        self.assertTrue(isinstance(LogLambdaMetrics.metrics['timers']['name'], float))

    def test_stop_timer_no_start_time(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.stop_timer('name')

        self.assertIsNone(LogLambdaMetrics.metrics['timers'].get('name'))

    def test_stop_timer_start_time_different_class(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.metrics['timers']['name'] = 'something'
        LogLambdaMetrics.stop_timer('name')

        self.assertIsNone(LogLambdaMetrics.metrics['timers'].get('name'))

    def test_counter(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.counter('counter_name', 1)

        self.assertTrue(LogLambdaMetrics.metrics['counters'].get('counter_name') == 1)

    def test_counter_pre_existing_count(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.metrics['counters']['counter_name'] = 1
        LogLambdaMetrics.counter('counter_name', 1)

        self.assertTrue(LogLambdaMetrics.metrics['counters'].get('counter_name') == 2)

    def test_counter_object_not_int_convertible(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.counter('counter_name', 'something')

        self.assertIsNone(LogLambdaMetrics.metrics['counters'].get('counter_name'))

    def test_gauge(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.gauge('name', 1)

        self.assertEqual(LogLambdaMetrics.metrics['gauges'].get('name'), 1)

    def test_gauge_item_not_json_serializable(self):
        LogLambdaMetrics.reset_metrics()
        obj = {'obj'}
        LogLambdaMetrics.gauge('name', obj)

        self.assertEqual(LogLambdaMetrics.metrics['gauges'].get('name'), None)

    def test_gauge_already_set(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.metrics['gauges']['name'] = 1
        LogLambdaMetrics.gauge('name', 'something')

        self.assertEqual(LogLambdaMetrics.metrics['gauges'].get('name'), 'something')

    def test_sets(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.sets('name', 'something')

        self.assertEqual(LogLambdaMetrics.metrics['sets'].get('name'), {'something'})
        self.assertTrue(isinstance(LogLambdaMetrics.metrics['sets'].get('name'), set))

    def test_sets_preexistingset(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.metrics['sets']['name'] = {'asdfasdf'}
        LogLambdaMetrics.sets('name', 'something')

        self.assertEqual(LogLambdaMetrics.metrics['sets'].get('name'), {'asdfasdf', 'something'})

    def test_sets_with_object_that_is_not_json_serializable(self):
        LogLambdaMetrics.reset_metrics()
        LogLambdaMetrics.metrics['sets']['name'] = {'asdfasdf'}
        LogLambdaMetrics.sets('name', {'another set'})

        self.assertEqual(LogLambdaMetrics.metrics['sets'].get('name'), {'asdfasdf'})

    def test_sanitize_timestamps(self):
        obj = {
            'first': datetime.datetime.now(),
            'second': 1
        }
        rv = LogLambdaMetrics.sanitize_timestamps(obj)
        self.assertEqual(len(rv), 1)
        self.assertEqual(obj['second'], 1)

    def test_sanitize_sets(self):
        obj = {
            'first': {'one', 'two'},
            'second': {'three', 'four'},
        }
        rv = LogLambdaMetrics.sanitize_sets(obj)
        self.assertTrue(isinstance(rv['first'], list))
        self.assertTrue(isinstance(rv['second'], list))
