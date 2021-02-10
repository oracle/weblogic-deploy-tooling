"""
Copyright (c) 2017, 2021, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

This module provides string manipulation helper methods that are not found in the WLST version of Jython
"""
import java.lang.String as JString
import java.util.Properties as Properties
import java.io.FileInputStream as FileInputStream
import java.io.IOException as IOException

import wlsdeploy.exception.exception_helper as exception_helper

from wlsdeploy.logging.platform_logger import PlatformLogger

__logger = PlatformLogger('wlsdeploy.util')
_class_name = 'string_utils'

STANDARD_VERSION_NUMBER_PLACES = 5


def is_empty(text):
    """
    Determine if a string value is either None or an empty string.
    :param text: the string to test
    :return: True, if the string has no content, False otherwise
    """
    return text is None or len(text) == 0


def rsplit(text, token=' ', maxsplit=-1):
    """
    Returns a list of the words in the provided string, separated by the delimiter string (starting from right).
    :param text: the string should be rsplit
    :param token: token dividing the string into split groups; default is space.
    :param maxsplit: Number of splits to do; default is -1 which splits all the items.
    :return: list of string elements
    """
    if maxsplit == 0:
        result = [text]
    else:
        components = text.split(token)
        if maxsplit > 0:
            desired_length = maxsplit + 1
            result = []
            if len(components) > desired_length:
                result.append('')
                for index, value in enumerate(components):
                    if index < len(components) - maxsplit:
                        if index > 0:
                            result[0] += token
                        result[0] += value
                    else:
                        result.append(value)
        else:
            result = components
    return result


def to_boolean(input_value):
    """
    Convert the input value to a proper boolean value.
    :param input_value: the value to convert
    :return: the corresponding boolean value, or False if the value is not convertible to a boolean
    """
    _method_name = 'to_boolean'

    if input_value in ['True', 'true', 1]:
        result = True
    elif input_value in ['False', 'false', 0]:
        result = False
    else:
        __logger.fine('WLSDPLY-01720', input_value, class_name=_class_name, method_name=_method_name)
        result = False
    return result


def load_properties(property_file, exception_type=None):
    """
    Load the key=value properties file into a Properties object
    and then store the properties in a dictionary.
    :param property_file: Name of the property file to read
    :param exception_type: Throw the indicated tool exception
    :raise Tool exception if exception type included, or IOException if None
    :return: property dictionary
    """
    _method_name = 'load_properties'
    prop_dict = dict()
    props = Properties()
    input_stream = None
    try:
        input_stream = FileInputStream(property_file)
        props.load(input_stream)
        input_stream.close()
    except IOException, ioe:
        if input_stream is not None:
            input_stream.close()
        if exception_type is None:
            raise ioe
        ex = exception_helper.create_exception(exception_type, 'WLSDPLY-01721', property_file,
                                               ioe.getLocalizedMessage(), error=ioe)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    for key in props.keySet():
        value = props.getProperty(key)
        prop_dict[key] = value

    return prop_dict


def is_weblogic_version_or_above(wls_version, str_version):
    """
    Is the provided version number equal to or greater than the version encapsualted by this version instance
    :param wls_version: the string representation of the current weblogic version
    :param str_version: the string representation of the version to be compared to the weblogic version
    :return: True if the provided version is equal or greater than the version represented by the wls_version argument
    """
    result = False
    array_version = str_version.split('.')
    array_wl_version = _get_wl_version_array(wls_version)

    len_compare = len(array_wl_version)
    if len(array_version) < len_compare:
        len_compare = len(array_version)

    idx = 0
    while idx < len_compare:
        compare_value = JString(array_version[idx]).compareTo(JString(array_wl_version[idx]))
        if compare_value < 0:
            result = True
            break
        elif compare_value > 0:
            result = False
            break
        elif idx + 1 == len_compare:
            result = True

        idx += 1

    return result


# We need to pad the actual version number for comparison purposes so
# that is is never shorter than the specified version.  Otherwise,
# actual version 12.2.1 will be considered to be equal to 12.2.1.1
#
def _get_wl_version_array(wl_version):
    """
    Get the WebLogic version number padded to the standard number of digits.
    :param wl_version: WebLogic version number
    :return: the padded WebLogic version number
    """
    result = wl_version.split('.')

    if len(result) < STANDARD_VERSION_NUMBER_PLACES:
        index = len(result)
        while index < STANDARD_VERSION_NUMBER_PLACES:
            result.append('0')
            index += 1

    return result