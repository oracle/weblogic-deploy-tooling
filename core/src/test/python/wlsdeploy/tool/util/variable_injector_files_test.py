"""
Copyright (c) 2024, Oracle and/or its affiliates.
The Universal Permissive License (UPL), Version 1.0
"""
import os
import unittest

from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython


class VariableInjectorFilesTest(BaseTestCase):
    """
    Test the variable injector file contents.
    """
    def __init__(self, *args):
        BaseTestCase.__init__(self, *args)
        self.INJECTORS_DIR = os.path.join(self.TEST_CONFIG_DIR, 'injectors')
        self.VALID_CODES = [ValidationCodes.VALID, ValidationCodes.CONTEXT_INVALID]

    def setUp(self):
        model_context = ModelContext("test", {})
        self.aliases = Aliases(model_context, wls_version=self.ALIAS_WLS_VERSION)

    def test_injector_files(self):
        """
        Verify that paths in the injector files are valid.
        """
        for file_name in os.listdir(self.INJECTORS_DIR):
            if file_name.endswith(".json"):
                file_path = os.path.join(self.INJECTORS_DIR, file_name)
                translator = FileToPython(file_path, use_ordering=True)
                injector_dict = translator.parse()
                for injector_path in injector_dict:
                    elements = injector_path.split('.')
                    location = LocationContext()
                    for element in elements[:-1]:
                        location.append_location(element)
                        name_token = self.aliases.get_name_token(location)
                        if name_token is not None:
                            location.add_name_token(name_token, 'TOKEN')

                        code, _message = self.aliases.is_version_valid_location(location)
                        is_valid = code in self.VALID_CODES
                        self.assertEqual(is_valid, True, "Folder " + str(element) + " in path " + str(injector_path)
                                         + " in injector file " + str(file_name) + " is not valid")

                    attribute_name = elements[-1]
                    code, _message = self.aliases.is_valid_model_attribute_name(location, attribute_name)
                    is_valid = code in self.VALID_CODES
                    self.assertEqual(is_valid, True, "Attribute " + str(attribute_name) + " in path " +
                                     str(injector_path) + " in injector file " + str(file_name) + " is not valid")


if __name__ == '__main__':
    unittest.main()
