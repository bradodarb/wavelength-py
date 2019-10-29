import logging
import os
# Kill Logging noise

if not os.environ.get('DEBUG'):
    logging.getLogger('pynamodb').setLevel(logging.CRITICAL)
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('nose').setLevel(logging.CRITICAL)
    logging.disable(logging.CRITICAL)
