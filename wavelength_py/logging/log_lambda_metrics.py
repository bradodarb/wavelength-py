"""

This class much like the LogLambdaBase class, is intended to act as a singleton. Whats more is that it is intended
to work in tandem with the existing logger codebase. Although a completely separate entity, this class and the metrics
it generates is to be attached to the log buffer before it is json seralized and flushed. As a result the following code
protects against adding objects to the metrics dictionary that are not json serializable.
"""

import datetime
from wavelength_py.logging.log_lambda_base import LogLambdaBase
from wavelength_py.logging.util.cast_checks import is_int_like, is_json_serializable


class LogLambdaMetrics:
    """
    This class is a singleton that has functionality that writes metrics gathering information into a dictionary.
    """
    KEY_COUNTERS = 'counters'
    KEY_TIMERS = 'timers'
    KEY_GAUGES = 'gauges'
    KEY_SETS = 'sets'

    metrics = {}

    @staticmethod
    def reset_metrics():
        """
        reset_metrics will as the name suggests re-set the metrics attribute to the default value.
        """
        LogLambdaMetrics.metrics = {
            LogLambdaMetrics.KEY_COUNTERS: {},
            LogLambdaMetrics.KEY_TIMERS: {},
            LogLambdaMetrics.KEY_GAUGES: {},
            LogLambdaMetrics.KEY_SETS: {},
        }

    @staticmethod
    def start_timer(name):
        """
        start_timer provided a specific name will start the process for a measuring time.
        The caller must also be responsible for calling stop_timer.
        """
        if not LogLambdaMetrics.metrics:
            return

        LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_TIMERS][str(name)] = (datetime.datetime.now())

    @staticmethod
    def stop_timer(name):
        """
        stop_timer when provided a name will attempt to stop the timer namespaced to that name. It assumes that
        start_timer has been called with that same name param. And therefore it expects an instance of
        datetime.datetime to be at that location. This is replaced with an float of the time elapsed since start.
        returns: None
        """
        if not LogLambdaMetrics.metrics:
            return

        attr = str(name)
        if attr not in LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_TIMERS]:
            LogLambdaBase.warn('LogLambdaMetrics#stop_timer',
                               ("stop_timer called on non-existing timer - %s" % name))
            return

        start_time = LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_TIMERS][attr]
        if isinstance(start_time, datetime.datetime):  # meaning it has not been set
            LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_TIMERS][attr] = (
                datetime.datetime.now() - start_time).total_seconds()
        else:
            LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_TIMERS].pop(attr)
            LogLambdaBase.warn(
                'LogLambdaMetrics#stop_timer',
                ("stop_timer encountered something other than a datetime.datetime instance - %s" % name))

    @staticmethod
    def counter(name: str, increment: int) -> None:
        """
        counter when procided a name and an increment will do one of 2 thigns. It will either create a counter object
        with the inputted value, or increment the pre-exisitng value by the increment param.
        returns: None
        """
        if not LogLambdaMetrics.metrics:
            return

        if not is_int_like(increment):
            LogLambdaBase.warn('LogLambdaMetrics#counter', 'called with object that is not int castable')
            return

        name, increment = str(name), int(increment)
        if name not in LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_COUNTERS]:
            LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_COUNTERS][name] = increment
            return

        LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_COUNTERS][name] += increment

    @staticmethod
    def gauge(name: str, item) -> None:
        """
        gauge simply sets the item to the provided namespace. Caller must ensure
        that the items placed into sets are json serializable. This is because
        we convert logs to json later down the line.
        """
        if not LogLambdaMetrics.metrics:
            return

        if not is_json_serializable(item):
            LogLambdaBase.warn('LogLambdaMetrics#gauge', 'called with object that is not json serializable')
            return

        LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_GAUGES][str(name)] = item

    @staticmethod
    def sets(name: str, item) -> None:
        """
        set etiher creates a set with the inputted item or appends the new item if a set already exists.
        """
        if not is_json_serializable(item):
            LogLambdaBase.warn('LogLambdaMetrics#sets', 'called with object that is not json serializable')
            return

        if LogLambdaMetrics.metrics:
            if name in LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_SETS]:
                LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_SETS][name].add(item)
            else:
                LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_SETS][name] = {item}

    @staticmethod
    def sanitize_timestamps(timestamps: {}) -> dict:
        """
        sanitize_timestamps ensures that there are no lingering instances of the datetime class. There helps protect
        against the case where a user has started a timestamp but has failed to close it.
        """
        new_dictionary = {}
        for k, value in timestamps.items():
            if not isinstance(value, datetime.datetime):
                new_dictionary[k] = value
        return new_dictionary

    @staticmethod
    def sanitize_sets(sets: {}) -> dict:
        """
        sanitize_sets converts the sets attribute into lists for the purposes of json seralization.
        """
        for k, value in sets.items():
            sets[k] = list(value)

        return sets

    @staticmethod
    def sanitized():
        """
        sanitize calls the other sanitize methods.
        """
        if LogLambdaMetrics.metrics:
            LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_TIMERS] = LogLambdaMetrics.sanitize_timestamps(
                LogLambdaMetrics.metrics.get(LogLambdaMetrics.KEY_TIMERS))
            LogLambdaMetrics.metrics[LogLambdaMetrics.KEY_SETS] = LogLambdaMetrics.sanitize_sets(
                LogLambdaMetrics.metrics.get(LogLambdaMetrics.KEY_SETS))
        return LogLambdaMetrics.metrics
