"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest
from java.util.logging import Level
from oracle.weblogic.deploy.logging import TestSummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util.model_context import ModelContext


class DeploymentsValidatorTest(BaseTestCase):
    _class_name = 'DeploymentsValidatorTest'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.RESOURCES_DIR = os.path.join(self.TEST_CLASSES_DIR, 'validation')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'validation')
        self.name = 'ValidationTestCase'
        self._logger = PlatformLogger('wlsdeploy.validate')

        # add summary handler to validate logger to check results
        self._summary_handler = TestSummaryHandler()

    def setUp(self):
        BaseTestCase.setUp(self)
        self._logger.logger.addHandler(self._summary_handler)

    def tearDown(self):
        BaseTestCase.tearDown(self)
        # remove summary handler for next test suite
        self._logger.logger.removeHandler(self._summary_handler)
        WLSDeployLogEndHandler.clearHandlers()

    def test_archive_path_validation(self):
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
        aliases = Aliases(model_context, wls_version=self.ALIAS_WLS_VERSION)

        validator = Validator(model_context, aliases)
        validator.validate_in_standalone_mode(model_dict, {})

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify 4 errors, no warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 4)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

        # myApp and myLib paths are not in the archive
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05025', 2)

        # myLib archive path is bad
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05240', 1)

        # myApp archive path is invalid
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05241', 1)


if __name__ == '__main__':
    unittest.main()
