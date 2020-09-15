"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
The Universal Permissive License (UPL), Version 1.0
"""

import unittest

import wlsdeploy.util.target_configuration_helper as HELPER
import wlsdeploy.util.target_configuration as CONFIG

from wlsdeploy.util.target_configuration import TargetConfiguration


class TargetConfigurationTests(unittest.TestCase):
    """

    Test the target configuration and helper methods.
    """

    target_with_cred_name = None
    target_without_cred_name = None

    def setUp(self):
        config = dict()
        config[CONFIG.CREDENTIALS_METHOD] = 'secrets'
        config[CONFIG.WLS_CREDENTIALS_NAME] = '__weblogic-credentials__'
        self.target_with_cred_name = TargetConfiguration(config)

        config2 = dict()
        config2[CONFIG.CREDENTIALS_METHOD] = 'secrets'
        self.target_without_cred_name = TargetConfiguration(config2)


    def testSecretWithWlsCredName(self):
        self.assertEqual('@@SECRET:__weblogic-credentials__:username@@',
                         HELPER.format_as_secret_token(HELPER.WEBLOGIC_CREDENTIALS_SECRET_NAME + ':username',
                                                       self.target_with_cred_name))

        self.assertEqual('@@SECRET:__weblogic-credentials__:password@@',
                         HELPER.format_as_secret_token(HELPER.WEBLOGIC_CREDENTIALS_SECRET_NAME + ':password',
                                                       self.target_with_cred_name))

        self.assertEqual('@@SECRET:@@ENV:DOMAIN_UID@@-something-else:password@@',
                         HELPER.format_as_secret_token('something-else:password', self.target_with_cred_name))


    def testSecretWithoutWlsCredName(self):
        self.assertEqual('@@SECRET:@@ENV:DOMAIN_UID@@-weblogic-credentials:username@@',
                         HELPER.format_as_secret_token(HELPER.WEBLOGIC_CREDENTIALS_SECRET_NAME + ':username',
                                                       self.target_without_cred_name))

        self.assertEqual('@@SECRET:@@ENV:DOMAIN_UID@@-weblogic-credentials:password@@',
                         HELPER.format_as_secret_token(HELPER.WEBLOGIC_CREDENTIALS_SECRET_NAME + ':password',
                                                       self.target_without_cred_name))

        self.assertEqual('@@SECRET:@@ENV:DOMAIN_UID@@-something-else:password@@',
                         HELPER.format_as_secret_token('something-else:password', self.target_without_cred_name))


    def testCreateSecretName(self):
        self.assertEqual('jdbc-generic1', HELPER.create_secret_name('JDBC.Generic1.PasswordEncrypted'))

        self.assertEqual('jdbc--weblogic--credentials',
                         HELPER.create_secret_name('JDBC.(WebLogic)-credentials.PasswordEncrypted'))

        self.assertEqual('jdbc--why', HELPER.create_secret_name('JDBC.-why?-.PasswordEncrypted'))

        self.assertEqual('jdbc-abc', HELPER.create_secret_name('-JDBC.abc-.PasswordEncrypted'))

        self.assertEqual('x', HELPER.create_secret_name('--??!!'))


if __name__ == '__main__':
    unittest.main()
