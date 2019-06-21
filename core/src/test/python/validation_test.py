"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest
import os

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.model_context import ModelContext

import validate
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases import alias_constants

import oracle.weblogic.deploy.util.TranslateException as TranslateException
from oracle.weblogic.deploy.validate import ValidateException

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
        _method_name = 'testModelValidation'

        _model_file = self._resources_dir + '/variablestest.yaml'
        _variable_file = self._resources_dir + '/variablestest.properties'
        _archive_file = self._resources_dir + '/variablestest.zip'

        mw_home = os.environ['MW_HOME']
        args_map = {
            '-oracle_home': mw_home,
            '-model_file': _model_file,
            '-variable_file': _variable_file,
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

    def testPrintUsageFoldersOnly(self):
        _method_name = 'testPrintUsageFoldersOnly'

        _FOLDERS_ONLY = '-folders_only'

        args = {
            '-oracle_home': os.environ['MW_HOME']
        }

        model_paths = [
            'resources:/FileStore'
        ]

        try:
            # Loop through valid list of model sections
            for model_path in model_paths:
                # Set print usage context
                args['-print_usage'] = '%s %s' % (model_path, _FOLDERS_ONLY)
                self._logger.info('args={0}', str(args), class_name=self._class_name, method_name=_method_name)
                model_context = ModelContext(self._program_name, args)
                model_validator = Validator(model_context, wlst_mode=WlstModes.ONLINE)
                model_validator.print_usage(model_path)
                self.assertEquals(True, True)
        except ValidateException, ve:
            self.fail(ve.getLocalizedMessage())

        return

    def testPrintUsageAttributesOnly(self):
        _method_name = 'testPrintUsageAttributesOnly'

        _ATTRIBUTES_ONLY = '-attributes_only'

        args = {
            '-oracle_home': os.environ['MW_HOME']
        }

        model_paths = [
            'domainInfo'
        ]

        try:
            # Loop through valid list of model sections
            for model_path in model_paths:
                # Set print usage context
                args['-print_usage'] = '%s %s' % (model_path, _ATTRIBUTES_ONLY)
                self._logger.info('args={0}', str(args), class_name=self._class_name, method_name=_method_name)
                model_context = ModelContext(self._program_name, args)
                model_validator = Validator(model_context, wlst_mode=WlstModes.ONLINE)
                model_validator.print_usage(model_path)
                self.assertEquals(True, True)
        except ValidateException, ve:
            self.fail(ve.getLocalizedMessage())

        return

    def testPrintUsageRecursive(self):
        _method_name = 'testPrintUsageRecursive'

        _RECURSIVE = '-recursive'

        args = {
            '-oracle_home': os.environ['MW_HOME']
        }

        model_paths = [
            'appDeployments:/Application'
        ]

        try:
            # Loop through valid list of model sections
            for model_path in model_paths:
                # Set print usage context
                args['-print_usage'] = '%s %s' % (model_path, _RECURSIVE)
                self._logger.info('args={0}', str(args), class_name=self._class_name, method_name=_method_name)
                model_context = ModelContext(self._program_name, args)
                model_validator = Validator(model_context, wlst_mode=WlstModes.ONLINE)
                model_validator.print_usage(model_path)
                self.assertEquals(True, True)
        except ValidateException, ve:
            self.fail(ve.getLocalizedMessage())

        return

    # def testPrintUsageCLAEnforcement(self):
    #     _method_name = 'testPrintUsageCLAEnforcement'
    #
    #     _FOLDERS_ONLY = '-folders_only'
    #     _RECURSIVE = '-recursive'
    #
    #     args = list()
    #     args.append(self._program_name)
    #     args.append('-oracle_home')
    #     args.append(os.environ['MW_HOME'])
    #     args.append('-print_usage')
    #     args.append('topology:/Server')
    #     args.append(_FOLDERS_ONLY)
    #     args.append(_RECURSIVE)
    #
    #     self._logger.info('args={0}', str(args), class_name=self._class_name, method_name=_method_name)
    #
    #     try:
    #         # Should raise an exception because control options
    #         # are mutually exclusive, and we passed _FOLDERS_ONLY
    #         # and _RECURSIVE
    #         validate.main(args)
    #     except SystemExit, se:
    #         exit_code = str(se)
    #         self.assertEqual(exit_code, '0')
    #
    #     return

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
