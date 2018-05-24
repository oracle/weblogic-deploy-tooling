"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The entry point for the discoverDomain tool.
"""
import os
import sys

from java.io import File
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion


sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

import wlsdeploy.tool.util.variable_injector as variable_injector
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.util import wlst_helper
from wlsdeploy.util import model_translator
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.weblogic_helper import WebLogicHelper

_program_name = 'injectVariables'
_class_name = 'variable_inject'
__logger = PlatformLogger('wlsdeploy.tool.util')
__wlst_mode = WlstModes.OFFLINE
__kwargs = dict()
__inserted = False
__tmp_model_dir = None

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_KEYWORDS_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    __process_model_args(optional_arg_map)
    __process_injector_file(optional_arg_map)
    __process_keywords_file(optional_arg_map)
    __process_properties_file(optional_arg_map)

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
    Verify that either the model_file or archive_file was provided and exists.
    If the model_file was not provided, the archive_file must be provided and the indicated archive file
    must contain a model file. Extract the model file if the archive_file was provided.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are invalid or an error occurs extracting the model from the archive
    """
    _method_name = '__process_model_args'
    global __tmp_model_dir

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_name = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]

        try:
            FileUtils.validateExistingFile(model_file_name)
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
            contains_model = archive_file.containsModel()
            if not contains_model:
                ex = exception_helper.create_cla_exception('WLSDPLY-19603', archive_file_name)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            else:
                __tmp_model_dir = FileUtils.createTempDirectory(_program_name)
                tmp_model_file = \
                    FileUtils.fixupFileSeparatorsForJython(archive_file.extractModel(__tmp_model_dir).getAbsolutePath())
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-20010', _program_name, archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = FileUtils.fixupFileSeparatorsForJython(tmp_model_file)
    else:
        ex = exception_helper.create_cla_exception('WLSDPLY-20015', _program_name, CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return


def __process_injector_file(optional_arg_map):
    _method_name = '__process_injector_file'
    if CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH in optional_arg_map:
        injector = optional_arg_map[CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH]
        __logger.fine('WLSDPLY-19600', injector, class_name=_class_name, method_name=_method_name)
        __kwargs[variable_injector.VARIABLE_INJECTOR_FILE_NAME_ARG] = injector


def __process_keywords_file(optional_arg_map):
    _method_name = '__process_keywords_file'
    if CommandLineArgUtil.VARIABLE_KEYWORDS_FILE_SWITCH in optional_arg_map:
        keywords = optional_arg_map[CommandLineArgUtil.VARIABLE_KEYWORDS_FILE_SWITCH]
        __logger.fine('WLSDPLY-19601', keywords, class_name=_class_name, method_name=_method_name)
        __kwargs[variable_injector.VARIABLE_KEYWORDS_FILE_NAME_ARG] = keywords


def __process_properties_file(optional_arg_map):
    _method_name = '__process_properties_file'
    if CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH in optional_arg_map:
        properties = optional_arg_map[CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH]
        __logger.fine('WLSDPLY-19602', properties, class_name=_class_name, method_name=_method_name)
        __kwargs[variable_injector.VARIABLE_FILE_NAME_ARG] = properties


def __inject(model, model_context):
    """
    Inject variables into the model file that is loaded into the model_context.
    :param model_context: the model context
    :return: True if variables were inserted into model: The updated model
    """
    __kwargs[variable_injector.VARIABLE_FILE_APPEND_ARG] = variable_injector.VARIABLE_FILE_UPDATE
    inserted, variable_model, variable_file_name = VariableInjector(_program_name, model, model_context,
                                                                    WebLogicHelper(
                                                                        __logger).get_actual_weblogic_version()). \
        inject_variables_keyword_file(**__kwargs)
    if inserted:
        model = Model(variable_model)
    return inserted, model


def __close_archive(model_context):
    """
    Close the archive object
    :param model_context: the model context
    """
    _method_name = '__close_archive'

    __logger.entering(_class_name=_class_name, method_name=_method_name)
    archive_file = model_context.get_archive_file()
    if archive_file:
        archive_file.close()
    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def __persist_model(model, model_context):
    """
    Save the model to the specified model file name or to the archive if the file name was not specified.
    :param model: the model to save
    :param model_context: the model context
    :raises DiscoverException: if an error occurs while create a temporary file for the model
                               or while adding it to the archive
    :raises TranslateException: if an error occurs while serializing the model or writing it to disk
    """
    _method_name = '__persist_model'

    __logger.entering(class_name=_class_name, method_name=_method_name)

    add_to_archive = False
    model_file_name = model_context.get_model_file()
    model_file = FileUtils.getCanonicalFile(File(model_file_name))
    if model_file_name is None:
        add_to_archive = True
    try:
        model_translator.PythonToFile(model.get_model()).write_to_file(model_file.getAbsolutePath())
    except TranslateException, ex:
        # Jython 2.2.1 does not support finally so use this like a finally block...
        if add_to_archive and not model_file.delete():
            model_file.deleteOnExit()
        raise ex

    if add_to_archive:
        try:
            archive_file = model_context.get_archive_file()
            archive_file.addModel(model_file, model_file_name)
            if not model_file.delete():
                model_file.deleteOnExit()
        except (WLSDeployArchiveIOException, IllegalArgumentException), arch_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-20023', _program_name,
                                                            model_file.getAbsolutePath(), model_file_name,
                                                            arch_ex.getLocalizedMessage(),
                                                            error=arch_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            if not model_file.delete():
                model_file.deleteOnExit()
            raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return


def __log_and_exit(exit_code, class_name, _method_name):
    """
    Helper method to log the exiting message and call sys.exit()
    :param exit_code: the exit code to use
    :param class_name: the class name to pass  to the logger
    :param _method_name: the method name to pass to the logger
    """
    __logger.exiting(result=exit_code, class_name=class_name, method_name=_method_name)
    sys.exit(exit_code)


def main(args):
    """
    The main entry point for the discoverDomain tool.

    :param args:
    :return:
    """
    _method_name = 'main'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    wlst_helper.silence()

    exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE

    model_context = None
    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        __log_and_exit(exit_code, _class_name, _method_name)

    model_file = model_context.get_model_file()
    try:
        model = FileToPython(model_file, True).parse()
    except TranslateException, te:
        __logger.severe('WLSDPLY-20009', _program_name, model_file, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    inserted, model = __inject(model, model_context)
    if inserted:
        __logger.info('WLSDPLY-19604', class_name=_class_name, method_name=_method_name)
        try:
            __persist_model(model, model_context)

        except TranslateException, ex:
            __logger.severe('WLSDPLY-20024', _program_name, model_context.get_archive_file_name(),
                            ex.getLocalizedMessage(), error=ex, class_name=_class_name, method_name=_method_name)
            __log_and_exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE, _class_name, _method_name)

    __close_archive(model_context)

    __logger.exiting(result=exit_code, class_name=_class_name, method_name=_method_name)
    sys.exit(exit_code)

if __name__ == 'main':
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
