"""
Boto utils
"""
from botocore.exceptions import ClientError


def get_boto3_error(error):
    """
    must be an instance of botocore.exceptions ClientError.
    """
    aws = {}
    message = ''

    # boto3 response
    if hasattr(error, 'response'):
        meta = error.response.get('ResponseMetadata')
        if meta:
            aws['status'] = meta['HTTPStatusCode']
        error = error.response.get('Error')
        if error:
            aws['code'] = error['Code']
            aws['message'] = error['Message']

    if hasattr(error, 'operation_name'):
        aws['op'] = error.operation_name

    if hasattr(error, 'message') or hasattr(error, 'Message'):
        message = error.message
    elif aws.get('message') or aws.get('Message'):
        message = aws['message']

    return {'message': message, 'aws': aws}


def is_a_boto3_throttle_error(error):
    """
    error must be an instance of botocore.exceptions ClientError.
    Determines if the error is a type of throttling error from AWS
    """
    if isinstance(error, ClientError):
        error = get_boto3_error(error)
    elif isinstance(error, dict) is False:
        return False

    http_status_code = error.get('aws', {}).get('status')
    if http_status_code in (429,):
        # too many requests = 429
        return True

    # not all AWS services adhere to the http request status code of 429 for
    # too many requests, do an error code check
    # this is fairly crude, to really do this properly exhaustively, have to
    # look at all the service specific schema files under botocore/data/
    # this just captures what are the retry codes that default botocore/data/_retry.json
    # looks for before it was set to an empty json object at build time.
    error_type = error.get('aws', {}).get('code')
    return error_type in ('Throttling', 'ThrottlingException',
                          'ProvisionedThroughputExceededException', 'RequestLimitExceeded',
                          'RequestThrottled', 'LimitExceededException',
                          'BandwidthLimitExceeded', 'TooManyRequestsException')
