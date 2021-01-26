"""
Custom Pynamodb attribute to support taxonomy.
"""
from functools import singledispatch

from pynamodb.attributes import UnicodeAttribute

from wavelength_py.model.util import safe_split


@singledispatch
def serialize_tag(source) -> None:
    """
    Default serializer for tags (if not supported by registered conversion we make it None).
    :param source: obj
    :return: None
    """


@serialize_tag.register(str)
def serialize_tag_str(source: str) -> str:
    """
    Tag is already a str, we are just returning it unmodified.
    :param source:
    :return: str
    """
    return source


@serialize_tag.register(list)
def serialize_tag_list(source: list) -> str:
    """
    Tag is a list, break it down to format.
    :param source:
    :return: str
    """
    if not source:
        return None

    source.sort()
    return f'::{"::".join(map(str, source))}::'


class TagAttribute(UnicodeAttribute):
    """
    A custom model activity.
    """

    def serialize(self, value):
        """
        When value is a list and return tag formatted str.
        When value is a str return str.
        Otherwise (in other cases) return None.
        :param value:
        :return:str
        """
        if value:
            return super(TagAttribute, self).serialize(serialize_tag(value))

        return value

    def deserialize(self, value: str):
        if value:
            if '::' in value:
                return super(TagAttribute, self).deserialize(safe_split(value, '::'))
            return super(TagAttribute, self).deserialize(value)

        return value
