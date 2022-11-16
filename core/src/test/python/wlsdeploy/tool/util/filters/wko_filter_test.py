"""
Copyright (c) 2021, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from base_test import BaseTestCase
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import APP_DEPLOYMENTS
from wlsdeploy.aliases.model_constants import AUTHENTICATION_PROVIDER
from wlsdeploy.aliases.model_constants import CALCULATED_LISTEN_PORTS
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.aliases.model_constants import PARTITION
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import RESOURCE_GROUP
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import VIRTUAL_TARGET
from wlsdeploy.tool.util.filters import wko_filter
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class WkoFilterTestCase(BaseTestCase):
    _program_name = 'wko_filter_test'
    _jta_cluster = 'JTACluster'
    _jta_cluster_info_list = 'DeterminerCandidateResourceInfoList'
    _description_name = 'Description'
    _multi_version_app = 'MultiVersionApp'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'prepare')
        self.PREPARE_OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'prepare')

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.PREPARE_OUTPUT_DIR)

    def testFilter(self):
        """
        Filter the model and verify the results
        """
        model_file = os.path.join(self.MODELS_DIR, 'wko-filter.yaml')
        translator = FileToPython(model_file, use_ordering=True)
        model = translator.parse()

        # online attributes are in the model before filtering

        jta_cluster = self._traverse(model, TOPOLOGY, CLUSTER, 'staticCluster', self._jta_cluster)
        self.assertEqual(True, self._jta_cluster_info_list in jta_cluster,
                         self._jta_cluster_info_list + " should be in " + self._jta_cluster + " before filtering")

        authenticator = self._traverse(model, TOPOLOGY, SECURITY_CONFIGURATION, REALM, 'yourRealm',
                                       AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR, DEFAULT_AUTHENTICATOR)
        self.assertEqual(True, self._description_name in authenticator,
                         self._description_name + " should be in " + DEFAULT_AUTHENTICATOR + " before filtering")

        my_app = self._traverse(model, APP_DEPLOYMENTS, APPLICATION, 'myApp')
        self.assertEqual(True, self._multi_version_app in my_app,
                         self._multi_version_app + " should be in \"myApp\" before filtering")

        # Apply the filter

        self._suspend_logs('wlsdeploy.tool.util')
        model_context = ModelContext(self._program_name, {})
        wko_filter.filter_model(model, model_context)
        self._restore_logs()

        # Machine and virtual target elements should be removed from the model

        topology = self._traverse(model, TOPOLOGY)
        self._no_dictionary_key(topology, MACHINE)
        self._no_dictionary_key(topology, VIRTUAL_TARGET)

        server_1 = self._traverse(model, TOPOLOGY, SERVER, 'm1')
        self._no_dictionary_key(server_1, MACHINE)

        template_1 = self._traverse(model, TOPOLOGY, SERVER_TEMPLATE, 'template-1')
        self._no_dictionary_key(template_1, MACHINE)

        # Partition and resource elements should be removed from the model

        resources = self._traverse(model, RESOURCES)
        self._no_dictionary_key(resources, PARTITION)
        self._no_dictionary_key(resources, RESOURCE_GROUP)

        # Dynamic clusters should have "CalculatedListenPorts" set to false

        for name in ['dynamicCluster', 'dynamicCluster2']:
            is_calc = self._traverse(model, TOPOLOGY, CLUSTER, name, DYNAMIC_SERVERS)[CALCULATED_LISTEN_PORTS]
            self.assertEqual(False, alias_utils.convert_boolean(is_calc),
                             CALCULATED_LISTEN_PORTS + ' for ' + name + ' is ' + str(is_calc) + ', should be false')

        # Online-only attributes should be removed from the model

        jta_cluster = self._traverse(model, TOPOLOGY, CLUSTER, 'staticCluster', self._jta_cluster)
        self._no_dictionary_key(jta_cluster, self._jta_cluster_info_list)

        authenticator = self._traverse(model, TOPOLOGY, SECURITY_CONFIGURATION, REALM, 'yourRealm',
                                       AUTHENTICATION_PROVIDER, DEFAULT_AUTHENTICATOR, DEFAULT_AUTHENTICATOR)
        self._no_dictionary_key(authenticator, self._description_name)

        my_app = self._traverse(model, APP_DEPLOYMENTS, APPLICATION, 'myApp')
        self._no_dictionary_key(my_app, self._multi_version_app)
