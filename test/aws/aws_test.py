import copy
import logging
import os
import unittest
from unittest.mock import MagicMock

from wavelength_serverless_lib.aws.aws_args import (get_authorization_header, get_headers, get_profiles, get_stage, get_claims,
                                              get_account_id,
                                              get_profile_id, HEADER_PROFILE_INDEX_KEY, get_entitlements, convert_body,
                                              convert_response, get_standard_response)
from wavelength_serverless_lib.errors.exceptions import Base422Exception

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)

sample_claims = {
    "custom:eids": "{\"eids\": [\"freeuser\"]}",
    "sub": "6e7661cd-318b-462f-a9ee-78332fd47ee5",
    "aud": "1ejfg8lluvk6cptu0u1t8pocov",
    "email_verified": "true",
    "event_id": "c049eb19-a01f-11e8-bf1c-9f61f6e82f32",
    "token_use": "id",
    "auth_time": "1534291886",
    "iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_RNodTkuNC",
    "cognito:username": "6e7661cd-318b-462f-a9ee-78332fd47ee5",
    "exp": "Wed Aug 15 01:11:26 UTC 2018",
    "iat": "Wed Aug 15 00:11:26 UTC 2018",
    "email": "nbuser681532544304@yopmail.com",
    "custom:profiles": "{\"profiles\": [ \"1\", \"2\", \"3\" ]}"
}

sample_event = {
    "resource": "/v1/testtoken",
    "path": "/sandbox/v1/testtoken",
    "httpMethod": "POST",
    "headers": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Authorization": "Bearer token",
        "cache-control": "no-cache",
        "CloudFront-Forwarded-Proto": "https",
        "CloudFront-Is-Desktop-Viewer": "true",
        "CloudFront-Is-Mobile-Viewer": "false",
        "CloudFront-Is-SmartTV-Viewer": "false",
        "CloudFront-Is-Tablet-Viewer": "false",
        "CloudFront-Viewer-Country": "US",
        "Content-Type": "application/json",
        "Host": "customer.sb.newbrandly.com",
        "Postman-Token": "e4719f8d-d932-401e-a480-b27ff3c3235b",
        "User-Agent": "PostmanRuntime/7.2.0",
        "Via": "1.1 1b5145bfbdaeb845833051651ce0832c.cloudfront.net (CloudFront)",
        "X-Amz-Cf-Id": "zYOOZiuWLYe6dApwVmXihGL2PtoDWgMQuNoVY6adqL88I6U4NanfDg==",
        "X-Amzn-Trace-Id": "Root=1-5b736fb0-a63d04e83cbda50045597edc",
        "x-api-key": "65c9EAisGH17YYZLiU6yX7M0F5wqgOHe5cZGKO5n",
        "X-Forwarded-For": "98.165.84.12, 70.132.22.79",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https"
    },
    "queryStringParameters": None,
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "b1neah",
        "authorizer": {
            "claims": sample_claims
        },
        "resourcePath": "/v1/testtoken",
        "httpMethod": "POST",
        "extendedRequestId": "Lo5jpE8rPHcF9tQ=",
        "requestTime": "15/Aug/2018:00:11:28 +0000",
        "path": "/sandbox/v1/testtoken",
        "accountId": "944330392717",
        "protocol": "HTTP/1.1",
        "stage": "sandbox",
        "requestTimeEpoch": 1534291888908,
        "requestId": "c1b4c500-a01f-11e8-8f08-bbcb3ca01eb8",
        "identity": {
            "apiKey": "65c9EAisGH17YYZLiU6yX7M0F5wqgOHe5cZGKO5n",
            "apiKeyId": "h7lb0pgjkk",
            "userAgent": "PostmanRuntime/7.2.0",
            "sourceIp": "98.165.84.12",
        },
        "apiId": "nyzizgksql"
    },
    "body": None,
    "isBase64Encoded": False
}


