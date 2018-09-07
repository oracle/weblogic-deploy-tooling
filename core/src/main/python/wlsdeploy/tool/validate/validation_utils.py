"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import re
import types

from oracle.weblogic.deploy.exception import ExceptionHelper

divider_string = '-----------------------------------------------'

_class_name = "validation_utils"
_variable_pattern = re.compile('\$\{[\w.-]+\}')
_property_pattern = re.compile('@@PROP:[\w.-]+@@')
_path_token_pattern = re.compile('@@[\w._]+@@')


def extract_path_tokens(tokenized_value):
    """
    Returns a Python list containing the path token expressions found in the
    tokenized_value argument

    :param tokenized_value:
    :return:
    """
    tokens = re.findall(_path_token_pattern, str(tokenized_value))
    if tokens is None:
        # tokenized_value didn't contain any variable expressions, so
        # return an empty list
        return []
    else:
        # tokenized_value contained at least 1 variable expressions, so
        # create a map of all the tokens and return the keys from that
        map_entry = {}
        map(map_entry.__setitem__, tokens, [])
        return map_entry.keys()


def format_message(key, *args):
    """

    :param key:
    :param args:
    :return:
    """
    return ExceptionHelper.getMessage(key, list(args))


def get_python_data_type(value):
    """
    Returns the aliases data type for a given Python object

    :param value: Python object to get the type for
    :return: A string stating the aliases data type
    """
    data_types_map = {
        types.StringType: 'string',
        types.IntType: 'integer',
        types.LongType: 'long',
        types.FloatType: 'float',
        types.DictionaryType: 'properties',
        "<type 'PyOrderedDict'>": 'properties',
        types.TupleType: 'list',
        types.ListType: 'list'
    }
    data_type = type(value)

    if data_type in data_types_map:
        rtnval = data_types_map[data_type]
    else:
        rtnval = data_type

    return rtnval


def get_properties(value):
    """
    Converts the specified value into a dict containing the NVPs (name-value pairs)

    :param value:
    :return:
    """
    rtnval = None
    if isinstance(value, dict):
        # value is already a Python dict, so just return it
        rtnval = value
    elif '=' in value:
        # value contains '=' character(s), so split on that to
        # come up with NVPs
        properties = value.split('=')
        if properties:
            rtnval = {properties[0]: properties[1]}

    if rtnval is None:
        # Couldn't tell what the delimiter used in value was, so just
        # return a dict with value as the value, and 'Value' as the key
        rtnval = {'Value': value}

    return rtnval


def extract_substitution_tokens(tokenized_value):
    """
    Returns a Python list containing the substitution variable expressions found in the
    tokenized_value argument

    :param tokenized_value:
    :return:
    """
    tokens = re.findall(_property_pattern, str(tokenized_value))
    if tokens is None:
        # tokenized_value didn't contain any variable expressions, so
        # return an empty list
        return []
    else:
        # tokenized_value contained at least 1 variable expressions, so
        # create a map of all the tokens and return the keys from that
        map_entry = {}
        map(map_entry.__setitem__, tokens, [])
        return map_entry.keys()


def is_compatible_data_type(expected_data_type, actual_data_type):
    """
    Returns boolean value indicating whether the actual_data_type argument is compatible
    with the expected_data_type, from a data typing perspective

    :param expected_data_type:
    :param actual_data_type:
    :return:
    """
    retval = False
    if expected_data_type == 'string':
        retval = (actual_data_type in ["<type 'str'>", "<type 'long'>"])
    elif expected_data_type == 'integer':
        retval = (actual_data_type in ["<type 'int'>", "<type 'long'>", "<type 'str'>"])
    elif expected_data_type == 'long':
        retval = (actual_data_type in ["<type 'int'>", "<type 'long'>", "<type 'str'>"])
    elif expected_data_type in ['boolean', 'java.lang.Boolean']:
        retval = (actual_data_type in ["<type 'int'>", "<type 'str'>", "<type 'long'>"])
    elif expected_data_type in ['float', 'double']:
        retval = (actual_data_type in ["<type 'float'>", "<type 'str'>"])
    elif expected_data_type == 'properties' or expected_data_type == 'dict':
        retval = (actual_data_type in ["<type 'PyOrderedDict'>", "<type 'dict'>", "<type 'str'>"])
    elif 'list' in expected_data_type:
        retval = (actual_data_type in ["<type 'list'>", "<type 'str'>"])
    elif expected_data_type in ['password', 'credential', 'jarray']:
        retval = (actual_data_type in ["<type 'str'>"])
    elif 'delimited_' in expected_data_type:
        retval = (actual_data_type in ["<type 'str'>", "<type 'list'>"])

    return retval


def print_indent(msg, level=1):
    """

    :param msg:
    :param level:
    :return:
    """
    result = ''
    i = 0
    while i < level:
        result += '  '
        i += 1
    print '%s%s' % (result, msg)
    return


def print_blank_lines(number=1):
    """

    :param number:
    :return:
    """
    i = 0
    while i < number:
        print
        i += 1

    return
