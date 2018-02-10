"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import unittest
import os
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.model_context import ModelContext

from wlsdeploy.validation.validator import Validator

import oracle.weblogic.deploy.util.TranslateException as TranslateException


class ValidationTestCase(unittest.TestCase):
    _program_name = 'validation_test'
    _class_name = 'ValidationTestCase'
    _resources_dir = '../../test-classes'
    _jms_mail_model_file = _resources_dir + '/test_jms_mail.json'
    _variable_file = _resources_dir + "/test_sub_variable_file.properties"
    _archive_file = _resources_dir + "/test_jms_archive.zip"
    _logger = PlatformLogger('wlsdeploy.validate')

    def setUp(self):
        self.name = 'ValidationTestCase'
        self.wls_helper = WebLogicHelper(self._logger)

    def testModelValidation(self):

        _method_name = 'testModelValidation'

        mw_home = os.environ['MW_HOME']
        args_map = {'-archive_file': self._archive_file, '-variable_file': self._variable_file,
                    '-oracle_home': mw_home, '-model_file': self._jms_mail_model_file}

        model_context = ModelContext('ValidationTestCase', args_map)

        try:
            model_dictionary = FileToPython(self._jms_mail_model_file).parse()
            model_validator = Validator(model_context)
            validation_status = model_validator.validate_in_tool_mode(model_dictionary,
                                                                      self._variable_file,
                                                                      self._archive_file)
            self._logger.info('WLSDPLY-03153',
                              Validator.ValidationStatus.from_value(validation_status),
                              class_name=self._class_name, method_name=_method_name)
        except TranslateException, te:
            validation_status = Validator.ValidationStatus.INVALID
            self._logger.severe('WLSDPLY-03162',
                                self._program_name,
                                self._jms_mail_model_file,
                                te.getLocalizedMessage(), error=te,
                                class_name=self._class_name, method_name=_method_name)

        self.assertNotEqual(validation_status, Validator.ValidationStatus.INVALID)

if __name__ == '__main__':
    unittest.main()