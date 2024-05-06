"""
Copyright (c) 2018, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the injectVariables tool.
"""
import os
import sys

from java.io import File
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import TranslateException
# Jython tools don't require sys.path modification

import wlsdeploy.tool.util.variable_injector as variable_injector
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.util import model_translator, cla_helper, tool_main
from wlsdeploy.util import path_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_translator import FileToPython

_program_name = 'injectVariables'
_class_name = 'variable_inject'
__logger = PlatformLogger('wlsdeploy.tool.util')
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH
]


def __process_args(args, is_encryption_supported):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :param is_encryption_supported: whether WDT encryption is supported by the JVM
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    argument_map = cla_util.process_args(args)

    cla_helper.validate_required_model(_program_name, argument_map)
    __process_variable_filename_arg(argument_map)

    return model_context_helper.create_context(_program_name, argument_map)


def __process_variable_filename_arg(argument_map):
    _method_name = '__process_variable_filename_arg'

    if CommandLineArgUtil.VARIABLE_FILE_SWITCH in argument_map:
        variable_file_name = argument_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]
        path_helper_obj = path_helper.get_path_helper()
        variable_dir_name = path_helper_obj.get_local_parent_directory(variable_file_name)
        if not os.path.exists(variable_dir_name):
            ex = exception_helper.create_cla_exception(
                ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-19606', CommandLineArgUtil.VARIABLE_FILE_SWITCH,
                variable_dir_name)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex


def __inject(model, model_context):
    """
    Inject variables into the model file that is loaded into the model_context.
    :param model_context: the model context
    :return: True if variables were inserted into model: The updated model
    """
    wlst_mode = model_context.get_target_wlst_mode()
    aliases = Aliases(model_context, wlst_mode)

    credential_injector = CredentialInjector(_program_name, model_context, aliases)

    credential_injector.inject_model_variables(model)

    injector = VariableInjector(_program_name, model_context, aliases, credential_injector.get_variable_cache())

    inserted, variable_model, variable_file_name =\
        injector.inject_variables_from_configuration(model, append_option=variable_injector.VARIABLE_FILE_UPDATE)

    if inserted:
        model = Model(variable_model)

    return inserted, model


def __persist_model(model, model_context):
    """
    Save the model to the specified model file name.
    :param model: the model to save
    :param model_context: the model context
    :raises TranslateException: if an error occurs while serializing the model or writing it to disk
    """
    _method_name = '__persist_model'

    __logger.entering(class_name=_class_name, method_name=_method_name)

    model_file_name = model_context.get_model_file()
    model_file = FileUtils.getCanonicalFile(File(model_file_name))
    model_translator.PythonToFile(model.get_model()).write_to_file(model_file.getAbsolutePath())

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def main(model_context):
    """
    The main entry point for the injectVariables tool.

    :param model_context: The model context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _exit_code = ExitCode.OK
    model_file = model_context.get_model_file()
    model = None
    try:
        model = FileToPython(model_file, True).parse()
    except TranslateException, te:
        __logger.severe('WLSDPLY-20009', _program_name, model_file, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        _exit_code = ExitCode.ERROR

    if _exit_code == ExitCode.OK:
        inserted, model = __inject(model, model_context)
        if inserted:
            __logger.info('WLSDPLY-19604', class_name=_class_name, method_name=_method_name)
            try:
                __persist_model(model, model_context)

            except TranslateException, ex:
                __logger.severe('WLSDPLY-20024', _program_name, model_context.get_archive_file_name(),
                                ex.getLocalizedMessage(), error=ex, class_name=_class_name, method_name=_method_name)
                _exit_code = ExitCode.ERROR

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