class TestAWSUtils(unittest.TestCase):

    def test_get_stage(self):
        context_mock = MagicMock()
        context_mock.function_name = 'stage-func'
        self.assertEqual(get_stage(context_mock), 'stage')
        os.environ['AWS_LAMBDA_FUNCTION_NAME'] = 'stage2-func'
        self.assertEqual(get_stage(None), 'stage2')

    def test_get_profiles(self):
        self.assertEqual(get_profiles(sample_event), ['1', '2', '3'])

    def test_get_headers(self):
        self.assertEqual(get_headers(sample_event), sample_event['headers'])

    def test_get_authorization_header(self):
        self.assertEqual(get_authorization_header(sample_event),
                         sample_event['headers']['Authorization'])

    def test_get_authorization_header_non_existant(self):
        test_obj = {'headers': {}}
        self.assertEqual(get_authorization_header(test_obj),
                         None)

    def test_get_claims(self):
        self.assertEqual(get_claims(sample_event), sample_claims)

    def test_get_claims_fail(self):
        fail_sample_event = copy.deepcopy(sample_event)
        del fail_sample_event['requestContext']
        self.assertEqual(get_claims(fail_sample_event), {})

    def test_get_account_id(self):
        self.assertEqual(get_account_id(sample_event), sample_claims['sub'])

    def test_get_account_id_fail(self):
        fail_sample_event = copy.deepcopy(sample_event)
        del fail_sample_event['requestContext']
        self.assertEqual(get_account_id(fail_sample_event), None)

    def test_get_of_profile_id_default(self):
        self.assertEqual(get_profile_id(sample_event), sample_claims['sub'] + '-1')

    def test_get_of_profile_id_fail(self):
        fail_sample_event = copy.deepcopy(sample_event)
        profiles = get_profiles(fail_sample_event)
        fail_sample_event['headers'][HEADER_PROFILE_INDEX_KEY] = str(len(profiles) + 1)
        with self.assertRaises(Base422Exception):
            get_profile_id(fail_sample_event)

    def test_get_of_profile_id_2(self):
        new_sample_event = copy.deepcopy(sample_event)
        new_sample_event['headers'][HEADER_PROFILE_INDEX_KEY] = '2'
        self.assertEqual(get_profile_id(new_sample_event), sample_claims['sub'] + '-2')

    def test_get_entitlements(self):
        self.assertEqual(get_entitlements(sample_event), ['freeuser'])

    def test_convert_body(self):
        self.assertEqual(convert_body('{ "test_key": "test_val"}'), {"test_key": "test_val"})

    def test_convert_response(self):
        self.assertEqual(convert_response({'body': {'test_key': 'test_val'}}), {'body': '{"test_key": "test_val"}'})

    def test_convert_response_with_str(self):
        self.assertEqual(convert_response({'body': '{"test_key": "test_val"}'}), {'body': '{"test_key": "test_val"}'})

    def test_get_standard_response(self):
        self.assertEqual(get_standard_response({'test123'}, 200), {'body': {'test123'},
                                                                   'headers': {'Access-Control-Allow-Credentials': True,
                                                                               'Access-Control-Allow-Origin': '*'},
                                                                   'statusCode': 200})

    def test_get_standard_response_300(self):
        self.assertEqual(get_standard_response({},
                                               300,
                                               {'header1': 'header_val_1'}),
                         {'body': {},
                          'headers': {'header1': 'header_val_1',
                                      'Access-Control-Allow-Credentials': True,
                                      'Access-Control-Allow-Origin': '*'},
                          'statusCode': 300})

    def test_get_standard_response_no_cors(self):
        self.assertEqual(get_standard_response({},
                                               200,
                                               {'header1': 'header_val_1'},
                                               False),
                         {'body': {},
                          'headers': {'header1': 'header_val_1'},
                          'statusCode': 200})


if __name__ == '__main__':
    unittest.main()
