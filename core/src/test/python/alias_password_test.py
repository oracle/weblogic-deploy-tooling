"""
Copyright (c) 2018, 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import unittest

import aliases_test
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.model_context import ModelContext


class AliasPasswordTestCase(unittest.TestCase):
    """
    Test domain-encrypted passwords in a model.
    """

    _logger = PlatformLogger('wlsdeploy.aliases')
    _wls_version = '12.2.1.3'
    _wlst_password_name = "Password"
    _wlst_password_encrypted_name = "PasswordEncrypted"

    _password = 'welcome1'
    _encrypted_password = '{AES}UC9rZld3blZFUnMraW12cHkydmtmdmpSZmNNMWVHajA6VERPYlJoeWxXU09IaHVrQzpBeWsrd2ZacVkyVT0='

    def setUp(self):
        model_context = ModelContext("test", {})
        self.aliases = Aliases(model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self._wls_version)
        self.online_aliases = Aliases(model_context, wlst_mode=WlstModes.ONLINE, wls_version=self._wls_version)

        self.location = aliases_test.get_jdbc_driver_params_location("Mine", self.aliases)

    def testOfflineModelNames(self):
        # Using offline WLST, only PasswordEncrypted is an attribute, and its value is encrypted.
        # The model name should be PasswordEncrypted.
        model_name, model_value = \
            self.aliases.get_model_attribute_name_and_value(self.location, self._wlst_password_encrypted_name,
                                                            self._encrypted_password)
        self.assertEquals(model_name, PASSWORD_ENCRYPTED)

    def testOnlineModelNames(self):
        # Using online WLST, both Password and PasswordEncrypted are WLST attributes.

        # The PasswordEncrypted WLST attribute should translate to the PasswordEncrypted model attribute.
        model_name, model_value = \
            self.online_aliases.get_model_attribute_name_and_value(self.location, self._wlst_password_encrypted_name,
                                                                   self._encrypted_password)
        self.assertEqual(model_name, PASSWORD_ENCRYPTED)

        # The Password WLST attribute should be skipped, since its value cannot be retrieved.
        # This is accomplished by returning a model name of None.
        model_name, model_value = \
            self.online_aliases.get_model_attribute_name_and_value(self.location, self._wlst_password_name,
                                                                   self._encrypted_password)
        self.assertEquals(model_name, None)

    def testOfflineWlstNames(self):
        # Using offline WLST, the PasswordEncrypted model attribute should translate to the PasswordEncrypted WLST
        # attribute, regardless of whether the password is encrypted.

        # using encrypted password
        wlst_name, wlst_value = \
            self.aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._encrypted_password)
        self.assertEqual(wlst_name, self._wlst_password_encrypted_name)
        self.assertEqual(wlst_value, self._encrypted_password)

        # using unencrypted password
        wlst_name, wlst_value = \
            self.aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._password)
        self.assertEquals(wlst_name, self._wlst_password_encrypted_name)

    def testOnlineWlstNames(self):
        # Using online WLST, the PasswordEncrypted model attribute should translate to the PasswordEncrypted WLST
        # attribute if the password is encrypted, otherwise to Password.

        # using encrypted password
        wlst_name, wlst_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED,
                                                                  self._encrypted_password)
        self.assertEqual(wlst_name, self._wlst_password_encrypted_name)
        self.assertEqual(wlst_value, self._encrypted_password)

        # using unencrypted password
        wlst_name, wlst_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._password)
        self.assertEquals(wlst_name, self._wlst_password_name)
