"""
Copyright (c) 2021, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

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


class ExtractTest(BaseTestCase):
    __logger = PlatformLogger('wlsdeploy.extract')
    wls_version = '12.2.1.3'

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'extract')
        self.EXTRACT_OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'extract')
        self.TARGET_SOURCE_DIR = os.path.abspath(self.TEST_CLASSES_DIR + '/../../../core/src/main/targetconfigs')

    def setUp(self):
        BaseTestCase.setUp(self)
        self._suspend_logs('wlsdeploy.extract')
        self._establish_directory(self.EXTRACT_OUTPUT_DIR)

        config_dir = os.path.join(self.TEST_OUTPUT_DIR, 'config')
        targets_dir = os.path.join(config_dir, 'targets')
        self._establish_directory(config_dir)
        self._establish_directory(targets_dir)

        self._copy_target_file(targets_dir, 'wko', 'target.json')
        self._copy_target_file(targets_dir, 'templates', 'wko-domain.yaml')

        # use WDT custom configuration to find target definition
        self._set_custom_config_dir(config_dir)

    def tearDown(self):
        BaseTestCase.tearDown(self)
        self._restore_logs()

        # clean up temporary WDT custom configuration environment variable
        self._clear_custom_config_dir()

    def _copy_target_file(self, targets_dir, target_name, target_file_name):
        target_dir = os.path.join(targets_dir, target_name)
        target_file = os.path.join(target_dir, target_file_name)
        if not os.path.exists(target_file):
            self._establish_directory(target_dir)
            source_file = os.path.join(self.TARGET_SOURCE_DIR, target_name, target_file_name)
            shutil.copy(source_file, target_file)

    def testDefaultModel(self):
        """
        Test that default values and information from the model
        are incorporated into the resulting domain resource file.
        """
        # Configure the target to set cluster replicas
        target_path = os.path.join(self.TEST_OUTPUT_DIR, 'config', 'targets', 'wko', 'target.json')
        config = JsonToPython(target_path).parse()
        config['set_cluster_replicas'] = True
        PythonToJson(config).write_to_json_file(target_path)

        resource = self._extract_domain_resource('1')

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
        resource = self._extract_domain_resource('2')

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

    # deprecated
    def testNamedObjectListModel(self):
        """
        Test that fields using the deprecated "named object list" in the kubernetes section of the model
        are transferred to the resulting domain resource file
        """
        resource = self._extract_domain_resource('3')

        # serverPod/env from the kubernetes section should be in the domain resource file
        env_list = self._traverse(resource, 'spec', 'serverPod', 'env')
        self._match_values("Env count", len(env_list), 2)
        self._match_values("Env 0", env_list[0]['name'], 'JAVA_OPTIONS')
        self._match_values("Env 1", env_list[1]['name'], 'USER_MEM_ARGS')

        # clusters from kubernetes section should be in the domain resource file
        cluster_list = self._traverse(resource, 'spec', 'clusters')
        self._match_values("Cluster count", len(cluster_list), 2)
        self._match_values("Cluster 0 clusterName", cluster_list[0]['clusterName'], 'CLUSTER_1')
        self._match_values("Cluster 1 clusterName", cluster_list[1]['clusterName'], 'CLUSTER_2')

    def _extract_domain_resource(self, suffix):
        model_file = os.path.join(self.MODELS_DIR, 'model-' + suffix + '.yaml')
        translator = FileToPython(model_file, use_ordering=True)
        model_dict = translator.parse()
        model = Model(model_dict)

        resource_file = os.path.join(self.EXTRACT_OUTPUT_DIR, 'domain-resource-' + suffix + '.yaml')
        args_map = {
            '-domain_home': '/u01/domain',
            '-oracle_home': '/oracle',
            '-domain_resource_file': resource_file,
            '-target': 'wko'
        }
        model_context = ModelContext('ExtractTest', args_map)
        aliases = Aliases(model_context, WlstModes.OFFLINE, self.wls_version)

        extractor = DomainResourceExtractor(model, model_context, aliases, self.__logger)
        extractor.extract()

        translator = FileToPython(resource_file, use_ordering=True)
        return translator.parse()
