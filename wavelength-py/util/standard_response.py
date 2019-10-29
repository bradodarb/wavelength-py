"""
Standard response formatter for Lambda
"""


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
    output, out_headers = {'statusCode': status_code}, {}
    if headers:
        out_headers.update(headers)
    if add_cors:
        out_headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True
        })
    output['headers'] = out_headers
    output['body'] = body
    return output
