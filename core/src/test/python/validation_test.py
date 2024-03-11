"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil
import unittest

from java.util.logging import Level
from oracle.weblogic.deploy.logging import SummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import TranslateException

from base_test import BaseTestCase
from validate import __perform_model_file_validation
from wlsdeploy.aliases import alias_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create import wlspolicies_helper
from wlsdeploy.tool.create import wlsroles_helper
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import env_helper
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class ValidationTestCase(BaseTestCase):
    _program_name = 'validation_test'
    _class_name = 'ValidationTestCase'
    _wls_version = '12.2.1.3'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.RESOURCES_DIR = os.path.join(self.TEST_CLASSES_DIR, 'validation')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'validation')
        self.STORE_MODEL = os.path.join(self.OUTPUT_DIR, 'validate-mii-model.json')

    def setUp(self):
        BaseTestCase.setUp(self)
        self.name = 'ValidationTestCase'
        self._logger = PlatformLogger('wlsdeploy.validate')
        self.wls_helper = WebLogicHelper(self._logger)

        # add summary handler to validate logger to check results
        self._summary_handler = SummaryHandler()
        self._logger.logger.addHandler(self._summary_handler)

        # Indicate that WDT should persist model file, including test filter
        self._establish_directory(self.OUTPUT_DIR)
        os.environ['__WLSDEPLOY_STORE_MODEL__'] = self.STORE_MODEL

        # Define custom configuration path for WDT, with custom filter files
        self.config_dir = self._set_custom_config_dir('validation-wdt-config')
        source_filters_file = os.path.join(self.RESOURCES_DIR, 'model_filters.json')
        shutil.copy(source_filters_file, self.config_dir)

    def tearDown(self):
        BaseTestCase.tearDown(self)
        # remove summary handler for next test suite
        self._logger.logger.removeHandler(self._summary_handler)
        WLSDeployLogEndHandler.clearHandlers()

        # Clean up model persistence file
        del os.environ['__WLSDEPLOY_STORE_MODEL__']

        # clean up temporary WDT custom configuration environment variable
        self._clear_custom_config_dir()

    def testModelValidation(self):
        _method_name = 'testModelValidation'

        # The model file refers to two File Stores that are not in the archive so validation should fail.

        _model_file = self.RESOURCES_DIR + '/variablestest.yaml'
        _variable_file = self.RESOURCES_DIR + '/variablestest.properties'
        _archive_file = self.RESOURCES_DIR + '/variablestest.zip'

        mw_home = env_helper.getenv('MW_HOME')
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

        _model_file = self.TEST_CLASSES_DIR + '/simple-model.yaml'
        _archive_file = self.TEST_CLASSES_DIR + "/SingleAppDomain.zip"
        _method_name = 'testYamlModelValidation'

        mw_home = env_helper.getenv('MW_HOME')
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

    def testYamlModelValidationWithRemoteOption(self):
        """
            Parse and validate a YAML model with '-remote' option, should fail with path error.
        """

        _model_file = self.TEST_CLASSES_DIR + '/simple-model2.yaml'
        _archive_file = self.TEST_CLASSES_DIR + "/SingleAppDomain.zip"
        _method_name = 'testYamlModelValidation'

        mw_home = env_helper.getenv('MW_HOME')
        args_map = {
            '-oracle_home': mw_home,
            '-model_file': _model_file,
            '-archive_file': _archive_file
        }

        model_context = ModelContext('ValidationTestCase', args_map)
        aliases = Aliases(model_context, wls_version=self._wls_version)
        model_context._remote = True
        try:
            model_dictionary = FileToPython(model_context.get_model_file()).parse()
            model_validator = Validator(model_context, aliases, wlst_mode=WlstModes.ONLINE)
            return_code = model_validator.validate_in_tool_mode(model_dictionary,
                                                                model_context.get_variable_file(),
                                                                model_context.get_archive_file_name())

            summary_handler = WLSDeployLogEndHandler.getSummaryHandler()
            self.assertNotEqual(summary_handler, None, "Summary Handler is None")
            self.assertEqual(summary_handler.getMaximumMessageLevel(), Level.SEVERE, "No SEVERE messages found")
            # 2 messages complaining about the path of these
            # domainBin: [ 'wlsdeploy/domainBin/setUserOverrides.sh' ]
            # domainLibraries: [ 'wlsdeploy/domainLibraries/fake.jar' ]
            self.assertEqual(summary_handler.getMessageCount(Level.SEVERE), 2, "Number of SEVERE messages do not match")
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

        self.assertEqual(return_code, Validator.ReturnCode.STOP)

    def test_wls_policies_validation(self):
        """
        Run the validation portion of the WLSPolicies helper and check for expected results.
        """
        wls_policies_dict = {
            'BuiltinPolicy': {
                'ResourceID': 'type=<jms>',
                'Policy': 'Grp(Monitors)'
            },
            'MissingResourceIDPolicy': {
                'Policy': 'Grp(Administrators)'
            },
            'MissingPolicyPolicy': {
                'ResourceID': 'type=<jms>, application=MyJmsModule, destinationType=queue, resource=MyQueue, action=browse'
            },
            'MyQueueBrowsePolicy': {
                'ResourceID': 'type=<jms>, application=MyJmsModule, destinationType=queue, resource=MyQueue, action=browse',
                'Policy': 'Grp(Administrators)'
            }
        }

        wls_policies_validator = wlspolicies_helper.get_wls_policies_validator(wls_policies_dict, None, self._logger)
        wls_policies_validator.validate_policies()

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify only 3 errors resulted
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 3)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

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

        wlsroles_validator = wlsroles_helper.get_wls_roles_validator(wlsroles_dict, self._logger)
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
        _model_file = self.TEST_CLASSES_DIR + '/simple-model.yaml'
        _archive_file = self.TEST_CLASSES_DIR + "/SingleAppDomain.zip"
        _method_name = 'testFilterInvokedOnModelValidation'

        mw_home = env_helper.getenv('MW_HOME')

        args_map = {
          '-oracle_home': mw_home,
          '-model_file': _model_file,
          '-archive_file': _archive_file
        }

        model_context = ModelContext('validate', args_map)

        # Invoke model validation
        __perform_model_file_validation(_model_file, model_context)

        # read persisted model file and convert to python dictionary
        model_dictionary = FileToPython(self.STORE_MODEL, True)._parse_json()

        # assert the validate filter made modifications and was persisted
        self.assertEquals('gumby1234', model_dictionary['domainInfo']['AdminPassword'],
                          "Expected validate filter to have changed AdminPassword to 'gumby1234'")

    def testDeploymentValidation(self):
        """
        Test for bad directory names in archive paths.
        """
        _method_name = 'testDeploymentValidation'

        model_dict = {
            'appDeployments': {
                'Application': {
                    'myApp': {
                        'SourcePath' : 'wlsdeploy/applicationsBad/abc.war'
                    }
                },
                'Library': {
                    'myLib': {
                        'SourcePath' : 'wlsdeploy/sharedLibrariesBad/abc.war'
                    }
                }
            }
        }

        args_map = {
            '-oracle_home': '/oracle'
        }
        model_context = ModelContext(self._class_name, args_map)
        aliases = Aliases(model_context, wls_version=self._wls_version)

        validator = Validator(model_context, aliases)
        validator.validate_in_standalone_mode(model_dict, {})

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify 4 errors were logged, 2 directory names are bad, and 2 paths aren't in archive
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 4)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

if __name__ == '__main__':
    unittest.main()
