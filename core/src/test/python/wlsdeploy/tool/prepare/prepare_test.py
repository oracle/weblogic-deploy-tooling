"""
Copyright (c) 2021, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

from base_test import BaseTestCase

from oracle.weblogic.deploy.util import PyOrderedDict
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
from wlsdeploy.tool.prepare.model_preparer import ModelPreparer
from wlsdeploy.util import string_utils
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class PrepareTestCase(BaseTestCase):

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'prepare')
        self.PREPARE_OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'prepare')

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.PREPARE_OUTPUT_DIR)

        config_dir = os.path.join(self.TEST_OUTPUT_DIR, 'config')
        self._establish_directory(config_dir)

        targets_dir = os.path.join(config_dir, 'targets')
        target_dir = os.path.join(targets_dir, 'test-1')
        target_file = os.path.join(target_dir, 'target.json')

        if not os.path.exists(target_file):
            self._establish_directory(targets_dir)
            self._establish_directory(target_dir)
            source_target_file = os.path.join(self.MODELS_DIR, 'target-1.json')
            shutil.copy(source_target_file, target_file)

        self._establish_injector_config(config_dir)

        # use WDT custom configuration to find target definition and injector config
        self._set_custom_config_dir(config_dir)

    def tearDown(self):
        BaseTestCase.tearDown(self)

        # clean up temporary WDT custom configuration environment variable
        self._clear_custom_config_dir()

    def testPrepare(self):
        """
        Run prepare on model-1, variables-1, and verify the results
        """
        model_files = os.path.join(self.MODELS_DIR, 'model-1.yaml')
        variable_files = os.path.join(self.MODELS_DIR, 'variables-1.properties')

        output_dir = os.path.join(self.PREPARE_OUTPUT_DIR, 'test-1')
        self._establish_directory(output_dir)

        args_map = {
            '-oracle_home': '/oracle',
            '-model_file': model_files,
            '-variable_file': variable_files,
            '-output_dir': output_dir,
            '-target': 'test-1'
        }

        model_context = ModelContext('PrepareModelTestCase', args_map)

        # disable relevant loggers, saving original levels
        self._suspend_logs('wlsdeploy.prepare_model', 'wlsdeploy.util', 'wlsdeploy.tool.util')

        preparer = ModelPreparer(model_files, model_context, output_dir)
        preparer.prepare_models()

        # Restore original log levels
        self._restore_logs()

        # Check the model file

        target_model_file = os.path.join(output_dir, 'model-1.yaml')
        translator = FileToPython(target_model_file, use_ordering=True)
        python_dict = translator.parse()

        self._match('@@SECRET:__weblogic-credentials__:username@@', python_dict, DOMAIN_INFO, ADMIN_USERNAME)
        self._match('@@SECRET:__weblogic-credentials__:password@@', python_dict, DOMAIN_INFO, ADMIN_PASSWORD)

        self._match('@@PROP:ms1.port@@', python_dict, TOPOLOGY, SERVER, 'ms1', LISTEN_PORT, )

        jdbc_resource = self._traverse(python_dict, RESOURCES, JDBC_SYSTEM_RESOURCE, 'ds1', JDBC_RESOURCE)
        self._match('@@PROP:JDBC.ds1.URL@@', jdbc_resource, JDBC_DRIVER_PARAMS, URL)
        self._match('@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-ds1:password@@', jdbc_resource, JDBC_DRIVER_PARAMS,
                    PASSWORD_ENCRYPTED)
        self._match('@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-ds1:username@@', jdbc_resource, JDBC_DRIVER_PARAMS,
                    PROPERTIES, 'user', DRIVER_PARAMS_PROPERTY_VALUE)

        # Check the variables file

        target_variables_file = os.path.join(output_dir, 'variables-1.properties')
        variables = string_utils.load_properties(target_variables_file)
        self._match(7001, variables, 'ms1.port')
        self._match('jdbc:oracle:thin:@host.com:1521/pdborcl', variables, 'JDBC.ds1.URL')
        self._match('a', variables, 'prefix')
        self._match('z', variables, 'suffix')

        # these were changed to secrets, and should not appear
        self._no_dictionary_key(variables, 'wls.user')
        self._no_dictionary_key(variables, 'wls.pass')
        self._no_dictionary_key(variables, 'ds.user.name')
        self._no_dictionary_key(variables, 'ds.user.password')

        # this was never used in the original model
        self._no_dictionary_key(variables, 'unused.xyz')

        # Check the results file

        target_results_file = os.path.join(output_dir, 'results.json')
        results_translator = FileToPython(target_results_file, use_ordering=True)
        results_dict = results_translator.parse()
        secrets_dict = results_dict['secrets']
        if not isinstance(secrets_dict, PyOrderedDict):
            self.fail('Secrets should be a PyOrderedDict')

        # db user secret should retain original value from the variables file
        self._match('dsUser9', secrets_dict, 'jdbc-ds1', 'keys', 'username')
