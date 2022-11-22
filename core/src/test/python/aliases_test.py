"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from org.python.modules import jarray
import unittest

from java.lang import Boolean
from java.lang import String, Long
from java.util import Properties

import weblogic.version as version_helper
from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.aliases import TypeUtils
from oracle.weblogic.deploy.aliases import VersionUtils

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
import wlsdeploy.aliases.model_constants as FOLDERS
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
import wlsdeploy.logging.platform_logger as platform_logger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext


class AliasesTestCase(unittest.TestCase):
    """
       1) Unit tests must be a class that extends unittest.TestCase
       2) Class methods with names starting with 'test' will be executed by the framework (all others skipped)
    """
    wls_version = '12.2.1.3'

    arg_map = {
        CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
        CommandLineArgUtil.DOMAIN_HOME_SWITCH: ''
    }

    logger = platform_logger.PlatformLogger('wlsdeploy.unittest')
    model_context = ModelContext("test", arg_map)

    # create a set of aliases for use with WLST
    aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.OFFLINE, wls_version=wls_version)
    online_aliases = Aliases(model_context=model_context, wlst_mode=WlstModes.ONLINE, wls_version=wls_version)

    def testDomainLevelAttributeAccessibility(self):
        location = LocationContext()
        string_value = ['9002', 9002]
        model_attribute_name = 'AdministrationPort'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])

        wlst_attribute_name = 'AdministrationPort'
        wlst_attribute_value = string_value[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(model_attribute_value, None)

        location.append_location(FOLDERS.JMX)
        location.add_name_token("JMX", 'mydomain')
        string_value = ['true', 'true']
        model_attribute_name = 'EditMBeanServerEnabled'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])
        return

    def testDatasourceRootPath(self):
        expected = '/JDBCSystemResource/my-datasource'
        location = LocationContext()
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'my-datasource')
        path = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(path, expected)

        location = LocationContext()
        kwargs = {token: 'my-datasource'}
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE, **kwargs)
        path = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(path, expected)
        return

    def testDatasourceParamsPath(self):
        expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDataSourceParams/NO_NAME_0'
        location = get_jdbc_ds_params_location('my-datasource', self.aliases)

        path = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(path, expected)
        return

    def testDatasourceDriverPropertiesPath(self):
        location = get_jdbc_params_properties_location('my-datasource', self.aliases)
        expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/' \
                   'JDBCDriverParams/NO_NAME_0/Properties/NO_NAME_0/Property'
        path1 = self.aliases.get_wlst_list_path(location)
        self.assertEqual(path1, expected)

        online_location = get_jdbc_params_properties_location('my-datasource', self.online_aliases)
        expected = '/JDBCSystemResources/my-datasource/JDBCResource/my-datasource/' \
                   'JDBCDriverParams/my-datasource/Properties/my-datasource/Properties'
        path2 = self.online_aliases.get_wlst_list_path(online_location)
        self.assertEqual(path2, expected)

        # Path to access a single property by name (user in this example)
        expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/' \
                   'JDBCDriverParams/NO_NAME_0/Properties/NO_NAME_0/Property/user'
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'user')
        path1 = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(path1, expected)

        expected = '/JDBCSystemResources/my-datasource/JDBCResource/my-datasource/' \
                   'JDBCDriverParams/my-datasource/Properties/my-datasource/Properties/user'
        online_location.add_name_token(self.aliases.get_name_token(online_location), 'user')
        path2 = self.online_aliases.get_wlst_attributes_path(online_location)
        self.assertEqual(path2, expected)
        return

    def testDatasourceMbeanListPath(self):
        expected = '/JDBCSystemResource'
        location = LocationContext()
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        path = self.aliases.get_wlst_list_path(location)
        self.assertEqual(path, expected)
        return

    def testDatasourceSubfoldersPath(self):
        expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource'
        location = get_jdbc_resource_location('my-datasource', self.aliases)
        path = self.aliases.get_wlst_subfolders_path(location)
        self.assertEqual(path, expected)
        return

    def testMachineMbeanListPath(self):
        expected = '/Machine'
        location = LocationContext()
        location.append_location(FOLDERS.MACHINE)
        path = self.aliases.get_wlst_list_path(location)
        self.assertEqual(path, expected)
        return

    def testDatasourceMbeanType(self):
        expected = 'JDBCSystemResource'
        location = LocationContext()
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        mbean_type = self.aliases.get_wlst_mbean_type(location)
        self.assertEqual(mbean_type, expected)
        return

    def testDatasourceSubfolderMbeanType(self):
        expected = 'JDBCDriverParams'
        location = get_jdbc_driver_params_location('my-datasource', self.aliases)
        mbean_type = self.aliases.get_wlst_mbean_type(location)
        self.assertEqual(mbean_type, expected)
        return

    def testDatasourceSubFolderMbeanName(self):
        expected = 'NO_NAME_0'
        location = get_jdbc_ds_params_location('my-datasource', self.aliases)
        mbean_name = self.aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, expected)
        return

    def testGetModelSubFolders(self):
        expected = ['JDBCOracleParams', 'JDBCConnectionPoolParams', 'JDBCXAParams',
                    'JDBCDataSourceParams', 'JDBCDriverParams']
        location = get_jdbc_resource_location('my-datasource', self.aliases)
        names = self.aliases.get_model_subfolder_names(location)
        self.assertEqual(len(names), len(expected))
        for name in names:
            self.assertEqual(name in expected, True)
        return

    def testAppDeploymentPathTokenReplacement(self):
        expected = self.model_context.replace_token_string('@@PWD@@/target/applications/simpleear.ear')
        location = LocationContext()
        location.append_location(FOLDERS.APPLICATION)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'simpleear')

        model_attribute_name = 'SourcePath'
        model_attribute_value = '@@PWD@@/target/applications/simpleear.ear'
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, expected)

        expected = self.model_context.replace_token_string('@@WL_HOME@@/common/deployable-libraries/jsf-2.0.war')
        location = LocationContext()
        location.append_location(FOLDERS.LIBRARY)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'jsf#2.0@1.0.0.0_2-0-2')

        model_attribute_name = 'SourcePath'
        model_attribute_value = '@@WL_HOME@@/common/deployable-libraries/jsf-2.0.war'
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, expected)
        return

    def testReadOnlyAttributeAccess(self):
        location = LocationContext()
        location.append_location(FOLDERS.APPLICATION)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'simpleear')

        model_attribute_name = 'AbsoluteSourcePath'
        model_attribute_value = '@@PWD@@/target/applications/simpleear.ear'
        wlst_attribute_name, wlst_attribute_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_name, None)
        self.assertEqual(wlst_attribute_value, None)
        return

    def testWlstAttributeValueConversion(self):
        location = get_jdbc_ds_params_location('my-datasource', self.aliases)

        string_value = ['Hello', 'Hello']
        model_attribute_name = 'AlgorithmType'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])

        string_value = ['123', 123]
        model_attribute_name = 'RowPrefetchSize'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])

        string_value = ['3600', Long(3600)]
        jms_location = LocationContext()
        jms_location.append_location(FOLDERS.JMS_SYSTEM_RESOURCE)
        jms_location.add_name_token(self.aliases.get_name_token(jms_location), 'my-module')
        jms_location.append_location(FOLDERS.JMS_RESOURCE)
        add_default_token_value(jms_location, self.aliases)
        jms_location.append_location(FOLDERS.CONNECTION_FACTORY)
        jms_location.add_name_token(self.aliases.get_name_token(jms_location), 'my-connectionfactory')
        jms_location.append_location(FOLDERS.DEFAULT_DELIVERY_PARAMS)
        add_default_token_value(jms_location, self.aliases)

        model_attribute_name = 'DefaultTimeToLive'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(jms_location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])
        self.assertEqual(wlst_attribute_value.getClass().getName(), 'java.lang.Long')

        string_value = [1, 'true']
        model_attribute_name = 'RowPrefetch'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])
        return

    def testWlstAttributeListValueConversion(self):
        location = get_jdbc_ds_params_location('my-datasource', self.aliases)

        model_attribute_name = 'JNDIName'
        model_attribute_value = 'com.bea.datasource1, com.bea.datasource2'
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        offlineList = ['com.bea.datasource1', 'com.bea.datasource2']
        self.assertEqual(wlst_attribute_value, offlineList)

        onlineList = jarray.zeros(2, String)
        onlineList[0] = 'com.bea.datasource1'
        onlineList[1] = 'com.bea.datasource2'
        wlst_attribute_name, wlst_attribute_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, onlineList)

        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, onlineList)
        self.assertEqual(wlst_attribute_value, offlineList)
        return

    def testModelAttributeValueConversion(self):
        location = LocationContext()
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'my-datasource')
        location.append_location(FOLDERS.JDBC_RESOURCE)
        location.append_location(FOLDERS.JDBC_DATASOURCE_PARAMS)

        string_value = ['Hello', 'Hello']
        wlst_attribute_name = 'AlgorithmType'
        wlst_attribute_value = string_value[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(model_attribute_value, string_value[1])

        string_value = ['123', 123]
        wlst_attribute_name = 'RowPrefetchSize'
        wlst_attribute_value = string_value[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(model_attribute_value, string_value[1])

        string_value = [1, True]
        wlst_attribute_name = 'RowPrefetch'
        wlst_attribute_value = string_value[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(alias_utils.convert_boolean(model_attribute_value), string_value[1])
        return

    def testConvertToTypeJarray(self):
        location = LocationContext()
        location.append_location(FOLDERS.SERVER)
        token_name = self.aliases.get_name_token(location)
        location.add_name_token(token_name, 'AdminServer')
        location.append_location('FederationServices')

        wlst_name = 'AssertionConsumerUri'
        wlst_value = jarray.zeros(2, String)
        wlst_value[0] = 'abc'
        wlst_value[1] = 'def'
        model_name, model_value = self.aliases.get_model_attribute_name_and_value(location, wlst_name, wlst_value)
        self.assertEqual(model_name, wlst_name)
        self.assertEqual(type(model_value), list)
        self.assertEqual(model_value, ['abc', 'def'])
        return

    def testGetWlstAttributeNameAndValue(self):
        location = get_jdbc_ds_params_location('my-datasource', self.aliases)

        # get wlst attribute value should return the value even if its the default
        string_value = ['0', 0]
        model_attribute_name = 'RowPrefetchSize'
        model_attribute_value = string_value[0]
        wlst_attribute_name, wlst_attribute_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_attribute_value)
        self.assertEqual(wlst_attribute_value, string_value[1])
        return

    def testGetModelAttributeNameAndValue(self):
        location = get_jdbc_ds_params_location('my-datasource', self.aliases)

        # get model attribute value should return the value only if its NOT the default
        boolean_values = ['false', None]
        wlst_attribute_name = 'RowPrefetch'
        wlst_attribute_value = boolean_values[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(model_attribute_value, boolean_values[1])

        # get model attribute value should return the value only if its NOT the default
        string_value = [None, None]
        wlst_attribute_name = 'RowPrefetchSize'
        wlst_attribute_value = string_value[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(model_attribute_value, string_value[1])

        # get model attribute value should return the value only if its NOT the default
        location = LocationContext()
        location.append_location(FOLDERS.SERVER)
        boolean_values = [0, None]
        wlst_attribute_name = 'NetworkClassLoadingEnabled'
        wlst_attribute_value = boolean_values[0]
        model_attribute_name, model_attribute_value = \
            self.aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, wlst_attribute_value)
        self.assertEqual(model_attribute_value, boolean_values[1])
        return

    def testGetWlstAttributeName(self):
        location = LocationContext()
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'my-datasource')
        location.append_location(FOLDERS.JDBC_RESOURCE)
        location.append_location(FOLDERS.JDBC_DATASOURCE_PARAMS)

        model_attribute_name = 'RowPrefetch'
        wlst_attribute_name = self.aliases.get_wlst_attribute_name(location, model_attribute_name)
        self.assertEqual(wlst_attribute_name, 'RowPrefetch')
        return

    def testGetWlstAttributeName2(self):
        location=LocationContext().append_location(FOLDERS.JMS_SYSTEM_RESOURCE)
        location.add_name_token(self.aliases.get_name_token(location), 'TheModule')
        location.append_location(FOLDERS.JMS_RESOURCE)
        add_default_token_value(location, self.aliases)
        location.append_location(FOLDERS.DISTRIBUTED_TOPIC)
        location.add_name_token(self.aliases.get_name_token(location), 'TheTopic')

        model_attribute_name = 'SafExportPolicy'
        result = self.aliases.get_wlst_attribute_name(location, model_attribute_name)
        self.assertEqual(result, 'SafExportPolicy')

        result = self.online_aliases.get_wlst_attribute_name(location, model_attribute_name)
        self.assertEqual(result, 'SAFExportPolicy')

        return

    def testIsWlstModelAttributeName(self):
        wls_version = '10.3.6'
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '10.3.6'
        }
        online_model_context = ModelContext("test", arg_map)
        online_aliases = Aliases(online_model_context, WlstModes.ONLINE, wls_version)
        location = get_jdbc_driver_params_location('my-datasource', self.aliases)
        model_attribute_name = 'QosDegradationAllowed'
        path = self.aliases.get_model_folder_path(location)
        expected = exception_helper.get_message('WLSDPLY-08408', model_attribute_name, path, wls_version)
        result, message = online_aliases.is_valid_model_attribute_name(location, model_attribute_name)
        self.assertEqual(result, ValidationCodes.INVALID)
        self.assertEqual(message, expected)

        offline_aliases = Aliases(self.model_context, WlstModes.OFFLINE, wls_version)
        location.pop_location()
        location.append_location(FOLDERS.JDBC_ORACLE_PARAMS)
        add_default_token_value(location, self.aliases)
        model_attribute_name = 'OnsWalletPasswordEncrypted'
        path = self.aliases.get_model_folder_path(location)
        expected = exception_helper.get_message('WLSDPLY-08407', model_attribute_name, path, wls_version)
        result, message = offline_aliases.is_valid_model_attribute_name(location, model_attribute_name)
        self.assertEqual(result, ValidationCodes.VALID)
        self.assertEqual(message, expected)

        location.pop_location()
        location.append_location(FOLDERS.JDBC_CONNECTION_POOL_PARAMS)
        add_default_token_value(location, self.aliases)
        model_attribute_name = 'CountOfTestFailuresTillFlush'
        earliest_version = '12.1.2'
        path = self.aliases.get_model_folder_path(location)
        expected = exception_helper.get_message('WLSDPLY-08207', model_attribute_name, path,
                                                wls_version, earliest_version)
        result, message = online_aliases.is_valid_model_attribute_name(location, model_attribute_name)
        self.assertEqual(result, ValidationCodes.VERSION_INVALID)
        self.assertEqual(message, expected)
        return

    def testIsPSUMatch(self):
        wls_version = '12.2.1.3.0.210929'
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '12.2.1.3.0.210929'
        }

        this_model_context = ModelContext("test", arg_map)

        online_aliases = Aliases(this_model_context, WlstModes.ONLINE, wls_version)
        location = LocationContext()
        location.append_location('SecurityConfiguration')
        location.add_name_token(online_aliases.get_name_token(location), 'domain')
        location.add_name_token('domain', 'system_test')
        model_attribute_name = 'RemoteAnonymousRmiiiopEnabled'
        value, message = online_aliases.is_valid_model_attribute_name(location, model_attribute_name)

        self.assertEqual(value, 2)

        wls_version = '12.2.1.4.0'
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '12.2.1.4'
        }

        this_model_context = ModelContext("test", arg_map)

        online_aliases = Aliases(this_model_context, WlstModes.ONLINE, wls_version)
        location = LocationContext()
        location.append_location('SecurityConfiguration')
        location.add_name_token(online_aliases.get_name_token(location), 'domain')
        location.add_name_token('domain', 'system_test')
        model_attribute_name = 'RemoteAnonymousRmiiiopEnabled'
        value, message = online_aliases.is_valid_model_attribute_name(location, model_attribute_name)

        self.assertEqual(value, 1)
        return

    def testPropertyTypes(self):
        expected = Properties()
        expected.put('key1', 'val1')
        expected.put('key2', 'val2')
        expected.put('key3', 'val3')

        test_string = 'key1=val1, key2=val2, key3=val3'
        result = TypeUtils.convertToType('properties', test_string)
        self.assertEqual(expected, result)

        test_dict = {"key1": "val1", "key2": "val2", "key3": "val3"}
        result = TypeUtils.convertToType('properties', test_dict)
        self._assertMapEqual(expected, result)

    def testNewGetWlstPaths(self):
        attr_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams/NO_NAME_0'
        folder_expected = attr_expected
        list_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams'
        create_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource'

        location = get_jdbc_driver_params_location('my-datasource', self.aliases)

        result = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(result, attr_expected)

        result = self.aliases.get_wlst_subfolders_path(location)
        self.assertEqual(result, folder_expected)

        result = self.aliases.get_wlst_list_path(location)
        self.assertEqual(result, list_expected)

        result = self.aliases.get_wlst_create_path(location)
        self.assertEqual(result, create_expected)

        attr_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams' \
                        '/NO_NAME_0/Properties/NO_NAME_0/Property/user'
        folder_expected = attr_expected
        list_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams' \
                        '/NO_NAME_0/Properties/NO_NAME_0/Property'
        create_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams' \
                          '/NO_NAME_0/Properties/NO_NAME_0'

        add_jdbc_params_properties(location, self.aliases)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'user')

        result = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(result, attr_expected)

        result = self.aliases.get_wlst_subfolders_path(location)
        self.assertEqual(result, folder_expected)

        result = self.aliases.get_wlst_list_path(location)
        self.assertEqual(result, list_expected)

        result = self.aliases.get_wlst_create_path(location)
        self.assertEqual(result, create_expected)
        return

    def testVersionFilteredFolders(self):
        old_wls_version = '10.3.6'
        new_wls_version = '12.2.1.3'
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '10.3.6'
        }
        old_model_context = ModelContext("test", arg_map)
        old_aliases = Aliases(old_model_context, WlstModes.OFFLINE, old_wls_version)
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '12.2.1.3'
        }
        new_model_context = ModelContext("test", arg_map)
        new_aliases = Aliases(new_model_context, WlstModes.OFFLINE, new_wls_version)
        location = LocationContext()
        location.append_location(FOLDERS.PARTITION)
        mbean_type = old_aliases.get_wlst_mbean_type(location)
        self.assertEqual(mbean_type, None, 'expected Partition type to be null')
        mbean_type = new_aliases.get_wlst_mbean_type(location)
        self.assertNotEqual(mbean_type, None, 'expected Partition type not to be null')

        location.pop_location()
        location.append_location(FOLDERS.CLUSTER)
        location.append_location(FOLDERS.DYNAMIC_SERVERS)
        mbean_type = old_aliases.get_wlst_mbean_type(location)
        self.assertEqual(mbean_type, None, 'expected DynamicServers type to be null')
        mbean_type = new_aliases.get_wlst_mbean_type(location)
        self.assertNotEqual(mbean_type, None, 'expected DynamicServers type not to be null')
        return

    def testVersionFilteredFoldersWithFolderParams(self):
        old_wls_version = '10.3.6'
        new_wls_version = '12.2.1.3'
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '10.3.6'
        }
        old_model_context = ModelContext("test", arg_map)
        old_aliases = Aliases(old_model_context, WlstModes.OFFLINE, old_wls_version)
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '12.2.1.3'
        }
        new_model_context =  ModelContext("test", arg_map)
        new_aliases = Aliases(new_model_context, WlstModes.OFFLINE, new_wls_version)
        location = LocationContext()
        location.append_location(FOLDERS.SAF_AGENT)
        name_token = old_aliases.get_name_token(location)
        location.add_name_token(name_token, 'SafAgent')
        location.append_location(FOLDERS.SAF_MESSAGE_LOG_FILE)
        mbean_type = old_aliases.get_wlst_mbean_type(location)
        self.assertEqual(mbean_type, None, 'expected SAF Agent Message Log type to be null')
        mbean_type = new_aliases.get_wlst_mbean_type(location)
        self.assertNotEqual(mbean_type, None, 'expected SAF Agent Message Log  not to be null')

        return

    def testDomainAttributeMethods(self):
        aliases = Aliases(self.model_context, WlstModes.OFFLINE)
        location = LocationContext()
        get_required_attributes = aliases.get_wlst_get_required_attribute_names(location)
        self.assertNotEqual(get_required_attributes, None, 'expected get-required attributes to not be None')
        restart_required_attributes = aliases.get_wlst_get_required_attribute_names(location)
        self.assertNotEqual(restart_required_attributes, None, 'expected restart-required attributes to not be None')
        return

    def testMTAliasLoading(self):
        # MT code is not functional in 14.1.1 so skip this test if using 14.1.1 or higher
        version = version_helper.getReleaseBuildVersion()
        if VersionUtils.compareVersions(version, '14.1.1') >= 0:
            return

        aliases = Aliases(self.model_context, WlstModes.OFFLINE)

        attr_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams/NO_NAME_0'
        folder_expected = attr_expected
        list_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams'
        create_expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource'

        location = get_jdbc_driver_params_location('my-datasource', self.aliases)

        result = aliases.get_wlst_attributes_path(location)
        self.assertEqual(result, attr_expected)
        result = aliases.get_wlst_subfolders_path(location)
        self.assertEqual(result, folder_expected)
        result = aliases.get_wlst_list_path(location)
        self.assertEqual(result, list_expected)
        result = aliases.get_wlst_create_path(location)
        self.assertEqual(result, create_expected)

        attr_expected = '/ResourceGroupTemplate/MyResourceGroupTemplate/JDBCSystemResource/my-datasource' \
                        '/JdbcResource/my-datasource/JDBCDriverParams/NO_NAME_0'
        folder_expected = attr_expected
        list_expected = '/ResourceGroupTemplate/MyResourceGroupTemplate/JDBCSystemResource/my-datasource' \
                        '/JdbcResource/my-datasource/JDBCDriverParams'
        create_expected = '/ResourceGroupTemplate/MyResourceGroupTemplate/JDBCSystemResource/my-datasource' \
                          '/JdbcResource/my-datasource'

        location = LocationContext()
        location.append_location(FOLDERS.RESOURCE_GROUP_TEMPLATE)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'MyResourceGroupTemplate')

        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        location.add_name_token(self.aliases.get_name_token(location), 'my-datasource')
        location.append_location(FOLDERS.JDBC_RESOURCE)
        add_default_token_value(location, self.aliases)
        location.append_location(FOLDERS.JDBC_DRIVER_PARAMS)
        add_default_token_value(location, self.aliases)

        result = aliases.get_wlst_attributes_path(location)
        self.assertEqual(result, attr_expected)
        result = aliases.get_wlst_subfolders_path(location)
        self.assertEqual(result, folder_expected)
        result = aliases.get_wlst_list_path(location)
        self.assertEqual(result, list_expected)
        result = aliases.get_wlst_create_path(location)
        self.assertEqual(result, create_expected)

        attr_expected = '/ResourceGroup/MyResourceGroup/JDBCSystemResource/my-datasource/JdbcResource' \
                        '/my-datasource/JDBCDriverParams/NO_NAME_0'
        folder_expected = attr_expected
        list_expected = '/ResourceGroup/MyResourceGroup/JDBCSystemResource/my-datasource/JdbcResource' \
                        '/my-datasource/JDBCDriverParams'
        create_expected = '/ResourceGroup/MyResourceGroup/JDBCSystemResource/my-datasource/JdbcResource/my-datasource'

        location = LocationContext()
        location.append_location(FOLDERS.RESOURCE_GROUP)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'MyResourceGroup')
        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        location.add_name_token(self.aliases.get_name_token(location), 'my-datasource')
        location.append_location(FOLDERS.JDBC_RESOURCE)
        add_default_token_value(location, self.aliases)
        location.append_location(FOLDERS.JDBC_DRIVER_PARAMS)
        add_default_token_value(location, self.aliases)

        result = aliases.get_wlst_attributes_path(location)
        self.assertEqual(result, attr_expected)
        result = aliases.get_wlst_subfolders_path(location)
        self.assertEqual(result, folder_expected)
        result = aliases.get_wlst_list_path(location)
        self.assertEqual(result, list_expected)
        result = aliases.get_wlst_create_path(location)
        self.assertEqual(result, create_expected)

        attr_expected = '/Partition/MyPartition/ResourceGroup/MyResourceGroup/JDBCSystemResource' \
                        '/my-datasource/JdbcResource/my-datasource/JDBCDriverParams/NO_NAME_0'
        folder_expected = attr_expected
        list_expected = '/Partition/MyPartition/ResourceGroup/MyResourceGroup/JDBCSystemResource' \
                        '/my-datasource/JdbcResource/my-datasource/JDBCDriverParams'
        create_expected = '/Partition/MyPartition/ResourceGroup/MyResourceGroup/JDBCSystemResource' \
                          '/my-datasource/JdbcResource/my-datasource'

        location = LocationContext()
        location.append_location(FOLDERS.PARTITION)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'MyPartition')

        location.append_location(FOLDERS.RESOURCE_GROUP)
        token = self.aliases.get_name_token(location)
        if token:
            location.add_name_token(token, 'MyResourceGroup')

        location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
        location.add_name_token(self.aliases.get_name_token(location), 'my-datasource')
        location.append_location(FOLDERS.JDBC_RESOURCE)
        add_default_token_value(location, self.aliases)
        location.append_location(FOLDERS.JDBC_DRIVER_PARAMS)
        add_default_token_value(location, self.aliases)

        result = aliases.get_wlst_attributes_path(location)
        self.assertEqual(result, attr_expected)
        result = aliases.get_wlst_subfolders_path(location)
        self.assertEqual(result, folder_expected)
        result = aliases.get_wlst_list_path(location)
        self.assertEqual(result, list_expected)
        result = aliases.get_wlst_create_path(location)
        self.assertEqual(result, create_expected)
        return

    def testChildNodeTypes(self):
        location = LocationContext()
        location.append_location(FOLDERS.SELF_TUNING)

        result = self.aliases.requires_unpredictable_single_name_handling(location)
        self.assertEqual(result, True)
        result = self.aliases.supports_multiple_mbean_instances(location)
        self.assertEqual(result, False)

        name_token = self.aliases.get_name_token(location)
        self.assertEqual(name_token, 'SELFTUNING')
        location.add_name_token("DOMAIN", 'mydomain')
        mbean_name = self.aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, 'NO_NAME_0')
        mbean_name = self.online_aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, 'mydomain')

        location.append_location(FOLDERS.WORK_MANAGER)
        result = self.aliases.requires_unpredictable_single_name_handling(location)
        self.assertEqual(result, False)
        result = self.aliases.supports_multiple_mbean_instances(location)
        self.assertEqual(result, True)

        name_token = self.aliases.get_name_token(location)
        self.assertEqual(name_token, 'WORKMANAGER')
        location.add_name_token(name_token, 'MyWorkManager')
        mbean_name = self.aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, 'MyWorkManager')
        mbean_name = self.online_aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, 'MyWorkManager')

        location.append_location('WorkManagerShutdownTrigger')
        location.add_name_token(self.aliases.get_name_token(location), 'MyWorkManager')
        result = self.aliases.supports_multiple_mbean_instances(location)
        self.assertEqual(result, False)

        name_token = self.aliases.get_name_token(location)
        self.assertEqual(name_token, 'WORKMANAGERSHUTDOWNTRIGGER')
        mbean_name = self.aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, 'NO_NAME_0')
        mbean_name = self.online_aliases.get_wlst_mbean_name(location)
        self.assertEqual(mbean_name, 'MyWorkManager')

        location = LocationContext().append_location(FOLDERS.SECURITY, FOLDERS.GROUP, DOMAIN='mydomain')
        result = self.aliases.supports_multiple_mbean_instances(location)
        self.assertEqual(result, True)
        return

    def testFlattenedFolders(self):
        location = get_jdbc_params_properties_location('my-datasource', self.aliases)
        flattened_info = self.aliases.get_wlst_flattened_folder_info(location)
        online_flattened_info = self.online_aliases.get_wlst_flattened_folder_info(location)
        self.assertNotEqual(flattened_info, None)
        name = flattened_info.get_mbean_name()
        online_name = online_flattened_info.get_mbean_name()
        type = flattened_info.get_mbean_type()
        self.assertEqual(name, 'NO_NAME_0')
        self.assertEqual(online_name, 'my-datasource')
        self.assertEqual(type, 'Properties')

        expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams/NO_NAME_0/Properties'
        result = self.aliases.get_wlst_flattened_folder_list_path(location)
        self.assertEqual(result, expected)

        expected = '/JDBCSystemResource/my-datasource/JdbcResource/my-datasource/JDBCDriverParams/NO_NAME_0'
        result = self.aliases.get_wlst_flattened_folder_create_path(location)
        self.assertEqual(result, expected)
        return

    def testModelFolderPath(self):
        location = get_jdbc_params_properties_location('my-datasource', self.aliases)

        expected = 'resources:/JDBCSystemResource/my-datasource/JdbcResource/JDBCDriverParams/Properties'
        path = self.aliases.get_model_folder_path(location)
        self.assertEqual(path, expected)

        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'user')

        expected = 'resources:/JDBCSystemResource/my-datasource/JdbcResource/JDBCDriverParams/Properties/user'
        path = self.aliases.get_model_folder_path(location)
        self.assertEqual(path, expected)

        expected = 'topology:/SecurityConfiguration/Realm/myrealm/AuthenticationProvider/' \
                   'MyLDAPAuthentication/LDAPAuthenticator'

        # Test artificial folder for security providers
        location = LocationContext().append_location(FOLDERS.SECURITY_CONFIGURATION)
        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'mydomain')

        location.append_location(FOLDERS.REALM)
        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'myrealm')

        location.append_location(FOLDERS.AUTHENTICATION_PROVIDER)
        token_name = self.aliases.get_name_token(location)
        if token_name is not None:
            location.add_name_token(token_name, 'MyLDAPAuthentication')

        location.append_location(FOLDERS.LDAP_AUTHENTICATOR)
        result = self.aliases.get_model_folder_path(location)
        self.assertEqual(result, expected)
        return

    def testIsValidModelFolderName(self):
        location = LocationContext()
        result, message = self.aliases.is_valid_model_folder_name(location, 'ServerTemplate')
        self.assertEqual(result, ValidationCodes.VALID)
        arg_map = {
            CommandLineArgUtil.ORACLE_HOME_SWITCH: '/oracleHome',
            CommandLineArgUtil.DOMAIN_HOME_SWITCH: '',
            CommandLineArgUtil.TARGET_VERSION_SWITCH: '12.1.1'
        }
        this_model_context = ModelContext("test", arg_map)
        aliases = Aliases(this_model_context, wls_version='12.1.1')
        result, message = aliases.is_valid_model_folder_name(location, 'ServerTemplate')
        self.assertEqual(result, ValidationCodes.VERSION_INVALID)

        result, message = self.aliases.is_valid_model_folder_name(location, 'ServerTemplates')
        self.assertEqual(result, ValidationCodes.INVALID)

        top_level_topology_folders = self.aliases.get_model_topology_top_level_folder_names()

        for folder in top_level_topology_folders:
            result, message = self.aliases.is_valid_model_folder_name(location, folder)
            self.assertEqual(result, ValidationCodes.VALID)

        return

    def testBooleanDefaultValues(self):
        location = LocationContext().append_location(FOLDERS.RESTFUL_MANAGEMENT_SERVICES, DOMAIN='mydomain')
        name, value = self.aliases.get_model_attribute_name_and_value(location, 'JavaServiceResourcesEnabled', 'false')
        self.assertEqual(name, 'JavaServiceResourcesEnabled')
        self.assertEqual(value, None)
        return

    def testGetWlstAttributeJavaBoolean(self):
        location = LocationContext().append_location(FOLDERS.SECURITY_CONFIGURATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'my-domain')
        location.append_location(FOLDERS.REALM, REALM="myrealm").\
            append_location(FOLDERS.AUTHENTICATION_PROVIDER, PROVIDER='myprovider').\
            append_location(FOLDERS.ACTIVE_DIRECTORY_AUTHENTICATOR)
        name, value = self.aliases.get_wlst_attribute_name_and_value(location, 'UseRetrievedUserNameAsPrincipal',
                                                                     'true')
        self.assertEqual(name, 'UseRetrievedUserNameAsPrincipal')
        self.assertEqual(value, Boolean('true'))
        return

    def testGetWlstAttributeJavaBooleanNewIssue157(self):
        location = LocationContext().append_location(FOLDERS.SECURITY_CONFIGURATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'my-domain')
        location.append_location(FOLDERS.REALM, REALM="myrealm"). \
            append_location(FOLDERS.AUTHENTICATION_PROVIDER, PROVIDER='myprovider'). \
            append_location(FOLDERS.ACTIVE_DIRECTORY_AUTHENTICATOR)
        name, value = self.aliases.get_wlst_attribute_name_and_value(location, 'UseTokenGroupsForGroupMembershipLookup',
                                                                     'true')
        self.assertEqual(name, 'UseTokenGroupsForGroupMembershipLookup')
        self.assertEqual(value, Boolean('true'))
        return

    def testSecurityProviderTypeHandling(self):
        location = LocationContext().append_location(FOLDERS.SECURITY_CONFIGURATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'my-domain')

        location.append_location(FOLDERS.REALM)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'myrealm')

        location.append_location(FOLDERS.AUTHENTICATION_PROVIDER)
        result = self.aliases.requires_artificial_type_subfolder_handling(location)
        self.assertEqual(result, True)

        location.append_location(FOLDERS.DEFAULT_AUTHENTICATOR)
        try:
            self.aliases.requires_artificial_type_subfolder_handling(location)
            self.assertEqual(True, False, 'Excepted AliasException to be thrown')
        except AliasException, ae:
            pass
        return

    def testSecurityProviderGetAttributes(self):
        location = LocationContext().append_location(FOLDERS.SECURITY_CONFIGURATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'my-domain')

        location.append_location(FOLDERS.REALM)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'myrealm')

        location.append_location(FOLDERS.AUTHENTICATION_PROVIDER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'MyDefaultAuthenticator')
        # result = self.aliases.get_wlst_attributes_path(location)
        # self.assertEqual(result,
        #                  '/SecurityConfiguration/my-domain/Realm/myrealm/AuthenticationProvider/MyDefaultAuthenticator')
        model_subfolder_name = self.aliases.get_model_subfolder_name(location,
                                                 'weblogic.security.providers.authentication.DefaultAuthenticatorMBean')
        self.assertEqual(model_subfolder_name, 'DefaultAuthenticator')
        location.append_location(model_subfolder_name)
        result = self.aliases.get_wlst_attributes_path(location)
        self.assertEqual(result,
                         '/SecurityConfiguration/my-domain/Realm/myrealm/AuthenticationProvider/MyDefaultAuthenticator')
        model_name, model_value = self.aliases.get_model_attribute_name_and_value(location, 'CompatibilityObjectName',
                                                                                  'MyObjectName')
        self.assertEqual(model_name, 'CompatibilityObjectName')
        self.assertEquals(model_value, 'MyObjectName')
        return

    def testJrfSecurityProviderDiscovery(self):
        location = LocationContext().append_location(FOLDERS.SECURITY_CONFIGURATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'my-domain')

        location.append_location(FOLDERS.REALM)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'myrealm')

        location.append_location(FOLDERS.AUTHENTICATION_PROVIDER)

        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'myprovider')
        result = self.aliases.get_model_subfolder_name(location,
                                                       'weblogic.security.providers.saml.SAMLAuthenticatorMBean')
        self.assertEqual(result, 'SAMLAuthenticator')
        return

    def testUsesPathTokenAttributeNames(self):
        location = LocationContext().append_location(FOLDERS.APPLICATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'my-app')

        expected = ['PlanPath', 'SourcePath', 'AltDescriptorPath', 'AltWLSDescriptorPath',
                    'InstallDir', 'PlanDir', 'AltDescriptorDir']
        result = self.aliases.get_model_uses_path_tokens_attribute_names(location)
        self.assertNotEqual(result, None, 'expected uses_path_tokens attribute names list to not be None')
        self.assertEqual(len(result), len(expected))
        for name in result:
            if name not in expected:
                self.assertEqual(True, False, "attribute name %s not in the list of expected names" % name)
        return

    def testDefaultValueStringCompares(self):
        location=LocationContext().append_location(FOLDERS.SERVER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'AdminServer')

        model_name, model_value = self.aliases.get_model_attribute_name_and_value(location, 'Notes', '')
        self.assertEqual(model_name, 'Notes')
        self.assertEqual(model_value, None)

        model_name, model_value = self.aliases.get_model_attribute_name_and_value(location, 'Notes', None)
        self.assertEqual(model_name, 'Notes')
        self.assertEqual(model_value, None)
        return

    def _assertMapEqual(self, expected, testObject):
        self.assertEqual(expected.size(), testObject.size())
        for key in expected.keys():
            self.assertEqual(expected.get(key), testObject.get(str(key).strip()))
        return

    def testIssue36Fix(self):
        base_location = LocationContext().append_location(FOLDERS.RESOURCE_MANAGER)
        token = self.aliases.get_name_token(base_location)
        base_location.add_name_token(token, 'ResourceManager-0')

        location = LocationContext(base_location).append_location(FOLDERS.CPU_UTILIZATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'CpuUtilization-0')
        location.append_location(FOLDERS.TRIGGER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'Trigger-0')

        expected = [FOLDERS.TRIGGER, '%ss' % FOLDERS.TRIGGER]

        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected[0])

        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected[1])

        location = LocationContext(base_location).append_location(FOLDERS.FILE_OPEN)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'FileOpen-0')
        location.append_location(FOLDERS.TRIGGER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'Trigger-0')

        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected[0])

        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected[1])

        location = LocationContext(base_location).append_location(FOLDERS.HEAP_RETAINED)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'HeapRetained-0')
        location.append_location(FOLDERS.TRIGGER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'Trigger-0')

        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected[0])

        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected[1])

        return

    def testIssue37Fix(self):
        location = LocationContext().append_location(FOLDERS.WLDF_SYSTEM_RESOURCE)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'WLDFSystemResource-0')
        location.append_location(FOLDERS.WLDF_RESOURCE)
        location.append_location(FOLDERS.WATCH_NOTIFICATION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'WatchNotification-0')
        location.append_location(FOLDERS.HEAP_DUMP_ACTION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'HeapDumpAction-0')

        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        expected = FOLDERS.HEAP_DUMP_ACTION
        self.assertEqual(wlst_mbean_type, expected)

        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        expected = '%ss' % FOLDERS.HEAP_DUMP_ACTION
        self.assertEqual(wlst_mbean_type, expected)

        return

    def testIssue38Fix(self):
        location = LocationContext().append_location(FOLDERS.PARTITION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'Partition-0')

        # Check offline value of wlst_mbean_type of FOLDERS.PARTITION
        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        expected = FOLDERS.PARTITION
        self.assertEqual(wlst_mbean_type, expected)

        # Check online value of wlst_mbean_type of FOLDERS.PARTITION.
        # There should be an 's' on the end of FOLDERS.PARTITION
        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        expected = '%ss' % FOLDERS.PARTITION
        self.assertEqual(wlst_mbean_type, expected)

        # Add FOLDERS.PARTITION_WORK_MANAGER to the location
        location.append_location(FOLDERS.PARTITION_WORK_MANAGER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'PartitionWorkManager-0')

        # Check offline value of wlst_mbean_type after adding
        # FOLDERS.PARTITION_WORK_MANAGER to the location. There
        # should not be an 's' on the end of FOLDERS.PARTITION_WORK_MANAGER
        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        expected = FOLDERS.PARTITION_WORK_MANAGER
        self.assertEqual(wlst_mbean_type, expected)

        # Check online value of wlst_mbean_type after adding
        # FOLDERS.PARTITION_WORK_MANAGER to the location. It
        # should be the same value as offline; no 's' on the
        # end of FOLDERS.PARTITION_WORK_MANAGER
        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected)

        # Check offline value of wlst_list_path after adding
        # FOLDERS.PARTITION_WORK_MANAGER to the location. There
        # should not be an 's' on the end of FOLDERS.PARTITION or
        # FOLDERS.PARTITION_WORK_MANAGER
        expected = [FOLDERS.PARTITION, 'Partition-0', FOLDERS.PARTITION_WORK_MANAGER]
        wlst_list_path = self.aliases.get_wlst_list_path(location)
        self.assertEqual(wlst_list_path, '/%s' % '/'.join(expected))

        # Check online value of wlst_list_path after adding
        # FOLDERS.PARTITION_WORK_MANAGER to the location. There
        # should be an 's' on the end of FOLDERS.PARTITION, but
        # not on the end of FOLDERS.PARTITION_WORK_MANAGER
        expected = ['%ss' % FOLDERS.PARTITION, 'Partition-0', FOLDERS.PARTITION_WORK_MANAGER]
        wlst_list_path = self.online_aliases.get_wlst_list_path(location)
        self.assertEqual(wlst_list_path, '/%s' % '/'.join(expected))

        # Check offline value of wlst_subfolders_path after adding
        # FOLDERS.PARTITION_WORK_MANAGER to the location. There
        # should be an 's' on the end of FOLDERS.PARTITION, but
        # not on the end of FOLDERS.PARTITION_WORK_MANAGER
        expected = [FOLDERS.PARTITION, 'Partition-0', FOLDERS.PARTITION_WORK_MANAGER, 'PartitionWorkManager-0']
        wlst_subfolders_path = self.aliases.get_wlst_subfolders_path(location)
        self.assertEqual(wlst_subfolders_path, '/%s' % '/'.join(expected))

        # Check online value of wlst_subfolders_path after adding
        # FOLDERS.PARTITION_WORK_MANAGER to the location. There
        # should be an 's' on the end of FOLDERS.PARTITION, but
        # not on the end of FOLDERS.PARTITION_WORK_MANAGER
        expected = ['%ss' % FOLDERS.PARTITION, 'Partition-0', FOLDERS.PARTITION_WORK_MANAGER, 'PartitionWorkManager-0']
        wlst_subfolders_path = self.online_aliases.get_wlst_subfolders_path(location)
        self.assertEqual(wlst_subfolders_path, '/%s' % '/'.join(expected))

        return

    def testIssue39Fix(self):
        location = LocationContext().append_location(FOLDERS.PARTITION)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'Partition-0')

        # Check offline value of wlst_mbean_type of FOLDERS.PARTITION
        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        expected = FOLDERS.PARTITION
        self.assertEqual(wlst_mbean_type, expected)

        # Check online value of wlst_mbean_type of FOLDERS.PARTITION.
        # There should be an 's' on the end of FOLDERS.PARTITION
        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        expected = '%ss' % FOLDERS.PARTITION
        self.assertEqual(wlst_mbean_type, expected)

        # Add FOLDERS.RESOURCE_MANAGER to the location
        location.append_location(FOLDERS.RESOURCE_MANAGER)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'ResourceManager-0')

        # Check offline value of wlst_mbean_type after adding
        # FOLDERS.RESOURCE_MANAGER to the location. There
        # should not be an 's' on the end of FOLDERS.RESOURCE_MANAGER
        wlst_mbean_type = self.aliases.get_wlst_mbean_type(location)
        expected = FOLDERS.RESOURCE_MANAGER
        self.assertEqual(wlst_mbean_type, expected)

        # Check online value of wlst_mbean_type after adding
        # FOLDERS.RESOURCE_MANAGER to the location. It
        # should be the same value as offline; no 's' on the
        # end of FOLDERS.RESOURCE_MANAGER
        wlst_mbean_type = self.online_aliases.get_wlst_mbean_type(location)
        self.assertEqual(wlst_mbean_type, expected)

        # Check offline value of wlst_list_path after adding
        # FOLDERS.RESOURCE_MANAGER to the location. There
        # should not be an 's' on the end of FOLDERS.PARTITION or
        # FOLDERS.RESOURCE_MANAGER
        expected = [FOLDERS.PARTITION, 'Partition-0', FOLDERS.RESOURCE_MANAGER]
        wlst_list_path = self.aliases.get_wlst_list_path(location)
        self.assertEqual(wlst_list_path, '/%s' % '/'.join(expected))

        # Check online value of wlst_list_path after adding
        # FOLDERS.RESOURCE_MANAGER to the location. There
        # should be an 's' on the end of FOLDERS.PARTITION, but
        # not on the end of FOLDERS.RESOURCE_MANAGER
        expected = ['%ss' % FOLDERS.PARTITION, 'Partition-0', FOLDERS.RESOURCE_MANAGER]
        wlst_list_path = self.online_aliases.get_wlst_list_path(location)
        self.assertEqual(wlst_list_path, '/%s' % '/'.join(expected))

        # Check offline value of wlst_subfolders_path after adding
        # FOLDERS.RESOURCE_MANAGER to the location. There
        # should be an 's' on the end of FOLDERS.PARTITION, but
        # not on the end of FOLDERS.RESOURCE_MANAGER
        expected = [FOLDERS.PARTITION, 'Partition-0', FOLDERS.RESOURCE_MANAGER, 'ResourceManager-0']
        wlst_subfolders_path = self.aliases.get_wlst_subfolders_path(location)
        self.assertEqual(wlst_subfolders_path, '/%s' % '/'.join(expected))

        # Check online value of wlst_subfolders_path after adding
        # FOLDERS.RESOURCE_MANAGER to the location. There
        # should be an 's' on the end of FOLDERS.PARTITION, but
        # not on the end of FOLDERS.RESOURCE_MANAGER
        expected = ['%ss' % FOLDERS.PARTITION, 'Partition-0', FOLDERS.RESOURCE_MANAGER, 'ResourceManager-0']
        wlst_subfolders_path = self.online_aliases.get_wlst_subfolders_path(location)
        self.assertEqual(wlst_subfolders_path, '/%s' % '/'.join(expected))

        return

    def testIssue50Fix(self):
        location = LocationContext().append_location(FOLDERS.SERVER_TEMPLATE)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'ServerTemplate-0')
        location.append_location(FOLDERS.WEB_SERVICE)
        location.append_location(FOLDERS.WEB_SERVICE_BUFFERING)

        wlst_attribute_name = self.aliases.get_wlst_attribute_name(location, 'RetryCount')
        expected = 'RetryCount'
        self.assertEqual(wlst_attribute_name, expected)

        wlst_attribute_name = self.online_aliases.get_wlst_attribute_name(location, 'RetryCount')
        self.assertEqual(wlst_attribute_name, expected)

        return

    def testIssue57Fix(self):
        location = LocationContext().append_location(FOLDERS.LOG)
        token = self.aliases.get_name_token(location)
        location.add_name_token(token, 'DemoDomain')

        expected = 'true'
        default_value = self.online_aliases.get_model_attribute_default_value(location, 'RotateLogOnStartup')
        self.assertEqual(default_value, expected)

        return

    def testIssue91Fix(self):
        location = LocationContext().append_location(FOLDERS.NM_PROPERTIES)

        expected = 'startWebLogic.sh'
        default_value = self.aliases.get_model_attribute_default_value(location, 'weblogic.StartScriptName')
        self.assertEqual(default_value, expected)

        expected = '/'
        wlst_list_path = self.aliases.get_wlst_list_path(location)
        self.assertEqual(wlst_list_path, expected)

        # NMProperties is an offline only folder and the get_model_attribute_default_value will throw and exception
        model_attribute_name = 'weblogic.StartScriptName'

        self.assertRaises(AliasException, getattr(self.online_aliases, 'get_model_attribute_default_value'),
                          location, model_attribute_name)

        # this method will not return an exception but should return a None
        default_name, default_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, 'script')
        expected = None
        self.assertEqual(default_value, expected)

        return

    def testGetModelAttributeName(self):
        location=LocationContext().append_location(FOLDERS.JMS_SYSTEM_RESOURCE)
        location.add_name_token(self.aliases.get_name_token(location), 'TheModule')
        location.append_location(FOLDERS.JMS_RESOURCE)
        add_default_token_value(location, self.aliases)
        location.append_location(FOLDERS.DISTRIBUTED_TOPIC)
        location.add_name_token(self.aliases.get_name_token(location), 'TheTopic')

        # model name should be the same, whether online or offline
        expected_model_name = 'SafExportPolicy'

        model_name = self.aliases.get_model_attribute_name(location, 'SafExportPolicy')
        self.assertEqual(model_name, expected_model_name)

        model_name = self.online_aliases.get_model_attribute_name(location, 'SAFExportPolicy')
        self.assertEqual(model_name, expected_model_name)

        return

    def testJarrayWithPreferredAndStringArray(self):
        location = LocationContext().append_location(FOLDERS.SERVER)
        location.add_name_token(self.aliases.get_name_token(location), 'AdminServer')
        empty_array = jarray.array([], String)
        attribute = 'JNDITransportableObjectFactoryList'
        expected = None

        actual_attr, actual_value = self.aliases.get_model_attribute_name_and_value(location, attribute, empty_array)
        self.assertEqual(expected, actual_value)

        actual_attr, actual_value = self.aliases.get_wlst_attribute_name_and_value(location, actual_attr, actual_value)
        self.assertEqual(expected, actual_value)

        attribute_array = jarray.array(['factory1', 'factory2'], String)
        model_expected = 'factory1,factory2'
        wlst_expected = attribute_array

        actual_attr, actual_value = self.aliases.get_model_attribute_name_and_value(location, attribute,
                                                                                    attribute_array)
        self.assertEqual(model_expected, actual_value)

        actual_attr, actual_value = self.aliases.get_wlst_attribute_name_and_value(location, actual_attr, actual_value)
        self.assertEqual(wlst_expected, actual_value)

    def testListGetToList(self):
        location = LocationContext().append_location(FOLDERS.SERVER)
        location.add_name_token(self.aliases.get_name_token(location), 'AdminServer')
        location = location.append_location(FOLDERS.SSL)
        location.add_name_token(self.aliases.get_name_token(location), 'AdminServer')
        wlst_list = "TLS;WITH_AES_256_CBC"
        expected_wlst_list = ['TLS', 'WITH_AES_256_CBC']
        expected_wlst_set_list = ['TLS', 'WITH_AES_256_CBC']
        attribute = 'Ciphersuite'

        actual_attr, actual_value = self.aliases.get_model_attribute_name_and_value(location, attribute, wlst_list)
        self.assertEqual(expected_wlst_list, actual_value)

        actual_attr, actual_value = self.aliases.get_wlst_attribute_name_and_value(location, actual_attr, actual_value)
        self.assertEqual(expected_wlst_set_list, actual_value)

    def testGetJTA(self):
        location = LocationContext()
        location.append_location(FOLDERS.JTA)
        location.add_name_token('DOMAIN', 'mydomain')
        offline_path = self.aliases.get_wlst_mbean_name(location)
        self.assertEqual('NO_NAME_0', offline_path)
        online_path = self.online_aliases.get_wlst_mbean_name(location)
        self.assertEqual('mydomain', online_path)

    def testJTAMigratableConstrainedCandidateServer(self):
        model_value = [ 'MS-1', 'MS-2']
        wlst_value_expected = 'MS-1,MS-2'
        location = LocationContext()
        location.append_location(FOLDERS.SERVER)
        location.add_name_token(self.aliases.get_name_token(location), 'MS-1')
        location.append_location(FOLDERS.JTA_MIGRATABLE_TARGET)
        location.add_name_token(self.aliases.get_name_token(location), 'NO_NAME_0')
        wlst_attribute, wlst_value = \
            self.aliases.get_wlst_attribute_name_and_value(location, FOLDERS.CONSTRAINED_CANDIDATE_SERVER, model_value)
        self.assertEquals(wlst_value_expected, wlst_value)

    def testReadOnlyDiscoverAttribute(self):
        location = LocationContext()
        location.add_name_token(self.online_aliases.get_name_token(location), 'my-domain')
        model_attribute, model_value = \
            self.online_aliases.get_model_attribute_name_and_value(location, FOLDERS.DOMAIN_VERSION, '12.2.1.3.0')
        self.assertEquals('12.2.1.3.0', model_value)
        wlst_attribute, wlst_value = \
            self.online_aliases.get_wlst_attribute_name_and_value(location, FOLDERS.DOMAIN_VERSION, '12.2.1.3.0')
        self.assertEquals(None, wlst_value)

    def testFolderOrder(self):
        expected_list = ['DefaultAuthenticator', 'DefaultIdentityAsserter']
        location = LocationContext()
        location.append_location(FOLDERS.SECURITY_CONFIGURATION)
        location.add_name_token(self.aliases.get_name_token(location), 'mydomain')
        location.append_location(FOLDERS.REALM)
        location.add_name_token(self.aliases.get_name_token(location), 'myrealm')
        location.append_location(FOLDERS.AUTHENTICATION_PROVIDER)
        actual_list = self.aliases.get_subfolders_in_order(location)
        self.assertEquals(len(expected_list), len(actual_list))
        self.assertEquals(expected_list[0], actual_list[0])
        self.assertEquals(expected_list[1], actual_list[1])


