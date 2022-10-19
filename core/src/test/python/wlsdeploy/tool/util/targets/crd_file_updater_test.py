"""
Copyright (c) 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import shutil

from base_test import BaseTestCase
from java.io import File

from wlsdeploy.tool.util.targets import crd_file_updater
from wlsdeploy.tool.util.targets import model_crd_helper
from wlsdeploy.util.model import Model
from wlsdeploy.yaml.yaml_translator import YamlToPython


class CrdFileUpdaterTest(BaseTestCase):

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'wko')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'wko')

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.OUTPUT_DIR)

    def test_crd_file_updater(self):
        """
        Test that kubernetes section of the model is merged into the
        domain resource file correctly.
        """
        documents = self._merge_and_read('k8s-model.yaml', 'wko-domain.yaml', model_crd_helper.WKO_VERSION_3)
        self._match_values("Document count", len(documents), 1)
        domain_resource = documents[0]

        # check simple fields
        self._check_domain_crd(domain_resource)

        # only one cluster was added
        cluster_list = self._traverse(domain_resource, 'spec', 'clusters')
        self._match_values("Cluster count", len(cluster_list), 3)
        self._match_values("Third cluster name", cluster_list[2]['clusterName'], 'cluster3')

        # replica count of the first cluster was overridden
        self._match_values("First cluster replicas", cluster_list[0]['replicas'], 999)

    def test_crd_file_updater_v4(self):
        """
        Test that kubernetes section of the model is merged into the
        domain resource file correctly.
        """
        documents = self._merge_and_read('k8s-model-v4.yaml', 'wko-domain-v4.yaml', model_crd_helper.WKO_VERSION_4)
        self._match_values("Document count", len(documents), 4)
        domain_resource = documents[0]

        # check simple fields
        self._check_domain_crd(domain_resource)

        # only one cluster was added
        cluster_list = self._traverse(domain_resource, 'spec', 'clusters')
        self._match_values("Domain cluster count", len(cluster_list), 3)
        self._match_values("Third domain cluster name", cluster_list[2]['name'], 'cluster3')

        # replica count of the first cluster was overridden
        cluster_resource = documents[1]
        replica_count = self._traverse(cluster_resource, 'spec', 'replicas')
        self._match_values("First cluster replicas", replica_count, 999)

    def _check_domain_crd(self, domain_resource):
        # domain home was overridden
        domain_home = self._traverse(domain_resource, 'spec', 'domainHome')
        self._match_values("Domain home", domain_home, "modelHome")

        # only one secret was added
        secret_list = self._traverse(domain_resource, 'spec', 'configuration', 'secrets')
        self._match_values("Cluster count", len(secret_list), 3)
        self._match_values("Third secret", secret_list[2], 'secret-three')

        # only one env was added
        env_list = self._traverse(domain_resource, 'spec', 'serverPod', 'env')
        self._match_values("Env count", len(env_list), 3)
        self._match_values("Third env name", env_list[2]['name'], 'FROM_MODEL')

        # value of the first env was overridden
        self._match_values("First env value", env_list[0]['value'], '-DfromModel')

    def _merge_and_read(self, model_name, crd_name, wko_version):
        """
        Merge the specified model to the specified CRD, then read and return the result.
        """
        model_file = os.path.join(self.MODELS_DIR, model_name)
        reader = YamlToPython(model_file, True)
        model_dict = reader.parse()
        model = Model(model_dict)

        # copy the domain resource file to the target directory
        source_file = os.path.join(self.MODELS_DIR, crd_name)
        output_file = os.path.join(self.OUTPUT_DIR, crd_name)
        shutil.copyfile(source_file, output_file)

        crd_helper = model_crd_helper.get_product_helper(model_crd_helper.WKO_PRODUCT_KEY, wko_version)
        crd_file_updater.update_from_model(File(output_file), model, crd_helper)

        # re-read the output file
        reader = YamlToPython(output_file, True)
        return reader.parse_documents()
