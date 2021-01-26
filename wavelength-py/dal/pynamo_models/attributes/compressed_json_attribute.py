"""
Pynamo Attribute for supporting compressed JSON
"""

# TODO move to lib

import base64
import zlib
from typing import Optional

import simplejson as json
from pynamodb.attributes import JSONAttribute

from wavelength_serverless_lib.logging.slog import StructLog as log

COMPRESSED_KEY = '__COMP__'


class CompressedJSONAttribute(JSONAttribute):
    """
    Compressed nested document that is serialized/deserialized from Dynamo
    """

    def serialize(self, value: dict) -> str:
        """
        Takes a json-serializable object and compresses it
        :param value: dict to serialize
        :return:str
        """

        return super().serialize(self._zip(value))

    def deserialize(self, value: str) -> Optional[dict]:
        """
        Deserializes a JSON string and unpacks it into normal dict if compressed, otherwise returns raw
        :param value: str
        :return: dict
        """
        if not value:
            return None

        return self._unzip(super().deserialize(value))

    @classmethod
    def _zip(cls, source: dict) -> dict:
        """
        serialize and encode a dict,  then decode as ascii to reduce char set size
        :param source:
        :return:
        """

        if not source or not isinstance(source, dict):
            return source

        result = base64.b64encode(
            zlib.compress(
                json.dumps(source).encode()
            )
        ).decode('ascii')  # reduce charset

        return {
            COMPRESSED_KEY: result
        }

    @classmethod
    def _unzip(cls, source: dict) -> dict:
        """
        check source dict for compression key and decompress if present, otherwise pass through
        :param source: dict
        :return: dict
        """

        if not source or not isinstance(source, dict):
            return source

        if COMPRESSED_KEY not in source:
            return source

        try:
            return json.loads(zlib.decompress(base64.b64decode(source[COMPRESSED_KEY])).decode())
        except ValueError as verr:
            log.warn('Pynamo Nested Decompression Failure', source, error=verr)
            return source
