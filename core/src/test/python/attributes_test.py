"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.util.model_context import ModelContext

_FOLDER_MISMATCH_MSG = '*** NAME MISMATCH: Folder %s in location %s should be %s'
_ATTR_MISMATCH_MSG = '*** ATTRIBUTE MISMATCH: Attribute %s in location %s should be %s'


class AttributesTestCase(unittest.TestCase):
    """
       1) Unit tests must be a class that extends unittest.TestCase
       2) Class methods with names starting with 'test' will be executed by the framework (all others skipped)
    """
    wls_version = '12.2.1.3'

    def testAttributeNames(self):
        model_context = ModelContext("test", { })
        aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self.wls_version)

        location = LocationContext()
        self._check_folder('Domain', location, aliases)

        for folder_name in aliases.get_model_top_level_folder_names():
            location = LocationContext()
            location.append_location(folder_name)
            self._check_folder(folder_name, location, aliases)

    #
    # This test ensures that the attribute names match the WLST offline attribute names in 12.2.1.3.
    #
    def _check_folder(self, name, location, aliases):
        wlst_name = aliases.get_wlst_mbean_type(location)

        if not self._is_filtered_folder(name, location) and wlst_name != name:
            message = self._format(_FOLDER_MISMATCH_MSG, name, location.get_folder_path(), wlst_name)
            self.assertEqual(name, wlst_name, message)

        attr_infos = aliases.get_model_attribute_names_and_types(location)
        for key in attr_infos.keys():
            wlst_key = aliases.get_wlst_attribute_name(location, key)
            if wlst_key is not None and wlst_key != key:
                message = self._format(_ATTR_MISMATCH_MSG, key, location.get_folder_path(), wlst_key)
                self.assertEqual(key, wlst_key, message)

        folder_names = aliases.get_model_subfolder_names(location)
        for folder_name in folder_names:
            location.append_location(folder_name)
            self._check_folder(folder_name, location, aliases)
            location.pop_location()
        return

    def _format(self, key, *args):
        return key % args

    #
    # WARNING: DO NOT add folders to this method without discussing with the need with others.
    #
    def _is_filtered_folder(self, name, location):
        result = False


        if name == 'Domain':
            result = True
        elif location.get_folder_path() == '/JDBCSystemResource/JdbcResource/JDBCDriverParams/Properties' and \
                name == 'Properties':
            result = True
        elif location.get_folder_path() == '/ResourceGroupTemplate/JDBCSystemResource/JdbcResource/JDBCDriverParams/Properties' and \
                name == 'Properties':
            result = True
        elif location.get_folder_path() == '/ResourceGroup/JDBCSystemResource/JdbcResource/JDBCDriverParams/Properties' and \
                name == 'Properties':
            result = True
        elif location.get_folder_path() == '/Partition/ResourceGroup/JDBCSystemResource/JdbcResource/JDBCDriverParams/Properties' and \
                name == 'Properties':
            result = True
        elif location.get_folder_path() == '/Application':
            result = True
        elif location.get_folder_path() == '/ResourceGroupTemplate/Application':
            result = True
        elif location.get_folder_path() == '/ResourceGroup/Application':
            result = True
        elif location.get_folder_path() == '/Partition/ResourceGroup/Application':
            result = True
        elif location.get_folder_path() == '/SecurityConfiguration/Realm/Auditor/DefaultAuditor':
            result = True
        elif location.get_folder_path() == '/SecurityConfiguration/Realm/AuthenticationProvider/TrustServiceIdentityAsserter':
            result = True
        return result

if __name__ == '__main__':
    unittest.main()