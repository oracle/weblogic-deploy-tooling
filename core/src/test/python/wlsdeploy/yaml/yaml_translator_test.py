"""
Copyright (c) 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from base_test import BaseTestCase
from oracle.weblogic.deploy.yaml import YamlException
from wlsdeploy.yaml.yaml_translator import PythonToYaml
from wlsdeploy.yaml.yaml_translator import YamlToPython


class YamlTranslatorTest(BaseTestCase):

    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.MODELS_DIR = os.path.join(self.TEST_CLASSES_DIR, 'yaml')
        self.OUTPUT_DIR = os.path.join(self.TEST_OUTPUT_DIR, 'yaml')

    def setUp(self):
        BaseTestCase.setUp(self)
        self._establish_directory(self.OUTPUT_DIR)

    def testMultipleDocuments(self):
        """
        Test that YAML with multiple documents can be read and written
        without alteration.
        """
        model_file = os.path.join(self.MODELS_DIR, 'multiple-docs.yaml')
        reader = YamlToPython(model_file, True)
        result = reader.parse_documents()
        self._match_values("Document count", len(result), 3)

        # write the document without exceptions
        output_file = os.path.join(self.OUTPUT_DIR, 'multiple-docs.yaml')
        writer = PythonToYaml(result)
        writer.write_to_yaml_file(output_file)

        # re-read the output file, and check document count
        reader = YamlToPython(output_file, True)
        result = reader.parse_documents()
        self._match_values("Re-read document count", len(result), 3)

    def testParseMultipleDocuments(self):
        """
        Test that YAML with multiple documents can not be read
        with the YamlToPython parse() method.
        """
        try:
            model_file = os.path.join(self.MODELS_DIR, 'multiple-docs.yaml')
            reader = YamlToPython(model_file, True)
            reader.parse()
            self.fail("Should not parse multiple-document YAML with parse()")
        except YamlException:
            pass

