import logging
import unittest

from botocore.exceptions import ClientError

from exos_serverless_lib.aws.boto_helper import is_a_boto3_throttle_error

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)

error_response_throttling = {
    'ResponseMetadata': {
        'RetryAttempts': 0,
        'HTTPStatusCode': 429,
        'RequestId': 'test_id',
        'HTTPHeaders': {'x-amzn-requestid': 'test_id',
                        'content-length': '100',
                        'connection': 'keep-alive',
                        'date': 'Sept, 25 Mar 2017 23:59:59 GMT',
                        'content-type': 'application/json',
                        'x-amzn-errortype': 'RequestLimitExceeded'
                        },
    },
    'Error': {
        'Message': u'Invalid REST API identifier specified',
        'Code': 'NotFoundException'
    }
}


class TestExceptions(unittest.TestCase):
    error_response_not_throttling = {
        'ResponseMetadata': {
            'RetryAttempts': 0,
            'HTTPStatusCode': 404,
            'RequestId': 'test_id',
            'HTTPHeaders': {'x-amzn-requestid': 'test_id',
                            'content-length': '100',
                            'connection': 'keep-alive',
                            'date': 'Sept, 25 Mar 2017 23:59:59 GMT',
                            'content-type': 'application/json',
                            'x-amzn-errortype': 'NotFoundException'
                            },
        },
        'Error': {
            'Message': u'Invalid REST API identifier specified',
            'Code': 'NotFoundException'
        }
    }

    def test_is_a_boto3_throttle_error(self):
        self.assertTrue(
            is_a_boto3_throttle_error(
                ClientError(
                    error_response_throttling,
                    'test_operation')))


if __name__ == '__main__':
    unittest.main()
