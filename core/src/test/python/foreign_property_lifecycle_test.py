"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from base_test import BaseTestCase
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.tool.deploy.jms_resources_deployer import JmsResourcesDeployer
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.target_configuration import TargetConfiguration


class _ModelContext(ModelContext):
    version = '26.1.0.0.0'

    def get_effective_wls_version(self):
        return self.version


class ForeignPropertyLifecycleTest(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.context = _ModelContext('test', {
            CommandLineArgUtil.USE_ENCRYPTION_SWITCH: True,
            CommandLineArgUtil.PASSPHRASE_SWITCH: 'test-passphrase'
        })
        self.aliases = Aliases(self.context, wls_version='26.1.0.0.0', wlst_mode=WlstModes.OFFLINE)
        self.ciphertext = encryption_utils.encrypt_one_password('test-passphrase', 'original-marker')

    def _location(self, folders, property_name=None):
        location = LocationContext()
        for folder in folders:
            location.append_location(folder)
            token = self.aliases.get_name_token(location)
            if token is not None:
                location.add_name_token(token, 'Example' + folder)
        if property_name is not None:
            location.add_name_token(self.aliases.get_name_token(location), property_name)
        return location

    def _provider(self):
        return self._location(['ForeignJNDIProvider'])

    def _jms(self, property_name):
        return self._location(['JMSSystemResource', 'JmsResource', 'ForeignServer', 'JNDIProperty'], property_name)

    def _cache_values(self, injector):
        cache = injector.get_variable_cache()
        values = [cache[key] for key in cache]
        values.sort()
        return values

    def test_provider_decrypts_wdt_values_without_changing_model_or_ordinary_properties(self):
        properties = {'vendor.one.encrypted': self.ciphertext, 'vendor.plain': self.ciphertext}
        name, value = self.aliases.get_wlst_attribute_name_and_value(self._provider(), 'Properties', properties)
        self.assertEqual('Properties', name)
        self.assertEqual('original-marker', value['vendor.one.encrypted'])
        self.assertEqual(self.ciphertext, value['vendor.plain'])
        self.assertEqual(self.ciphertext, properties['vendor.one.encrypted'])

    def test_provider_plaintext_and_existing_entries_are_preserved(self):
        name, value = self.aliases.get_wlst_attribute_name_and_value(
            self._provider(), 'Properties', {'vendor.one.encrypted': 'plain-marker'},
            existing_wlst_value={'existing': 'existing-marker'})
        self.assertEqual('plain-marker', value['vendor.one.encrypted'])
        self.assertEqual('existing-marker', value['existing'])

    def test_provider_older_version_does_not_decrypt_suffix_values(self):
        aliases = Aliases(self.context, wls_version='14.1.2.0.0', wlst_mode=WlstModes.OFFLINE)
        name, value = aliases.get_wlst_attribute_name_and_value(
            self._provider(), 'Properties', {'vendor.one.encrypted': self.ciphertext})
        self.assertEqual(self.ciphertext, value['vendor.one.encrypted'])

    def test_jms_decrypts_marked_value_without_changing_model(self):
        deployer = JmsResourcesDeployer.__new__(JmsResourcesDeployer)
        deployer.aliases = self.aliases
        deployer.model_context = self.context
        nodes = {'Value': self.ciphertext}
        self.assertEqual('original-marker', deployer._decrypt_jndi_property('vendor.one.encrypted', nodes)['Value'])
        self.assertEqual(self.ciphertext, nodes['Value'])
        self.assertEqual(self.ciphertext, deployer._decrypt_jndi_property('vendor.plain', nodes)['Value'])
        self.context.version = '14.1.2.0.0'
        self.assertEqual(self.ciphertext, deployer._decrypt_jndi_property('vendor.one.encrypted', nodes)['Value'])

    def test_provider_tokenizes_distinct_marked_keys_and_leaves_ordinary_values(self):
        self.context._discover_passwords = True
        injector = CredentialInjector('test', self.context, self.aliases)
        properties = {'vendor.one.encrypted': 'first-marker', 'vendor.two.encrypted': 'second-marker',
                      'vendorXoneXencrypted': 'ordinary-marker'}
        model = {'Properties': properties}
        injector.check_and_tokenize(model, 'Properties', self._provider())
        self.assertEqual('ordinary-marker', properties['vendorXoneXencrypted'])
        self.assertEqual(True, properties['vendor.one.encrypted'].startswith('@@'))
        self.assertEqual(True, properties['vendor.two.encrypted'].startswith('@@'))
        self.assertEqual(False, properties['vendor.one.encrypted'] == properties['vendor.two.encrypted'])
        self.assertEqual(['first-marker', 'second-marker'], self._cache_values(injector))

    def test_default_provider_tokenization_does_not_cache_passwords(self):
        injector = CredentialInjector('test', self.context, self.aliases)
        model = {'Properties': {'vendor.one.encrypted': '--FIX ME--'}}
        injector.check_and_tokenize(model, 'Properties', self._provider())
        self.assertEqual([''], self._cache_values(injector))

    def test_jms_tokenization_names_include_actual_property_keys(self):
        self.context._discover_passwords = True
        injector = CredentialInjector('test', self.context, self.aliases)
        first = {'Value': 'first-marker'}
        second = {'Value': 'second-marker'}
        injector.check_and_tokenize(first, 'Value', self._jms('vendor.one.encrypted'))
        injector.check_and_tokenize(second, 'Value', self._jms('vendor.two.encrypted'))
        self.assertEqual(False, first['Value'] == second['Value'])
        self.assertEqual(['first-marker', 'second-marker'], self._cache_values(injector))

    def test_jms_explicit_key_controls_tokenization_and_secret_decryption(self):
        self.context._discover_passwords = True
        self.context._target_configuration = TargetConfiguration({'credentials_method': 'secrets'})
        injector = CredentialInjector('test', self.context, self.aliases)
        location = self._jms('NO_NAME_0')
        nodes = {'Key': 'vendor.secret.encrypted', 'Value': self.ciphertext}
        injector.check_and_tokenize(nodes, 'Value', location)
        self.assertEqual(True, nodes['Value'].startswith('@@SECRET:'))
        self.assertEqual(True, nodes['Value'].endswith(':password@@'))
        self.assertEqual(['original-marker'], self._cache_values(injector))
        self.assertEqual('NO_NAME_0', location.get_name_for_token(self.aliases.get_name_token(location)))

        same_key = {'Key': 'vendor.secret.encrypted', 'Value': self.ciphertext}
        injector.check_and_tokenize(same_key, 'Value', self._jms('different-instance'))
        self.assertEqual(nodes['Value'], same_key['Value'])

    def test_jms_plain_key_overrides_encrypted_instance_name(self):
        injector = CredentialInjector('test', self.context, self.aliases)
        nodes = {'Key': 'vendor.plain', 'Value': 'ordinary-marker'}
        injector.check_and_tokenize(nodes, 'Value', self._jms('vendor.secret.encrypted'))
        self.assertEqual('ordinary-marker', nodes['Value'])
        self.assertEqual(0, len(injector.get_variable_cache()))

    def test_jms_deployment_uses_explicit_key(self):
        deployer = JmsResourcesDeployer.__new__(JmsResourcesDeployer)
        deployer.aliases = self.aliases
        deployer.model_context = self.context
        nodes = {'Key': 'vendor.secret.encrypted', 'Value': self.ciphertext}
        self.assertEqual('original-marker', deployer._decrypt_jndi_property('NO_NAME_0', nodes)['Value'])
        self.assertEqual(self.ciphertext, nodes['Value'])
        nodes = {'Key': 'vendor.plain', 'Value': self.ciphertext}
        self.assertEqual(self.ciphertext, deployer._decrypt_jndi_property('vendor.secret.encrypted', nodes)['Value'])
        self.context.version = '14.1.2.0.0'
        nodes = {'Key': 'vendor.secret.encrypted', 'Value': self.ciphertext}
        self.assertEqual(self.ciphertext, deployer._decrypt_jndi_property('NO_NAME_0', nodes)['Value'])

    def test_jms_ordinary_and_older_version_values_are_not_tokenized(self):
        injector = CredentialInjector('test', self.context, self.aliases)
        nodes = {'Value': 'ordinary-marker'}
        injector.check_and_tokenize(nodes, 'Value', self._jms('vendor.plain'))
        self.assertEqual('ordinary-marker', nodes['Value'])
        self.context.version = '14.1.2.0.0'
        injector.check_and_tokenize(nodes, 'Value', self._jms('vendor.one.encrypted'))
        self.assertEqual('ordinary-marker', nodes['Value'])
        self.assertEqual(0, len(injector.get_variable_cache()))

    def test_encrypted_discovery_values_are_decrypted_for_secret_output(self):
        self.context._discover_passwords = True
        self.context._target_configuration = TargetConfiguration({'credentials_method': 'secrets'})
        injector = CredentialInjector('test', self.context, self.aliases)
        provider = {'Properties': {'vendor.one.encrypted': self.ciphertext}}
        jms = {'Value': self.ciphertext}
        injector.check_and_tokenize(provider, 'Properties', self._provider())
        injector.check_and_tokenize(jms, 'Value', self._jms('vendor.two.encrypted'))
        self.assertEqual(['original-marker', 'original-marker'], self._cache_values(injector))
        self.assertEqual(True, provider['Properties']['vendor.one.encrypted'].endswith(':password@@'))
        self.assertEqual(True, jms['Value'].endswith(':password@@'))

    def test_encrypted_discovery_values_stay_encrypted_in_variable_files(self):
        self.context._discover_passwords = True
        injector = CredentialInjector('test', self.context, self.aliases)
        provider = {'Properties': {'vendor.one.encrypted': self.ciphertext}}
        jms = {'Value': self.ciphertext}
        injector.check_and_tokenize(provider, 'Properties', self._provider())
        injector.check_and_tokenize(jms, 'Value', self._jms('vendor.two.encrypted'))
        self.assertEqual([self.ciphertext, self.ciphertext], self._cache_values(injector))


if __name__ == '__main__':
    import unittest
    unittest.main()
