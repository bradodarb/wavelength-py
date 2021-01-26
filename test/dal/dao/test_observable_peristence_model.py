# -*- coding: utf-8 - *-

import logging
import unittest

from schematics.types import StringType

from wavelength_serverless_lib.dal.dao.models.observable_persistence_model import ObservablePersistenceModel

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class ModelTestMock(ObservablePersistenceModel):
    """
    Self-persisting base model
    """
    account_id = StringType()
    kind = StringType()


class TestObservablePersistenceModel(unittest.TestCase):

    def test_init(self):
        model = ModelTestMock({
            'account_id': '123345'
        }, protected_fields=[])

        self.assertEqual(model.account_id, '123345')

    def test_changes_are_tracked(self):
        model = ModelTestMock({
            'account_id': '123345'
        })
        model.kind = 'test kind'

        self.assertTrue('kind' in model._changes)

    def test_changes_can_be_reset(self):
        model = ModelTestMock({
            'account_id': '123345'
        })
        model.kind = 'test kind'

        self.assertTrue('kind' in model._changes)

        model.flush_changes()

        self.assertFalse(bool(model._changes))


if __name__ == '__main__':
    unittest.main()
