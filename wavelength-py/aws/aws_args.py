"""
Common utils for extracting info from AWS data structures
"""
import json
import os

from schleppy import reach

from wavelength_serverless_lib.errors.exceptions import Base422Exception
from wavelength_serverless_lib.util import standard_response

HEADER_PROFILE_INDEX_KEY = 'PROFILE_IDX'
EIDS_CUSTOM_CLAIM = "custom:eids"
PROFILES_CUSTOM_CLAIM = "custom:profiles"


def get_stage(context=None):
    """
    Retrieves the stage based on a few possible input(s)
    is stage declared in the event.
    is stage prefixed in the function name in the context.
    is stage prefixed in the function name as an env variable.
    """
    if context is not None:
        tokens = context.function_name.split('-')
    else:
        tokens = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', '').split('-')
    return tokens[-2] if (len(tokens) > 1) else None


def convert_body(body):
    """
    Attempts to convert the body of an event to a json object.
    This is a general function not necessarily just for events.
    In the event it is unable to convert to json the original input is returned.
    """
    if body and isinstance(body, str):
        try:
            return json.loads(body)
        except Exception:  # pylint: disable=broad-except
            pass
    return body


def convert_response(response):
    """
    Attempts to converts the body of an event from a str to json object.
    """
    if response and isinstance(response, dict):
        body = response.get('body')
        if body is not None and not isinstance(body, str):
            try:
                response['body'] = json.dumps(body)
            except Exception:  # pylint: disable=broad-except
                pass
    return response


def get_profile_id(event):
    """
    Gets the profile id from an event containing the authorization markup from a AWS authorizer
    Default behavior,
    if the OF:PROFILE_IDX header is not set it defaults to the first profile
    If the profiles field is not set in the authorization code it defaults to the first profile.

    return profile id or None, if the event is malformed, missing 'sub' in a claim

    Raises Base422Exception if profiles are defined as a claim and the index in the header is out of range
    """
    account_id = get_account_id(event)
    if not account_id:
        return None

    index = 1
    headers = get_headers(event)
    if headers:
        index = int(headers.get(HEADER_PROFILE_INDEX_KEY, '1'))
        if (index > 1) and (index > len(get_profiles(event))):
            raise Base422Exception('Invalid Profile Index Header, index value outside of profiles list length')
    return account_id + f'-{index}'


def get_headers(event):
    """Gets the headers from the standard lambda event."""

    return event.get('headers', {})


def get_authorization_header(event):
    """Gets the authorization header from the standard lambda event, returns None if not present."""

    return reach(event, "headers.Authorization", options={'default': None})


def get_claims(event):
    """Attempts to get the dictionary of claims from within standard lambda event."""

    return reach(event, 'requestContext.authorizer.claims', options={'default': {}})


def get_account_id(event):
    """Gets the account id from a standard lambda event."""

    return reach(event, 'requestContext.authorizer.claims.sub', options={'default': None})


def get_entitlements(event):
    """Gets the list of entitlement from within standard lambda event."""

    claims = get_claims(event)
    if claims:
        return convert_body(claims.get(EIDS_CUSTOM_CLAIM, {'eids': []})).get('eids')
    return {}


def get_profiles(event):
    """Gets the list of profiles from a claim within standard lambda event."""
    claims = get_claims(event)
    if claims:
        return convert_body(claims.get(PROFILES_CUSTOM_CLAIM, {'profiles': []})).get('profiles')
    return []


def get_standard_response(body, status_code=200, headers=None, add_cors=True):
    """
    Creates the standard response for a lambda return.
    params
        body: a string or object to return, do not covert using json dumps before,
               this will be handled in the log lambda wrapper to enahnce return
               logging by keeping the response as an object until it is returned.
        status_code: standard HTTP status code result, use the standard exception to handle non 200 and 300 results.
                     Do not handle 400 or 500 errors here. Raise and standard 400 or 500 exception will be handled by
                     the log lambda decorator
        headers: Any additional non CORS header, for CORS header use the add_cors parameter (true by default_
        add_cors: Adds cors headers, default is true (always)
    """
    return standard_response.get_standard_response(body, status_code, headers, add_cors)  # Backward compatible
