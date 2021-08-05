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
from wlsdeploy.util import string_utils
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

        # Check the model file

        target_model_file = os.path.join(output_dir, 'model-1.yaml')
        translator = FileToPython(target_model_file, use_ordering=True)
        python_dict = translator.parse()

        domain_info = self._traverse(python_dict, DOMAIN_INFO)
        self._match(domain_info, ADMIN_USERNAME, '@@SECRET:__weblogic-credentials__:username@@')
        self._match(domain_info, ADMIN_PASSWORD, '@@SECRET:__weblogic-credentials__:password@@')

        ms1 = self._traverse(python_dict, TOPOLOGY, SERVER, 'ms1')
        self._match(ms1, LISTEN_PORT, '@@PROP:ms1.port@@')

        resources = self._traverse(python_dict, RESOURCES)
        ds_params = self._traverse(resources, JDBC_SYSTEM_RESOURCE, 'ds1', JDBC_RESOURCE, JDBC_DRIVER_PARAMS)
        self._match(ds_params, URL, '@@PROP:JDBC.ds1.URL@@')
        self._match(ds_params, PASSWORD_ENCRYPTED, '@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-ds1:password@@')
        user = self._traverse(ds_params, PROPERTIES, 'user')
        self._match(user, DRIVER_PARAMS_PROPERTY_VALUE, '@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-ds1:username@@')

        # Check the variables file

        target_variables_file = os.path.join(output_dir, 'variables-1.properties')
        variables = string_utils.load_properties(target_variables_file)
        self._match_variable(variables, 'ms1.port', 7001)
        self._match_variable(variables, 'JDBC.ds1.URL', 'jdbc:oracle:thin:@host.com:1521/pdborcl')

        # these were changed to secrets, and should not appear
        self._no_variable(variables, 'wls.user')
        self._no_variable(variables, 'wls.pass')
        self._no_variable(variables, 'ds.user.name')
        self._no_variable(variables, 'ds.user.password')

        # Check the secrets file

        target_secrets_file = os.path.join(output_dir, 'k8s_secrets.json')
        secrets_translator = FileToPython(target_secrets_file, use_ordering=True)
        secrets_dict = secrets_translator.parse()
        secrets_list = secrets_dict['secrets']
        if not isinstance(secrets_list, list):
            self.fail('Secrets should be a list')

        # db user secret should retain original value from the variables file
        db_secret = self._find_secret(secrets_list, 'jdbc-ds1')
        db_keys = self._traverse(db_secret, 'keys')
        self._match(db_keys, 'username', 'dsUser9')

    def _match(self, model_dict, key, value):
        model_value = model_dict[key]
        self.assertEquals(model_value, value, key + ' equals ' + str(model_value) + ' should be ' + value)

    def _match_variable(self, variables, key, value):
        if key not in variables:
            self.fail('Variables should contain ' + key)
        file_value = variables[key]
        if file_value != str(value):
            self.fail('Variable ' + key + ' equals ' + str(file_value) + ', should equal ' + str(value))

    def _no_variable(self, variables, key):
        if key in variables:
            self.fail('Variables should not contain ' + key)

    def _traverse(self, model_dict, *args):
        value = model_dict
        for arg in args:
            if not isinstance(value, dict):
                self.fail('Element ' + arg + ' parent is not a dictionary in ' + ','.join(list(args)))
            if arg not in value:
                self.fail('Element ' + arg + ' not found in ' + ','.join(list(args)))
            value = value[arg]
        return value

    def _find_secret(self, secrets, name):
        for secret in secrets:
            secret_name = self._traverse(secret, 'secretName')
            if secret_name == name:
                return secret
        self.fail('No secret named ' + name)
