"""
Validation utils for Bravado
"""
from bravado_core.request import unmarshal_request
from bravado_core.spec import Spec
from bravado_core.validate import validate_object
from jsonschema import ValidationError
from schleppy import reach
from yaml import load, Loader

from wavelength_serverless_lib.errors.exceptions import Base422Exception
from wavelength_serverless_lib.validation.util import RequestValidationModel


class Validator:
    """
    Validation helper class for validating against OpenAPI schemas
    """

    def __init__(self, spec_file_path, options: dict = None):
        if not options:
            options = {
                'validate_swagger_spec': False,
                'validate_requests': True,
                'validate_responses': False,
                'use_models': True,
            }
        with open(spec_file_path, 'r') as spec:
            self.spec_source = load(spec.read(), Loader)
            self.spec = Spec.from_dict(self.spec_source, config=options)

    def validate(self, validation_key: str, model: dict):
        """
        Validate based on a schema definition
        :param validation_key: path in swagger document to find schema
        :param model: model to validate
        :return: None if validation is successful, otherwise an exception will be raised
        """
        spec = reach(self.spec_source, validation_key)
        if not spec:
            raise Base422Exception('No validation available',
                                   reason='A spec was requested but not resolved from API decs')
        try:
            validate_object(self.spec, spec, model)
        except ValidationError as verr:
            raise Base422Exception('Validation Failed', str(verr))

    def validate_request(self, resource: str, operation: str, model: RequestValidationModel):
        """
        Validate a 'request-like' object
        :param resource: API resource pointer
        :param operation: operation on resource
        :param model: model to validate
        :return: None if validation is successful, otherwise an exception will be raised
        """

        spec = self.spec.resources[resource].operations[operation]
        if not spec:
            raise Base422Exception('No validation available',
                                   reason='A spec was requested but not resolved from API decs')
        try:
            request_data = unmarshal_request(model, spec)
        except (ValidationError, BaseException) as err:
            raise Base422Exception('Validation Failed', str(err))
        return request_data
