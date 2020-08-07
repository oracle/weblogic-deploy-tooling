"""
Copyright (c) 2019, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import aliases_test
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class AliasEncryptedModelTestCase(unittest.TestCase):
    """
    Test cases for a the -use_encryption feature.
    """

    _logger = PlatformLogger('wlsdeploy.aliases')
    _wls_version = '12.2.1.3'
    _wlst_password_name = "Password"
    _wlst_password_encrypted_name = "PasswordEncrypted"

    _passphrase = 'RE a drop of golden sun'
    _password = 'welcome1'
    _encrypted_password = '{AES}UC9rZld3blZFUnMraW12cHkydmtmdmpSZmNNMWVHajA6VERPYlJoeWxXU09IaHVrQzpBeWsrd2ZacVkyVT0='

    def setUp(self):
        # construct aliases as if the -use_encryption and -passphrase switches were used
        model_context = ModelContext("test", {CommandLineArgUtil.USE_ENCRYPTION_SWITCH: 'true',
                                              CommandLineArgUtil.PASSPHRASE_SWITCH: self._passphrase})
        self.aliases = Aliases(model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self._wls_version)
        self.online_aliases = Aliases(model_context, wlst_mode=WlstModes.ONLINE, wls_version=self._wls_version)

        self.location = aliases_test.get_jdbc_driver_params_location("Mine", self.aliases)

    def testOfflineWlstNames(self):
        # Using offline WLST, the PasswordEncrypted model attribute should translate to the PasswordEncrypted WLST
        # attribute, regardless of whether the password is encrypted. The password value should be plain text.

        # using encrypted password
        wlst_name, wlst_value = \
            self.aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._encrypted_password)
        self.assertEqual(wlst_name, self._wlst_password_encrypted_name)
        self.assertEqual(wlst_value, self._password)

        # using unencrypted password
        wlst_name, wlst_value = \
            self.aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._password)
        self.assertEquals(wlst_name, self._wlst_password_encrypted_name)
        self.assertEqual(wlst_value, self._password)

    def testOnlineWlstNames(self):
        # Using online WLST, the PasswordEncrypted model attribute should always translate to the Password WLST
        # attribute, and the value should translate to the unencrypted value.

        # using encrypted password
        wlst_name, wlst_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED,
                                                                  self._encrypted_password)
        self.assertEqual(wlst_name, self._wlst_password_name)
        self.assertEqual(wlst_value, self._password)

        # using unencrypted password
        wlst_name, wlst_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._password)
        self.assertEquals(wlst_name, self._wlst_password_name)
        self.assertEqual(wlst_value, self._password)
