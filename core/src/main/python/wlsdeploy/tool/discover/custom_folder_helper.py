"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import java.lang.Exception as JException
import java.lang.String as String
import java.lang.NumberFormatException as NumberFormatException
import java.lang.Long as Long
import java.lang.Double as Double
import java.lang.Integer as Integer
import java.lang.Boolean as Boolean
import java.lang.Enum as Enum
import java.math.BigInteger as BigInteger
import java.util.Map as Map
import java.util.Properties as Properties
import javax.management.ObjectName as ObjectName

import oracle.weblogic.deploy.util.PyOrderedDict as PyOrderedDict

import wlsdeploy.aliases.alias_constants as alias_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.util.mbean_utils import MBeanUtils
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_class_name = 'CustomFolderHelper'


class CustomFolderHelper(object):
    """
    Helper for locating the custom MBeans and attributes
    These require special handling, since they do not have alias definitions.
    """
    __cipher_text_prefixes = ["{AES}", "{AES-256}"]

    def __init__(self, aliases, logger, model_context, exception_type):
        self._exception_type = exception_type
        self._model_context = model_context
        self._logger = logger
        if self._logger is None:
            self._logger = PlatformLogger('wlsdeploy.discover')
        self._alias_helper = AliasHelper(aliases, self._logger, self._exception_type)
        self._weblogic_helper = WebLogicHelper(self._logger)
        self._wlst_helper = WlstHelper(self._logger, self._exception_type)
        self._info_helper = MBeanUtils(self._model_context, self._alias_helper, self._exception_type)

    def discover_custom_mbean(self, base_location, model_type, mbean_name):
        """
        Discover the custom mbean attributes using the MBeanInfo for the proxy.
        :param base_location: the current context for the location
        :param model_type: The parent type of the custom MBean
        :param mbean_name: the name of the custom mbean instance
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'discover_custom_mbean'
        self._logger.entering(base_location.get_folder_path(), model_type, mbean_name, class_name=_class_name,
                              method_name=_method_name)
        location = LocationContext(base_location)
        subfolder_result = PyOrderedDict()

        attribute_helper = self._info_helper.get_info_attribute_helper(location)
        if attribute_helper is None:
            self._logger.warning('WLSDPLY-06753', model_type, str(attribute_helper), mbean_name,
                                 class_name=_class_name, method_name=_method_name)
        else:
            subfolder_result[mbean_name] = PyOrderedDict()
            self._logger.finer('WLSDPLY-06757', attribute_helper.mbean_string(),
                               class_name=_class_name, method_name=_method_name)
            short_name = attribute_helper.get_mbean_name()
            # This is not like other custom interface names and should be changed to be more flexible
            interface_name = security_provider_interface_name(attribute_helper.get_mbean_interface_name())
            subfolder_result[mbean_name][interface_name] = PyOrderedDict()
            self._logger.info('WLSDPLY-06751', model_type, short_name, class_name=_class_name, method_name=_method_name)
            self._logger.info('WLSDPLY-06752', mbean_name, model_type, short_name, class_name=_class_name,
                              method_name=_method_name)
            subfolder_result[mbean_name][interface_name] = self.__get_model_attribute_map(attribute_helper)
        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return subfolder_result

    def get_mbean_interface(self, location, bean_name):
        """
        Return the MBean instance MBean interface name for the current location.
        :param location: context for location of the MBean
        :param bean_name: name of MBean for which to get the interface
        :return: MBean interface name for MBean instance
        """
        _method_name = 'get_mbean_interface'
        self._logger.entering(location.get_folder_path(), class_name=_class_name, method_name=_method_name)

        bean_instance = self._get_mbean_instance(location, bean_name)
        mbean_interface = None
        if bean_instance is not None:
            interfaces = bean_instance.getClass().getInterfaces()
            if not interfaces:
                self._logger.info('WLSDPLY-06124', str(location), str(bean_instance))
            else:
                for interface in interfaces:
                    interface_name = str(interface)
                    if 'MBean' in interface_name:
                        self._logger.finer('WLSDPLY-06126', interface_name,
                                           self._alias_helper.get_model_folder_path(location),
                                           class_name=_class_name, method_name=_method_name)
                        mbean_interface = interface_name
                        break
        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=mbean_interface)
        return mbean_interface

    def get_from_bean_proxy(self, location, mbean_instance, method_name, attribute):
        _method_name = 'get_from_bean_proxy'
        self._logger.entering(location.folder_path(), method_name, attribute,
                              class_name=_class_name, method_name=_method_name)

        success = False
        value = None
        try:
            get_method = getattr(mbean_instance, method_name)
            if get_method is not None:
                value = get_method()
                success = True
            else:
                self._logger.finer('Get method {0} is not found on mbean {1} attribute {2}',
                                   method_name, location.folder_path(), attribute,
                               class_name=_class_name, method_name=_method_name)
        except (Exception, JException), e:
            self._logger.finest('MBean {0} attribute {1} getter {2} cannot be invoked on the mbean_instance : {3}',
                                location.folder_path(), method_name, attribute, str(e),
                            class_name=_class_name, method_name=_method_name)
        self._logger.exiting(class_name=_class_name, method_name=_method_name, result=value)
        return success, value

    def __get_model_attribute_map(self, attribute_helper):
        """
        Return the model attributes for the MBean
        :param attribute_helper: context for the current MBean
        :return: model ready dictionary of the discovered MBean
        """
        _method_name = '__get_model_attribute_map_'
        self._logger.entering(str(attribute_helper), class_name=_class_name, method_name=_method_name)
        mbean_attributes = PyOrderedDict()
        for attribute_name in attribute_helper.get_mbean_attributes():
            model_value = self.__get_model_attribute_value(attribute_helper, attribute_name)
            if model_value is not None:
                mbean_attributes[attribute_name] = model_value
        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return mbean_attributes

    def __get_model_attribute_value(self, attribute_helper, attribute_name):
        """
        Retrieve the wlst value for the attribute and convert the value into a model appropriate format.
        If the attribute is read only, or the value is empty, or the value is the default, return None
        :param attribute_helper: context for the current MBean
        :param attribute_name: current MBean attribute being processed
        :return: Converted model attribute value
        """
        _method_name = 'get_model_attribute_value'
        add_value = None
        if attribute_helper.is_read_only(attribute_name):
            self._logger.finer('WLDSPLY-06754', attribute_name, attribute_helper.mbean_string(),
                               class_name=_class_name, method_name=_method_name)
        else:
            wlst_value = attribute_helper.get_value(attribute_name)
            model_type, model_value = self.__convert_to_type(attribute_helper, attribute_name, wlst_value)
            default_value = self.__get_default_value(attribute_helper, attribute_name)
            if not is_empty(model_value):
                if is_empty(default_value) or not self.value_is_default(model_value, model_type, default_value):
                    add_value = model_value
            if add_value is not None and model_type == alias_constants.PASSWORD:
                add_value = alias_constants.PASSWORD_TOKEN

        return add_value

    def __get_default_value(self, attribute_helper, attribute_name):
        _method_name = 'default_value'
        default = attribute_helper.get_default_value(attribute_name)
        self._logger.finer('{0} attribute {1} has default value of {2} with type of {3}',
                           attribute_helper.mbean_string(), attribute_name, default, type(default),
                           class_name=_class_name, method_name=_method_name)
        if not is_empty(default):
            __, default = self.__convert_to_type(attribute_helper, attribute_name, default)
        return default

    def __convert_to_type(self, attribute_helper, attr_name, wlst_value):
        _method_name = '__convert_to_type'
        converted = None
        converted_type = None
        mbean_string = attribute_helper.mbean_string()
        attr_type = attribute_type(attribute_helper, attr_name)
        try:
            if attribute_helper.is_encrypted(attr_name):
                if attr_type == str or attr_type == 'java.lang.String':
                    self._logger.fine('Skip clear text password attribute {0} at location {1}', attr_name,
                                      mbean_string, class_name=_class_name, method_name=_method_name)
                elif attr_type == '[B':
                    converted_type = alias_constants.PASSWORD
                    if wlst_value is not None:
                        converted = str(String(wlst_value))
            elif attr_type == 'int' or attr_type == 'java.lang.Integer':
                converted_type = alias_constants.INTEGER
                converted = convert_numeric(Integer, wlst_value)
            elif attr_type == 'long' or attr_type == 'java.lang.Long':
                converted_type = alias_constants.LONG
                converted = convert_numeric(Long, wlst_value)
            elif attr_type == 'double' or attr_type == 'java.lang.Double':
                converted_type = alias_constants.DOUBLE
                converted = convert_numeric(Double, wlst_value)
            elif attr_type == 'float' or attr_type == 'java.lang.Float':
                self._logger.fine('Attribute {0} at location {1} is type float and no alias constants for float. '
                                  'The type of value is {2}', attr_name, mbean_string, type(wlst_value),
                                  class_name=_class_name, method_name=_method_name)
                converted_type = alias_constants.DOUBLE
                converted = convert_numeric(Double, wlst_value)
            elif attr_type == 'java.math.BigInteger':
                self._logger.fine('Attribute {0} for {1} is java type BigInteger. Converting to long',
                                  attr_name, mbean_string, class_name=_class_name, method_name=_method_name)
                converted_type, converted = convert_big_integer(wlst_value)
            elif attr_type == 'str' or attr_type == 'java.lang.String' or attr_type == 'string':
                converted_type = alias_constants.STRING
                converted = convert_string(wlst_value)
            elif attr_type == 'bool' or attr_type == 'boolean' or attr_type == 'java.lang.Boolean':
                converted_type = alias_constants.BOOLEAN
                # add a convert to boolean
                converted = Boolean(wlst_value)
            elif attr_type == 'dict' or attr_type == 'java.util.Properties' or attr_type == 'java.util.Map':
                converted_type = alias_constants.PROPERTIES
                create_dictionary(wlst_value)
            elif attr_type.endswith('Enum'):
                converted_type = alias_constants.STRING
                if wlst_value is not None:
                    converted = wlst_value.toString()
            elif attr_type == 'PyArray' or attr_type.startswith('[L'):
                converted_type = alias_constants.JARRAY
                converted = create_array(wlst_value)
            elif attr_type == list:
                converted_type = alias_constants.LIST
                converted = create_array(wlst_value)
                if converted is not None:
                    converted = list(converted)
            else:
                converted_type, converted = convert_value(wlst_value)
        except Exception, e:
            self._logger.fine('{0} Unable to convert attribute {1} to data type {2} : {3}',
                              mbean_string, attr_name, converted_type, str(e),
                              class_name=_class_name, method_name=_method_name)
        if converted_type is not None:
            print_orig = wlst_value
            print_conv = converted
            if converted_type == alias_constants.PASSWORD:
                print_orig = '<masked>'
                print_conv = print_orig
            self._logger.fine('{0} Attribute {1} WLST value {2} converted to data type {3} value {4}',
                              mbean_string, attr_name, print_orig, converted_type, print_conv,
                              class_name=_class_name, method_name=_method_name)
        else:
            self._logger.info('{0} Unable to determine the data type for attribute {1}',
                              mbean_string, attr_name, class_name=_class_name, method_name=_method_name)
        return converted_type, converted

    def __value_is_default(self, model_value, model_type, default_value):
        if model_type == alias_constants.LIST:
            return equal_lists(model_value, default_value)
        elif model_type == alias_constants.PROPERTIES:
            return equal_lists(model_value.keys(), default_value.keys()) and \
                   equal_lists(model_value.values(), default_value.values())
        elif model_type == alias_constants.JARRAY:
            return equal_jarrays(model_value, default_value)
        elif model_type == alias_constants.STRING:
            return model_value == default_value
        elif model_type == alias_constants.OBJECT:
            return model_value.equals(default_value)
        else:
            return model_value == default_value


def equal_lists(list1, list2):
    if len(list1) == len(list2):
        return len(list(set(list1) - set(list2))) == 0


def equal_jarrays(array1, array2):
    if len(array1) == len(array2):
        for item1 in array1:
            found = False
            for item2 in array2:
                if item1.equals(item2):
                    found = True
                    break
            if not found:
                return False
        return True
    return False


def security_provider_interface_name(mbean_interface):
    """
    This is too tied into security providers.
    This needs something more to differentiate Security Provider interface "like" name from other custom mbeans
    :param mbean_interface: interface for the MBean
    :return: massaged name specific to the security provider
    """
    result = mbean_interface
    idx = mbean_interface.rfind('MBean')
    if idx > 0:
        result = result[:idx-1]
    return result


def attribute_type(attribute_helper, attribute_name):
    attr_type = None
    check_type = attribute_helper.get_type(attribute_name)
    if check_type is not None:
        attr_type = str(check_type)
    return attr_type


def create_enumeration_list(enumeration):
    enumeration_list = list()
    while enumeration.hasMoreElements():
        enumeration_list.append(enumeration.nextElement())
    return enumeration_list


def convert_numeric(class_type, number):
    if number is None:
        return None
    try:
        converted = class_type.valueOf(number)
    except NumberFormatException:
        converted = None
    return converted


def convert_big_integer(value):
    """
    Convert the big integer value to long.
    :param value: big integer string or number value
    :return: converted to long
    """
    if value is None:
        return None
    try:
        bi = BigInteger(value)
        converted = bi.longValue()
    except NumberFormatException:
        converted = None
    return converted


def is_empty(value):
    return value is None or (type(value) in [list, dict] and len(value) == 0) or \
    ((type(value) == str or isinstance(value, String)) and
     (len(value) == 0 or value == '[]' or value == 'null' or value == 'None'))


def convert_string(value):
    converted = None
    if not is_empty(value):
        converted = str(value)
    return converted


def create_array(iterable):
    """
    Create an array from the jarray or list objects.
    :param iterable: a List object or other iterable type
    :return: an array or a string containing the converted contents from the provided iterable
    """
    my_array = None
    if iterable:
        my_array = []
        for element in iterable:
            __, converted = convert_value(element)
            my_array.append(converted)
    return my_array


def create_dictionary(value):
    my_dict = PyOrderedDict()
    if instanceof(value, dict):
        for key, item in value.items():
            my_dict[key] = item
    elif instanceof(value, Properties):
        for key in value.stringPropertyNames():
            my_dict[key] = value.getProperty(key)
    elif instanceof(value, Map):
        for entry in value.entrySet():
            my_dict[entry.getKey()] = entry.getValue()
    return my_dict


def convert_value(value):
    if isinstance(value, ObjectName):
        converted_type = alias_constants.STRING
        converted = value.getKeyProperty('Name')
    elif isinstance(value, String):
        converted_type = alias_constants.STRING
        converted = str(value)
    elif isinstance(value, Enum):
        converted_type = alias_constants.STRING
        converted = str(value.toString())
    else:
        converted_type = alias_constants.OBJECT
        converted = value
    return converted_type, converted
