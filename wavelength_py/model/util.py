"""
Model utility functions
"""
from datetime import timezone, datetime, timedelta
from typing import Callable, Union


def get_posix_timestamp(datetime_value=None):
    """
    :param datetime_value: datetime
    :return: milliseconds from epoch
    """
    if datetime_value is None:
        datetime_value = datetime.utcnow()
    datetime_value = datetime_value.replace(tzinfo=timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)  # use POSIX epoch
    return round((datetime_value - epoch) / timedelta(microseconds=1))


def get_posix_date(epoch_seconds_value):
    """
    :param epoch_seconds_value: epoch milliseconds
    :return: datetime
    """
    try:
        return (datetime(1970, 1, 1, tzinfo=timezone.utc) +
                timedelta(microseconds=epoch_seconds_value))
    except (ValueError, TypeError):
        return None


def get_range_key(key, date=None, reverse=False) -> str:
    """
    :return: str
    """
    if reverse:
        template = '{1}::{0}'
    else:
        template = '{0}::{1}'

    if date is None:
        date = datetime.utcnow()

    if isinstance(date, datetime):
        return template.format(get_posix_timestamp(date), key)
    return template.format(key, date)


def safe_split(source: str, delimiter=',', converter: Callable = lambda x: x):
    """
    Splits a string via the delimiter, throws out any empties and strips the whitespace from each item
    :param source: str
    :param delimiter: str
    :param converter: Callable
    :return: list
    """
    if not source:
        return []
    return list(filter(None, [converter(item.strip()) for item in source.split(delimiter)]))


def safe_bool(source: Union[bool, str]):
    """
    Returns a boolean value from semantic string
    :param source: str
    :return: bool
    """
    if isinstance(source, str):
        return source.strip().lower() in ['true', 'yes', '1', 'ok']
    return source
