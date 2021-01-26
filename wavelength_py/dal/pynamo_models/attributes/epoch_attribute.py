"""
Custom Pynamodb attribute for epoch datetimes.
"""
from decimal import Decimal
from functools import singledispatch

import arrow

from pynamodb.attributes import NumberAttribute

from wavelength_py.model.util import get_posix_timestamp


@singledispatch
def serialize_epoch(source) -> None:
    """
    Default serializer for epochs (if not supported by registered conversion we make it None).
    :param source: obj
    :return: None
    """
    pass  # pylint: disable=W0107


@serialize_epoch.register(str)
def serialize_epoch_str(source: str) -> int:
    """
    Only date-time formmated strings are supported, parse it down to an int.
    :param source:
    :return: int
    """
    try:
        return get_posix_timestamp(arrow.get(source))
    except Exception:
        raise ValueError('Unable to parse string as a datetime')


@serialize_epoch.register(int)
def serialize_epoch_int(source: int) -> int:
    """
    Epoch is an int, pass it through
    :param source:
    :return: int
    """

    if isinstance(source, bool):
        raise ValueError('Boolean not supported for Epoch')

    return source


@serialize_epoch.register(float)
@serialize_epoch.register(Decimal)
def serialize_epoch_numeric(source) -> int:
    """
    Epoch is numeric but not an int, round it
    :param source:
    :return: int
    """

    return round(source)


class EpochAttribute(NumberAttribute):
    """
    A custom model activity.
    """

    def serialize(self, value):
        """
        When value is a list and return epoch formatted str.
        When value is a str return str.
        Otherwise (in other cases) return None.
        :param value:
        :return:str
        """
        if value:
            return super(EpochAttribute, self).serialize(serialize_epoch(value))

        return value
