"""
Copyright (c) 2019, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Utility CLS methods shared by multiple tools.
"""
import os

from java.io import File
from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import String
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.validate import ValidateException

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_utils
from wlsdeploy.util import getcreds
from wlsdeploy.util import model_helper
from wlsdeploy.util import model_translator
from wlsdeploy.util import path_utils

from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model_translator import FileToPython


__logger = PlatformLogger('wlsdeploy.util')
_class_name = 'cla_helper'

_store_environment_variable = '__WLSDEPLOY_STORE_MODEL__'

__tmp_model_dir = None


def validate_optional_archive(program_name, optional_arg_map):
    """
    If the archive file was specified on the command line, verify that it exists.
    :param program_name: the name of the calling program, for logging
    :param optional_arg_map: the optional arguments from the command line
    :raises CLAException: if the archive was specified and does not exist
    """
    _method_name = 'validate_optional_archive'

    if CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        archive_file_name = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        archive_files = cla_utils.get_archive_files(archive_file_name)

        for archive_file in archive_files:
            try:
                FileUtils.validateExistingFile(archive_file)
            except IllegalArgumentException, iae:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                           'WLSDPLY-20014', program_name, archive_file_name,
                                                           iae.getLocalizedMessage(), error=iae)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex


def validate_model_present(program_name, optional_arg_map):
    """
    Determine if the model file was passed separately or requires extraction from the archive.
    If the model is in the archive, extract it to the temporary model location, and set that file as the
    MODEL_FILE_SWITCH argument.
    The MODEL_FILE_SWITCH value may be specified as multiple comma-separated models.
    The ARCHIVE_FILE_SWITCH value may be specified as multiple comma-separated archives.
    :param program_name: the name of the calling program, for logging
    :param optional_arg_map: the optional arguments from the command line
    :raises CLAException: if the specified model is not an existing file, or the model is not found in the archive,
    or the model is not found from either argument
    """
    _method_name = 'validate_model_present'
    global __tmp_model_dir

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_value = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]
        model_files = cla_utils.get_model_files(model_file_value)

        for model_file in model_files:
            try:
                FileUtils.validateExistingFile(model_file)
            except IllegalArgumentException, iae:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                           'WLSDPLY-20006', program_name, model_file,
                                                           iae.getLocalizedMessage(), error=iae)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

    elif CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        archive_file = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        archive_helper = ArchiveHelper(archive_file, None, __logger, exception_helper.ExceptionType.CLA)

        if archive_helper.contains_model():
            __tmp_model_dir, tmp_model_file = archive_helper.extract_model(program_name)
            model_file_name = FileUtils.fixupFileSeparatorsForJython(tmp_model_file.getAbsolutePath())
            optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file_name
        else:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-20026', program_name, archive_file,
                                                       CommandLineArgUtil.MODEL_FILE_SWITCH)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
                                                   'WLSDPLY-20015', program_name,
                                                   CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def validate_variable_file_exists(program_name, argument_map):
    """
    Validate that the variable file(s) exist.
    Assume that the caller allows multiple variables files.
    :param program_name: the name of the tool
    :param argument_map: the program arguments
    """
    method_name = 'validate_variable_file_exists'
    if CommandLineArgUtil.VARIABLE_FILE_SWITCH in argument_map:
        result_files = []  # type: list
        value = argument_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]
        files = value.split(CommandLineArgUtil.MODEL_FILES_SEPARATOR)
        for file in files:
            try:
                variable_file = FileUtils.validateExistingFile(file)
                result_files.append(variable_file.getAbsolutePath())
            except IllegalArgumentException, iae:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                           'WLSDPLY-20031', program_name, file,
                                                           iae.getLocalizedMessage(), error=iae)
                __logger.throwing(ex, class_name=_class_name, method_name=method_name)
                raise ex

        argument_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH] = ",".join(result_files)


def process_encryption_args(optional_arg_map):
    """
    If the user is using model encryption, get the passphrase from stdin, and put it in the argument map.
    If the passphrase switch was specified in the arg map, just use it directly.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if an error occurs reading the passphrase input from the user
    """
    _method_name = '__process_encryption_args'

    if CommandLineArgUtil.USE_ENCRYPTION_SWITCH in optional_arg_map and \
            CommandLineArgUtil.PASSPHRASE_SWITCH not in optional_arg_map:
        try:
            passphrase = getcreds.getpass('WLSDPLY-20002')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-20003', ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = String(passphrase)


