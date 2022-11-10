"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates. 
The Universal Permissive License (UPL), Version 1.0
"""

import java.lang.Boolean as Boolean
import java.lang.Double as Double
import java.lang.Enum as Enum
import java.lang.Exception as JException
import java.lang.Integer as Integer
import java.lang.Long as Long
import java.lang.NumberFormatException as NumberFormatException
import java.lang.String as String
import java.math.BigInteger as BigInteger
import java.util.Map as Map
import java.util.Properties as Properties
import javax.management.ObjectName as ObjectName

import oracle.weblogic.deploy.util.PyOrderedDict as PyOrderedDict

import wlsdeploy.aliases.alias_constants as alias_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.mbean_utils import MBeanUtils
from wlsdeploy.tool.util.variable_injector import STANDARD_PASSWORD_INJECTOR
from wlsdeploy.tool.util.wlst_helper import WlstHelper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_logger = PlatformLogger('wlsdeploy.discover')
_class_name = 'CustomFolderHelper'


class CustomFolderHelper(object):
    """
    Helper for locating the custom MBeans and its attributes.

    These require special handling, since they do not have alias definitions.
    Discover the MBean attributes using the information provided by the MBeanAttributes
    wrapper class.
    """

    def __init__(self, aliases, logger, model_context, exception_type, credential_injector=None):
        global _logger
        self._exception_type = exception_type
        self._model_context = model_context
        if logger is not None:
            _logger = logger
        self._weblogic_helper = WebLogicHelper(_logger)
        self._wlst_helper = WlstHelper(self._exception_type)
        self._info_helper = MBeanUtils(self._model_context, aliases, self._exception_type)
        self._credential_injector = credential_injector

    def discover_custom_mbean(self, base_location, model_type, mbean_name):
        """
        Discover the Custom MBean attributes using its MBeanInfo.
        :param base_location: the current context for the location
        :param model_type: The parent type of the custom MBean
        :param mbean_name: the name of the custom MBean instance
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'discover_custom_mbean'
        _logger.entering(base_location.get_folder_path(), model_type, mbean_name,
                         class_name=_class_name, method_name=_method_name)
        location = LocationContext(base_location)
        subfolder_result = PyOrderedDict()

        attribute_helper = self._info_helper.get_info_attribute_helper(location)
        if attribute_helper is None:
            _logger.warning('WLSDPLY-06753', model_type, str_helper.to_string(attribute_helper), mbean_name,
                            class_name=_class_name, method_name=_method_name)
        else:
            subfolder_result[mbean_name] = PyOrderedDict()
            _logger.finer('WLSDPLY-06757', attribute_helper.mbean_string(),
                          class_name=_class_name, method_name=_method_name)
            short_name = attribute_helper.get_mbean_name()
            # This is not like other custom interface names and should be changed to be more flexible
            interface_name = security_provider_interface_name(attribute_helper.get_mbean_instance(),
                                                              attribute_helper.get_mbean_interface_name())
            subfolder_result[mbean_name][interface_name] = PyOrderedDict()
            _logger.info('WLSDPLY-06751', model_type, short_name, class_name=_class_name, method_name=_method_name)
            _logger.info('WLSDPLY-06752', mbean_name, model_type, short_name,
                         class_name=_class_name, method_name=_method_name)
            subfolder_result[mbean_name][interface_name] = self.get_model_attribute_map(location, attribute_helper)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return subfolder_result

    def get_model_attribute_map(self, location, attribute_helper):
        """
        Return a map of the MBean's attributes, in model format, which do not have default values.
        :param location: location context for the current MBean
        :param attribute_helper: context for the current MBean
        :return: model ready dictionary of the discovered MBean
        """
        _method_name = 'get_model_attribute_map'
        _logger.entering(str_helper.to_string(attribute_helper), class_name=_class_name, method_name=_method_name)
        mbean_attributes = PyOrderedDict()
        for attribute_name in attribute_helper.get_mbean_attributes():
            model_value = self.get_model_attribute_value(attribute_helper, attribute_name)
            if model_value is not None:
                mbean_attributes[attribute_name] = model_value
                self.__inject_token(location, mbean_attributes, attribute_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return mbean_attributes

    def get_model_attribute_value(self, attribute_helper, attribute_name, wlst_value='unknown'):
        """
        Retrieve the WLST value for the attribute and convert the value into a model appropriate format.
        If the attribute is read only, or the value is empty, or the value is the default, return None
        :param attribute_helper: context for the current MBean
        :param attribute_name: current MBean attribute being processed
        :param wlst_value: if provided, use this WLST value for the attribute instead of from the MBean instance
        :return: Converted model attribute value
        """
        _method_name = 'get_model_attribute_value'
        add_value = None
        mbean_string = attribute_helper.mbean_string()
        if attribute_helper.is_read_only(attribute_name):
            _logger.finer('WLSDPLY-06776', mbean_string, attribute_name,
                          class_name=_class_name, method_name=_method_name)
        else:
            model_type, model_value = self.__convert_to_type(attribute_helper, attribute_name, wlst_value)
            if model_type is not None:
                print_conv = model_value
                if model_type == alias_constants.PASSWORD:
                    print_orig = alias_constants.MASKED
                    print_conv = print_orig
                _logger.finer('WLSDPLY-06770', mbean_string, attribute_name, model_type,
                              str_helper.to_string(print_conv), class_name=_class_name, method_name=_method_name)
                default_value = self.__get_default_value(attribute_helper, attribute_name)
                if not is_empty(model_value):
                    if not is_empty(default_value):
                        converted_type, default_value = self.convert(default_value, type(default_value))
                    if is_empty(default_value) or not self.is_default(model_value, model_type, default_value):
                        add_value = model_value
                if add_value is not None and model_type == alias_constants.PASSWORD:
                    add_value = alias_constants.PASSWORD_TOKEN

#             else:
#                 _logger.finer('WLSDPLY-06771', mbean_string, attribute_name, attribute_helper.get_type(attribute_name),
#                               class_name=_class_name, method_name=_method_name)

        return add_value

    def convert(self, value, value_type):
        """
        Public function to convert the value with value_type to a model compatible value.
        :param value: Value to be converted into the appropriate model data type
        :param value_type: data type of the value
        :return: converted data type and value
        """
        _method_name = 'convert_method'
        if str_helper.to_string(value_type).startswith('<type '):
           # strip off type, introduced in 14.1.1
           value_type = str_helper.to_string(value_type)[7:-2]
        converted_type = None
        converted = None
        try:
            if value_type == '[B':
                converted_type = alias_constants.PASSWORD
                converted = convert_byte_buffer(value)
            elif value_type == 'int' or value_type == 'java.lang.Integer':
                converted_type = alias_constants.INTEGER
                converted = convert_numeric(Integer, value)
            elif value_type == 'long' or value_type == 'java.lang.Long':
                converted_type = alias_constants.LONG
                converted = convert_numeric(Long, value)
            elif value_type == 'double' or value_type == 'java.lang.Double':
                converted_type = alias_constants.DOUBLE
                converted = convert_numeric(Double, value)
            elif value_type == 'float' or value_type == 'java.lang.Float':
                _logger.info('WLSDPLY-06766', value_type, class_name=_class_name, method_name=_method_name)
            elif value_type == 'java.math.BigInteger':
                converted_type, converted = convert_big_integer(value)
                _logger.fine('WLSDPLY-06767', converted, converted_type,
                             class_name=_class_name, method_name=_method_name)
            elif value_type == 'str' or value_type == 'java.lang.String' or value_type == 'string':
                converted_type = alias_constants.STRING
                converted = convert_string(value)
            elif value_type == 'bool' or value_type == 'boolean' or value_type == 'java.lang.Boolean':
                converted_type = alias_constants.BOOLEAN
                converted = convert_boolean(value)
            elif value_type == 'dict' or value_type == 'java.util.Properties' or value_type == 'java.util.Map':
                converted_type = alias_constants.PROPERTIES
                converted = create_dictionary(value)
            elif value_type.endswith('Enum'):
                converted_type = alias_constants.STRING
                if value is not None:
                    converted = value.toString()
            elif value_type == 'PyArray' or value_type.startswith('[L') or value_type == 'array.array':
                converted = create_array(value)
                if converted is not None:
                    converted_type = alias_constants.JARRAY
            elif value_type == 'list':
                converted = create_array(value)
                if converted is not None:
                    converted_type = alias_constants.LIST
            else:
                converted_type, converted = convert_value(value)
                _logger.fine('WLSDPLY-06768', value_type, converted_type,
                             class_name=_class_name, method_name=_method_name)
        except Exception, e:
            _logger.fine('WLSDPLY-06769', value_type, converted_type, str_helper.to_string(e),
                         class_name=_class_name, method_name=_method_name)
        return converted_type, converted

    def is_default(self, model_value, model_type, default_value):
        """
        Compare the model value to the model default value to determine if it is a default.
        If this is running in offline Discover then the default value might differ from the MBeanInfo value,
        which is geared towards online. If it is offline and the default value is not empty but the
        WLST value indicates empty (i.e. zero length string or zero in a numeric field) then return True.
        :param model_value: WLST value converted to model value
        :param model_type: data type of the model value using the alias_constants nomenclature
        :param default_value: WLST default value converted to model value
        :return: True if the model value is the default value
        """
        _method_name = 'is_default'
        mvalue = model_value
        dvalue = default_value
        if model_type == alias_constants.PASSWORD:
            mvalue = alias_constants.MASKED
            dvalue = alias_constants.MASKED
        _logger.finest('WLSDPLY-06772', mvalue, model_type, dvalue,
                       class_name=_class_name, method_name=_method_name)
        is_default = False
        if model_type == alias_constants.LIST:
            is_default = equal_lists(model_value, default_value)
        elif model_type == alias_constants.PROPERTIES:
            is_default = equal_dictionary(model_value, default_value)
        elif model_type == alias_constants.JARRAY:
            is_default = equal_jarrays(model_value, default_value)
        elif model_type == alias_constants.STRING:
            is_default = model_value == default_value or self.__offline_default(model_value, model_type, default_value)
        elif model_type == alias_constants.OBJECT:
            is_default = model_value.equals(default_value)
        elif model_type in alias_constants.ALIAS_NUMERIC_DATA_TYPES:
            is_default = model_value == default_value or \
                         self.__offline_default_numeric(model_value, model_type, default_value)
        elif model_type != alias_constants.PASSWORD:
            is_default = model_value == default_value
        _logger.finest('WLSDPLY-06773', Boolean(is_default),
                       class_name=_class_name, method_name=_method_name)
        return is_default

    def __convert_to_type(self, attribute_helper, attr_name, wlst_value):
        """
        Convert the provided value from WLST type to model type.
        :param attribute_helper: helper from which to retrieve the WLST attribute type
        :param attr_name: attribute name
        :param wlst_value: WLST value to convert for model
        :return: converted value
        """
        _method_name = '__convert_to_type'
        mbean_string = attribute_helper.mbean_string()
        attr_type = attribute_type(attribute_helper, attr_name)
        _logger.finest('WLSDPLY-06763', mbean_string, attr_name, attr_type,
                       class_name=_class_name, method_name=_method_name)

        if attribute_helper.is_clear_text_encrypted(attr_name):
            _logger.fine('WLSDPLY-06777', mbean_string, attr_name,
                         class_name=_class_name, method_name=_method_name)
            converted_type = None
            converted = None
        else:
            if wlst_value == 'unknown':
                wlst_value = attribute_helper.get_value(attr_name)
            converted_type, converted = self.convert(wlst_value, attr_type)

        return converted_type, converted

    def __get_default_value(self, attribute_helper, attribute_name):
        """
        Retrieve the default value for the attribute through the attribute helper.
        :param attribute_helper: Helper to generically provide attribute information
        :param attribute_name: Name of the attribute from which to retrieve the default value
        :return: default value converted to model type
        """
        _method_name = '__get_default_value'
        default = attribute_helper.get_default_value(attribute_name)
        _logger.finest('WLSDPLY-06762', attribute_helper.mbean_string(), attribute_name, default,
                       class_name=_class_name, method_name=_method_name)
        converted_default = None
        if not is_empty(default):
            __, converted_default = self.__convert_to_type(attribute_helper, attribute_name, default)
        return converted_default

    def __offline_default(self, model_value, model_type, default_value):
        _method_name = '__offline_default'
        if self._model_context.is_wlst_offline() and is_empty(model_value) and not is_empty(default_value):
            _logger.fine('WLSDPLY-06775', model_type, str_helper.to_string(model_value),
                         str_helper.to_string(default_value), class_name=_class_name, method_name=_method_name)
            return True
        return False

    def __offline_default_numeric(self, model_value, model_type, default_value):
        _method_name = '__offline_default_numeric'
        if self._model_context.is_wlst_offline() and \
                (model_value is None or model_value == 0) and default_value != 0:
            _logger.fine('WLSDPLY-06775', model_type, str_helper.to_string(model_value),
                         str_helper.to_string(default_value), class_name=_class_name, method_name=_method_name)
            return True
        return False

    def __inject_token(self, location, model_section, attribute_name):
        if self._credential_injector is not None:
            if model_section[attribute_name] == alias_constants.PASSWORD_TOKEN:
                self._credential_injector.custom_injection(model_section, attribute_name, location,
                                                           STANDARD_PASSWORD_INJECTOR)


def equal_dictionary(dict1, dict2):
    if dict1 is not None and dict2 is not None:
        dict1_keys = dict1.keys()
        if equal_lists(dict1_keys, dict2.keys()):
            for key in dict1_keys:
                if dict1[key] != dict2[key]:
                    return False
            return True
    return False


def equal_lists(list1, list2):
    """
    Compare the two lists for values that are in the first or second but not both
    :param list1: first list of values
    :param list2: second list of values
    :return: True if all values in each list are in the other list
    """
    if list1 is not None and list2 is not None and len(list1) == len(list2):
        return (len([item for item in list1 if item not in list2]) +
                len([item for item in list2 if item not in list1])) == 0
    return False


def equal_jarrays(array1, array2):
    """
    Compare the two jarrays for values that are in the first or second but not both
    :param array1: first jarray of values
    :param array2: second jarray of values
    :return: True if the values in the first jarray are the exact values in the second jarray
    """
    if len(array1) == len(array2):
        for item1 in array1:
            found = False
            for item2 in array2:
                if item1 == item2:
                    found = True
                    break
            if not found:
                return False
        return True
    return False


def security_provider_interface_name(mbean_instance, mbean_interface_name):
    """
    Return the name that is used to look up the custom Security Provider MBeanInfo.

    This is too tightly coupled to be in this class.
    This needs something more to differentiate Security Provider Interface which is formatted differently from other
    custom MBean Interface names.
    :param mbean_instance: instance for the current custom MBean
    :param mbean_interface_name: interface for the MBean
    :return: provider class name returned from the massaged MBean name
    """
    _method_name = 'security_provider_interface_name'
    try:
        getter = getattr(mbean_instance, 'getProviderClassName')
        result = getter()
        if result.endswith('ProviderMBean'):
            result = mbean_interface_name
            _logger.warning('WLSDPLY-06779', str_helper.to_string(mbean_instance),
                            class_name=_class_name, method_name=_method_name)
    except (Exception, JException):
        _logger.warning('WLSDPLY-06778', mbean_interface_name, class_name=_class_name, method_name=_method_name)
        result = mbean_interface_name
    idx = result.rfind('MBean')
    if idx > 0:
        result = result[:idx]
    return result


def attribute_type(attribute_helper, attribute_name):
    """
    Use the attribute helper to return the attribute type.
    :param attribute_helper: wrapper Class is a helper to extract attribute information
    :param attribute_name: name of the attribute to type
    :return: data type of the attribute
    """
    attr_type = None
    check_type = attribute_helper.get_type(attribute_name)
    if check_type is not None:
        attr_type = str_helper.to_string(check_type)
    return attr_type


def create_enumeration_list(enumeration):
    """
    The attribute value is a Java Enumeration class. Convert the iterable to string values.
    :param enumeration: Enumeration iterable
    :return: string list of values
    """
    enumeration_list = list()
    if not is_empty(enumeration):
        while enumeration.hasMoreElements():
            enumeration_list.append(enumeration.nextElement())
    return enumeration_list


def convert_numeric(class_type, number):
    """
    Convert the numeric to appropriate model value using the Java Class representing the number.
    :param class_type: Java Class to convert into a model type
    :param number: value to be converted
    :return: model value from WLST value
    """
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
    _method_name = 'convert_big_integer'
    converted_type = alias_constants.LONG
    converted = None
    if value is not None:
        try:
            converted = BigInteger(value).longValue()
        except NumberFormatException, nfe:
            _logger.fine('WLSDPLY-06774', value, type(value), nfe.getMessage(),
                         class_name=_class_name, method_name=_method_name)
    return converted_type, converted


def is_empty(value):
    """
    Determine if the provided value is empty.
    :param value: attribute value to test for empty
    :return: True if the attribute does not contain a value
    """
    return value is None or (type(value) in [list, dict] and len(value) == 0) or \
        ((isinstance(value, basestring) or isinstance(value, String)) and
            (len(value) == 0 or value == '[]' or value == 'null' or value == 'None'))


def convert_string(value):
    """
    Convert the provided value to a python string.
    :param value: value to convert to string
    :return: string form of value or None if the value does not contain a value
    """
    converted = None
    if not is_empty(value):
        converted = str_helper.to_string(value)
    return converted


def convert_boolean(boolean_value):
    if boolean_value is not None:
        return Boolean(boolean_value).toString()
    return None


def convert_byte_buffer(buffer_value):
    if buffer_value is not None:
        return str_helper.to_string(String(buffer_value))
    return None


def create_array(iterable):
    """
    Create an array from the jarray or list objects.
    :param iterable: a List object or other iterable type
    :return: an array or a string containing the converted contents from the provided iterable
    """
    my_array = None
    if is_iterable(iterable):
        my_array = list()
        for element in iterable:
            __, converted = convert_value(element)
            my_array.append(converted)
    elif iterable is None:
        my_array = list()
    return my_array


def create_dictionary(value):
    """
    Convert the value that is a dict, properties or map type to a python dictionary.
    :param value: value to be converted to python dictionary
    :return: python dictionary of key, value from original type
    """
    my_dict = PyOrderedDict()
    if not is_empty(value):
        if isinstance(value, dict) or isinstance(value, PyOrderedDict):
            for key, item in value.items():
                my_dict[key] = item
        elif isinstance(value, Properties):
            for key in value.stringPropertyNames():
                my_dict[key] = value.getProperty(key)
        elif isinstance(value, Map):
            for result in value.entrySet():
                my_dict[result.getKey()] = result.getValue()
    return my_dict


def convert_value(value):
    """
    Convert the value that does not have a well known data type with the information directly from the value.
    Select the appropriate data type from the conversion.
    :param value: value to convert which does not have well-known converted value
    :return: converted value and type of the converted value
    """
    converted = None
    converted_type = None
    if not is_empty(value):
        if isinstance(value, ObjectName):
            converted_type = alias_constants.STRING
            converted = value.getKeyProperty('Name')
        elif isinstance(value, String):
            converted_type = alias_constants.STRING
            converted = str_helper.to_string(value)
        elif isinstance(value, Enum):
            converted_type = alias_constants.STRING
            converted = str_helper.to_string(value.toString())
        else:
            converted_type = alias_constants.OBJECT
            converted = value
    return converted_type, converted


def is_iterable(iterable):
    """
    Determine if the provided object is an iterable type.
    :param iterable: Object to test
    :return: True if the object is an instance of an iterable data type
    """
    try:
        iter(iterable)
        return True
    except TypeError:
        return False
