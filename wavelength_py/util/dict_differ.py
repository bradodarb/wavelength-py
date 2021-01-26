"""
Finds delta on two dicts for things like change detection
"""


class DictDiffer:
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, new_dict, past_dict):
        """
        Constructor pass two dicts current and the original
        """

        self._new_dict, self._past_dict = new_dict, past_dict
        self._set_new, self._set_past = set(new_dict.keys()), set(past_dict.keys())
        self._intersect = self._set_new.intersection(self._set_past)

    def added(self):
        """
        Get keys of added dict items to new dictionary
        """
        return self._set_new - self._intersect

    def removed(self):
        """
        Get removed keys from old dict to new
        """
        return self._set_past - self._intersect

    def changed(self):
        """
        Get keys of changed dict values of the same key
        """
        return set(o for o in self._intersect if self._past_dict[o] != self._new_dict[o])

    def unchanged(self):
        """
        Get unchanged values of the same key
        """
        return set(o for o in self._intersect if self._past_dict[o] == self._new_dict[o])
