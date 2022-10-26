"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest
import os
from java.util.logging import Level

from oracle.weblogic.deploy.logging import SummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.model_context import ModelContext

from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases import alias_constants

from validate import __perform_model_file_validation

import oracle.weblogic.deploy.util.TranslateException as TranslateException
import oracle.weblogic.deploy.validate.ValidateException as ValidateException

from wlsdeploy.tool.create import wlsroles_helper


class ValidationTestCase(unittest.TestCase):
    _program_name = 'validation_test'
    _class_name = 'ValidationTestCase'
    _resources_dir = '..' + os.sep + '..' + os.sep + 'test-classes'
    # Model persistence file
    _wlsdeply_store_model = os.path.abspath(os.getcwd()) + os.sep + _resources_dir + os.sep + 'validate-mii-model.json'
    # _variable_file = _resources_dir + "/test_sub_variable_file.properties"
    # _model_file = _resources_dir + '/test_empty.json'
    # _variable_file = _resources_dir + "/test_invalid_variable_file.properties"
    # _archive_file = _resources_dir + "/test_jms_archive.zip"
    _wls_version = '12.2.1.3'

    def setUp(self):
        self.name = 'ValidationTestCase'
        self._logger = PlatformLogger('wlsdeploy.validate')
        self.wls_helper = WebLogicHelper(self._logger)

        # add summary handler to validate logger to check results
        self._summary_handler = SummaryHandler()
        self._logger.logger.addHandler(self._summary_handler)

        # Define custom configuration path for WDT
        os.environ['WDT_CUSTOM_CONFIG'] = self._resources_dir
        # Indicate that WDT should persist model file
        os.environ['__WLSDEPLOY_STORE_MODEL__'] = self._wlsdeply_store_model

    def tearDown(self):
        # remove summary handler for next test suite
        self._logger.logger.removeHandler(self._summary_handler)
        WLSDeployLogEndHandler.clearHandlers()

        # Clean up temporary WDT custom configuration environment variables
        # and model persistence files
        del os.environ['WDT_CUSTOM_CONFIG']
        del os.environ['__WLSDEPLOY_STORE_MODEL__']
        self.deleteFile(self._wlsdeply_store_model)

    def testModelValidation(self):
        _method_name = 'testModelValidation'

        # The model file refers to two File Stores that are not in the archive so validation should fail.

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
        aliases = Aliases(model_context, wls_version=self._wls_version)

        try:
            model_dictionary = FileToPython(model_context.get_model_file()).parse()
            model_validator = Validator(model_context, aliases, wlst_mode=WlstModes.ONLINE)
            return_code = model_validator.validate_in_tool_mode(model_dictionary,
                                                                model_context.get_variable_file(),
                                                                model_context.get_archive_file_name())
        except TranslateException, te:
            return_code = Validator.ReturnCode.STOP
            self._logger.severe('WLSDPLY-20009',
                                self._program_name,
                                model_context.get_model_file(),
                                te.getLocalizedMessage(), error=te,
                                class_name=self._class_name, method_name=_method_name)

        self.assertEqual(return_code, Validator.ReturnCode.STOP)

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
        aliases = Aliases(model_context, wls_version=self._wls_version)

        try:
            model_dictionary = FileToPython(model_context.get_model_file()).parse()
            model_validator = Validator(model_context, aliases, wlst_mode=WlstModes.ONLINE)
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

    def testWLSRolesValidation(self):
        """
        Run the validation portion of the WLSRoles helper and check for expected results.
        """
        _method_name = 'testWLSRolesValidation'

        wlsroles_dict = {'Admin':     {'UpdateMode': 'append',
                                       'Expression': 'Grp(AppAdmin)'},
                         'Deployer':  {'UpdateMode': 'prepend',
                                       'Expression': 'Grp(AppDeployer)'},
                         'Tester':    {'Expression': 'Grp(AppTester)'},
                         'MyEmpty':   { },
                         'MyTester':  {'UpdateMode': 'append',
                                       'Expression': 'Grp(MyTester)'},
                         'MyTester2': {'UpdateMode': 'replace',
                                       'Expression': 'Grp(MyTester2)'},
                         'MyTester3': {'UpdateMode': 'bad',
                                       'Expression': 'Grp(MyTester3)'}}

        wlsroles_validator = wlsroles_helper.validator(wlsroles_dict, self._logger)
        wlsroles_validator.validate_roles()

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify only warnings resulted
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 0)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 3)

    def testFilterInvokedOnModelValidation(self):
        """
        Verify filter was run and changes are persisted to model file
        """

        # Setup model context arguments
        _model_file = self._resources_dir + '/simple-model.yaml'
        _archive_file = self._resources_dir + "/SingleAppDomain.zip"
        _method_name = 'testFilterInvokedOnModelValidation'

        mw_home = os.environ['MW_HOME']

        args_map = {
          '-oracle_home': mw_home,
          '-model_file': _model_file,
          '-archive_file': _archive_file
        }

        model_context = ModelContext('validate', args_map)

        try:
          # Invoke model validation
          __perform_model_file_validation(_model_file, model_context)

          # read persisted model file and convert to python dictionary
          model_dictionary = FileToPython(self._wlsdeply_store_model, True)._parse_json()
        except ValidateException, ve:
          self._logger.severe('WLSDPLY-20000', self._program_name, ve.getLocalizedMessage(), error=ve,
                        class_name=self._class_name, method_name=_method_name)

        # assert the validate filter made modifications and was persisted
        self.assertEquals('gumby1234', model_dictionary['domainInfo']['AdminPassword'], "Expected validate filter to have changed AdminPassword to 'gumby1234'")

    def deleteFile(self, path):
      try:
        os.remove(path)
      except OSError:
        pass

if __name__ == '__main__':
    unittest.main()
