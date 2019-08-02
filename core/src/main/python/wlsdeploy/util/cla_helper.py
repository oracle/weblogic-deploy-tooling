"""
Copyright (c) 2019, Oracle and/or its affiliates. All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at http://oss.oracle.com/licenses/upl.

Utility CLS methods shared by multiple tools.
"""
from java.lang import IllegalArgumentException, IllegalStateException
from oracle.weblogic.deploy.util import FileUtils, WLSDeployArchive, WLSDeployArchiveIOException

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import cla_utils
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


def merge_model_files(model_file_value):
    """
    Merge the model files specified by the model file value.
    It may be a single file, or a comma-separated list of files.
    :param model_file_value: the value specified as a command argument
    :return: the merge model dictionary
    """
    merged_model = OrderedDict()
    model_files = cla_utils.get_model_files(model_file_value)

    for model_file in model_files:
        model = FileToPython(model_file, True).parse()
        _merge_dictionaries(merged_model, model)

    return merged_model


def _merge_dictionaries(dictionary, new_dictionary):
    """
    Merge the values from the new dictionary to the existing one.
    :param dictionary: the existing dictionary
    :param new_dictionary: the new dictionary to be merged
    """
    for key in new_dictionary:
        new_value = new_dictionary[key]
        if key not in dictionary:
            dictionary[key] = new_value
        else:
            value = dictionary[key]
            if isinstance(value, dict) and isinstance(new_value, dict):
                _merge_dictionaries(value, new_value)
            else:
                dictionary[key] = new_value
