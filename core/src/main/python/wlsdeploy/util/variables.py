"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import re

from java.lang import Boolean
from java.io import BufferedReader
from java.io import File
from java.io import FileOutputStream
from java.io import FileReader
from java.io import PrintWriter
from java.io import IOException

from oracle.weblogic.deploy.util import PyOrderedDict as OrderedDict

from wlsdeploy.util import path_utils
from wlsdeploy.util import string_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging import platform_logger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil

_class_name = "variables"
_logger = platform_logger.PlatformLogger('wlsdeploy.variables')
_file_variable_pattern = re.compile("(@@FILE:([\w.\\\/:-]+)@@)")
_property_pattern = re.compile("(@@PROP:([\\w.-]+)@@)")
_environment_pattern = re.compile("(@@ENV:([\\w.-]+)@@)")
_secret_pattern = re.compile("(@@SECRET:([\\w.-]+):([\\w.-]+)@@)")
_file_nested_variable_pattern = re.compile("(@@FILE:(@@[\w]+@@[\w.\\\/:-]+)@@)")

# these match a string containing ONLY a token
_property_string_pattern = re.compile("^(@@PROP:([\\w.-]+)@@)$")
_secret_string_pattern = re.compile("^(@@SECRET:([\\w.-]+):([\\w.-]+)@@)$")

# if this pattern is found, token substitution was incomplete
_unresolved_token_pattern = re.compile("(@@(PROP|FILE|ENV|SECRET):)")

_secret_dirs_variable = "WDT_MODEL_SECRETS_DIRS"
_secret_dir_pairs_variable = "WDT_MODEL_SECRETS_NAME_DIR_PAIRS"

_secret_token_map = None


def load_variables(file_path, allow_multiple_files=False):
    """
    Load a dictionary of variables from the specified file(s).
    :param file_path: the file from which to load properties
    :param allow_multiple_files: if True, allow a comma-separated list of variable files
    :return the dictionary of variables
    :raises VariableException if an I/O error occurs while loading the variables from the file
    """
    method_name = "load_variables"

    if allow_multiple_files:
        paths = file_path.split(CommandLineArgUtil.MODEL_FILES_SEPARATOR)
    else:
        paths = [file_path]

    variable_map = {}

    for path in paths:
        try:
            variable_map.update(string_utils.load_properties(path))
        except IOException, ioe:
            ex = exception_helper.create_variable_exception('WLSDPLY-01730', path, ioe.getLocalizedMessage(),
                                                            error=ioe)
            _logger.throwing(ex, class_name=_class_name, method_name=method_name)
            raise ex

    return variable_map


def write_variables(program_name, variable_map, file_path, append=False):
    """
    Write variables to file while preserving order of the variables.
    :param program_name: name of the calling program
    :param variable_map: map or variable properties to write to file
    :param file_path: the file to which to write the properties
    :param append: defaults to False. Append properties to the end of file
    :raises VariableException if an error occurs while storing the variables in the file
    """
    _method_name = 'write_variables'
    _logger.entering(program_name, file_path, append, class_name=_class_name, method_name=_method_name)
    pw = None
    try:
        pw = PrintWriter(FileOutputStream(File(file_path), Boolean(append)), Boolean('true'))
        for key, value in variable_map.iteritems():
            formatted = '%s=%s' % (key, value)
            pw.println(formatted)
        pw.close()
    except IOException, ioe:
        _logger.fine('WLSDPLY-20007', program_name, file_path, ioe.getLocalizedMessage())
        ex = exception_helper.create_variable_exception('WLSDPLY-20007', program_name, file_path,
                                                        ioe.getLocalizedMessage(), error=ioe)
        _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        if pw is not None:
            pw.close()
        raise ex
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def write_sorted_variables(program_name, variable_map, file_path, append=False):
    """
    Write the dictionary of variables to the specified file, in alphabetical order by key.
    :param program_name: name of tool that invoked the method which will be written to the variable properties file
    :param variable_map: the dictionary of variables
    :param file_path: the file to which to write the properties
    :param append: defaults to False. Append properties to the end of file
    :raises VariableException if an error occurs while storing the variables in the file
    """
    _method_name = 'write_sorted_variables'
    _logger.entering(program_name, file_path, append, class_name=_class_name, method_name=_method_name)

    sorted_keys = variable_map.keys()
    sorted_keys.sort()
    sorted_map = OrderedDict()
    for key in sorted_keys:
        sorted_map[key] = variable_map[key]

    write_variables(program_name, sorted_map, file_path, append)
    _logger.exiting(class_name=_class_name, method_name=_method_name)


