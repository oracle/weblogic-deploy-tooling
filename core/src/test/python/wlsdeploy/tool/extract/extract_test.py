"""
Copyright (c) 2021, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.json.json_translator import PythonToJson
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.extract.domain_resource_extractor import DomainResourceExtractor
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.yaml.yaml_translator import YamlToPython


class ExtractTest(BaseTestCase):
    __logger = PlatformLogger('wlsdeploy.extract')
    wls_version = '12.2.1.3'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'extract')
        self.EXTRACT_OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'extract')
        self.config_dir = None

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.EXTRACT_OUTPUT_DIR)
        self.config_dir = self._set_custom_config_dir('extract-wdt-config')

    def tearDown(self):
        BaseTestCase.tearDown(self)

        # clean up temporary WDT custom configuration environment variable
        self._clear_custom_config_dir()

    def testDefaultModel(self):
        """
        Test that default values and information from the model
        are incorporated into the resulting domain resource file.
        """
        # Configure the target to set cluster replicas
        target_path = os.path.join(self.config_dir, 'targets', 'wko', 'target.json')
        config = JsonToPython(target_path).parse()
        config['set_cluster_replicas'] = True
        PythonToJson(config).write_to_json_file(target_path)

        documents = self._extract_resource_documents('1', 'wko', 'wko-domain.yaml')
        resource = documents[0]

        # clusters from topology should be in the domain resource file
        cluster_list = self._traverse(resource, 'spec', 'clusters')
        self._match_values("Cluster count", len(cluster_list), 2)
        self._match_values("Cluster 0 clusterName", cluster_list[0]['clusterName'], 'cluster1')
        self._match_values("Cluster 0 replicas", cluster_list[0]['replicas'], 3)
        self._match_values("Cluster 1 clusterName", cluster_list[1]['clusterName'], 'cluster2')
        self._match_values("Cluster 1 replicas", cluster_list[1]['replicas'], 12)

        # secrets from the model should be in the domain resource file
        secret_list = self._traverse(resource, 'spec', 'configuration', 'secrets')
        self._match_values("Secret count", len(secret_list), 2)
        self._match_values("Secret 0", secret_list[0], 'demodomain-m1-system')
        self._match_values("Secret 1", secret_list[1], 'demodomain-m2-system')

    def testKubernetesModel(self):
        """
        Test that fields from the kubernetes section of the model
        are transferred to the resulting domain resource file
        """
        documents = self._extract_resource_documents('2', 'wko', 'wko-domain.yaml')
        resource = documents[0]

        # clusters from kubernetes section should be in the domain resource file
        cluster_list = self._traverse(resource, 'spec', 'clusters')
        self._match_values("Cluster count", len(cluster_list), 2)
        self._match_values("Cluster 0 clusterName", cluster_list[0]['clusterName'], 'CLUSTER_1')
        self._match_values("Cluster 1 clusterName", cluster_list[1]['clusterName'], 'CLUSTER_2')

        # secrets from the kubernetes section should be in the domain resource file
        secret_list = self._traverse(resource, 'spec', 'configuration', 'secrets')
        self._match_values("Secret count", len(secret_list), 2)
        self._match_values("Secret 0", secret_list[0], 'secret-1')
        self._match_values("Secret 1", secret_list[1], 'secret-2')

    def testVerrazzanoModel(self):
        """
        Test that fields from the verrazzano section of the model
        are transferred to the resulting domain resource file
        """
        documents = self._extract_resource_documents('3', 'vz', 'vz-application.yaml')
        application_resource = documents[0]

        # a model application component was added to 2 from the template
        component_list = self._traverse(application_resource, 'spec', 'components')
        self._match_values("Application component count", len(component_list), 3)
        self._match_values("Application component 2 name", component_list[2]['componentName'],
                           'base-domain-from-model')

        trait_list = self._traverse(component_list[0], 'traits')
        self._match_values("Application trait count", len(trait_list), 3)

        ingress_trait = self._traverse(trait_list[1], 'trait')
        rule_list = self._traverse(ingress_trait, 'spec', 'rules')
        self._match_values("Ingress trait rule count", len(rule_list), 3)

        # m1 has paths added from the verrazzano section
        m1_rule = rule_list[0]
        m1_path_list = self._traverse(m1_rule, 'paths')
        self._match_values("Server 1 rule path count", len(m1_path_list), 2)

        # m2 has no rules, only sample comments
        m2_rule = rule_list[1]
        self._match_values("Server 2 has no paths", 'paths' in m2_rule, False)

        configmap_resource = documents[2]

        # one entry was added to config map
        data_map = self._traverse(configmap_resource, 'spec', 'workload', 'data')
        self._match_values("Configmap data count", len(data_map), 2)

        # the DB entry was update with a new URL
        db_key = 'wdt_jdbc.yaml'
        db_host_text = '@modelhost:1521'
        self._match_values("Configmap data has key " + db_key, db_key in data_map, True)
        self._match_values("Configmap JDBC URL contains " + db_host_text, db_host_text in data_map[db_key], True)

    def _extract_resource_documents(self, suffix, target_name, output_file_name):
        model_file = os.path.join(self.MODELS_DIR, 'model-' + suffix + '.yaml')
        translator = FileToPython(model_file, use_ordering=True)
        model_dict = translator.parse()
        model = Model(model_dict)

        args_map = {
            '-domain_home': '/u01/domain',
            '-oracle_home': '/oracle',
            '-output_dir': self.EXTRACT_OUTPUT_DIR,
            '-target': target_name
        }
        model_context = ModelContext('ExtractTest', args_map)
        aliases = Aliases(model_context, WlstModes.OFFLINE, self.wls_version)

        extractor = DomainResourceExtractor(model, model_context, aliases, self.__logger)
        extractor.extract()

        resource_file = os.path.join(self.EXTRACT_OUTPUT_DIR, output_file_name)
        reader = YamlToPython(resource_file, True)
        return reader.parse_documents()
