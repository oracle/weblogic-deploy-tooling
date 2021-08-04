"""
Copyright (c) 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import unittest

from java.util.logging import Level

from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import LISTEN_PORT
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.model_constants import PROPERTIES
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import URL
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.prepare.model_preparer import ModelPreparer
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class PrepareTestCase(unittest.TestCase):
    RESOURCES_DIR = os.path.abspath(os.getcwd() + '/../../test-classes')
    CONFIG_DIR = os.path.join(RESOURCES_DIR, 'config')
    MODELS_DIR = os.path.join(RESOURCES_DIR, 'prepare')
    TESTS_DIR = os.path.abspath(os.getcwd() + '/../../unit-tests')
    OUTPUT_DIR = os.path.join(TESTS_DIR, 'prepare')

    def setUp(self):
        if not os.path.isdir(self.TESTS_DIR):
            os.mkdir(self.TESTS_DIR)

        if not os.path.isdir(self.OUTPUT_DIR):
            os.mkdir(self.OUTPUT_DIR)

        # use WDT custom configuration to find target definition
        os.environ['WDT_CUSTOM_CONFIG'] = self.CONFIG_DIR

    def tearDown(self):
        # clean up temporary WDT custom configuration environment variable
        del os.environ['WDT_CUSTOM_CONFIG']

    def testPrepare(self):
        """
        Run prepare on model-1, variables-1, and verify the results
        """
        model_files = os.path.join(self.MODELS_DIR, 'model-1.yaml')
        variable_files = os.path.join(self.MODELS_DIR, 'variables-1.properties')

        output_dir = os.path.join(self.OUTPUT_DIR, 'test-1')
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        args_map = {
            '-oracle_home': '/oracle',
            '-model_file': model_files,
            '-variable_file': variable_files,
            '-output_dir': output_dir,
            '-target': 'test-1'
        }

        model_context = ModelContext('PrepareModelTestCase', args_map)

        # disable relevant loggers, saving original levels
        loggers = {'wlsdeploy.prepare_model': None, 'wlsdeploy.util': None, 'wlsdeploy.tool.util': None}
        for key in loggers:
            logger = PlatformLogger(key)
            loggers[key] = logger.get_level()
            logger.set_level(Level.OFF)

        prepare_logger = PlatformLogger('wlsdeploy.prepare_model')
        preparer = ModelPreparer(model_files, model_context, prepare_logger, output_dir)
        preparer.prepare_models()

        # Restore original levels to logs
        for key in loggers:
            logger = PlatformLogger(key)
            logger.set_level(loggers[key])

        target_model_file = os.path.join(output_dir, 'model-1.yaml')

        translator = FileToPython(target_model_file, use_ordering=True)
        pythonDict = translator.parse()

        domainInfo = pythonDict[DOMAIN_INFO]
        self.assertEquals(domainInfo[ADMIN_USERNAME], '@@SECRET:__weblogic-credentials__:username@@',
                          'Admin user ' + domainInfo[ADMIN_USERNAME] + ' should be a secret')
        self.assertEquals(domainInfo[ADMIN_PASSWORD], '@@SECRET:__weblogic-credentials__:password@@',
                          'Admin password ' + domainInfo[ADMIN_PASSWORD] + ' should be a secret')

        topology = pythonDict[TOPOLOGY]
        server = topology[SERVER]
        self.assertEquals(server['ms1'][LISTEN_PORT], '@@PROP:Server.ms1.ListenPort@@', 'Listen port was tokenized')

        resources = pythonDict[RESOURCES]
        dsParams = resources[JDBC_SYSTEM_RESOURCE]['ds1'][JDBC_RESOURCE][JDBC_DRIVER_PARAMS]
        self.assertEquals(dsParams[URL], '@@PROP:JDBC.ds1.URL@@', 'DS URL was tokenized')
        self.assertEquals(dsParams[PASSWORD_ENCRYPTED], '@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-ds1:password@@',
                          'DS password became a secret')
        userName = dsParams[PROPERTIES]['user'][DRIVER_PARAMS_PROPERTY_VALUE]
        self.assertEquals(userName, '@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-ds1:username@@',
                          'DS user name was tokenized')
