"""
Default config for DAL
"""
from wavelength_py.dal.dynamodb.util import BotoThrottleConfig


class DalConfig(BotoThrottleConfig):
    """
    DAL configuration settings
    """
    results_default_limit: int = 10
    # Table States:
    table_state_new = 'NEW'
    table_state_modified = 'MOD'
    table_state_deleted = 'DEL'
    table_state_invalid = 'ERR'
