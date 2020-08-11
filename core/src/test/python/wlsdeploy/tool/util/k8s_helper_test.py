"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

from wlsdeploy.tool.util import k8s_helper


class K8sHelperTestCase(unittest.TestCase):
    _program_name = 'k8s_helper_test'
    _class_name = 'K8sHelperTestCase'

    def testDomainUidCompliant(self):
        """
        Verify domain UID based on domain name is DNS-1123 compatible.
        """
        self._check_uid("base_domain", "base-domain")
        self._check_uid("My Domain", "my-domain")
        self._check_uid("my.a#$^!z.domain", "my.a----z.domain")
        self._check_uid("my.123.domain", "my.123.domain")

    def _check_uid(self, domain_name, expected_uid):
        domain_uid = k8s_helper.get_domain_uid(domain_name)
        self.assertEquals(expected_uid, domain_uid, "Domain UID for " + domain_name + " should be " + expected_uid)


if __name__ == '__main__':
    unittest.main()
