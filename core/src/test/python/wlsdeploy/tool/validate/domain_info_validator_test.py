"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest
from java.util.logging import Level
from oracle.weblogic.deploy.logging import TestSummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import DATABASE_TYPE
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import ORACLE_DATABASE_CONNECTION_TYPE
from wlsdeploy.aliases.model_constants import RCU_DATABASE_TYPE
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import WLS_POLICIES
from wlsdeploy.aliases.model_constants import WLS_ROLES
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util.model_context import ModelContext


class DomainInfoValidatorTest(BaseTestCase):
    _class_name = 'DomainInfoValidatorTest'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.RESOURCES_DIR = os.path.join(self.TEST_CLASSES_DIR, 'validation')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'validation')

        self._logger = PlatformLogger('wlsdeploy.validate')

        # add summary handler to validate logger to check results
        self._summary_handler = TestSummaryHandler()

    def setUp(self):
        BaseTestCase.setUp(self)
        self._logger.logger.addHandler(self._summary_handler)

        args_map = {
            '-oracle_home': '/oracle'
        }
        model_context = ModelContext(self._class_name, args_map)
        aliases = Aliases(model_context, wls_version=self.ALIAS_WLS_VERSION)
        self.validator = Validator(model_context, aliases)

    def tearDown(self):
        BaseTestCase.tearDown(self)
        # remove summary handler for next test suite
        self._logger.logger.removeHandler(self._summary_handler)
        WLSDeployLogEndHandler.clearHandlers()

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

        model_dict = {
            DOMAIN_INFO: {
                WLS_POLICIES: wls_policies_dict
            }
        }

        self.validator.validate_in_standalone_mode(model_dict, {})

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify only 3 errors resulted
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 2)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

        # MissingPolicyPolicy and MissingResourceIDPolicy are missing required attributes
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-12600', 2)

    def test_wls_roles_validation(self):
        """
        Run the validation portion of the WLSRoles helper and check for expected results.
        """
        _method_name = 'test_wls_roles_validation'

        wlsroles_dict = {'Admin':     {'UpdateMode': 'append',
                                       'Expression': 'Grp(AppAdmin)'},
                         'Deployer':  {'UpdateMode': 'prepend',
                                       'Expression': 'Grp(AppDeployer)'},
                         'Tester':    {'Expression': 'Grp(AppTester)'},
                         'MyEmpty':   {},
                         'MyTester':  {'UpdateMode': 'append',
                                       'Expression': 'Grp(MyTester)'},
                         'MyTester2': {'UpdateMode': 'replace',
                                       'Expression': 'Grp(MyTester2)'},
                         'MyTester3': {'UpdateMode': 'bad',
                                       'Expression': 'Grp(MyTester3)'}}

        model_dict = {
            DOMAIN_INFO: {
                WLS_ROLES: wlsroles_dict
            }
        }

        self.validator.validate_in_standalone_mode(model_dict, {})

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify only warnings resulted
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 0)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 3)

        # MyEmpty has no expression value
        self._validate_message_key(handler, Level.WARNING, 'WLSDPLY-12501', 1)

        # MyTester role is not a global role
        self._validate_message_key(handler, Level.WARNING, 'WLSDPLY-12502', 1)

        # MyTester3 has invalid update mode
        self._validate_message_key(handler, Level.WARNING, 'WLSDPLY-12503', 1)

    def test_rcu_db_info_validation(self):
        model_dict = {
            DOMAIN_INFO: {
                RCU_DB_INFO: {
                    DATABASE_TYPE: 'ATPx',
                    RCU_DATABASE_TYPE: 'SQLSERVERx',
                    ORACLE_DATABASE_CONNECTION_TYPE: 'SSLx'
                }
            }
        }

        self.validator.validate_in_standalone_mode(model_dict, {})

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # three fields have invalid values
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05302', 3)


if __name__ == '__main__':
    unittest.main()
