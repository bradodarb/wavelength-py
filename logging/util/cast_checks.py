"""
Utilities to check if inputs can be converted to various outputs
"""
import json


def is_int_like(obj):
    """
     provided an object returns a bool indicating if it can be casted to json or not.
    :returns: bool
    """
    try:
        int(obj)
        return True
    except:  # pylint: disable=bare-except
        return False


def is_json_serializable(obj):
    """
    is_json_serializable provided an object returns a bool indicating if it can be serialized to json or not.
    :returns: bool
    """
    try:
        json.dumps(obj)
        return True
    except:  # pylint: disable=bare-except
        return False
