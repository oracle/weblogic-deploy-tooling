"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.util.model_context import ModelContext


class AttributesTypeTestCase(unittest.TestCase):
    """
    This test verifies that the every alias attribute that has the model type "delimited_string" returns a
    comma-delimited string for method get_model_attribute_name_and_value.  The model should always use
    comma-delimited values, except for the special case of delimited_string[space], which has special handling.

    This test currently only verifies attributes for the 12.2.1.3 offline alias structure.  Values that are
    obsolete in 12.2.1.3, or were created since 12.2.1.3 are not included.
    """
    wls_version = '12.2.1.3'

    def testDelimitedAttributes(self):
        model_context = ModelContext("test", {})
        aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self.wls_version)

        location = LocationContext()
        self._check_folder(location, aliases)

        for folder_name in aliases.get_model_top_level_folder_names():
            location = LocationContext()
            location.append_location(folder_name)
            self._check_folder(location, aliases)

    def _check_folder(self, location, aliases):
        wlst_name = aliases.get_wlst_mbean_type(location)
        if wlst_name is None:
            # folders added since 12.2.1.3 are not in the alias structure.
            # this test does not validate attributes in those folders.
            return

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
