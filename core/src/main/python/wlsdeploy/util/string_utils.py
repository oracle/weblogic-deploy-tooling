"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

This module provides string manipulation helper methods that are not found in the WLST version of Jython
"""
import java.util.Properties as Properties
import java.io.FileInputStream as FileInputStream
import java.io.IOException as IOException

from oracle.weblogic.deploy.aliases import VersionUtils
import wlsdeploy.exception.exception_helper as exception_helper

from wlsdeploy.logging.platform_logger import PlatformLogger

__logger = PlatformLogger('wlsdeploy.util')
_class_name = 'string_utils'


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
    return VersionUtils.compareVersions(wls_version, str_version) >= 0
