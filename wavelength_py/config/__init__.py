# pylint: disable=invalid-name
# pylint: disable=protected-access
"""
Lightweight config value resolver
"""
import os

from typing import Union, Dict


class Config:
    """
    Class that resolves env vars as getters that can be given default values
    via class level members

    Env value will always override
    """

    LOCK_THRESHOLD = 0.1, float

    # Default values and constants:
    DEFAULT_LAMBDA_EXEC_MIN_TIME = 10000, int  # time in millis (10 second default)
    DEFAULT_REQUEST_TIMEOUT = 10, int
    MAX_NUMBER_OF_CLIENT_RETRIES = 5, int
    CLIENT_RETRY_WAIT_EXPONENTIAL_MULTIPLIER = 500, int
    CLIENT_RETRY_WAIT_EXPONENTIAL_MAX = 10000, int

    DATA_CACHE_TTL = .001, float

    def __init__(self):
        """
        creates default values from class members
        """
        instance_type = type(self)
        defaults_key = f'_{instance_type.__name__}__defaults'
        parsers_key = f'_{instance_type.__name__}__parsers'
        self.parsers = getattr(instance_type, parsers_key) if hasattr(instance_type, parsers_key) else {}
        self.defaults = getattr(instance_type, defaults_key) if hasattr(instance_type,
                                                                        defaults_key) else self.get_members()

        instance_type.__defaults = self.defaults
        instance_type.__parsers = self.parsers
        for item in self.defaults:
            if hasattr(instance_type, item):
                delattr(instance_type, item)

    def __getattr__(self, name) -> Union[str, int, float, bool]:
        """
        Attempt to resolve value from os.environ with fallback support for constants
        :param name: attribute namestr
        :return: Union[str, int, float, bool]
        """
        result = os.environ.get(name, self.defaults.get(name))
        if result:
            if type(self).__parsers.get(name):
                return type(self).__parsers[name](result)
        return result

    def parse_value(self, key, val) -> str:
        """
        Support supplied type converter, cache for later resolution
        :param val: if tuple, attempt to use second part of tuple to
        ensure to convert the value, defaults to str
        :return: Union[str, int, float, bool]
        """
        if isinstance(val, tuple) and callable(val[1]):
            self.parsers[key] = val[1]
            return str(val[0])

        return str(val)

    def get_members(self) -> Dict[str, str]:
        """
        Gets class level attributes
        :return: dict
        """
        return {k: self.parse_value(k, v) for k, v in vars(type(self)).items()
                if k and not isinstance(v, property) and not (callable(v) or k.startswith("__"))}

    @property
    def stage(self):
        """
        stage is an overwrite property.
        """
        return self.stageName


CONFIG = Config()
