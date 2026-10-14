"""
Copyright (c) 2026, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from base_test import BaseTestCase
from wlsdeploy.aliases import alias_constants
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.tool.discover.discoverer import Discoverer
from wlsdeploy.tool.discover.jms_resources_discoverer import JmsResourcesDiscoverer
from wlsdeploy.tool.encrypt import encryption_utils


class _Context(object):
    discover_passwords = False
    encrypt_passwords = False
    ssh = False

    def is_discover_passwords(self):
        return self.discover_passwords

    def is_encrypt_discovered_passwords(self):
        return self.encrypt_passwords

    def is_discover_rcu_datasources(self):
        return False

    def get_domain_home(self):
        return '/test-domain'

    def is_ssh(self):
        return self.ssh

    def get_encryption_passphrase(self):
        return 'test-passphrase'


class _WebLogicHelper(object):
    def __init__(self):
        self.calls = []
        self.fail_decryption = False

    def decrypt(self, value, domain_home):
        self.calls.append((value, domain_home))
        if self.fail_decryption:
            raise ValueError('invalid ciphertext')
        return 'decrypted-marker'


class _Aliases(object):
    def get_model_folder_path(self, location):
        return location.get_folder_path()

    def get_name_token(self, location):
        return 'FOLDERNAME'

    def get_wlst_attribute_name(self, location, attribute):
        return attribute


class _WlstHelper(object):
    property_name = None

    def get(self, attribute):
        return self.property_name


class _JmsDiscoverer(JmsResourcesDiscoverer):
    def _find_names_in_folder(self, location):
        return ['NO_NAME_0', 'NO_NAME_1']

    def _get_attributes_for_current_location(self, location):
        if location.get_name_for_token('FOLDERNAME') == 'NO_NAME_0':
            return {model_constants.KEY: 'vendor.password.encrypted'}
        return {model_constants.KEY: 'vendor.encrypted.option'}

    def _populate_model_parameters(self, dictionary, location):
        self._wlst_helper.property_name = self._get_attributes_for_current_location(location)[model_constants.KEY]
        dictionary['Value'] = self._check_attribute('Value', 'ciphertext', location)


class ForeignPropertiesDiscovererTest(BaseTestCase):
    def _discoverer(self, discoverer_class=Discoverer, version='26.1.0.0.0'):
        discoverer = discoverer_class.__new__(discoverer_class)
        discoverer._model_context = _Context()
        discoverer._weblogic_helper = _WebLogicHelper()
        discoverer._att_handler_map = OrderedDict()
        discoverer._wls_version = version
        discoverer._aliases = _Aliases()
        discoverer._wlst_helper = _WlstHelper()
        discoverer.download_temporary_dir = '/downloaded-domain'
        return discoverer

    def _provider_location(self):
        return LocationContext().append_location(model_constants.FOREIGN_JNDI_PROVIDER)

    def _properties(self):
        properties = OrderedDict()
        properties['vendor.password.encrypted'] = 'ciphertext\\='
        properties['vendor.encrypted.option'] = 'ordinary-value'
        properties['vendor.empty.encrypted'] = ''
        return properties

    def test_provider_masks_only_suffix_marked_properties(self):
        discoverer = self._discoverer()
        original = self._properties()
        result = discoverer._check_attribute(model_constants.PROPERTIES, original, self._provider_location())
        self.assertEqual(alias_constants.PASSWORD_TOKEN, result['vendor.password.encrypted'])
        self.assertEqual('ordinary-value', result['vendor.encrypted.option'])
        self.assertEqual('', result['vendor.empty.encrypted'])
        self.assertEqual('ciphertext\\=', original['vendor.password.encrypted'])
        self.assertEqual([], discoverer._weblogic_helper.calls)

    def test_provider_decrypts_and_normalizes_escaped_padding(self):
        discoverer = self._discoverer()
        discoverer._model_context.discover_passwords = True
        result = discoverer._check_attribute(model_constants.PROPERTIES, self._properties(), self._provider_location())
        self.assertEqual('decrypted-marker', result['vendor.password.encrypted'])
        self.assertEqual([('ciphertext=', '/test-domain')], discoverer._weblogic_helper.calls)

    def test_provider_reencrypts_when_requested(self):
        discoverer = self._discoverer()
        discoverer._model_context.discover_passwords = True
        discoverer._model_context.encrypt_passwords = True
        result = discoverer._check_attribute(model_constants.PROPERTIES, self._properties(), self._provider_location())
        decrypted = encryption_utils.decrypt_one_password('test-passphrase', result['vendor.password.encrypted'])
        self.assertEqual('decrypted-marker', decrypted)

    def test_provider_uses_downloaded_domain_for_ssh(self):
        discoverer = self._discoverer()
        discoverer._model_context.discover_passwords = True
        discoverer._model_context.ssh = True
        discoverer._check_attribute(model_constants.PROPERTIES, self._properties(), self._provider_location())
        self.assertEqual([('ciphertext=', '/downloaded-domain')], discoverer._weblogic_helper.calls)

    def test_provider_decryption_failure_is_not_hidden(self):
        discoverer = self._discoverer()
        discoverer._model_context.discover_passwords = True
        discoverer._weblogic_helper.fail_decryption = True
        self.assertRaises(ValueError, discoverer._check_attribute, model_constants.PROPERTIES,
                          self._properties(), self._provider_location())

    def test_older_versions_and_other_properties_are_unchanged(self):
        original = self._properties()
        discoverer = self._discoverer(version='14.1.2.0.0')
        self.assertEqual(original, discoverer._check_attribute(
            model_constants.PROPERTIES, original, self._provider_location()))
        discoverer._wls_version = '26.1.0.0.0'
        location = LocationContext().append_location(model_constants.MAIL_SESSION)
        self.assertEqual(original, discoverer._check_attribute(model_constants.PROPERTIES, original, location))

    def test_provider_in_resource_group_is_processed(self):
        discoverer = self._discoverer()
        location = LocationContext().append_location(model_constants.RESOURCE_GROUP)
        location.append_location(model_constants.FOREIGN_JNDI_PROVIDER)
        result = discoverer._check_attribute(model_constants.PROPERTIES, self._properties(), location)
        self.assertEqual(alias_constants.PASSWORD_TOKEN, result['vendor.password.encrypted'])

    def _jms_properties(self, discoverer):
        location = LocationContext().append_location(model_constants.JMS_SYSTEM_RESOURCE)
        location.append_location(model_constants.JMS_RESOURCE)
        location.append_location(model_constants.FOREIGN_SERVER)
        folder, properties = discoverer._get_foreign_server_properties(location)
        self.assertEqual(model_constants.JNDI_PROPERTY, folder)
        return properties

    def test_jms_masks_using_key_instead_of_offline_folder_name(self):
        discoverer = self._discoverer(_JmsDiscoverer)
        properties = self._jms_properties(discoverer)
        self.assertEqual(alias_constants.PASSWORD_TOKEN, properties['vendor.password.encrypted']['Value'])
        self.assertEqual('ciphertext', properties['vendor.encrypted.option']['Value'])
        self.assertEqual([], discoverer._weblogic_helper.calls)

    def test_jms_decrypts_using_domain_key(self):
        discoverer = self._discoverer(_JmsDiscoverer)
        discoverer._model_context.discover_passwords = True
        properties = self._jms_properties(discoverer)
        self.assertEqual('decrypted-marker', properties['vendor.password.encrypted']['Value'])
        self.assertEqual([('ciphertext', '/test-domain')], discoverer._weblogic_helper.calls)

    def test_jms_older_version_is_unchanged(self):
        discoverer = self._discoverer(_JmsDiscoverer, '14.1.2.0.0')
        properties = self._jms_properties(discoverer)
        self.assertEqual('ciphertext', properties['vendor.password.encrypted']['Value'])


if __name__ == '__main__':
    import unittest
    unittest.main()
