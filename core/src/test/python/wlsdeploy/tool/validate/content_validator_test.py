"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest
from java.util.logging import Level
from oracle.weblogic.deploy.logging import TestSummaryHandler
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import CROSS_DOMAIN
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import REMOTE_RESOURCE
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.content_validator import ContentValidator
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class ContentValidatorTest(BaseTestCase):
    _class_name = 'ContentValidatorTest'

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

    def test_dynamic_dynamic_cluster_server_templates(self):
        """
        Test errors when multiple dynamic servers have the same server template.
        """
        model_dict = {
            TOPOLOGY: {
                CLUSTER: {
                    'clusterOne': {
                        DYNAMIC_SERVERS: {
                            SERVER_TEMPLATE: 'templateOne'
                        }
                    },
                    'clusterTwo': {
                        DYNAMIC_SERVERS: {
                            SERVER_TEMPLATE: 'templateOne'
                        }
                    },
                    'clusterThree': {
                        DYNAMIC_SERVERS: {
                        }
                    }
                }
            }
        }

        validator = self.create_validator()
        validator.validate_model_content(model_dict)

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify no errors, 2 warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 0)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 2)

        # clusterThree does not have a server template
        self._validate_message_key(handler, Level.WARNING, 'WLSDPLY-05200', 1)

        # clusterOne and clusterTwo have the same server template
        self._validate_message_key(handler, Level.WARNING, 'WLSDPLY-05201', 1)

    def test_wls_credential_mappings(self):
        model_dict = {
            DOMAIN_INFO: {
                WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS: {
                    CROSS_DOMAIN: {
                        'map1': {
                            # these 3 are required
                            # 'RemoteDomain': 'otherDomain',
                            # 'RemoteUser': 'otherUser',
                            # 'RemotePassword': 'welcome1',
                        }
                    },
                    REMOTE_RESOURCE: {
                        'map2': {
                            # these 3 are required
                            # 'RemoteHost': 'otherHost',
                            # 'RemoteUser': 'otherUser',
                            # 'RemotePassword': 'welcome1',
                        }
                    }
                }
            }
        }

        validator = self.create_validator()
        validator.validate_model_content(model_dict)

        handler = self._summary_handler
        self.assertNotEqual(handler, None, "Summary handler is not present")

        # Verify 2 errors, no warnings
        self.assertEqual(handler.getMessageCount(Level.SEVERE), 6)
        self.assertEqual(handler.getMessageCount(Level.WARNING), 0)

        # 6 missing attributes for mappings
        self._validate_message_key(handler, Level.SEVERE, 'WLSDPLY-05210', 6)

    def create_validator(self):
        args_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracle'
        }
        self._model_context = ModelContext(self._class_name, args_map)
        self._aliases = Aliases(self._model_context, wls_version=self.ALIAS_WLS_VERSION)

        return ContentValidator(self._model_context, self._aliases)


if __name__ == '__main__':
    unittest.main()