def get_default_variable_file_name(model_context):
    """
    Generate location and file name for the variable file.
    If model file is present, use the model file name and location;
    else, use the archive file name and location.
    :param model_context: contains the model and archive file arguments
    :return: location and file name of variable properties file.
    """
    _method_name = 'get_default_variable_file_name'

    if model_context.get_target() is not None:
        default_variable_file = os.path.join(model_context.get_output_dir(), model_context.get_target() +
                                             "_variable.properties")
    else:
        extract_file_name = model_context.get_model_file()
        if not extract_file_name:
            extract_file_name = model_context.get_archive_file_name()
        default_variable_file = path_utils.get_filename_no_ext_from_path(extract_file_name)

        if default_variable_file:
            default_variable_file = os.path.join(path_utils.get_pathname_from_path(extract_file_name),
                                                 default_variable_file + '.properties')
    if default_variable_file:
        _logger.finer('WLSDPLY-01736', default_variable_file, class_name=_class_name, method_name=_method_name)

    return default_variable_file


def get_variable_names(text):
    """
    Get the list of variable names in the supplied text.
    :param text: the text to search for variables
    :return: a list of variable names
    """
    names = []
    if '@@' in text:
        matches = _property_pattern.findall(text)
        for token, key in matches:
            names.append(key)

    return names


def substitute_value(text, variables, model_context):
    """
    Perform token substitutions on a single text value.
    If errors occur during substitution, throw a single VariableException.
    :param text: the original text
    :param variables: a dictionary of variables for substitution
    :param model_context: used to resolve variables in file paths
    """
    method_name = 'substitute_value'
    error_info = {'errorCount': 0}
    result = _substitute(text, variables, model_context, error_info)
    error_count = error_info['errorCount']
    if error_count:
        ex = exception_helper.create_variable_exception("WLSDPLY-01740", error_count)
        _logger.throwing(ex, class_name=_class_name, method_name=method_name)
        raise ex
    return result


def substitute(dictionary, variables, model_context):
    """
    Substitute fields in the specified dictionary with variable values.
    If errors occur during substitution, throw a single VariableException.
    :param dictionary: the dictionary in which to substitute variables
    :param variables: a dictionary of variables for substitution
    :param model_context: used to resolve variables in file paths
    """
    method_name = '_substitute'
    error_info = {'errorCount': 0}
    _process_node(dictionary, variables, model_context, error_info)
    error_count = error_info['errorCount']
    if error_count:
        ex = exception_helper.create_variable_exception("WLSDPLY-01740", error_count)
        _logger.throwing(ex, class_name=_class_name, method_name=method_name)
        raise ex


def _process_node(nodes, variables, model_context, error_info):
    """
    Process variables in the node.
    :param nodes: the dictionary to process
    :param variables: the variables to use
    :param model_context: used to resolve variables in file paths
    :param error_info: collects information about errors encountered
    """
    # iterate over copy to avoid concurrent change for add/delete
    if isinstance(nodes, OrderedDict):
        nodes_iterator = OrderedDict(nodes)
    else:
        nodes_iterator = dict(nodes)
    for key in nodes_iterator:
        value = nodes[key]

        # if the key changes with substitution, remove old key and map value to new key
        new_key = _substitute(key, variables, model_context, error_info)
        if new_key is not key:
            del nodes[key]
            nodes[new_key] = value

        if isinstance(value, dict):
            _process_node(value, variables, model_context, error_info)

        elif isinstance(value, list):
            for member in value:
                if type(member) in [str, unicode]:
                    index = value.index(member)
                    value[index] = _substitute(member, variables, model_context, error_info, key)

        elif type(value) in [str, unicode]:
            nodes[key] = _substitute(value, variables, model_context, error_info, key)


