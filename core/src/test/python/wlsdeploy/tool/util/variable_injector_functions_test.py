"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import unittest

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import MACHINE
from wlsdeploy.tool.util import variable_injector_functions
from wlsdeploy.util import variables
from wlsdeploy.util.model_context import ModelContext


class VariableInjectorFunctionsTests(unittest.TestCase):
    """
    Test the variable injector functions methods.
    """
    wls_version = '12.2.1.3'
    attribute_name = 'Notes'

    def setUp(self):
        model_context = ModelContext("test", {})
        self.aliases = Aliases(model_context)
        self.location = LocationContext().append_location(MACHINE)
        self.name_token = self.aliases.get_name_token(self.location)
        self.short_name = self.aliases.get_folder_short_name(self.location)

    def testFormatVariableName(self):
        """
        Verify that names from location are converted to valid variable names.
        """
        # spaces in model name
        self._check_name('My Machine', 'My-Machine')

        # parenthesis can be in model name
        self._check_name('ohMy-(datasource)', 'ohMy--datasource-')

        # versioned library names may be model names
        self._check_name('Lib.oracle.wsm.idmrest.sharedlib#1.0@12.2.1.3.Target',
                         'Lib.oracle.wsm.idmrest.sharedlib-1.0-12.2.1.3.Target')

    def _check_name(self, name, expected_key):
        """
        Verify that the specified name is converted to match the expected key.
        A machine location is created with the supplied name and converted to a variable name.
        An expected value is constructed using the expected key and known parameters.
        :param name: the name to be converted
        :param expected_key: the expected variable key
        """
        self.location.add_name_token(self.name_token, name)
        variable_name = variable_injector_functions.format_variable_name(self.location, self.attribute_name,
                                                                         self.aliases)

        # verify that a property built with this value will parse correctly
        property_text = '@@PROP:%s@@' % variable_name
        matches = variables._property_pattern.findall(property_text)
        self.assertEqual(1, len(matches), "Property %s should parse correctly" % property_text)

        expected_name = "%s.%s.%s" % (self.short_name, expected_key, self.attribute_name)
        self.assertEqual(expected_name, variable_name)


if __name__ == '__main__':
    unittest.main()