def validate_model(program_name, model_dictionary, model_context, aliases, wlst_mode,
                   validate_crd_sections=True):
    """
    Validate the model dictionary based on the specified model context and aliases.
    The tool will exit if exceptions are encountered, or the validation returns a STOP code.
    :param program_name: the program name, for logging
    :param model_dictionary: the model dictionary
    :param model_context: the model context
    :param aliases: the aliases
    :param wlst_mode: offline or online
    :param validate_crd_sections: True if CRD sections (such as kubernetes) should be validated
    :return:
    """
    _method_name = 'validate_model'

    try:
        validator = Validator(model_context, aliases, wlst_mode=wlst_mode, validate_crd_sections=validate_crd_sections)

        # no need to pass the variable file for processing, substitution has already been performed
        return_code = validator.validate_in_tool_mode(model_dictionary, variables_file_name=None,
                                                      archive_file_name=model_context.get_archive_file_name())
    except ValidateException, ex:
        __logger.severe('WLSDPLY-20000', program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        tool_exception = \
            exception_helper.create_exception(aliases.get_exception_type(), 'WLSDPLY-20000', program_name,
                                              ex.getLocalizedMessage(), error=ex)
        __logger.throwing(tool_exception, class_name=_class_name, method_name=_method_name)
        raise tool_exception

    if return_code == Validator.ReturnCode.STOP:
        __logger.severe('WLSDPLY-20001', program_name, class_name=_class_name, method_name=_method_name)
        tool_exception = \
            exception_helper.create_exception(aliases.get_exception_type(), 'WLSDPLY-20001', program_name)
        __logger.throwing(tool_exception, class_name=_class_name, method_name=_method_name)
        raise tool_exception


def load_model(program_name, model_context, aliases, filter_type, wlst_mode, validate_crd_sections=True):
    """
    Load the model based on the arguments in the model context.
    Apply the variable substitution, if specified, and validate the model.
    Apply any model filters of the specified type that are configured, and re-validate if necessary
    The tool will exit if exceptions are encountered.
    :param program_name: the program name, for logging
    :param model_context: the model context
    :param aliases: the alias configuration
    :param filter_type: the type of any filters to be applied
    :param wlst_mode: offline or online
    :param validate_crd_sections: True if CRD sections (such as kubernetes) should be validated
    :return: the resulting model dictionary
    """
    _method_name = 'load_model'

    variable_map = {}
    try:
        if model_context.get_variable_file():
            # callers of this method allow multiple variable files
            variable_map = variables.load_variables(model_context.get_variable_file(), allow_multiple_files=True)
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        tool_exception = \
            exception_helper.create_exception(aliases.get_exception_type(), 'WLSDPLY-20004', program_name,
                                              ex.getLocalizedMessage(), error=ex)
        __logger.throwing(tool_exception, class_name=_class_name, method_name=_method_name)
        raise tool_exception

    model_file_value = model_context.get_model_file()
    try:
        model_dictionary = merge_model_files(model_file_value, variable_map)
    except TranslateException, te:
        __logger.severe('WLSDPLY-09014', program_name, model_file_value, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        tool_exception = \
            exception_helper.create_exception(aliases.get_exception_type(), 'WLSDPLY-09014', program_name,
                                              model_file_value, te.getLocalizedMessage(), error=te)
        __logger.throwing(tool_exception, class_name=_class_name, method_name=_method_name)
        raise tool_exception

    try:
        variables.substitute(model_dictionary, variable_map, model_context)
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        tool_exception = \
            exception_helper.create_exception(aliases.get_exception_type(), 'WLSDPLY-20004', program_name,
                                              ex.getLocalizedMessage(), error=ex)
        __logger.throwing(tool_exception, class_name=_class_name, method_name=_method_name)
        raise tool_exception

    filter_helper.apply_filters(model_dictionary, filter_type, model_context)

    persist_model(model_context, model_dictionary)

    validate_model(program_name, model_dictionary, model_context, aliases, wlst_mode,
                   validate_crd_sections=validate_crd_sections)

    return model_dictionary


def process_online_args(optional_arg_map):
    """
    Determine if we are executing in online mode and if so, validate/prompt for the necessary parameters.
    :param optional_arg_map: the optional arguments map
    :return: the WLST mode
    :raises CLAException: if an error occurs reading input from the user
    """
    _method_name = 'process_online_args'

    mode = WlstModes.OFFLINE
    if CommandLineArgUtil.ADMIN_URL_SWITCH in optional_arg_map:
        if CommandLineArgUtil.ADMIN_USER_SWITCH not in optional_arg_map:
            try:
                username = getcreds.getuser('WLSDPLY-09001')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                           'WLSDPLY-09002', ioe.getLocalizedMessage(), error=ioe)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_USER_SWITCH] = username

        if CommandLineArgUtil.ADMIN_PASS_SWITCH not in optional_arg_map:
            try:
                password = getcreds.getpass('WLSDPLY-09003')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                           'WLSDPLY-09004', ioe.getLocalizedMessage(), error=ioe)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_PASS_SWITCH] = String(password)

        mode = WlstModes.ONLINE
        optional_arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH] = 'online'
    return mode