def _substitute(text, variables, model_context, error_info, attribute_name=None):
    """
    Substitute token placeholders with their derived values.
    :param text: the text to process for token placeholders
    :param variables: the variables to use
    :param model_context: used to determine the validation method (strict, lax, etc.)
    :param error_info: collects information about errors encountered
    :return: the replaced text
    """
    method_name = '_substitute'
    validation_config = model_context.get_validate_configuration()
    problem_found = False

    # skip lookups for text with no @@
    if '@@' in text:

        # do properties first, to cover the case @@FILE:/dir/@@PROP:name@@.txt@@
        matches = _property_pattern.findall(text)
        for token, key in matches:
            # log, or throw an exception if key is not found.
            if key not in variables:
                allow_unresolved = validation_config.allow_unresolved_variable_tokens()
                if model_context.get_variable_file() is not None:
                    _report_token_issue('WLSDPLY-01732', method_name, allow_unresolved, key)
                else:
                    _report_token_issue('WLSDPLY-01734', method_name, allow_unresolved, key)

                _increment_error_count(error_info, allow_unresolved)
                problem_found = True
                continue

            value = variables[key]
            text = text.replace(token, value)

        # check environment variables before @@FILE:/dir/@@ENV:name@@.txt@@
        matches = _environment_pattern.findall(text)
        for token, key in matches:
            if str_helper.to_string(key) not in os.environ:
                allow_unresolved = validation_config.allow_unresolved_environment_tokens()
                _report_token_issue('WLSDPLY-01737', method_name, allow_unresolved, key)
                _increment_error_count(error_info, allow_unresolved)
                problem_found = True
                continue
            value = os.environ.get(str_helper.to_string(key))
            text = text.replace(token, value)

        # check secret variables before @@FILE:/dir/@@SECRET:name:key@@.txt@@
        matches = _secret_pattern.findall(text)
        for token, name, key in matches:
            value = _resolve_secret_token(name, key, model_context)
            if value is None:
                # does not match, only report for non target case
                allow_unresolved = validation_config.allow_unresolved_environment_tokens()
                secret_token = name + ':' + key
                known_tokens = _list_known_secret_tokens()
                _report_token_issue('WLSDPLY-01739', method_name, allow_unresolved, secret_token, known_tokens)
                _increment_error_count(error_info, allow_unresolved)
                problem_found = True
                continue
            text = text.replace(token, value)

        matches = _file_variable_pattern.findall(text)
        for token, path in matches:
            allow_unresolved = validation_config.allow_unresolved_file_tokens()
            value = _read_value_from_file(path, allow_unresolved)
            if value is None:
                _increment_error_count(error_info, allow_unresolved)
                problem_found = True
                continue
            text = text.replace(token, value)

        # special case for @@FILE:@@ORACLE_HOME@@/dir/name.txt@@
        matches = _file_nested_variable_pattern.findall(text)
        for token, path in matches:
            path = model_context.replace_token_string(path)
            allow_unresolved = validation_config.allow_unresolved_file_tokens()
            value = _read_value_from_file(path, allow_unresolved)
            if value is None:
                _increment_error_count(error_info, allow_unresolved)
                problem_found = True
                continue
            text = text.replace(token, value)

        # if any @@TOKEN: remains in the value, log an error.
        # if previous problems were found, don't perform this check.
        matches = _unresolved_token_pattern.findall(text)
        if matches and not problem_found:
            match = matches[0]
            token = match[1]
            sample = "@@" + token + ":<name>"
            if token == "SECRET":
                sample += ":<key>"
            sample += "@@"

            # always log SEVERE, these are syntax errors in the value
            allow_unresolved = False
            if attribute_name is None:
                _report_token_issue("WLSDPLY-01745", method_name, allow_unresolved, text, sample)
            else:
                _report_token_issue("WLSDPLY-01746", method_name, allow_unresolved, attribute_name, text, sample)
                _increment_error_count(error_info, allow_unresolved)

    return text


