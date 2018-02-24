"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import re

from java.io import FileInputStream
from java.io import FileOutputStream
from java.io import IOException
from java.util import Properties

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging import platform_logger

_class_name = "variables"
_logger = platform_logger.PlatformLogger('wlsdeploy.variables')
_variable_pattern = re.compile("\\$\\{[\w.-]+\\}")


def load_variables(file_path):
    """
    Load a dictionary of variables from the specified file.
    :param file_path: the file from which to load properties
    :return the dictionary of variables
    :raises VariableException if an I/O error occurs while loading the variables from the file
    """
    method_name = "load_variables"

    variable_map = {}
    props = Properties()
    input_stream = None
    try:
        input_stream = FileInputStream(file_path)
        props.load(input_stream)
        input_stream.close()
    except IOException, ioe:
        ex = exception_helper.create_variable_exception('WLSDPLY-01730', file_path,
                                                        ioe.getLocalizedMessage(), error=ioe)
        _logger.throwing(ex, class_name=_class_name, method_name=method_name)
        if input_stream is not None:
            input_stream.close()
        raise ex

    for key in props.keySet():
        value = props.getProperty(key)
        variable_map[key] = value

    return variable_map


def write_variables(variable_map, file_path):
    """
    Write the dictionary of variables to the specified file.
    :param variable_map: the dictionary of variables
    :param file_path: the file to which to write the properties
    :raises VariableException if an error occurs while storing the variables in the file
    """
    method_name = 'write_variables'
    props = Properties()
    for key in variable_map:
        value = variable_map[key]
        props.setProperty(key, value)

    comment = exception_helper.get_message('WLSDPLY-01731')
    output_stream = None
    try:
        output_stream = FileOutputStream(file_path)
        props.store(output_stream, comment)
        output_stream.close()
    except IOException, ioe:
        ex = exception_helper.create_variable_exception('WLSDPLY-20007', file_path,
                                                        ioe.getLocalizedMessage(), error=ioe)
        _logger.throwing(ex, class_name=_class_name, method_name=method_name)
        if output_stream is not None:
            output_stream.close()
        raise ex
    return


def get_variable_names(text):
    """
    Get the list of variable names in the supplied text.
    :param text: the text to search for variables
    :return: a list of variable names
    """
    names = []
    if '${' in text:
        tokens = _variable_pattern.findall(text)
        if tokens is not None:
            for token in tokens:
                names.append(token[2:-1])
    return names


def substitute(dictionary, variables):
    """
    Substitute fields in the specified dictionary with variable values.
    :param dictionary: the dictionary in which to substitute variables
    :param variables: a dictionary of variables for substitution
    """
    _process_node(dictionary, variables)


def _process_node(nodes, variables):
    """
    Process variables in the node.
    :param nodes: the dictionary to process
    :param variables: the variables to use
    """
    # iterate over copy to avoid concurrent change for add/delete
    if type(nodes) is OrderedDict:
        nodes_iterator = OrderedDict(nodes)
    else:
        nodes_iterator = dict(nodes)
    for key in nodes_iterator:
        value = nodes[key]

        # if the key changes with substitution, remove old key and map value to new key
        new_key = _substitute(key, variables)
        if new_key is not key:
            nodes.pop(key)
            nodes[new_key] = value

        if isinstance(value, dict):
            _process_node(value, variables)
        elif type(value) is str:
            nodes[key] = _substitute(value, variables)


def _substitute(text, variables):
    """
    Substitute the variable placeholders with the variable value.
    :param text: the text to process for variable placeholders
    :param variables: the variables to use
    :return: the replaced text
    """
    method_name = '_substitute'

    if '${' in text:
        tokens = _variable_pattern.findall(text)
        if tokens:
            for token in tokens:
                key = token[2:-1]
                if key not in variables:
                    ex = exception_helper.create_variable_exception('WLSDPLY-01732', key)
                    _logger.throwing(ex, class_name=_class_name, method_name=method_name)
                    raise ex
                value = variables[key]
                text = text.replace(token, value)

    return text

