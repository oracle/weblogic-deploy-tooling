"""
Copyright (c) 2021, 2023, Oracle and/or its affiliates.
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
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class PrepareTestCase(BaseTestCase):

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'prepare')
        self.PREPARE_OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'prepare')
        self.config_dir = None

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.PREPARE_OUTPUT_DIR)

        config_dir = os.path.join(self.TEST_OUTPUT_DIR, 'config')
        self._establish_directory(config_dir)

        # use WDT custom configuration to find target definition and injector config
        self.config_dir = self._set_custom_config_dir('prepare-wdt-config')
        targets_dir = os.path.join(self.config_dir, 'targets')
        target_dir = os.path.join(targets_dir, 'test-1')
        target_file = os.path.join(target_dir, 'target.json')

        self._establish_directory(target_dir)
        source_target_file = os.path.join(self.MODELS_DIR, 'target-1.json')
        shutil.copy(source_target_file, target_file)

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

        preparer = ModelPreparer(model_files, model_context, output_dir)
        preparer.prepare_models()

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

    def testPrepareForeignProperties(self):
        self._prepare_foreign_properties(False)

    def testPrepareEncryptedForeignProperties(self):
        self._prepare_foreign_properties(True)

    def _prepare_foreign_properties(self, encrypted):
        model_file = os.path.join(self.MODELS_DIR, 'foreign-properties.yaml')
        output_dir = os.path.join(self.PREPARE_OUTPUT_DIR, 'foreign-' + str(encrypted))
        self._establish_directory(output_dir)
        variable_file = os.path.join(self.PREPARE_OUTPUT_DIR, 'foreign.properties')
        provider_value = 'provider-marker'
        jms_value = 'jms-marker'
        if encrypted:
            provider_value = encryption_utils.encrypt_one_password('test-passphrase', provider_value)
            jms_value = encryption_utils.encrypt_one_password('test-passphrase', jms_value)
        stream = open(variable_file, 'w')
        try:
            stream.write('provider.secret=%s\njms.secret=%s\nordinary=ordinary-marker\n'
                         'mail.user=mail-user\nmail.password=mail-marker\n' % (provider_value, jms_value))
        finally:
            stream.close()
        context = ModelContext('PrepareModelTestCase', {
            '-oracle_home': '/oracle', '-model_file': model_file, '-variable_file': variable_file,
            '-output_dir': output_dir, '-target': 'test-1', '-target_version': '26.1.0.0.0',
            '-passphrase': 'test-passphrase'
        })
        preparer = ModelPreparer(model_file, context, output_dir)
        preparer.prepare_models()
        model = FileToPython(os.path.join(output_dir, 'foreign-properties.yaml'), use_ordering=True).parse()
        provider = model[RESOURCES]['ForeignJNDIProvider']['provider'][PROPERTIES]
        jms = model[RESOURCES]['JMSSystemResource']['module']['JmsResource']['ForeignServer']['foreign']['JNDIProperty']
        for token in [provider['vendor.one.encrypted'], provider['vendor.two.encrypted'],
                      jms['vendor.jms.encrypted']['Value'], jms['NO_NAME_0']['Value']]:
            self.assertEqual(True, token.startswith('@@SECRET:'))
            self.assertEqual(True, token.endswith(':password@@'))
        self.assertEqual('@@PROP:ordinary@@', provider['vendor.plain'])
        self.assertEqual('@@PROP:ordinary@@', jms['vendor.plain']['Value'])
        self.assertEqual('@@PROP:ordinary@@', jms['ordinary.encrypted']['Value'])
        self.assertEqual('vendor.explicit.encrypted', jms['NO_NAME_0']['Key'])
        secrets = FileToPython(os.path.join(output_dir, 'results.json'), use_ordering=True).parse()['secrets']
        for token, value in [(provider['vendor.one.encrypted'], 'provider-marker'),
                             (provider['vendor.two.encrypted'], 'second-marker'),
                             (jms['vendor.jms.encrypted']['Value'], 'jms-marker'),
                             (jms['NO_NAME_0']['Value'], 'jms-marker')]:
            secret_name = token[len('@@SECRET:@@ENV:DOMAIN_UID@@-'):-len(':password@@')]
            self._match(value, preparer.credential_injector.get_variable_cache(), secret_name + ':password')
            self._match(None, secrets, secret_name, 'keys', 'password')
        self._match('mail-user', secrets, 'mail-mail-properties-smtp', 'keys', 'username')
        self._match('', secrets, 'mail-mail-properties-smtp', 'keys', 'password')
        output_variables = string_utils.load_properties(os.path.join(output_dir, 'foreign.properties'))
        self._match('ordinary-marker', output_variables, 'ordinary')
        self._no_dictionary_key(output_variables, 'provider.secret')
        self._no_dictionary_key(output_variables, 'jms.secret')
