# # TODO - enable this once used on a project
# """
# Module to support creating a lock like object
# """
# import time
#
# from pynamodb.exceptions import PutError
# from pynamodb.expressions.condition import And, Or
# from pynamodb.expressions.operand import Path
#
# from wavelength_py.config import CONFIG
# from wavelength_py.dal.dao.commands.post_filter_pynamo_command import PostFilteredPynamoCommand
# from wavelength_py.dal.dao.models.platform_persistence_model import PynamoPersistenceModel
# from wavelength_py.dal.pynamo_models.util import pynamo_write_handler
# from wavelength_py.errors.exceptions import Base404Exception, Base409Exception
# from wavelength_py.model.util import get_posix_timestamp
#
#
# class AcquireLockFailureException(Base409Exception):
#     """
#     409 Exception unable to acquire lock for resource.
#     """
#
#
# class PynamoAquireLockCommand(PostFilteredPynamoCommand):
#     """
#     This class encapsulates creating a lock type object
#     """
#
#     def __init__(self, parent_model: PynamoPersistenceModel):
#         super().__init__(parent_model, post_filter=filter_active_locks)
#         self._validate_db_model_schema()
#         self.lock = None
#
#     def _validate_db_model_schema(self):
#         return (hasattr(self._parent.db_model, 'ttl') and
#                 hasattr(self._parent.db_model, 'created_at') and
#                 hasattr(self._parent.db_model, 'kind'))
#
#     def _execute(self):
#         """
#         Execute - Attempt to create a lock model and return the result if successful,
#          otherwise return None if one exists and isn't expired
#         :return: None
#         """
#         self.lock = self._create_lock()
#         if self.lock:
#             return self._parent.build(self.lock.to_json())
#         return self._check_lock_exists()
#
#     def __call__(self):
#         return self._execute()
#
#     def _check_lock_exists(self):
#         try:
#             result = super()._execute()
#         except Base404Exception:
#             # No model was found in super
#             return False
#
#         if result:
#             raise AcquireLockFailureException('Failed to lock. A different process is running.')
#
#         return False
#
#     @pynamo_write_handler
#     def _create_lock(self):
#         """
#         Create record
#         :return:None
#         """
#         now = int(time.time())
#         ttl = (now + CONFIG.LOCK_THRESHOLD)
#         created_at = get_posix_timestamp()
#         keys = self._parent.get_key()
#         if len(keys) > 1:
#             raise ValueError('Lock command only supports single keyed models')
#         record = self._parent.db_model(keys[0], created_at=created_at, ttl=ttl, kind=self._parent.kind)
#         try:
#             record.save(Or(self._parent.db_model.hash_id.does_not_exist(),
#                            And(self._parent.db_model.hash_id == Path(self._parent.hash_id),
#                                self._parent.db_model.ttl <= now)))
#         except PutError:
#             return None
#
#         return record
#
#
# def filter_active_locks(record):
#     """
#     Return True if a lock was found but the TTL was expired, otherwise return False
#     """
#     if record and record.ttl:
#         now = int(time.time())
#         return record.ttl > now
#     return False