def clean_up_temp_files():
    """
    If a temporary directory was created to extract the model from the archive, delete the directory and its contents.
    """
    global __tmp_model_dir

    if __tmp_model_dir is not None:
        FileUtils.deleteDirectory(__tmp_model_dir)
        __tmp_model_dir = None


def merge_model_files(model_file_value, variable_map=None):
    """
    Merge the model files specified by the model file value.
    It may be a single file, or a comma-separated list of files.
    :param variable_map: variables to be used for name resolution, or None
    :param model_file_value: the value specified as a command argument
    :return: the merge model dictionary
    """
    merged_model = OrderedDict()
    model_files = cla_utils.get_model_files(model_file_value)

    for model_file in model_files:
        model = FileToPython(model_file, True).parse()
        merge_model_dictionaries(merged_model, model, variable_map)

    return merged_model


def merge_model_dictionaries(dictionary, new_dictionary, variable_map):
    """
    Merge the values from the new dictionary to the existing one.
    Use variables to resolve keys.
    :param dictionary: the existing dictionary
    :param new_dictionary: the new dictionary to be merged
    :param variable_map: variables to be used for name resolution, or None
    """
    for new_key in new_dictionary:
        new_value = new_dictionary[new_key]
        dictionary_key, replace_key = _find_dictionary_merge_key(dictionary, new_key, variable_map)

        # the key is not in the original dictionary, just add it
        if dictionary_key is None:
            dictionary[new_key] = new_value

        # the new key should replace the existing one - delete the existing key and add the new one
        elif replace_key:
            del dictionary[dictionary_key]
            if not model_helper.is_delete_name(new_key):
                dictionary[new_key] = new_value

        # the key is in both dictionaries - merge if the values are dictionaries, otherwise replace the value
        else:
            value = dictionary[dictionary_key]
            if isinstance(value, dict) and isinstance(new_value, dict):
                merge_model_dictionaries(value, new_value, variable_map)
            else:
                dictionary[new_key] = new_value


def _find_dictionary_merge_key(dictionary, new_key, variable_map):
    """
    Find the key corresponding to new_key in the specified dictionary.
    Determine if the new_key should completely replace the value in the dictionary.
    If no direct match is found, and a variable map is specified, perform check with variable substitution.
    If keys have the same name, but one has delete notation (!server), that is a match, and replace is true.
    :param dictionary: the dictionary to be searched
    :param new_key: the key being checked
    :param variable_map: variables to be used for name resolution, or None
    :return: tuple - the corresponding key from the dictionary, True if dictionary key should be replaced
    """
    if new_key in dictionary:
        return new_key, False

    new_is_delete = model_helper.is_delete_name(new_key)
    match_new_key = _get_merge_match_key(new_key, variable_map)

    for dictionary_key in dictionary.keys():
        dictionary_is_delete = model_helper.is_delete_name(dictionary_key)
        match_dictionary_key = _get_merge_match_key(dictionary_key, variable_map)
        if match_dictionary_key == match_new_key:
            replace_key = new_is_delete != dictionary_is_delete
            return dictionary_key, replace_key

    return None, False


def _get_merge_match_key(key, variable_map):
    """
    Get the key name to use for matching in model merge.
    This includes resolving any variables, and removing delete notation if present.
    :param key: the key to be examined
    :param variable_map: variable map to use for substitutions
    :return: the key to use for matching
    """

    match_key = variables.substitute_key(key, variable_map)

    if model_helper.is_delete_name(match_key):
        match_key = model_helper.get_delete_item_name(match_key)
    return match_key


def persist_model(model_context, model_dictionary):
    """
    If environment variable __WLSDEPLOY_STORE_MODEL__ is set, save the specified model.
    If the variable's value starts with a slash, save to that file, otherwise use a default location.
    :param model_context: the model context
    :param model_dictionary: the model to be saved
    """
    _method_name = 'persist_model'

    if check_persist_model():
        store_value = os.environ.get(_store_environment_variable)

        if os.path.isabs(store_value):
            file_path = store_value
        elif model_context.get_domain_home() is not None:
            file_path = model_context.get_domain_home() + os.sep + 'wlsdeploy' + os.sep + 'domain_model.json'
        else:
            file_dir = FileUtils.createTempDirectory('wlsdeploy')
            file_path = File(file_dir, 'domain_model.json').getAbsolutePath()

        __logger.info('WLSDPLY-01650', file_path, class_name=_class_name, method_name=_method_name)

        persist_dir = path_utils.get_parent_directory(file_path)
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)

        model_file = FileUtils.getCanonicalFile(File(file_path))
        model_translator.PythonToFile(model_dictionary).write_to_file(model_file.getAbsolutePath())


def check_persist_model():
    """
    Determine if the model should be persisted, based on the environment variable __WLSDEPLOY_STORE_MODEL__
    :return: True if the model should be persisted
    """
    return os.environ.has_key(_store_environment_variable)
