"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import os
import re

from java.lang import Boolean
from java.io import BufferedReader
from java.io import File
from java.io import FileInputStream
from java.io import FileOutputStream
from java.io import FileReader
from java.io import IOException
from java.util import Properties

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.util import path_utils
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging import platform_logger

_class_name = "variables"
_logger = platform_logger.PlatformLogger('wlsdeploy.variables')
_variable_pattern = re.compile("\\$\\{[\w.-]+\\}")
_file_variable_pattern = re.compile("@@FILE:[\w.\\\/:-]+@@")
_property_pattern = re.compile("@@PROP:[\w.-]+@@")
_file_nested_variable_pattern = re.compile("@@FILE:@@[\w]+@@[\w.\\\/:-]+@@")


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


def write_variables(program_name, variable_map, file_path, append=False):
    """
    Write the dictionary of variables to the specified file.
    :param program_name: name of tool that invoked the method which will be written to the variable properties file
    :param variable_map: the dictionary of variables
    :param file_path: the file to which to write the properties
    :param append: defaults to False. Append properties to the end of file
    :raises VariableException if an error occurs while storing the variables in the file
    """
    _method_name = 'write_variables'
    _logger.entering(program_name, file_path, append, class_name=_class_name, method_name=_method_name)
    props = Properties()
    for key in variable_map:
        value = variable_map[key]
        props.setProperty(key, value)

    comment = exception_helper.get_message('WLSDPLY-01731', program_name)
    output_stream = None
    try:
        output_stream = FileOutputStream(File(file_path), Boolean(append))
        props.store(output_stream, comment)
        output_stream.close()
    except IOException, ioe:
        ex = exception_helper.create_variable_exception('WLSDPLY-20007', file_path,
                                                        ioe.getLocalizedMessage(), error=ioe)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        if output_stream is not None:
            output_stream.close()
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def get_default_variable_file_name(model_context):
    """
    Generate location and file name for the variable file.
    If model file is present, use the model file name and location;
    else, use the archive file name and location.
    :param model_context: contains the model and archive file arguments
    :return: location and file name of variable properties file.
    """
    _method_name = 'get_default_variable_file_name'
    extract_file_name = model_context.get_model_file()
    if not extract_file_name:
        extract_file_name = model_context.get_archive_file_name()
    default_variable_file = path_utils.get_filename_no_ext_from_path(extract_file_name)
    if default_variable_file:
        default_variable_file = os.path.join(path_utils.get_pathname_from_path(extract_file_name),
                                             default_variable_file + '.properties')
        _logger.finer('WLSDPLY-01736', default_variable_file, class_name=_class_name, method_name=_method_name)
    return default_variable_file


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

    if '@@' in text:
        tokens = _property_pattern.findall(text)
        if tokens:
            for token in tokens:
                names.append(token[7:-2])

    return names


def substitute(dictionary, variables, model_context):
    """
    Substitute fields in the specified dictionary with variable values.
    :param dictionary: the dictionary in which to substitute variables
    :param variables: a dictionary of variables for substitution
    :param model_context: used to resolve variables in file paths
    """
    _process_node(dictionary, variables, model_context)


def _process_node(nodes, variables, model_context):
    """
    Process variables in the node.
    :param nodes: the dictionary to process
    :param variables: the variables to use
    :param model_context: used to resolve variables in file paths
    """
    # iterate over copy to avoid concurrent change for add/delete
    if type(nodes) is OrderedDict:
        nodes_iterator = OrderedDict(nodes)
    else:
        nodes_iterator = dict(nodes)
    for key in nodes_iterator:
        value = nodes[key]

        # if the key changes with substitution, remove old key and map value to new key
        new_key = _substitute(key, variables, model_context)
        if new_key is not key:
            nodes.pop(key)
            nodes[new_key] = value

        if isinstance(value, dict):
            _process_node(value, variables, model_context)
        elif type(value) is str:
            nodes[key] = _substitute(value, variables, model_context)


def _substitute(text, variables, model_context):
    """
    Substitute the variable placeholders with the variable value.
    :param text: the text to process for variable placeholders
    :param variables: the variables to use
    :param model_context: used to resolve variables in file paths
    :return: the replaced text
    """
    method_name = '_substitute'

    if '${' in text:
        tokens = _variable_pattern.findall(text)
        if tokens:
            for token in tokens:
                key = token[2:-1]
                # for ${key} variables, leave them in place if not defined.
                # there are cases where WebLogic allows ${key} values, such as server templates.
                # ${key} substitution is deprecated, so log if replacement occurs.
                if key in variables:
                    value = variables[key]
                    text = text.replace(token, value)
                    _logger.info('WLSDPLY-01735', token, key, method_name=method_name, class_name=_class_name)

    # skip lookups for text with no @@
    if '@@' in text:

        # do properties first, to cover the case @@FILE:/dir/@@PROP:name@@.txt@@
        tokens = _property_pattern.findall(text)
        if tokens:
            for token in tokens:
                key = token[7:-2]
                # for @@PROP:key@@ variables, throw an exception if key is not found.
                if key not in variables:
                    ex = exception_helper.create_variable_exception('WLSDPLY-01732', key)
                    _logger.throwing(ex, class_name=_class_name, method_name=method_name)
                    raise ex
                value = variables[key]
                text = text.replace(token, value)

        tokens = _file_variable_pattern.findall(text)
        if tokens:
            for token in tokens:
                path = token[7:-2]
                value = _read_value_from_file(path)
                text = text.replace(token, value)

        # special case for @@FILE:@@ORACLE_HOME@@/dir/name.txt@@
        tokens = _file_nested_variable_pattern.findall(text)
        if tokens:
            for token in tokens:
                path = token[7:-2]
                path = model_context.replace_token_string(path)
                value = _read_value_from_file(path)
                text = text.replace(token, value)

    return text


def _read_value_from_file(file_path):
    """
    Read a single text value from the first line in the specified file.
    :param file_path: the file from which to read the value
    :return: the text value
    :raises BundleAwareException if an error occurs while reading the value
    """
    method_name = '_read_value_from_file'

    try:
        file_reader = BufferedReader(FileReader(file_path))
        line = file_reader.readLine()
        file_reader.close()
    except IOException, e:
        ex = exception_helper.create_variable_exception('WLSDPLY-01733', file_path, e.getLocalizedMessage(), error=e)
        _logger.throwing(ex, class_name=_class_name, method_name=method_name)
        raise ex

    if line is None:
        ex = exception_helper.create_variable_exception('WLSDPLY-01734', file_path)
        _logger.throwing(ex, class_name=_class_name, method_name=method_name)
        raise ex

    return str(line).strip()
