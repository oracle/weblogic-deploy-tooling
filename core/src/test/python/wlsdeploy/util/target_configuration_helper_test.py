"""
Copyright (c) 2020, 2024, Oracle Corporation and/or its affiliates.
The Universal Permissive License (UPL), Version 1.0
"""

import unittest

import aliases_test
import wlsdeploy.util.target_configuration_helper as HELPER
import wlsdeploy.util.target_configuration as CONFIG
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DOMAIN_INFO_ALIAS
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import OPSS_WALLET_PASSPHRASE
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext

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

        wls_version = '12.2.1.3'

        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: ''
        }

        model_context = ModelContext("test", arg_map)

        # create a set of aliases for use with WLST
        self.aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE, wls_version=wls_version)

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

    def testFormatSecretName(self):
        # convert to lower case and append
        location = aliases_test.get_jdbc_resource_location('Generic1', self.aliases)
        self.assertEqual('jdbc-generic1', HELPER.format_secret_name(location, location, None, self.aliases))

        # change special chars to hyphens
        location = aliases_test.get_jdbc_resource_location('(WebLogic)-credentials', self.aliases)
        self.assertEqual('jdbc--weblogic--credentials',
                         HELPER.format_secret_name(location, location, None, self.aliases))

        # change special chars to hyphens, and strip
        location = aliases_test.get_jdbc_resource_location('-why?-', self.aliases)
        self.assertEqual('jdbc--why', HELPER.format_secret_name(location, location, None, self.aliases))

    def testGetSecretPath(self):
        # domainInfo:/OPSSSecrets has a secret key "walletPassword"
        info_location = LocationContext()
        info_att_location = LocationContext().append_location(DOMAIN_INFO_ALIAS)
        self.assertEqual('opsssecrets:walletPassword', HELPER.get_secret_path(info_location, info_att_location,
                                                                              OPSS_WALLET_PASSPHRASE, self.aliases))

        # domainInfo:/RCUDbInfo/javax.net.ssl.keyStorePassword has dots in the name
        rcu_location = LocationContext().append_location(RCU_DB_INFO)
        secret_path = HELPER.get_secret_path(rcu_location, rcu_location, DRIVER_PARAMS_KEYSTOREPWD_PROPERTY,
                                             self.aliases)
        self.assertEqual('rcudbinfo-sslkeystore:password', secret_path)


if __name__ == '__main__':
    unittest.main()
