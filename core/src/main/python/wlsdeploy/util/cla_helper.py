"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Utility CLS methods shared by multiple tools.
"""
from java.lang import IllegalArgumentException, IllegalStateException
from oracle.weblogic.deploy.util import FileUtils, WLSDeployArchive, WLSDeployArchiveIOException

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import cla_utils
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

        try:
            FileUtils.validateExistingFile(archive_file_name)
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
        archive_file_name = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        try:
            archive_file = WLSDeployArchive(archive_file_name)
            __tmp_model_dir = FileUtils.createTempDirectory(program_name)
            tmp_model_raw_file = archive_file.extractModel(__tmp_model_dir)
            if not tmp_model_raw_file:
                ex = exception_helper.create_cla_exception('WLSDPLY-20026', program_name, archive_file_name,
                                                           CommandLineArgUtil.MODEL_FILE_SWITCH)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

            model_file_name = FileUtils.fixupFileSeparatorsForJython(tmp_model_raw_file.getAbsolutePath())
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-20010', program_name, archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file_name

    else:
        ex = exception_helper.create_cla_exception('WLSDPLY-20015', program_name,
                                                   CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return


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

    if variable_map is not None:
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
    match_key = variables.substitute_key(key, variable_map)
    if deployer_utils.is_delete_name(match_key):
        match_key = deployer_utils.get_delete_item_name(match_key)
    return match_key
