"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import java.util.Properties as JProperties

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict


def get_dictionary_element(dictionary, element_name):
    """
    Retrieve the value for the provided element name from the dictionary.
    Return empty dictionary if name is not in the dictionary.
    :param dictionary: to find the element name
    :param element_name: for which to retrieve the value
    :return: value from the dictionary
    """

    if element_name in dictionary:
        result = dictionary[element_name]
    elif type(dictionary) is OrderedDict:
        result = OrderedDict()
    else:
        result = dict()

    return result


def get_dictionary_attributes(dictionary):
    """
    Get the attributes and skip the dictionary attributes from the dictionary.
    :param dictionary: to return the skimmed down attribute list
    :return: list of attributes
    """
    result_list = OrderedDict()
    if dictionary:
        for key, value in dictionary.iteritems():
            if not isinstance(value, dict):
                result_list[key] = value
    return result_list


def is_empty_dictionary_element(dictionary, element_name):
    """
    Determine if the element in the dictionary for the element name is not present or empty.
    :param dictionary: containing element
    :param element_name: of the element in the dictionary
    :return: True if the element is not present, or is present and is empty
    """
    result = False
    if element_name in dictionary:
        if len(dictionary[element_name]) == 0:
            result = True
    else:
        result = True

    return result


def get_element(dictionary, element_name):
    """
    Retrieve the value for the provided element name from the dictionary.
    Return None if name is not in the dictionary.
    :param dictionary: to find the element name
    :param element_name: for which to retrieve the value
    :return: value from the dictionary
    """
    result = None
    if element_name in dictionary:
        result = dictionary[element_name]
    return result


def format_dictionary_element_name(parent, key):
    """
    Format a string representation dictionary and key formatted as <parent>['<key>'}
    :param parent: name of dictionary
    :param key: key to element in dictionary
    :return: string representation of element
    """
    return str(parent) + '[' + str(key) + ']'


def create_property_object(properties_string):
    """
    create a java Properties instance from a string properties.

    :param properties_string: semi-colon separated string of key=value properties
    :return: java Properties instance
    """
    result = JProperties()
    if properties_string is not None and len(properties_string) > 0:
        str_properties = properties_string.split(';')
        for str_property in str_properties:
            property_elements = str_property.split('=')
            result.setProperty(property_elements[0], property_elements[1])
    return result
