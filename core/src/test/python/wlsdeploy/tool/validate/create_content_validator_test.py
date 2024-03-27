"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest
from java.util.logging import Level
from oracle.weblogic.deploy.create import RCURunner
from oracle.weblogic.deploy.logging import TestSummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_DATABASE_TYPE
from wlsdeploy.aliases.model_constants import RCU_DB_CONN_STRING
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.create_content_validator import CreateDomainContentValidator
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class CreateContentValidatorTest(BaseTestCase):
    _class_name = 'CreateContentValidatorTest'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self._logger = PlatformLogger('wlsdeploy.validate')

    def setUp(self):
        BaseTestCase.setUp(self)

        # add summary handler to validate logger to check results
        self._summary_handler = TestSummaryHandler()
        self._logger.logger.addHandler(self._summary_handler)

    def tearDown(self):
        BaseTestCase.tearDown(self)

        # remove summary handler for next test
        self._logger.logger.removeHandler(self._summary_handler)
        WLSDeployLogEndHandler.clearHandlers()

    def test_empty_rcu(self):
        """
        Test errors for missing fields when running RCU.
        """
        model_dict = self._build_model_from_rcu_db_info({})

        validator = self.create_validator(run_rcu=True)
        validator.validate_model_content(model_dict)

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify 5 errors, no warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 5)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

        # no rcu_prefix or rcu_schema_password
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05304', 2)

        # no connection string and no oracle.net.tns_admin
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05306', 1)

        # no connection string and no tns.alias
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05307', 1)

        # admin password is missing, and we are running RCU
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05305', 1)

    def test_rcu_without_required(self):
        """
        No errors or warnings if the typedef doesn't require RCU.
        """
        model_dict = self._build_model_from_rcu_db_info({})

        validator = self.create_validator(requires_rcu=False)
        validator.validate_model_content(model_dict)

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify no errors or warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 0)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

    def test_rcu_without_running(self):
        """
        Should be no errors if admin password missing, and not running rcu.
        """
        model_dict = self._build_model_from_rcu_db_info({
            RCU_PREFIX: 'WDT',
            RCU_SCHEMA_PASSWORD: 'password',
            RCU_DB_CONN_STRING: 'somedb.example.com:1234/orclpdb'
        })

        validator = self.create_validator()
        validator.validate_model_content(model_dict)

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify no errors or warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 0)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

    def test_rcu_db_type(self):
        """
        Non-ORACLE db should give an error if connection string missing, no TNS option.
        """
        model_dict = self._build_model_from_rcu_db_info({
            RCU_PREFIX: 'WDT',
            RCU_SCHEMA_PASSWORD: 'password',
            RCU_ADMIN_PASSWORD: 'admin',
            RCU_DATABASE_TYPE: RCURunner.SQLSERVER_DB_TYPE
        })

        validator = self.create_validator()
        validator.validate_model_content(model_dict)

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify 1 error, no warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 1)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

        # no connection string and not ORACLE db
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05301', 1)

    def create_validator(self, run_rcu=False, requires_rcu=True):
        # create a model context to simulate running RCU for JRF
        args_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracle',
            CommandLineArgUtil.DOMAIN_TYPE_SWITCH: 'JRF',
            CommandLineArgUtil.RUN_RCU_SWITCH: run_rcu,
            CommandLineArgUtil.DOMAIN_TYPEDEF: FakeTypeDef(requires_rcu)
        }

        self._model_context = ModelContext(self._class_name, args_map)
        self._aliases = Aliases(self._model_context, wls_version=self.ALIAS_WLS_VERSION)

        return CreateDomainContentValidator(self._model_context, None, self._aliases)

    def _build_model_from_rcu_db_info(self, rcu_db_info):
        return {
            DOMAIN_INFO: {
                ADMIN_USERNAME: 'weblogic',
                ADMIN_PASSWORD: 'welcome1',
                RCU_DB_INFO: rcu_db_info
            }
        }


class FakeTypeDef(object):
    """
    A minimal type def to create test model context
    """
    def __init__(self, requires_rcu):
        self._requires_rcu = requires_rcu

    def requires_rcu(self):
        return self._requires_rcu

    def finish_initialization(self, _model_context):
        pass


if __name__ == '__main__':
    unittest.main()
