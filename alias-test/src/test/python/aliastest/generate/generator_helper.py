"""
Copyright (c) 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import types

import java.lang.Boolean as Boolean
import java.util.logging.Level as Level
from java.lang import Object
from javax.management import ObjectName

import org.python.core.PyArray as PyArray
import org.python.core.PyInstance as PyInstance

from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.aliases.alias_constants as alias_constants

import aliastest.generate.generator_wlst as generator_wlst
import aliastest.util.all_utils as all_utils
from aliastest.util.helper import TestHelper

VARIATIONS = {'ies': 'y', 'es': '', 's': ''}


class GeneratorHelper:
    """
    Common helper methods for generation of folder and attribute information for both online and offline
    generators.
    """

    __logger = PlatformLogger('test.aliases.generate', resource_bundle_name='aliastest_rb')
    __logger.set_level(Level.FINER)
    __class_name = 'GeneratorHelper'

    def __init__(self, model_context, dictionary):
        self._dictionary = dictionary
        self._helper = TestHelper(model_context)
        self._ignore_list = self._helper.aliases().get_ignore_attribute_names()

    def add_default_value(self, dictionary, lsa_map, cmo_helper, method_helper, attribute_name=None):
        """
         Add information about the attribute value to the dictionary. Store the values from the wlst.ls() map
         and from the wlst.get(). If the attribute is not present in the ls map, or the get fails, a FAIL will be
         stored in the dictionary. Convert the type of the attribute to an aliases attribute type.
        :param dictionary: where to store the value results
        :param lsa_map: map returned from the ls('a') at the current location
        :param cmo_helper: Helper for additional information not provided by GET or LSA
        :param method_helper: Method helper to assist in decisions
        :param attribute_name: Optional parameter if the attribute_name is not the same as the one in the CMO helper
        """
        _method_name = 'add_default_value'
        self.__logger.entering(str(cmo_helper), class_name=self.__class_name, method_name=_method_name)
        if attribute_name is None:
            attribute_name = cmo_helper.get_name()
        mbean_type = cmo_helper.get_mbean_type()

        if lsa_map is not None and attribute_name in lsa_map:
            lsa_value = lsa_map.get(attribute_name)
            self.__logger.finest('WLSDPLYST-01101', attribute_name, lsa_value,
                                 class_name=self.__class_name, method_name=_method_name)
        else:
            self.__logger.finer('WLSDPLYST-01102', attribute_name,
                                class_name=self.__class_name, method_name=_method_name)
            lsa_value = all_utils.FAIL

        cmo_attr_type = all_utils.UNKNOWN
        cmo_value = all_utils.FAIL
        if self._is_valid_cmo_attribute(cmo_helper):
            if cmo_helper.is_encrypted():
                cmo_attr_type = alias_constants.PASSWORD
                cmo_value = cmo_helper.default_value()
            else:
                cmo_attr_type = cmo_helper.attribute_type()
                cmo_value = cmo_helper.default_value()
        elif method_helper is not None and self._is_valid_cmo_attribute(method_helper):
            cmo_attr_type = method_helper.attribute_type()
            cmo_value = method_helper.default_value()
            self.__logger.fine('MBean {0} attribute {1} is using CMO method for cmo info : '
                               'cmo_attr_type={2} cmo_value={3}',
                               mbean_type, attribute_name, cmo_attr_type, cmo_value,
                               class_name=self.__class_name, method_name=_method_name)

        if cmo_value != all_utils.FAIL and cmo_attr_type != all_utils.UNKNOWN:
            dictionary[all_utils.CMO_TYPE] = self.type_it(mbean_type, attribute_name, cmo_attr_type)
            dictionary[all_utils.CMO_DEFAULT] = \
                self.convert_attribute(attribute_name, cmo_value, value_type=dictionary[all_utils.CMO_TYPE])
            self.__logger.finest('MBean {5} attribute {0} {1}  is {2} and {3} is {4}',
                                 attribute_name, all_utils.CMO_TYPE, dictionary[all_utils.CMO_TYPE],
                                 all_utils.CMO_DEFAULT, dictionary[all_utils.CMO_DEFAULT],
                                 mbean_type, class_name=self.__class_name, method_name=_method_name)
        else:
            self.__logger.finer('MBean {0} attribute {1} cmo_value has invalid value {2} for type or '
                                'invalid type {3}',
                                mbean_type, attribute_name, cmo_value, cmo_attr_type,
                                class_name=self.__class_name, method_name=_method_name)

        success, get_value = generator_wlst.get(attribute_name)
        if success is False:
            get_value = all_utils.FAIL

        if get_value != all_utils.FAIL:
            if method_helper is not None:
                get_attr_type = method_helper.attribute_type()
            elif get_value is not None:
                if isinstance(get_value, PyInstance):
                    get_attr_type = get_value.getClass().getName()
                else:
                    get_attr_type = type(get_value)
            else:
                get_attr_type = all_utils.UNKNOWN

            dictionary[all_utils.GET_TYPE] = self.type_it(mbean_type, attribute_name, get_attr_type)
            dictionary[all_utils.GET_DEFAULT] = \
                self.convert_attribute(attribute_name, get_value, value_type=dictionary[all_utils.GET_TYPE])
            self.__logger.finest('Attribute {0} {1}  is {2} and {3} is {4}', attribute_name, all_utils.GET_TYPE,
                                 dictionary[all_utils.GET_TYPE], all_utils.GET_DEFAULT,
                                 dictionary[all_utils.GET_DEFAULT],
                                 class_name=self.__class_name, method_name=_method_name)

        if lsa_value != all_utils.FAIL:

            if lsa_value is not None:
                if isinstance(lsa_value, PyInstance):
                    if lsa_value.getClass().isAssignableFrom(Object):
                        lsa_attr_type = lsa_value.getClass().getName()
                    else:
                        lsa_attr_type = str(lsa_value.getClass())
                else:
                    lsa_attr_type = type(lsa_value)
                if lsa_attr_type in [str, unicode]:
                    lsa_value = lsa_value.rstrip()
            else:
                lsa_attr_type = all_utils.UNKNOWN

            if lsa_value is not None and cmo_attr_type == alias_constants.PASSWORD and \
                    (self._is_string_type(lsa_attr_type) and lsa_value.startswith('****')):
                lsa_value = None
                dictionary[all_utils.LSA_TYPE] = alias_constants.PASSWORD
            else:
                dictionary[all_utils.LSA_TYPE] = self.type_it(mbean_type, attribute_name, lsa_attr_type)
            dictionary[all_utils.LSA_DEFAULT] = \
                self.convert_attribute(attribute_name, lsa_value, value_type=dictionary[all_utils.LSA_TYPE])
            self._add_lsa_readwrite(dictionary, attribute_name)
            self.__logger.finest('Attribute {0} {1} is {2} and {3} is {4}', attribute_name, all_utils.LSA_TYPE,
                                 dictionary[all_utils.LSA_TYPE], all_utils.LSA_DEFAULT,
                                 dictionary[all_utils.LSA_DEFAULT],
                                 class_name=self.__class_name, method_name=_method_name)

        if lsa_value == all_utils.FAIL and get_value == all_utils.FAIL and cmo_value == all_utils.FAIL:
            self.__logger.fine('WLSDPLYST-01111', attribute_name,
                               class_name=self.__class_name, method_name=_method_name)
        elif lsa_value == all_utils.FAIL and get_value == all_utils.FAIL:
            self.__logger.fine('CMO type only for MBean {0} attribute {1}', mbean_type, attribute_name,
                               lass_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def massage_special(self, attribute, attribute_type, lsa_value, get_value):
        """
        Determine if the attribute is an encrypted, and return the massaged values.
        :param attribute: name of the attribute
        :param attribute_type: property type of the attribute value
        :param lsa_value: value of the attribute in the ls() map
        :param get_value: value of the attribute from a get
        :return: massaged encrypted values
        """
        massage_lsa = lsa_value
        massage_get = get_value
        # Set all password LSA values to None as the LSA always returns '*****' even for None
        if attribute_type == alias_constants.PASSWORD and massage_lsa != all_utils.FAIL:
            self.__logger.finest('WLSDPLYST-01104', attribute,
                                 class_name=self.__class_name, method_name='massage_special')
            massage_lsa = None
        return massage_lsa, massage_get

    def _is_valid_lsa(self, attribute_helper):
        _method_name = '_is_valid_lsa'
        valid = True
        attribute_name = attribute_helper.get_name()
        mbean_type = attribute_helper.get_mbean_type()
        self.__logger.entering(attribute_name, mbean_type, class_name=self.__class_name, method_name=_method_name)
        if self._should_ignore(attribute_helper):
            self.__logger.finest('MBeanInfo attribute {0} is in the WDT ignore list for MBean {1}',
                                 attribute_name, mbean_type,
                                 class_name=self.__class_name, method_name=_method_name)
            valid = False
        # The following is the best can do
        elif attribute_helper.is_attribute_found() and attribute_helper.is_attribute() is False:
            self.__logger.finest('Ignore MBean {0} attribute {1} that is not an attribute type', mbean_type,
                                 attribute_name,
                                 class_name=self.__class_name, method_name=_method_name)
            valid = False
        elif self._is_clear_text_password(attribute_helper):
            self.__logger.finest('Ignore MBean{1} attribute {0} that is a clear text password attribute',
                                 attribute_name, mbean_type, class_name=self.__class_name, method_name=_method_name)
            valid = False
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(valid))
        return valid

    def _is_valid_no_mbean(self, mbean_type, helper):
        _method_name = '_is_valid_no_mbean'
        valid = True
        attribute_name = helper.get_name()
        self.__logger.entering(attribute_name, mbean_type, class_name=self.__class_name, method_name=_method_name)
        if self._should_ignore(helper):
            self.__logger.finest('MBeanInfo attribute {0} is in the WDT ignore list for MBean {1}',
                                 attribute_name, mbean_type,
                                 class_name=self.__class_name, method_name=_method_name)
            valid = False
        elif self._is_clear_text_password(helper):
            self.__logger.finest('Ignore MBean{1} attribute {0} that is a clear text password attribute',
                                 attribute_name, mbean_type, class_name=self.__class_name, method_name=_method_name)
            valid = False
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(valid))
        return valid

    def _is_valid_method_only_attribute(self, method_helper):
        _method_name = '_is_valid_method_only_attribute'
        attribute = method_helper.get_name()
        mbean_type = method_helper.get_mbean_type()
        self.__logger.entering(attribute, mbean_type, class_name=self.__class_name, method_name=_method_name)
        valid = self._is_valid_cmo_attribute(method_helper) and method_helper.is_writable()
        self.__logger.exiting(result=valid, class_name=self.__class_name, method_name=_method_name)
        return valid

    def _is_valid_cmo_attribute(self, mbi_helper, info_helper=None):
        _method_name = '_is_valid_cmo_attribute'
        attribute = mbi_helper.get_name()
        mbean_type = mbi_helper.get_mbean_type()
        self.__logger.entering(attribute, mbean_type, class_name=self.__class_name, method_name=_method_name)
        valid = True
        if not self._is_valid_attribute(attribute, mbi_helper, info_helper) or \
                not self._valid_getter_on_mbean_instance(mbi_helper):
            self.__logger.finer('Ignore MBeanInfo attribute {0} for MBean {1} that cannot be retrieved '
                                'with either wlst.get() or CMO read method', attribute, mbean_type,
                                class_name=self.__class_name, method_name=_method_name)
            valid = False
        self.__logger.exiting(result=valid, class_name=self.__class_name, method_name=_method_name)
        return valid

    def _is_valid_attribute(self, converted_name, helper, info_helper=None):
        _method_name = '_is_valid_attribute'
        mbean_type = helper.get_mbean_type()
        self.__logger.entering(mbean_type, converted_name, class_name=self.__class_name, method_name=_method_name)
        valid = True
        if helper.is_attribute() is False:
            self.__logger.finest('MBean {0} attribute {1} is not marked as an attribute.',
                                 mbean_type, converted_name, Boolean(helper.is_mbean()),
                                 class_name=self.__class_name, method_name=_method_name)
            valid = False
        elif self._should_ignore(helper):
            self.__logger.finest('MBean {0} attribute {1} is in the WDT ignore list', mbean_type, converted_name,
                                 class_name=self.__class_name, method_name=_method_name)
            valid = False
        elif self._is_clear_text_password(helper):
            self.__logger.finer('Ignore MBeanInfo attribute {0} for MBean {1} that is a clear text password attribute',
                                converted_name, mbean_type, class_name=self.__class_name, method_name=_method_name)
            valid = False
        self.__logger.exiting(result=Boolean(valid), class_name=self.__class_name, method_name=_method_name)
        return valid

    def _valid_getter_on_mbean_instance(self, helper):
        return self._can_get(helper.get_mbean_type(), helper.get_name()) or helper.is_valid_getter()

    def convert_attribute(self, attribute, value, value_type=None):
        """
        Convert the attribute into a value that can be stored in the generated json file and properly
        returned for verification against the alias default value
        :param attribute: attribute name
        :param value: attribute value
        :param value_type: type of the attribute value
        :return: converted value
        """
        _method_name = 'convert_attribute'
        self.__logger.entering(attribute, value, value_type, class_name=self.__class_name, method_name=_method_name)
        if value is not None and '$Proxy' in str(type(value)):
            if value.isProxyClass(ObjectName):
                return_value = value.getKeyProperty('Name')
            else:
                return_value = value.toString()
        elif value is None or value_type == alias_constants.PASSWORD or \
                (value_type == alias_constants.STRING and (value == 'null' or value == 'none')):
            return_value = 'None'
        elif value is None or value == 'null' or value == 'none' \
                or value_type == alias_constants.PASSWORD:
            return_value = 'None'
        elif not isinstance(value, basestring) and \
                (value_type == alias_constants.BOOLEAN or value_type == alias_constants.JAVA_LANG_BOOLEAN):
            if value:
                return_value = Boolean.toString(Boolean.TRUE)
            else:
                return_value = Boolean.toString(Boolean.FALSE)
        elif isinstance(value, (types.ListType, types.TupleType, PyArray)):
            return_value = list()
            for entry in value:
                return_value.append(self.convert_attribute(attribute, entry, value_type))
        elif value_type == alias_constants.OBJECT or isinstance(value, Object):
            return_value = value.toString()
        else:
            return_value = value
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=return_value)
        return return_value

    def type_it(self, mbean_type, attr_name, attr_type):
        """
        Return the aliases name for the domain attribute type
        :param mbean_type: MBean type for logging purposes
        :param attr_name: attribute name
        :param attr_type: attribute type
        :return: aliases name for the attribute type
        """
        _method_name = 'type_it'
        self.__logger.entering(mbean_type, attr_name, attr_type, class_name=self.__class_name, method_name=_method_name)
        if attr_type is None:
            self.__logger.fine('No attribute type passed for MBean {0} attribute {1}', mbean_type, attr_name,
                               class_name=self.__class_name, method_name=_method_name)
            return_type = all_utils.UNKNOWN
        elif attr_type == all_utils.FAIL:
            return_type = attr_type
        elif attr_type == int or 'java.lang.Integer' in str(attr_type) or 'int' in str(attr_type):
            return_type = alias_constants.INTEGER
        elif attr_type in [str, unicode] or str(attr_type) == "<type 'java.lang.String'>" or \
                attr_type == 'java.lang.String' or 'string' in str(attr_type):
            return_type = alias_constants.STRING
        elif attr_type == bool or 'boolean' in str(attr_type):
            return_type = alias_constants.BOOLEAN
        elif 'java.lang.Boolean' in str(attr_type):
            return_type = alias_constants.JAVA_LANG_BOOLEAN
        elif attr_type == long or 'java.lang.Long' in str(attr_type) or 'java.math.BigInteger' in str(attr_type) or \
                'long' in str(attr_type):
            return_type = alias_constants.LONG
        elif attr_type == float or 'java.lang.Float' in str(attr_type) or 'float' in str(attr_type) or \
                'java.lang.Double' in str(attr_type) or 'double' in str(attr_type):
            return_type = alias_constants.DOUBLE
        elif attr_type == dict or str(attr_type) == "<type 'java.util.Properties'>" or \
                attr_type == 'java.util.Properties' or attr_type == 'java.util.Map' or \
                str(attr_type) == "<type 'java.util.Map'>":
            return_type = alias_constants.PROPERTIES
        elif '[B' in str(attr_type) or "array('b'" in str(attr_type):
            return_type = alias_constants.PASSWORD
        elif 'Enum' in str(attr_type):
            return_type = alias_constants.STRING
        elif attr_type == PyArray or attr_type == '[Ljavax.management.ObjectName;' or \
            ((str(attr_type).startswith('weblogic.') or str(attr_type).startswith('java'))
             and str(attr_type).endswith('[]')) or '[L' in str(attr_type):
            return_type = alias_constants.JARRAY
        elif attr_type == list:
            return_type = alias_constants.LIST
        elif (isinstance(attr_type, basestring) and
              ('javax.management.ObjectName' in attr_type or 'weblogic.' in attr_type or 'java.' in attr_type)) or \
                'javax.management.ObjectName' in str(attr_type) or 'weblogic.' in str(attr_type) or \
                'java.' in str(attr_type):
            return_type = alias_constants.OBJECT
        else:
            return_type = attr_type
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=return_type)
        return return_type

    def _add_lsa_readwrite(self, attribute_map, lsa_name):
        _method_name = '_get_lsa_readwrite'
        self.__logger.entering(lsa_name, class_name=self.__class_name, method_name=_method_name)
        attributes_str = generator_wlst.lsa_string()
        read_type = None
        if attributes_str is not None:
            for attribute_str in attributes_str.split('\n'):
                if attribute_str:
                    read_type = attribute_str[0:4].strip()
                    attr = attribute_str[7:attribute_str.find(' ', 7)+1].strip()
                    if attr == lsa_name:
                        if read_type == '-rw-':
                            attribute_map[all_utils.READ_TYPE] = all_utils.READ_WRITE
                        elif read_type == '-r--':
                            attribute_map[all_utils.READ_TYPE] = all_utils.READ_ONLY
                        break

        self.__logger.finer('WLSDPLYST-01136', lsa_name, read_type,
                            class_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name)

    def _can_get(self, mbean_type, attribute_name, index=0):
        success = generator_wlst.can_get(mbean_type, attribute_name)
        while not success and index < len(VARIATIONS):
            key = VARIATIONS.keys()[index]
            if attribute_name.endswith(key):
                converted = attribute_name[:len(attribute_name)-len(key)-1] + VARIATIONS[key]
                success = self._can_get(mbean_type, converted, index)
            index += 1

        return success

    def invoke_creator(self, mbean_instance, mbean_type, attribute_name, method_name, child_mbean_name):
        _method_name = 'invoke_creator'
        import java.lang.Exception as JException
        success = False
        try:
            set_method = getattr(mbean_instance, method_name)
            if set_method is not None:
                self.__logger.finer('Invoking method {0} for MBean {1} {2} with value {3}', method_name, mbean_type,
                                    attribute_name, child_mbean_name,
                                    class_name=self.__class_name, method_name=_method_name)
                set_method(child_mbean_name)
                success = True
            else:
                self.__logger.finest('Setter/creator method {0} is not found on mbean {1} {2}',
                                     method_name, mbean_type, attribute_name,
                                     class_name=self.__class_name, method_name=_method_name)
        except (Exception, JException), e:
            self.__logger.finest('WLSDPLYST-01330', mbean_type, method_name, attribute_name, str(e),
                                 class_name=self.__class_name, method_name=_method_name)
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=success)
        return success

    def _slim_maps(self, methods_map, mbean_info_map):
        """
        Use the mbean info map containment type to pluck out (best able) the subfolders
        :param methods_map: contains the methods from the mbean interface
        :param mbean_info_map: contans the property descriptors from the MBeanInfo
        """
        self._remove_subfolders(methods_map, mbean_info_map)
        self._remove_unused_methods(methods_map)

    def _remove_should_ignores(self, check_map):
        for attribute_name in [name for name in check_map]:
            if attribute_name in self._ignore_list:
                check_map.pop(attribute_name)

    def _should_ignore(self, attribute_helper):
        return attribute_helper.get_name() in self._ignore_list

    def _remove_subfolders(self, methods_map, mbean_info_map):
        for attribute_name in mbean_info_map.keys():
            if all_utils.is_subfolder(mbean_info_map[attribute_name]):
                mbean_info_map.pop(attribute_name)
                methods_map.pop(attribute_name, None)

    def _remove_unused_methods(self, methods_map):
        for attribute_name in methods_map:
            if attribute_name in all_utils.IGNORE_METHODS_LIST:
                methods_map.pop(attribute_name)

    def _is_string_type(self, attribute_type):
        return attribute_type in [str, unicode] or attribute_type == 'java.lang.String'

    def _is_clear_text_password(self, helper):
        _method_name = '_is_clear_text_password'
        self.__logger.entering(helper.get_name(), class_name=self.__class_name, method_name=_method_name)
        if helper.is_attribute_found():
            cleartext = helper.is_encrypted() and self._is_string_type(helper.attribute_type())
        else:
            cleartext = all_utils.is_clear_text_password(helper.get_name())
        self.__logger.exiting(result=Boolean(cleartext), class_name=self.__class_name, method_name=_method_name)
        return cleartext

    def _is_valid_folder(self, attribute_helper):
        _method_name = '_is_valid_folder'
        self.__logger.entering(attribute_helper.str(), class_name=self.__class_name, method_name=_method_name)
        result = attribute_helper.is_mbean()
        self.__logger.exiting(class_name=self.__class_name, method_name=_method_name, result=Boolean(result))
        return result


def filename():
    return 'generated'
