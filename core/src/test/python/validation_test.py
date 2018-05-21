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

from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases import alias_constants

import oracle.weblogic.deploy.util.TranslateException as TranslateException


class ValidationTestCase(unittest.TestCase):
    _program_name = 'validation_test'
    _class_name = 'ValidationTestCase'
    _resources_dir = '../../test-classes'
    # _variable_file = _resources_dir + "/test_sub_variable_file.properties"
    # _model_file = _resources_dir + '/test_empty.json'
    # _variable_file = _resources_dir + "/test_invalid_variable_file.properties"
    # _archive_file = _resources_dir + "/test_jms_archive.zip"
    _logger = PlatformLogger('wlsdeploy.validate')

    def setUp(self):
        self.name = 'ValidationTestCase'
        self.wls_helper = WebLogicHelper(self._logger)

    def testModelValidation(self):

        _model_file = self._resources_dir + '/test_jms_mail.json'
        _method_name = 'testModelValidation'

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-model_file': _model_file
        }

        model_context = ModelContext('ValidationTestCase', args_map)

        try:
            model_dictionary = FileToPython(model_context.get_model_file()).parse()
            model_validator = Validator(model_context,
                                        wlst_mode=WlstModes.ONLINE)
            return_code = model_validator.validate_in_tool_mode(model_dictionary,
                                                                model_context.get_variable_file(),
                                                                model_context.get_archive_file_name())
            self._logger.info('The Validator.validate_in_tool_mode() call returned {0}',
                              Validator.ReturnCode.from_value(return_code),
                              class_name=self._class_name, method_name=_method_name)
        except TranslateException, te:
            return_code = Validator.ReturnCode.STOP
            self._logger.severe('WLSDPLY-20009',
                                self._program_name,
                                model_context.get_model_file(),
                                te.getLocalizedMessage(), error=te,
                                class_name=self._class_name, method_name=_method_name)

        self.assertNotEqual(return_code, Validator.ReturnCode.STOP)

    def testIsCompatibleDataType(self):
        _method_name = 'testIsCompatibleDataType'

        for expected_data_type in alias_constants.ALIAS_DATA_TYPES:
            retval = validation_utils.is_compatible_data_type(expected_data_type, "<type 'str'>")
            if retval is False:
                self._logger.info('if/elif statements in validation_utils.is_compatible_data_type(), '
                                  'needs to updated to know about the {0} data type!',
                                  expected_data_type,
                                  class_name=self._class_name, method_name=_method_name)
            self.assertEqual(retval, True)

    def testYamlModelValidation(self):
        """
            Parse and validate a YAML model with '-' list type and attributes with negative values.
        """

        _model_file = self._resources_dir + '/simple-model.yaml'
        _archive_file = self._resources_dir + "/SingleAppDomain.zip"
        _method_name = 'testYamlModelValidation'

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-model_file': _model_file,
            '-archive_file': _archive_file
        }

        model_context = ModelContext('ValidationTestCase', args_map)

        try:
            model_dictionary = FileToPython(model_context.get_model_file()).parse()
            model_validator = Validator(model_context,
                                        wlst_mode=WlstModes.ONLINE)
            return_code = model_validator.validate_in_tool_mode(model_dictionary,
                                                                model_context.get_variable_file(),
                                                                model_context.get_archive_file_name())
            self._logger.info('The Validator.validate_in_tool_mode() call returned {0}',
                              Validator.ReturnCode.from_value(return_code),
                              class_name=self._class_name, method_name=_method_name)
        except TranslateException, te:
            return_code = Validator.ReturnCode.STOP
            self._logger.severe('WLSDPLY-20009',
                                self._program_name,
                                model_context.get_model_file(),
                                te.getLocalizedMessage(), error=te,
                                class_name=self._class_name, method_name=_method_name)

        self.assertNotEqual(return_code, Validator.ReturnCode.STOP)

if __name__ == '__main__':
    unittest.main()
