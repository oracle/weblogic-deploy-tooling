"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

from base_test import BaseTestCase
from java.io import File

from wlsdeploy.tool.util.targets import output_file_helper
from wlsdeploy.util.model import Model
from wlsdeploy.yaml.yaml_translator import YamlToPython


class OutputFileHelperTest(BaseTestCase):

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'wko')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'wko')

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.OUTPUT_DIR)

    def testOutputFileHelper(self):
        """
        Test that kubernetes section of the model is merge into the
        domain resource file correctly.
        """
        model_file = os.path.join(self.MODELS_DIR, 'k8s-model.yaml')
        reader = YamlToPython(model_file, True)
        model_dict = reader.parse()
        model = Model(model_dict)

        # copy the domain resource file to the target directory
        file_name = 'wko-domain.yaml'
        source_file = os.path.join(self.MODELS_DIR, file_name)
        output_file = os.path.join(self.OUTPUT_DIR, file_name)
        shutil.copyfile(source_file, output_file)

        output_file_helper.update_from_model(File(output_file), model)

        # re-read the output file
        reader = YamlToPython(output_file, True)
        resource = reader.parse()

        # domain home was overridden
        domain_home = self._traverse(resource, 'spec', 'domainHome')
        self._match_values("Domain home", domain_home, "modelHome")

        # only one cluster was added
        cluster_list = self._traverse(resource, 'spec', 'clusters')
        self._match_values("Cluster count", len(cluster_list), 3)
        self._match_values("Third cluster name", cluster_list[2]['clusterName'], 'cluster3')

        # replica count of the first cluster was overridden
        self._match_values("First cluster replicas", cluster_list[0]['replicas'], 999)

        # only one secret was added
        secret_list = self._traverse(resource, 'spec', 'configuration', 'secrets')
        self._match_values("Cluster count", len(secret_list), 3)
        self._match_values("Third secret", secret_list[2], 'secret-three')

        # only one env was added
        env_list = self._traverse(resource, 'spec', 'serverPod', 'env')
        self._match_values("Env count", len(env_list), 3)
        self._match_values("Third env name", env_list[2]['name'], 'FROM_MODEL')

        # value of the first env was overridden
        self._match_values("First env value", env_list[0]['value'], '-DfromModel')