def _increment_error_count(error_info, allow_unresolved):
    if not allow_unresolved:
        error_info['errorCount'] = error_info['errorCount'] + 1


def _read_value_from_file(file_path, allow_unresolved):
    """
    Read a single text value from the first line in the specified file.
    :param file_path: the file from which to read the value
    :param allow_unresolved: if True, log INFO instead of SEVERE for lookup failures
    :return: the text value
    :raises BundleAwareException if an error occurs while reading the value
    """
    method_name = '_read_value_from_file'

    try:
        file_reader = BufferedReader(FileReader(file_path))
        line = file_reader.readLine()
        file_reader.close()
    except IOException, e:
        _report_token_issue('WLSDPLY-01733', method_name, allow_unresolved, file_path, e.getLocalizedMessage())
        return None

    if line is None:
        line = ''

    return str_helper.to_string(line).strip()


def _resolve_secret_token(name, key, model_context):
    """
    Return the value associated with the specified secret name and key.
    If the name and key are found in the directory map, return the associated value.
    :param name: the name of the secret (a directory name or mapped name)
    :param key: the name of the file containing the secret
    :param model_context: used to determine the validation method (strict, lax, etc.)
    :return: the secret value, or None if it is not found
    """
    global _secret_token_map

    if _secret_token_map is None:
        _init_secret_token_map(model_context)

    secret_token = name + ':' + key
    return dictionary_utils.get_element(_secret_token_map, secret_token)


def _init_secret_token_map(model_context):
    """
    Initialize a global map of name/value tokens to secret values.
    The map includes secrets found below the directories specified in WDT_MODEL_SECRETS_DIRS,
    and in WDT_MODEL_SECRETS_NAME_DIR_PAIRS assignments.
    :param model_context: used to determine the validation method (strict, lax, etc.)
    """
    method_name = '_init_secret_token_map'
    global _secret_token_map

    log_method = _logger.warning
    if model_context.get_validate_configuration().allow_unresolved_secret_tokens():
        log_method = _logger.info

    _secret_token_map = dict()

    # add name/key pairs for files in sub-directories of directories in WDT_MODEL_SECRETS_DIRS.

    locations = os.environ.get(str_helper.to_string(_secret_dirs_variable), None)
    if locations is not None:
        for secret_dir in locations.split(","):
            if not os.path.isdir(secret_dir):
                # log at WARN or INFO, but no exception is thrown
                log_method('WLSDPLY-01738', _secret_dirs_variable, secret_dir, class_name=_class_name,
                           method_name=method_name)
                continue

            for subdir_name in os.listdir(secret_dir):
                subdir_path = os.path.join(secret_dir, subdir_name)
                if os.path.isdir(subdir_path):
                    _add_file_secrets_to_map(subdir_path, subdir_name, model_context)

    # add name/key pairs for files in directories assigned in WDT_MODEL_SECRETS_NAME_DIR_PAIRS.
    # these pairs will override if they were previously added as sub-directory pairs.

    dir_pairs_text = os.environ.get(str_helper.to_string(_secret_dir_pairs_variable), None)
    if dir_pairs_text is not None:
        dir_pairs = dir_pairs_text.split(',')
        for dir_pair in dir_pairs:
            result = dir_pair.split('=')
            if len(result) != 2:
                log_method('WLSDPLY-01735', _secret_dir_pairs_variable, dir_pair, class_name=_class_name,
                           method_name=method_name)
                continue

            secret_dir = result[1]
            if not os.path.isdir(secret_dir):
                log_method('WLSDPLY-01738', _secret_dir_pairs_variable, secret_dir, class_name=_class_name,
                           method_name=method_name)
                continue

            name = result[0]
            _add_file_secrets_to_map(secret_dir, name, model_context)


