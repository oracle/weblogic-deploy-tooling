"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The WLS Deploy tooling entry point for the validateModel tool.
"""
import javaos as os
import sys

from java.lang import IllegalArgumentException
from java.lang import IllegalStateException

from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.validate import ValidateException

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import wlst_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_program_name = 'validateModel'
_class_name = 'validate'
__logger = PlatformLogger('wlsdeploy.validate')
__wls_helper = WebLogicHelper(__logger)
__wlst_mode = WlstModes.OFFLINE
__tmp_model_dir = None

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH, # Used by shell script to locate WLST
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.PRINT_USAGE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.TARGET_VERSION_SWITCH,
    CommandLineArgUtil.TARGET_MODE_SWITCH,
    CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH,
    CommandLineArgUtil.FOLDERS_ONLY_SWITCH,
    CommandLineArgUtil.RECURSIVE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    __verify_required_args_present(required_arg_map)
    __process_model_args(optional_arg_map)
    __process_print_usage_args(optional_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)

    return ModelContext(_program_name, combined_arg_map)


def __verify_required_args_present(required_arg_map):
    """
    Verify that the required args are present.
    :param required_arg_map: the required arguments map
    :raises CLAException: if one or more of the required arguments are missing
    """
    _method_name = '__verify_required_args_present'

    for req_arg in __required_arguments:
        if req_arg not in required_arg_map:
            ex = exception_helper.create_cla_exception('WLSDPLY-20005', _program_name, req_arg)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


def __process_model_args(optional_arg_map):
    """
    Determine if the model file was passed separately or requires extraction from the archive.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments were not valid or an error occurred extracting the model from the archive
    """
    _method_name = '__process_model_args'
    global __tmp_model_dir

    if CommandLineArgUtil.PRINT_USAGE_SWITCH in optional_arg_map:
        # nothing to do since we are printing help information rather than validating supplied artifacts...
        return

    something_to_validate = False
    if CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        #
        # Verify that the archive file exists
        #
        archive_file_name = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        try:
            FileUtils.validateExistingFile(archive_file_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-20014', _program_name, archive_file_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        something_to_validate = True

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_name = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]

        try:
            # Reset the value in the arg map so that the value is always a java.io.File object...
            optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = FileUtils.validateExistingFile(model_file_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-20006', _program_name, model_file_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        archive_file_name = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        try:
            archive_file = WLSDeployArchive(archive_file_name)
            #
            # If the model file was not specified, check to see if the archive contains one.
            # If so, extract it and use it; otherwise, validate will only validate the archive structure.
            #
            if archive_file.containsModel():
                __tmp_model_dir = FileUtils.createTempDirectory(_program_name)
                model_file = archive_file.extractModel(__tmp_model_dir)
                optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-20010', _program_name, archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        something_to_validate = True

    if not something_to_validate:
        ex = exception_helper.create_cla_exception('WLSDPLY-05400', _program_name,
                                                   CommandLineArgUtil.PRINT_USAGE_SWITCH,
                                                   CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return

def __process_print_usage_args(optional_arg_map):
    """
    Validate the -print_usage related arguments.
    :param optional_arg_map: the optional argument map
    :raises: CLAException: if the arguments are not valid
    """
    _method_name = '__process_print_usage_args'

    if CommandLineArgUtil.PRINT_USAGE_SWITCH in optional_arg_map:
        print_usage_path = optional_arg_map[CommandLineArgUtil.PRINT_USAGE_SWITCH]
        found_controller_arg = None
        if CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH in optional_arg_map:
            found_controller_arg = CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH

        if CommandLineArgUtil.FOLDERS_ONLY_SWITCH in optional_arg_map:
            if found_controller_arg is None:
                found_controller_arg = CommandLineArgUtil.FOLDERS_ONLY_SWITCH
            else:
                ex = exception_helper.create_cla_exception('WLSDPLY-05401', _program_name,
                                                           CommandLineArgUtil.PRINT_USAGE_SWITCH,
                                                           CommandLineArgUtil.FOLDERS_ONLY_SWITCH, found_controller_arg)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

        if CommandLineArgUtil.RECURSIVE_SWITCH in optional_arg_map:
            if found_controller_arg is None:
                found_controller_arg = CommandLineArgUtil.RECURSIVE_SWITCH
            else:
                ex = exception_helper.create_cla_exception('WLSDPLY-05401', _program_name,
                                                           CommandLineArgUtil.PRINT_USAGE_SWITCH,
                                                           CommandLineArgUtil.RECURSIVE_SWITCH, found_controller_arg)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
        if found_controller_arg is not None:
            __logger.fine('WLSDPLY-05402', _program_name, CommandLineArgUtil.PRINT_USAGE_SWITCH, print_usage_path,
                          found_controller_arg, class_name=_class_name, method_name=_method_name)
    return

def __clean_up_temp_files():
    """
    If a temporary directory was created to extract the model from the archive, delete the directory and its contents.
    """
    global __tmp_model_dir

    if __tmp_model_dir is not None:
        FileUtils.deleteDirectory(__tmp_model_dir)
        __tmp_model_dir = None


def __perform_model_file_validation(model_file_name, model_context):
    """

    :param model_file_name:
    :param model_context:
    :return:
    :raises ValidationException:
    """

    _method_name = '__perform_model_file_validation'

    print_usage = model_context.get_print_usage()

    __logger.entering(model_file_name,
                      class_name=_class_name, method_name=_method_name)

    try:
        model_dictionary = FileToPython(model_file_name.getAbsolutePath(), True).parse()
        model_validator = Validator(model_context, logger=__logger)
        validation_results = model_validator.validate_in_standalone_mode(model_dictionary,
                                                                         model_context.get_variable_file(),
                                                                         model_context.get_archive_file_name())
    except TranslateException, te:
        __logger.severe('WLSDPLY-20009', _program_name, model_file_name.getAbsolutePath(), te.getLocalizedMessage(),
                        error=te, class_name=_class_name, method_name=_method_name)
        ex = exception_helper.create_validate_exception(te.getLocalizedMessage(), error=te)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    if print_usage is None:
        __logger.info('WLSDPLY-05403',
                      model_file_name,
                      validation_results.get_errors_count(),
                      validation_results.get_warnings_count(),
                      validation_results.get_infos_count(),
                      class_name=_class_name, method_name=_method_name)

    validation_results.print_details()

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def main(args):
    """
    The main entry point for the validateModel tool.

    :param args:
    :return:
    """
    _method_name = 'main'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), arg, class_name=_class_name, method_name=_method_name)

    wlst_helper.silence()

    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(exit_code)

    print_usage = model_context.get_print_usage()

    if print_usage is not None:
        try:
            model_validator = Validator(model_context, logger=__logger)
            model_validator.print_usage(print_usage)
        except ValidateException, ve:
            __logger.severe('WLSDPLY-05404', _program_name, ve.getLocalizedMessage(), error=ve,
                            class_name=_class_name, method_name=_method_name)
            sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)
    else:
        try:
            model_file_name = model_context.get_model_file()

            if model_file_name is not None:
                __perform_model_file_validation(model_file_name,
                                                model_context)

        except ValidateException, ve:
            __logger.severe('WLSDPLY-20000', _program_name, ve.getLocalizedMessage(), error=ve,
                            class_name=_class_name, method_name=_method_name)
            __clean_up_temp_files()
            sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    __clean_up_temp_files()

    return

if __name__ == "main":
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
