""" Base Model """
import json
from collections import OrderedDict
from typing import Dict, Any

import re
import simplejson
from schematics import Model
from schematics.exceptions import DataError

from exos_serverless_lib.errors.exceptions import Base422Exception


class BaseModel(Model):
    """ Base class for deriving models (request && response) """

    def __init__(self, *args, **kwargs):
        try:
            kwargs['validate'] = kwargs.get('validate', True)
            super(BaseModel, self).__init__(*args, **kwargs)
        except (DataError, Exception) as error:
            raise Base422Exception(str(error)) from error

    def to_json(self):
        """ Camel-case and serialize dao to dict
        :return: dict
        """
        source = self.to_primitive()
        return BaseModel.convert_dict(source, BaseModel.to_camel_case)

    def to_dumps(self):
        """ Camel-case and serialize dao to JSON string
        :return: str
        """
        return json.dumps(self.to_json())

    def from_json(self, source):
        """  Builds dao from a camel-cased dict
        :param source: camel-cased dict
        :return: None
        """

        ctor = BaseModel.convert_dict(source, BaseModel.to_snake_case)
        self.__init__(ctor)
        return self

    def from_jsons(self, source):
        """ Builds dao from a JSON string
        :param source:
        :return: None
        """
        result = json.loads(source)
        self.from_json(result)
        return self

    @classmethod
    def convert_dict(cls, source, conversion):
        """  Recursively converts dict keys based on passed in conversion function
        :param self:
        :param source:
        :param conversion:
        :return:
        """
        result = OrderedDict()
        for k in source:
            key = conversion(k)
            if isinstance(source[k], dict):
                result[key] = BaseModel.convert_dict(source[k], conversion)
            elif isinstance(source[k], list):
                result[key] = BaseModel.convert_list(source[k], conversion)
            else:
                result[key] = source[k]
        return result

    @classmethod
    def convert_list(cls, source, conversion):
        """  Recursively converts list items based on passed in conversion function
        :param self:
        :param source:
        :param conversion:
        :return:
        """
        result = []
        for i in source:
            if isinstance(i, list):
                result.append(BaseModel.convert_list(i, conversion))
            elif isinstance(i, dict):
                result.append(BaseModel.convert_dict(i, conversion))
            else:
                result.append(i)
        return result

    @classmethod
    def to_camel_case(cls, word, uppercase_first_letter=False):
        """ Convert strings to CamelCase.
        @param word: str to convert
        @param uppercase_first_letter: boolean True if first letter is upper
        """
        if uppercase_first_letter:
            return re.sub(r"(?:^|_)(.)", lambda m: m.group(1).upper(), word)

        return word[0].lower() + BaseModel.to_camel_case(word, True)[1:]

    @classmethod
    def to_snake_case(cls, word):
        """ Convert strings to snake_case.
        @param word: str to convert
        """
        word = re.sub(r"([A-Z]+)([A-Z][a-z])", r'\1_\2', word)
        word = re.sub(r"([a-z\d])([A-Z])", r'\1_\2', word)
        word = word.replace("-", "_")
        return word.lower()


class SerializerBase:
    """
    Utility class to facilitate converting objects to dicts
    """

    def json_from_key(self, keys: list) -> Dict[str, Any]:
        """
        builds a dict from the supplied keys
        :param keys: list[str]
        :return: dict
        """
        result = {}  # type: Dict[str, Any]
        for key in keys:
            if hasattr(self, key):
                result.update(**{key: getattr(self, key)})
        return result

    def dumps_from(self, keys: list) -> str:
        """
        Converts to dict then serializes as to string
        :param keys: list[str]
        :return: str
        """
        result = self.json_from_key(keys)
        return simplejson.dumps(result)