def _clear_secret_token_map():
    """
    Used by unit tests to force reload of map.
    """
    global _secret_token_map
    _secret_token_map = None


def _add_file_secrets_to_map(dir, name, model_context):
    """
    Add the secret from each file in the specified directory to the map.
    :param dir: the directory to be examined
    :param name: the name to be used in the map token
    :param model_context: used to determine the validation method (strict, lax, etc.)
    """
    global _secret_token_map

    for file_name in os.listdir(dir):
        file_path = os.path.join(dir, file_name)
        if os.path.isfile(file_path):
            token = name + ":" + file_name
            allow_unresolved = model_context.get_validate_configuration().allow_unresolved_secret_tokens()
            _secret_token_map[token] = _read_value_from_file(file_path, allow_unresolved)


def _list_known_secret_tokens():
    """
    Returns a string representation of the available secret name/path tokens.
    """
    global _secret_token_map

    keys = list(_secret_token_map.keys())
    keys.sort()

    ret = ''
    for key in keys:
        if ret != '':
            ret += ', '
        ret += "'" + key + "'"
    return ret


def _report_token_issue(message_key, method_name, allow_unresolved, *args):
    """
    Log a message at the level corresponding to the validation method (SEVERE for strict, INFO otherwise).
    The lax validation method can be used to verify the model without resolving tokens.
    :param message_key: the message key to be logged and used for exceptions
    :param method_name: the name of the calling method for logging
    :param allow_unresolved: if True, log INFO instead of SEVERE for lookup failures
    :param args: arguments for use in the message
    """
    log_method = _logger.severe
    if allow_unresolved:
        log_method = _logger.info

    log_method(message_key, class_name=_class_name, method_name=method_name, *args)


def substitute_key(text, variables):
    """
    Substitute any @@PROP values in the text and return.
    If the corresponding variable is not found, leave the @@PROP value in place.
    :param text: the text to be evaluated
    :param variables: the variable map
    :return: the substituted text value
    """
    if variables is not None:
        matches = _property_pattern.findall(text)
        for token, key in matches:
            if key in variables:
                value = variables[key]
                text = text.replace(token, value)

    matches = _environment_pattern.findall(text)
    for token, key in matches:
        # log, or throw an exception if key is not found.
        if str_helper.to_string(key) not in os.environ:
            continue

        value = os.environ.get(str_helper.to_string(key))
        text = text.replace(token, value)

    return text


def has_variables(text):
    """
    Determine if the specified text contains any variable references.
    :param text: the text to be evaluated
    :return: True if the text contains variable references, False otherwise
    """
    matches = _property_pattern.findall(text)
    return len(matches) > 0


def get_variable_matches(text):
    """
    Return a list containing a tuple for each property key in the specified text.
    Each tuple contains the full expression (@@PROP:<key>@@) and just the key (<key>).
    :param text: the text to be evaluated
    :return: a list of tuples
    """
    return _property_pattern.findall(text)


def is_variable_string(value):
    """
    Return True if the value contains ONLY a variable token.
    """
    if not isinstance(value, basestring):
        return False
    return bool(_property_string_pattern.match(value))


def get_variable_string_key(value):
    """
    Return the variable key if the value contains ONLY a variable token.
    """
    if not isinstance(value, basestring):
        return None
    matches = _property_string_pattern.findall(value)
    if len(matches) > 0:
        return matches[0][1]
    return None


def is_secret_string(value):
    """
    Return True if the value contains ONLY a secret token.
    """
    if not isinstance(value, basestring):
        return False
    return bool(_secret_string_pattern.match(value))
