"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.util.model_context import ModelContext


class AttributesTypeTestCase(unittest.TestCase):
    """
       1) Unit tests must be a class that extends unittest.TestCase
       2) Class methods with names starting with 'test' will be executed by the framework (all others skipped)
    """
    wls_version = '12.2.1.3'

    def testDelimitedAttributes(self):
        # This test ensures that delimited attributes are always comma-delimited for the model.
        # Space-delimited attributes are allowed to bypass this rule.

        model_context = ModelContext("test", {})
        aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self.wls_version)

        location = LocationContext()
        self._check_folder(location, aliases)

        for folder_name in aliases.get_model_top_level_folder_names():
            location = LocationContext()
            location.append_location(folder_name)
            self._check_folder(location, aliases)

    def _check_folder(self, location, aliases):
        test_value = ['one', 'two']
        expected_value = ','.join(test_value)

        attr_infos = aliases.get_model_attribute_names_and_types(location)
        for key in attr_infos.keys():
            model_type = attr_infos[key]
            if model_type.startswith("delimited_string") and not model_type.endswith("[space]"):

                wlst_name = aliases.get_wlst_attribute_name(location, key)
                if wlst_name is not None:
                    model_name, value = aliases.get_model_attribute_name_and_value(location, wlst_name, test_value)
                    message = "Value for attribute " + key + " in location " + str(location.get_folder_path()) + \
                        " should be comma-delimited"
                    self.assertEqual(expected_value, value, message)

        folder_names = aliases.get_model_subfolder_names(location)
        for folder_name in folder_names:
            new_location = LocationContext(location).append_location(folder_name)
            self._check_folder(new_location, aliases)
        return


if __name__ == '__main__':
    unittest.main()
