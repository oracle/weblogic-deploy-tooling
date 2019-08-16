"""
Copyright (c) 2018, 2019, Oracle Corporation and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.
"""
import jarray
import unittest

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class AliasPasswordTestCase(unittest.TestCase):

    _logger = PlatformLogger('wlsdeploy.aliases')
    _wls_version = '12.2.1.3'
    _wlst_password_name = "Password"
    _wlst_password_encrypted_name = "PasswordEncrypted"

    _passphrase = 'RE a drop of golden sun'
    _password = 'welcome1'
    _encrypted_password = '{AES}UC9rZld3blZFUnMraW12cHkydmtmdmpSZmNNMWVHajA6VERPYlJoeWxXU09IaHVrQzpBeWsrd2ZacVkyVT0='
    _encrypted_password_bytes = jarray.array(_encrypted_password, 'b')

    def setUp(self):
        model_context = ModelContext("test", {CommandLineArgUtil.USE_ENCRYPTION_SWITCH: 'true',
                                              CommandLineArgUtil.PASSPHRASE_SWITCH: self._passphrase})
        self.aliases = Aliases(model_context, wlst_mode=WlstModes.OFFLINE, wls_version=self._wls_version)
        self.online_aliases = Aliases(model_context, wlst_mode=WlstModes.ONLINE, wls_version=self._wls_version)

        self.location = LocationContext()
        self.location.append_location(JDBC_SYSTEM_RESOURCE)
        self.location.add_name_token(self.aliases.get_name_token(self.location), "Mine")
        self.location.append_location(JDBC_RESOURCE)
        self.location.append_location(JDBC_DRIVER_PARAMS)

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
        self.assertEqual(wlst_value, self._password)

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
        self.assertEqual(wlst_value, self._password)

        # using unencrypted password
        wlst_name, wlst_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(self.location, PASSWORD_ENCRYPTED, self._password)
        self.assertEquals(wlst_name, self._wlst_password_name)
