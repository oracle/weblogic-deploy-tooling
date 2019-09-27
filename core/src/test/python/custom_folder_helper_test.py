"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import unittest

from org.python.modules import jarray

from java.lang import Boolean
from java.util import HashMap
from java.lang import String
from java.io import ByteArrayOutputStream
from java.io import DataOutputStream
from java.io import IOException
from java.util import Properties

from oracle.weblogic.deploy.util import PyOrderedDict

import wlsdeploy.aliases.alias_constants as alias_constants
import wlsdeploy.logging.platform_logger as platform_logger
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.discover.custom_folder_helper import CustomFolderHelper
from wlsdeploy.util.cla_utils import CommandLineArgUtil as CLA
from wlsdeploy.util.model_context import ModelContext


class CustomFolderHelperTestCase(unittest.TestCase):
    """

    Test the Custom MBean attribute conversion routines which convert from WLST value to Model value.
    Test comparison of converted model value to default value.
    """

    _custom_helper = None
    _logger = platform_logger.PlatformLogger('wlsdeploy.unittest')
    _aliases = None
    _model_context = None

    _wls_version = '12.2.1.3'

    def setUp(self):
        arg_map = dict()
        arg_map[CLA.ORACLE_HOME_SWITCH] = '/my/path/to/oracle'
        arg_map[CLA.TARGET_MODE_SWITCH] = 'offline'

        self._model_context = ModelContext("test", arg_map)
        self._aliases = Aliases(model_context=self._model_context, wlst_mode=WlstModes.OFFLINE,
                                wls_version=self._wls_version)
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
        converted_type, converted_value = self._custom_helper.convert(byte_array, '[B')
        self.common_test_converted(alias_constants.PASSWORD_TOKEN, alias_constants.PASSWORD,
                                   converted_value, converted_type)

    def testListEqualsDefault(self):
        list_value = ['foo', 'bar']
        list_default = list(list_value)
        converted_type, converted_value = self._custom_helper.convert(list_value, 'list')
        self.common_test_converted(list_value, alias_constants.LIST, converted_value, converted_type)
        self.common_test_default(list_default, 'list', converted_value, converted_type, True)

    def testListNotDefaultLengthDiff(self):
        list_value = ['foo', 'bar']
        list_default = ['bar']
        converted_type, converted_value = self._custom_helper.convert(list_value, 'list')
        self.common_test_converted(list_value, alias_constants.LIST, converted_value, converted_type)
        self.common_test_default(list_default, 'list', converted_value, converted_type, False)

    def testListNotDefaultElementsDiff(self):
        list_value = ['abc', 'xyz']
        list_default = ['bar', 'foo']
        converted_type, converted_value = self._custom_helper.convert(list_value, 'list')
        self.common_test_converted(list_value, alias_constants.LIST, converted_value, converted_type)
        self.common_test_default(list_default, 'list', converted_value, converted_type, False)

    def testJarrayEqualsDefault(self):
        jarray_value = jarray.array(['Idcs_user_assertion', 'idcs_user_assertion'], String)
        expected_value = ['Idcs_user_assertion', 'idcs_user_assertion']
        jarray_default = ['idcs_user_assertion', 'Idcs_user_assertion']
        converted_type, converted_value = self._custom_helper.convert(jarray_value, '[L')
        self.common_test_converted(expected_value, alias_constants.JARRAY, converted_value, converted_type)
        self.common_test_default(jarray_default, str(type(jarray_default)), converted_value, converted_type, True)

    def testJarryDoesNotEqualDefaultDiffLength(self):
        jarray_value = jarray.array(['idcs_user_assertion'], String)
        expected_value = ['idcs_user_assertion']
        jarray_default = ['idcs_user_assertion', 'Idcs_user_assertion']
        converted_type, converted_value = self._custom_helper.convert(jarray_value, 'PyArray')
        self.common_test_converted(expected_value, alias_constants.JARRAY, converted_value, converted_type)
        self.common_test_default(jarray_default, 'PyArray', converted_value, converted_type, False)

    def testJarryDoesNotEqualDefaultDiffValue(self):
        jarray_value = jarray.array(['nonmatch', 'idcs_user_assertion'], String)
        expected_value = ['nomatch', 'idcs_user_assertion']
        jarray_default = ['idcs_user_assertion', 'Idcs_user_assertion']
        converted_type, converted_value = self._custom_helper.convert(jarray_value, 'PyArray')
        self.common_test_converted(expected_value, alias_constants.JARRAY, converted_value, converted_type)
        self.common_test_default(jarray_default, str(type(jarray_default)), converted_value, converted_type, False)

    def testMatchesEmptyJarray(self):
        jarray_value = None
        expected_value = []
        jarray_default = jarray.array([], String)
        converted_type, converted_value = self._custom_helper.convert(jarray_value, '[L')
        self.common_test_converted(expected_value, alias_constants.JARRAY, converted_value, converted_type)
        self.common_test_default(jarray_default, 'PyArray', converted_value, converted_type, True)

    def testBooleanDefault(self):
        bool_value = Boolean(False)
        expected_value = 'false'
        expected_default = expected_value
        converted_type, converted_value = self._custom_helper.convert(bool_value, 'java.lang.Boolean')
        self.common_test_converted(expected_value, alias_constants.BOOLEAN, converted_value, converted_type)
        self.common_test_default(expected_default, 'bool', converted_value, converted_type, True)

    def testBooleanNotDefault(self):
        bool_value = False
        expected_value = 'false'
        expected_default = True
        converted_type, converted_value = self._custom_helper.convert(bool_value, 'bool')
        self.common_test_converted(expected_value, alias_constants.BOOLEAN, converted_value, converted_type)
        self.common_test_default(expected_default, 'bool', converted_value, converted_type, False)

    def testDictionaryDefault(self):
        dict_value = {'integer1': 111, 'integer2': 112}
        dict_default = {'integer2': 112, 'integer1': 111}
        converted_type, converted_value = self._custom_helper.convert(dict_value, 'dict')
        self.common_test_converted(dict_value, alias_constants.PROPERTIES, converted_value, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        self.common_test_default(dict_default, 'dict', converted_value, converted_type, True)

    def testDictionaryNotDefault(self):
        dict_value = {'integer1': 111, 'integer2': 112}
        dict_default = dict()
        converted_type, converted_value = self._custom_helper.convert(dict_value, 'dict')
        self.common_test_converted(dict_value, alias_constants.PROPERTIES, converted_value, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        self.common_test_default(dict_default, 'dict', converted_value, converted_type, False)

    def testPropertiesDefault(self):
        prop_value = Properties()
        prop_value.setProperty('value1', 'foo')
        prop_value.setProperty('value2', 'bar')
        prop_value.setProperty('value3', 'equal')
        prop_default = Properties(prop_value)
        expected_value = {'value3': 'equal', 'value1': 'foo', 'value2': 'bar'}
        converted_type, converted_value = self._custom_helper.convert(prop_value, 'java.util.Properties')
        self.common_test_converted(expected_value, alias_constants.PROPERTIES, converted_value, converted_type)
        self.common_test_default(prop_default, 'java.util.Properties', converted_value, converted_type, True)

    def testPropertiesNotDefault(self):
        prop_value = Properties()
        prop_value.setProperty('value1', 'foo')
        prop_value.setProperty('value2', 'bar')
        prop_value.setProperty('value3', 'equal')
        expected_value = {'value1': 'foo', 'value2': 'bar', 'value3': 'equal'}
        prop_default = {'value2': 'foo', 'value1': 'bar', 'value3': 'equal'}
        converted_type, converted_value = self._custom_helper.convert(prop_value, 'java.util.Properties')
        self.common_test_converted(expected_value, alias_constants.PROPERTIES, converted_value, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        self.common_test_default(prop_default, 'dict', converted_value, converted_type, False)

    def testMapDefault(self):
        map_value = HashMap()
        map_value.put('value1', 'foo')
        map_value.put('value2', 'bar')
        map_value.put('value3', 'equal')
        expected_value = {'value1': 'foo', 'value2': 'bar', 'value3': 'equal'}
        map_default = HashMap()
        map_default.put('value1', 'foo')
        map_default.put('value2', 'bar')
        map_default.put('value3', 'equal')

        converted_type, converted_value = self._custom_helper.convert(map_value, 'java.util.Map')
        self.common_test_converted(expected_value, alias_constants.PROPERTIES, converted_value, converted_type)
        self.assertEquals(PyOrderedDict, type(converted_value))
        self.common_test_default(map_default, 'java.util.Map', converted_value, converted_type, True)

    def testMapNotDefault(self):
        map_value = HashMap()
        map_value.put('value1', 'foo')
        map_value.put('value2', 'bar')
        map_value.put('value3', 'equal')
        expected_value = {'value1': 'foo', 'value2': 'bar', 'value3': 'equal'}

        map_default = dict()
        map_default['value1'] = 'eightball'
        map_default['value2'] = 'bar'
        map_default['value3'] = 'equal'

        converted_type, converted_value = self._custom_helper.convert(map_value, 'java.util.Map')
        self.common_test_converted(expected_value, alias_constants.PROPERTIES, converted_value, converted_type)
        self.assertEquals(alias_constants.PROPERTIES, converted_type)
        self.common_test_default(map_default, 'dict', converted_value, converted_type, False)

    def testIntegerDefault(self):
        port_value = '0'
        expected_value = 0
        default_value = expected_value
        converted_type, converted_value = self._custom_helper.convert(port_value, 'java.lang.Integer')
        self.common_test_converted(expected_value, alias_constants.INTEGER, converted_value, converted_type)
        self.common_test_default(default_value, 'int', converted_value, converted_type, True)

    def testIntegerNotDefault(self):
        port_value = 1443
        expected_value = port_value
        default_value = 0
        converted_type, converted_value = self._custom_helper.convert(port_value, 'int')
        self.common_test_converted(expected_value, alias_constants.INTEGER, converted_value, converted_type)
        self.common_test_default(default_value, 'int', converted_value, converted_type, False)

    def testBigIntegerConvert(self):
        big_value = '67999'
        expected_value = 67999L
        default_value = 0
        converted_type, converted_value = self._custom_helper.convert(big_value, 'java.math.BigInteger')
        self.common_test_converted(expected_value, alias_constants.LONG, converted_value, converted_type)
        self.common_test_default(default_value, 'long', converted_value, converted_type, False)

    def testDoubleConvert(self):
        double_value = '67999'
        expected_value = 67999
        default_value = expected_value
        converted_type, converted_value = self._custom_helper.convert(double_value, 'java.lang.Double')
        self.common_test_converted(expected_value, alias_constants.DOUBLE, converted_value, converted_type)
        self.common_test_default(default_value, 'double', converted_value, converted_type, True)

    def testFloatConvert(self):
        float_value = 4.2e-4
        expected_value = None
        converted_type, converted_value = self._custom_helper.convert(float_value, 'float')
        self.common_test_converted(expected_value, None, converted_value, converted_type)

    def common_test_default(self, default_value, default_type, model_value, model_type, expected):
        converted_type, converted_default = self._custom_helper.convert(default_value, default_type)
        return_result = self._custom_helper.is_default(model_value, model_type, converted_default)
        self.assertEquals(expected, return_result)

    def common_test_converted(self, expected_value, expected_type, model_value, model_type):

        self.assertEquals(expected_type, model_type)
        if expected_type == alias_constants.LIST:
            self.is_expected_list(expected_value, model_value)
        elif expected_type == alias_constants.PROPERTIES:
            self.is_expected_dict(expected_value, model_value)
        else:
            self.is_expected(expected_value, model_value)

    def is_expected(self, expected_value, model_value):
        return expected_value is not None and model_value is not None and expected_value == model_value

    def is_expected_list(self, expected_list, converted_list):
        return expected_list is not None and converted_list is not None and \
            self.roll_list(expected_list, converted_list) and self.roll_list(converted_list, expected_list)

    def roll_list(self, list1, list2):
        for item in list1:
            if item not in list2:
                return False
        return True

    def is_expected_dict(self, expected_dict, converted_dict):
        return expected_dict is not None and converted_dict is not None and \
               self.roll_dict(expected_dict, converted_dict) and self.roll_dict(converted_dict, expected_dict)

    def roll_dict(self, dict1, dict2):
        dict1_keys = dict1.keys()
        for key in dict2.keys():
            if key not in dict1_keys or dict2[key] != dict1[key]:
                return False
        return True


if __name__ == '__main__':
    unittest.main()
