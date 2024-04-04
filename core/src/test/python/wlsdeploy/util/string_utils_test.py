"""
Copyright (c) 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.util import string_utils

class StringUtilsTest(unittest.TestCase):
    def test_is_wls_version_or_above_above_returns_true(self):
        actual = string_utils.is_weblogic_version_or_above('12.2.1.3.0.210930', '12.2.1.3.0')
        self.assertEqual(True, actual)

    def test_is_wls_version_or_above_equal_returns_true(self):
        actual = string_utils.is_weblogic_version_or_above('12.2.1.3.0.210930', '12.2.1.3.0.210930')
        self.assertEqual(True, actual)

    def test_is_wls_version_or_above_below_returns_false(self):
        actual = string_utils.is_weblogic_version_or_above('12.2.1.3.0.210930', '12.2.1.3.0.220930')
        self.assertEqual(False, actual)