def get_jdbc_ds_params_location(name, aliases):
    location = get_jdbc_resource_location(name, aliases)
    location.append_location(FOLDERS.JDBC_DATASOURCE_PARAMS)
    add_default_token_value(location, aliases)
    return location


def get_jdbc_params_properties_location(name, aliases):
    location = get_jdbc_driver_params_location(name, aliases)
    add_jdbc_params_properties(location, aliases)
    return location


def add_jdbc_params_properties(location, aliases):
    location.append_location(FOLDERS.JDBC_DRIVER_PARAMS_PROPERTIES)
    # don't add the token for property name

    # token for flattened Properties folder
    flat_info = aliases.get_wlst_flattened_folder_info(location)
    location.add_name_token(flat_info.get_path_token(), flat_info.get_mbean_name())


def get_jdbc_driver_params_location(name, aliases):
    location = get_jdbc_resource_location(name, aliases)
    location.append_location(FOLDERS.JDBC_DRIVER_PARAMS)
    add_default_token_value(location, aliases)
    return location


def get_jdbc_resource_location(name, aliases):
    location = LocationContext()
    location.append_location(FOLDERS.JDBC_SYSTEM_RESOURCE)
    location.add_name_token(aliases.get_name_token(location), name)
    location.append_location(FOLDERS.JDBC_RESOURCE)
    add_default_token_value(location, aliases)
    return location


def add_default_token_value(location, aliases):
    token = aliases.get_name_token(location)
    name = aliases.get_wlst_mbean_name(location)
    location.add_name_token(token, name)


if __name__ == '__main__':
    unittest.main()
