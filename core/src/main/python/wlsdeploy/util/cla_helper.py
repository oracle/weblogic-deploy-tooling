"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Utility CLS methods shared by multiple tools.
"""
from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import String
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.validate import ValidateException
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_utils
from wlsdeploy.util import tool_exit
from wlsdeploy.util import getcreds
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_translator import FileToPython

import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict

__logger = PlatformLogger('wlsdeploy.util')
_class_name = 'cla_helper'

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
                ex = exception_helper.create_cla_exception('WLSDPLY-20014', program_name, archive_file_name,
                                                           iae.getLocalizedMessage(), error=iae)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
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
                ex = exception_helper.create_cla_exception('WLSDPLY-20006', program_name, model_file,
                                                           iae.getLocalizedMessage(), error=iae)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

    elif CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        archive_file = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        archive_helper = ArchiveHelper(archive_file, None, __logger, exception_helper.ExceptionType.CLA)

        if archive_helper.contains_model():
            tmp_model_dir, tmp_model_file = archive_helper.extract_model(program_name)
            model_file_name = FileUtils.fixupFileSeparatorsForJython(tmp_model_file.getAbsolutePath())
            optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file_name
        else:
            ex = exception_helper.create_cla_exception('WLSDPLY-20026', program_name, archive_file,
                                                       CommandLineArgUtil.MODEL_FILE_SWITCH)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    else:
        ex = exception_helper.create_cla_exception('WLSDPLY-20015', program_name,
                                                   CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return


def validate_variable_file_exists(program_name, optional_arg_map):
    method_name = '_validate_variable_file_arg'
    if CommandLineArgUtil.VARIABLE_FILE_SWITCH in optional_arg_map:
        value = optional_arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]
        try:
            variable_file = FileUtils.validateExistingFile(value)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-20031', program_name, value,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH] = variable_file.getAbsolutePath()
    return


def verify_required_args_present(program_name, required_arguments, required_arg_map):
    """
    Verify that the required args are present.
    :param required_arguments: the required arguments to be checked
    :param required_arg_map: the required arguments map
    :raises CLAException: if one or more of the required arguments are missing
    """
    _method_name = '__verify_required_args_present'

    for req_arg in required_arguments:
        if req_arg not in required_arg_map:
            ex = exception_helper.create_cla_exception('WLSDPLY-20005', program_name, req_arg)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


def process_encryption_args(optional_arg_map):
    """
    If the user is using model encryption, get the passphrase from stdin, and put it in the argument map.
    If the passphrase switch was specified in the arg map, just use it directly.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if an error occurs reading the passphrase inout from the user
    """
    _method_name = '__process_encryption_args'

    if CommandLineArgUtil.USE_ENCRYPTION_SWITCH in optional_arg_map and \
            CommandLineArgUtil.PASSPHRASE_SWITCH not in optional_arg_map:
        try:
            passphrase = getcreds.getpass('WLSDPLY-20002')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception('WLSDPLY-20003', ioe.getLocalizedMessage(), error=ioe)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = String(passphrase)
    return


def validate_model(program_name, model_dictionary, model_context, aliases, wlst_mode):
    """
    Validate the model dictionary based on the specified model context and aliases.
    The tool will exit if exceptions are encountered, or the validation returns a STOP code.
    :param program_name:
    :param model_dictionary:
    :param model_context:
    :param aliases:
    :param wlst_mode:
    :return:
    """
    _method_name = 'validate_model'

    try:
        validator = Validator(model_context, aliases, wlst_mode=wlst_mode)

        # no need to pass the variable file for processing, substitution has already been performed
        return_code = validator.validate_in_tool_mode(model_dictionary, variables_file_name=None,
                                                      archive_file_name=model_context.get_archive_file_name())
    except ValidateException, ex:
        __logger.severe('WLSDPLY-20000', program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    if return_code == Validator.ReturnCode.STOP:
        __logger.severe('WLSDPLY-20001', program_name, class_name=_class_name, method_name=_method_name)
        clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)


def load_model(program_name, model_context, aliases, filter_type, wlst_mode):
    """
    Load the model based on the arguments in the model context.
    Apply the variable substitution, if specified, and validate the model.
    Apply any model filters of the specified type that are configured, and re-validate if necessary
    The tool will exit if exceptions are encountered.
    :param program_name: the program name, for logging
    :param model_context: the model context
    :param aliases: the alias configuration
    :param wlst_mode: offline or online
    :param filter_type: the type of any filters to be applied
    :return: the resulting model dictionary
    """
    _method_name = 'load_model'

    variable_map = {}
    try:
        if model_context.get_variable_file():
            variable_map = variables.load_variables(model_context.get_variable_file())
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    model_file_value = model_context.get_model_file()
    try:
        model_dictionary = merge_model_files(model_file_value, variable_map)
    except TranslateException, te:
        __logger.severe('WLSDPLY-09014', program_name, model_file_value, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    try:
        variables.substitute(model_dictionary, variable_map, model_context)
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    validate_model(program_name, model_dictionary, model_context, aliases, wlst_mode)

    if filter_helper.apply_filters(model_dictionary, filter_type):
        # if any filters were applied, re-validate the model
        validate_model(program_name, model_dictionary, model_context, aliases, wlst_mode)


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
        _merge_dictionaries(merged_model, model, variable_map)

    return merged_model


def _merge_dictionaries(dictionary, new_dictionary, variable_map):
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
            if not deployer_utils.is_delete_name(new_key):
                dictionary[new_key] = new_value

        # the key is in both dictionaries - merge if the values are dictionaries, otherwise replace the value
        else:
            value = dictionary[dictionary_key]
            if isinstance(value, dict) and isinstance(new_value, dict):
                _merge_dictionaries(value, new_value, variable_map)
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

    new_is_delete = deployer_utils.is_delete_name(new_key)
    match_new_key = _get_merge_match_key(new_key, variable_map)

    for dictionary_key in dictionary.keys():
        dictionary_is_delete = deployer_utils.is_delete_name(dictionary_key)
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
    if variable_map is not None:
        match_key = variables.substitute_key(key, variable_map)
    else:
        match_key = key

    if deployer_utils.is_delete_name(match_key):
        match_key = deployer_utils.get_delete_item_name(match_key)
    return match_key
