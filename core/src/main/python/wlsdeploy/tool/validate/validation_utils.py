"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import re
import types

from java.io import IOException
from java.io import FileInputStream
from java.lang import IllegalArgumentException
from java.util import Properties

from oracle.weblogic.deploy.exception import ExceptionHelper
from oracle.weblogic.deploy.validate import ValidateException

from wlsdeploy.exception import exception_helper

divider_string = '-----------------------------------------------'

_class_name = "validation_utils"
_variable_pattern = re.compile('\$\{[\w.-]+\}')
_path_token_pattern = re.compile('@@[\w._]+@@')


def load_model_variables_file_properties(variable_properties_file, logger):
    """

    :param variable_properties_file:
    :param logger:
    :return:
    """
    _method_name = 'load_model_variables_file_properties'

    variable_properties = Properties()

    try:
        prop_inputstream = FileInputStream(variable_properties_file)
        variable_properties.load(prop_inputstream)
        prop_inputstream.close()
        variable_properties = __expand_model_variable_properties(variable_properties,
                                                                 variable_properties_file,
                                                                 logger)
    except (IOException, IllegalArgumentException), e:
        ex = exception_helper.create_validate_exception('WLSDPLY-01730', variable_properties_file,
                                                        e.getLocalizedMessage(), error=e)
        logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    except ValidateException:
        # This ValidationException is thrown by __expand_model_variable_properties(). Later,
        # there will be code that handles these in a "context-driven" way, but for now just
        # catch and ignore them. This is okay because the calling code performs substitution
        # variable validation, which will create validation ERROR messages for the situation
        # that caused the exception.
        pass

    return variable_properties


def __expand_model_variable_properties(loaded_properties, variable_properties_file, logger):
    """

    :param loaded_properties:
    :param variable_properties_file:
    :param logger:
    :return:
    """

    _method_name = '__expand_model_variable_properties'

    expanded_properties = Properties()
    property_names = loaded_properties.stringPropertyNames()

    # Loop through all the properties looking for variable expressions
    for property_name in property_names:
        property_value = loaded_properties.get(property_name)
        if '${' in property_value and '}' in property_value:
            # property_value contains a variable expression, so extract
            # the tokens
            tokens = extract_substitution_tokens(property_value)
            logger.finer('tokens={0}', str(tokens),
                         class_name=_class_name, method_name=_method_name)
            # Loop through all the tokens
            for token in tokens:
                variable_name = token[2:len(token)-1]
                # Attempt to get valiable value from properties
                variable_value = loaded_properties.get(variable_name)
                logger.finer('variable_name={0}, variable_value={1}',
                             variable_name, variable_value,
                             class_name=_class_name, method_name=_method_name)

                if variable_value is not None:
                    # Found variable_name in the properties, so add variable_name
                    # and variable_value to expanded_properties
                    property_value = property_value.replace(token, variable_value)
                    expanded_properties.setProperty(property_name, property_value)
                else:
                    # variable_name wasn't in properties, so throw an exception
                    ex = exception_helper.create_validate_exception('WLSDPLY-05300',
                                                                    variable_name,
                                                                    variable_properties_file)
                    logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                    raise ex

        else:
            # property_value didn't contain a variable expression, so just
            # add variable_name and variable value to expanded_properties
            expanded_properties.setProperty(property_name, property_value)

    return expanded_properties


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
    tokens = re.findall(_variable_pattern, str(tokenized_value))
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
        retval = (actual_data_type in ["<type 'int'>", "<type 'str'>"])
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
