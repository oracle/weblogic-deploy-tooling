"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import unittest

from org.python.modules import jarray

from java.util import HashMap
from java.lang import String
from java.lang import System
from java.io import ByteArrayOutputStream
from java.io import DataOutputStream
from java.io import File
from java.io import IOException
from java.util import Properties

from oracle.weblogic.deploy.util import PyOrderedDict

import wlsdeploy.aliases.alias_constants as alias_constants
import wlsdeploy.logging.platform_logger as platform_logger
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.discover.custom_folder_helper import CustomFolderHelper
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.mbean_utils import MBeanInfoAttributes
from wlsdeploy.util.cla_utils import CommandLineArgUtil as CLA
from wlsdeploy.util.model_context import ModelContext

_mbean_interface = 'weblogic.security.providers.authentication.OracleIdentityCloudIntegratorMBean'
_interface_for_model = 'weblogic.security.providers.authentication.OracleIdentityCloudIntegrator'
_provider_name = 'IoT IDCS Authenticator'


class CustomFolderHelperTestCase(unittest.TestCase):
    """
    Test extracting MBeanInfo from an MBean that is loaded into the WLST 12.2.1.3.
    In this case, the selected MBean is the IDCS or OracleIdentityCloudIntegrationMBean. This MBean
    is delivered with Oracle 12.2.1.3 weblogic installs. Since WLST is started when this test runs,
    it will be loaded into the classpath. There is no need to open a domain to get the MBeanInfo for this MBean.
    The test does not go through a path that requires a domain MBean instance. The WLST value is supplied by
    each test.

    Test the Custom MBean attribute conversion routines which convert from WLST value to Model value and
    test that defaults return None.
    """

    _custom_helper = None
    _oracle_home = None
    _logger = platform_logger.PlatformLogger('wlsdeploy.unittest')
    _location = None
    _bean_info_access = None
    _aliases = None
    _alias_helper = None
    _helper = None
    _model_context = None

    _wls_version = '12.2.1.3'

    _mbean_info = None

    def setUp(self):
        wlst_dir = File(System.getProperty('unit-test-wlst-dir'))
        self._oracle_home = wlst_dir.getParentFile().getParentFile().getParentFile().getCanonicalPath()
        arg_map = dict()
        arg_map[CLA.ORACLE_HOME_SWITCH] = self._oracle_home
        arg_map[CLA.TARGET_MODE_SWITCH] = 'offline'

        self._model_context = ModelContext("test", arg_map)
        self._aliases = Aliases(model_context=self._model_context, wlst_mode=WlstModes.OFFLINE,
                                wls_version=self._wls_version)
        self._alias_helper = AliasHelper(self._aliases, self._logger, ExceptionType.DISCOVER)
        self._location = LocationContext().append_location('SecurityConfiguration')
        self._location.add_name_token(self.name_token(self._location), 'testdomain')
        self._location.append_location('Realm').add_name_token(self.name_token(self._location), 'myrealm'). \
            append_location('AuthenticationProvider'). \
            add_name_token(self.name_token(self._location), 'IoT IDCS Authenticator')
        self._helper = MBeanInfoAttributes(self._model_context, self._alias_helper, ExceptionType.DISCOVER,
                                           self._location, _mbean_interface)
        self._custom_helper = CustomFolderHelper(self._aliases, self._logger, self._model_context,
                                                 ExceptionType.DISCOVER)
        return

    def testEncryptedPassword(self):
        credential_string = 'AES}0vlIcO+I+VWV9aQ1wzQUa1qtByh4D9d0I1dJHa7HsdE='
        try:
            bos = ByteArrayOutputStream()
            dos = DataOutputStream(bos)
            dos.writeBytes(credential_string)
            byte_array = bos.toByteArray()
            dos.close()
        except IOException, ioe:
            self.fail('Unexpected exception writing out credential : ', str(ioe))
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'ClientSecretEncrypted', byte_array)
        self.assertEqual(alias_constants.PASSWORD_TOKEN, return_result)

    def testClearTextPassword(self):
        credential_string = '*******'
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'ClientSecret', credential_string)
        self.assertEquals(None, return_result)

    def testListEqualsDefault(self):
        list_value = ['foo', 'bar']
        list_default = list(list_value)
        converted_type, converted = self._custom_helper.convert(list_value, 'list')
        self.assertEquals(alias_constants.LIST, converted_type)
        __, converted_default = self._custom_helper.convert(list_default, 'list')
        return_result = self._custom_helper.is_default(converted, converted_type, converted_default)
        self.assertEquals(True, return_result)

    def testListNotDefaultLengthDiff(self):
        list_value = ['foo', 'bar']
        list_default = ['bar']
        converted_type, converted = self._custom_helper.convert(list_value, 'list')
        self.assertEquals(alias_constants.LIST, converted_type)
        __, converted_default = self._custom_helper.convert(list_default, 'list')
        return_result = self._custom_helper.is_default(converted, converted_type, converted_default)
        self.assertEquals(False, return_result)

    def testListNotDefaultElementsDiff(self):
        list_value = ['abc', 'xyz']
        list_default = ['bar', 'foo']
        converted_type, converted = self._custom_helper.convert(list_value, 'list')
        self.assertEquals(2, len(converted))
        self.assertEquals(alias_constants.LIST, converted_type)
        __, converted_default = self._custom_helper.convert(list_default, 'list')
        return_result = self._custom_helper.is_default(converted, converted_type, converted_default)
        self.assertEquals(False, return_result)

    def testJarrayEqualsDefault(self):
        jarray_value = jarray.array(['Idcs_user_assertion', 'idcs_user_assertion'], String)
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'ActiveTypes', jarray_value)
        self.assertEquals(None, return_result)

    def testJarryDoesNotEqualDefault(self):
        length_diff = jarray.array(['idcs_user_assertion'], String)
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'ActiveTypes', length_diff)
        self.assertNotEquals(None, return_result)
        self.assertEquals(list, type(return_result))
        self.assertEquals(1, len(return_result))
        value_diff = jarray.array(['nonmatch', 'idcs_user_assertion'], String)
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'ActiveTypes', value_diff)
        self.assertNotEquals(None, return_result)
        self.assertEquals(list, type(return_result))
        self.assertEquals(2, len(return_result))

    def testMatchesEmptyJarray(self):
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'SyncFilterUserHeaderNames', None)
        self.assertEquals(None, return_result)

    def testReadOnly(self):
        return_result = self._custom_helper.\
            get_model_attribute_value(self._helper, 'ProviderClassName',
                                      'weblogic.security.providers.authentication.IDCSIntegratorProviderImpl')
        self.assertEquals(None, return_result)

    def testBooleanDefault(self):
        bool_value = False
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'SSLEnabled', bool_value)
        self.assertEquals(None, return_result)

    def testBooleanNotDefault(self):
        bool_value = False
        return_result = self._custom_helper.get_model_attribute_value(self._helper,
                                                                      'SyncFilterOnlyClientCertRequests', bool_value)
        self.assertEquals('false', return_result)

    def testDictionaryDefault(self):
        dict_value = {'integer1': 111, 'integer2': 112}
        dict_default = {'integer2': 112, 'integer1': 111}
        converted_type, converted_value = self._custom_helper.convert(dict_value, 'dict')
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        __, default_value = self._custom_helper.convert(dict_default, 'dict')
        return_result = self._custom_helper.is_default(converted_value, converted_type, default_value)
        self.assertEquals(True, return_result)

    def testDictionaryNotDefault(self):
        dict_value = { 'integer1': 111, 'integer2': 112 }
        dict_default = dict()
        converted_type, converted_value = self._custom_helper.convert(dict_value, 'dict')
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        __, default_value = self._custom_helper.convert(dict_default, 'dict')
        return_result = self._custom_helper.is_default(converted_value, converted_type, default_value)
        self.assertEquals(False, return_result)

    def testPropertiesDefault(self):
        prop_value = Properties()
        prop_value.setProperty('value1', 'foo')
        prop_value.setProperty('value2', 'bar')
        prop_value.setProperty('value3', 'equal')
        prop_default = Properties(prop_value)
        converted_type, converted_value = self._custom_helper.convert(prop_value, 'java.util.Properties')
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        __, default_value = self._custom_helper.convert(prop_default, 'java.util.Properties')
        return_result = self._custom_helper.is_default(converted_value, converted_type, default_value)
        self.assertEquals(True, return_result)

    def testPropertiesNotDefault(self):
        prop_value = Properties()
        prop_value.setProperty('value1', 'foo')
        prop_value.setProperty('value2', 'bar')
        prop_value.setProperty('value3', 'equal')
        prop_default = Properties()
        prop_default.setProperty('value1', 'foo')
        prop_default.setProperty('value4', 'bar')
        prop_default.setProperty('value3', 'equal')
        converted_type, converted_value = self._custom_helper.convert(prop_value, 'java.util.Properties')
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        __, default_value = self._custom_helper.convert(prop_default, 'java.util.Properties')
        return_result = self._custom_helper.is_default(converted_value, converted_type, default_value)
        self.assertEquals(False, return_result)

    def testMapDefault(self):
        map_value = HashMap()
        map_value.put('value1', 'foo')
        map_value.put('value2', 'bar')
        map_value.put('value3', 'equal')

        map_default = HashMap()
        map_default.putAll(map_value)

        converted_type, converted_value = self._custom_helper.convert(map_value, 'java.util.Map')
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        __, default_value = self._custom_helper.convert(map_default, 'java.util.Map')
        return_result = self._custom_helper.is_default(converted_value, converted_type, default_value)
        self.assertEquals(True, return_result)

    def testMapNotDefault(self):
        map_value = HashMap()
        map_value.put('value1', 'foo')
        map_value.put('value2', 'bar')
        map_value.put('value3', 'equal')

        map_default = HashMap()
        map_default.put('value1', 'eightball')
        map_default.put('value2', 'bar')
        map_default.put('value3', 'equal')

        converted_type, converted_value = self._custom_helper.convert(map_value, 'java.util.Map')
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        __, default_value = self._custom_helper.convert(map_default, 'java.util.Map')
        return_result = self._custom_helper.is_default(converted_value, converted_type, default_value)
        self.assertEquals(False, return_result)

    def testOfflineIntegerNotDefault(self):
        offline_default = 0
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'CacheSize', offline_default)
        self.assertEquals(None, return_result)

    def testIntegerNotDefault(self):
        port_value = 1443
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'Port', port_value)
        self.assertEquals(port_value, return_result)

    def testIntegerDefault(self):
        port_value = 0
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'Port', port_value)
        self.assertEquals(None, return_result)
        port_value = None
        return_result = self._custom_helper.get_model_attribute_value(self._helper, 'Port', port_value)
        self.assertEquals(None, return_result)

    def testBigIntegerConvert(self):
        big_value = '67999'
        converted_type, converted = self._custom_helper.convert(big_value, 'java.math.BigInteger')
        self.assertEquals(alias_constants.LONG, converted_type)
        self.assertEquals(67999L, converted)

    def testDoubleConvert(self):
        double_value = '67999'
        converted_type, converted = self._custom_helper.convert(double_value, 'java.lang.Double')
        self.assertEquals(alias_constants.DOUBLE, converted_type)
        self.assertEquals(67999, converted)

    def testFloatConvert(self):
        float_value = 4.2e-4
        converted_type, converted = self._custom_helper.convert(float_value, 'float')
        self.assertEquals(alias_constants.DOUBLE, converted_type)
        self.assertEquals(float_value, converted)

    def name_token(self, location):
        return self._alias_helper.get_name_token(location)


if __name__ == '__main__':
    unittest.main()
