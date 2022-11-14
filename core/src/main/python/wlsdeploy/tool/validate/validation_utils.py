"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re
import types

from oracle.weblogic.deploy.exception import ExceptionHelper
import wlsdeploy.util.unicode_helper as str_helper

divider_string = '-----------------------------------------------'

_class_name = "validation_utils"
_path_token_pattern = re.compile('@@[\w.]+@@')

_type_str = "<type 'str'>"
_type_int = "<type 'int'>"
_type_long = "<type 'long'>"
_type_float = "<type 'float'>"
_type_unicode = "<type 'unicode'>"
_type_bool = "<type 'bool'>"
_type_py_real_boolean = "<type 'PyRealBoolean'>"
_type_orcl_py_real_boolean = "<type 'oracle.weblogic.deploy.util.PyRealBoolean'>"
_type_list = "<type 'list'>"
_type_dict = "<type 'dict'>"
_type_py_ordered_dict = "<type 'PyOrderedDict'>"
_type_orcl_py_ordered_dict = "<type 'oracle.weblogic.deploy.util.PyOrderedDict'>"

def extract_path_tokens(tokenized_value):
    """
    Returns a Python list containing the path token expressions found in the
    tokenized_value argument

    :param tokenized_value:
    :return:
    """
    path_pattern = _path_token_pattern
    path_value = tokenized_value
    if tokenized_value.isunicode():
        path_pattern = unicode(_path_token_pattern)
    elif not isinstance(tokenized_value, basestring):
        path_value = str_helper.to_string(tokenized_value)
    tokens = re.findall(path_pattern, path_value)
    if len(tokens) == 0:
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
        _type_unicode: 'unicode',
        types.IntType: 'integer',
        types.LongType: 'long',
        types.FloatType: 'float',
        types.DictionaryType: 'properties',
        _type_py_ordered_dict: 'properties',
        _type_py_real_boolean: 'boolean',
        _type_orcl_py_real_boolean: 'boolean',
        types.TupleType: 'list',
        types.ListType: 'list'
    }
    data_type = type(value)
    if data_type in data_types_map:
        rtnval = data_types_map[data_type]
    elif str_helper.to_string(data_type) in data_types_map:
        rtnval = data_types_map[str_helper.to_string(data_type)]
    else:
        rtnval = str_helper.to_string(data_type)

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


def is_compatible_data_type(expected_data_type, actual_data_type):
    """
    Returns boolean value indicating whether the actual_data_type argument is compatible
    with the expected_data_type, from a data typing perspective

    :param expected_data_type:
    :param actual_data_type:
    :return:
    """
    retval = False
    if expected_data_type in ['string', 'unicode']:
        retval = (actual_data_type in [_type_str, _type_int, _type_long, _type_float,
                                       _type_unicode, _type_bool, _type_py_real_boolean,
                                       _type_orcl_py_real_boolean])
    elif expected_data_type == 'integer':
        retval = (actual_data_type in [_type_int, _type_long, _type_str, _type_unicode])
    elif expected_data_type == 'long':
        retval = (actual_data_type in [_type_int, _type_long, _type_str, _type_unicode])
    elif expected_data_type in ['boolean', 'java.lang.Boolean']:
        retval = (actual_data_type in [_type_int, _type_str, _type_long, _type_unicode, _type_bool,
                                       _type_py_real_boolean, _type_orcl_py_real_boolean])
    elif expected_data_type in ['float', 'double']:
        retval = (actual_data_type in [_type_float, _type_str, _type_unicode])
    elif expected_data_type == 'properties' or expected_data_type == 'dict':
        retval = (actual_data_type in [_type_py_ordered_dict, _type_orcl_py_ordered_dict, _type_dict, _type_str])
    elif 'list' in expected_data_type:
        retval = (actual_data_type in [_type_list, _type_str, _type_unicode])
    elif expected_data_type in ['password', 'credential', 'jarray']:
        retval = (actual_data_type in [_type_str, _type_unicode])
    elif 'delimited_' in expected_data_type:
        retval = (actual_data_type in [_type_str, _type_list, _type_unicode])

    return retval
