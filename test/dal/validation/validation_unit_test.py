# -*- coding: utf-8 -*-

import logging
import os
import unittest

from wavelength_serverless_lib.errors.exceptions import Base422Exception
from wavelength_serverless_lib.validation.validation import Validator

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)

spec_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swagger.yml')
VALIDATION = Validator(spec_file_path)


class TestModelUtils(unittest.TestCase):

    def setUp(self):
        log.info("==================================================")
        log.info("======   Test: %s, SetUp", self.id())
        log.info("==================================================")

    def tearDown(self):
        log.info("--------------------------------------------------")
        log.info("------   Test: %s, TearDown", self.id())
        log.info("--------------------------------------------------")

    def test_validates_model(self):
        pet = {
            'id': 123,
            'name': 'fido'
        }
        self.assertIsNone(VALIDATION.validate('definitions.Pet', pet))

        with self.assertRaises(Base422Exception):
            VALIDATION.validate('definitions.Pet', {'id': 'bad'})


if __name__ == '__main__':
    unittest.main()
