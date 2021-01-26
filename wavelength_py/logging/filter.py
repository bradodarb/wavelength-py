"""
Whitelisting for logs
"""
FILTER_VALUE = "*"


def nested_get(input_dict, nested_keys):
    """
    Provided a dictionary and a list of strings (representing keys). This
    function uses the items wihtin nested_keys as keys within the input_dict.
    And will attempted to access and return the object outlined in the
    nested_keys list.
    """
    a_dict = input_dict
    for key in nested_keys:
        new_val = _nested_get(a_dict, key)
        if new_val is not None:
            a_dict = new_val
        else:
            return None
    return a_dict


def _nested_get(a_dict, key):
    new_val = None
    if hasattr(a_dict, 'get'):
        new_val = a_dict.get(key)

    return new_val


class NestedFilter:
    """
    NestedFilter is a data structure that is used for filtering out nested
    dictionaries. The path attribute is used to access a nested dictionary.
    The attrs attrs attribute is used to describe the attributes on the
    nested dictionary to modify.
    """

    def __init__(self, path, attrs):
        self.path = path
        self.attrs = attrs


def whitelist(input_dict, nested_filter, filter_value=FILTER_VALUE):
    """
    whitelist provided a dictionary, and a an instance of nested_filter.
    Will attempt to modify the nested input_dict as request.
    """
    nested_val = nested_get(input_dict, nested_filter.path)
    if (nested_val) and (isinstance(nested_val, dict)):
        return _transform_nested_whitelist(input_dict, nested_filter, filter_value)

    return input_dict


def _transform_nested_whitelist(input_dict, nested_filter, filter_value):
    length = len(nested_filter.path)
    a_dict = input_dict
    for i in range(length):
        k = nested_filter.path[i]
        if i == (length - 1):  # last item in nested_keys
            a_dict[k] = _whitelist_dict(a_dict.get(k), nested_filter.attrs, filter_value)
            break
        a_dict = a_dict.get(k)
    return input_dict


def _whitelist_dict(input_dict, attrs, filter_value):
    for k in input_dict:
        if k not in attrs:
            input_dict[k] = filter_value
    return input_dict
