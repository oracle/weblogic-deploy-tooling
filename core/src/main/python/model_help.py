"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the modelHelp tool.
"""
import os
import sys
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion

# Jython tools don't require sys.path modification

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.modelhelp.model_help_printer import ModelHelpPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import cla_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil

_program_name = 'modelHelp'
_class_name = 'model_help'
__logger = PlatformLogger('wlsdeploy.modelhelp')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH,
    CommandLineArgUtil.FOLDERS_ONLY_SWITCH,
    CommandLineArgUtil.RECURSIVE_SWITCH,
    # deprecated
    CommandLineArgUtil.MODEL_SAMPLE_SWITCH
]

__output_types = [
    CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH,
    CommandLineArgUtil.FOLDERS_ONLY_SWITCH,
    CommandLineArgUtil.RECURSIVE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments.
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    _method_name = '__process_args'

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    argument_map = cla_util.process_args(args, trailing_arg_count=1)

    # zero or one output type arguments should be set
    found = False
    for key in __output_types:
        if key in argument_map:
            if found:
                types_text = ', '.join(__output_types)
                ex = exception_helper.create_cla_exception('WLSDPLY-10100', types_text)
                ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            found = True

    if CommandLineArgUtil.MODEL_SAMPLE_SWITCH in argument_map:
        __logger.warning('WLSDPLY-10106', CommandLineArgUtil.MODEL_SAMPLE_SWITCH,
                         class_name=_class_name, method_name=_method_name)

    return model_context_helper.create_context(_program_name, argument_map)


def print_help(model_path, model_context):
    """
    Prints the folders and/or attributes for the specified given model_path,
    using control_option to filter what is output
    :param model_path: the model path to print help for
    :param model_context: the model context, used to determine print options
    :return: an exit code
    """
    _method_name = 'print_help'

    __logger.entering(model_path, class_name=_class_name, method_name=_method_name)

    # default to NORMAL
    control_option = ControlOptions.NORMAL

    # determine control option using the model_context
    if model_context.get_recursive_control_option():
        control_option = ControlOptions.RECURSIVE
    elif model_context.get_attributes_only_control_option():
        control_option = ControlOptions.ATTRIBUTES_ONLY
    elif model_context.get_folders_only_control_option():
        control_option = ControlOptions.FOLDERS_ONLY

    aliases = Aliases(model_context)
    printer = ModelHelpPrinter(aliases, __logger)
    printer.print_model_help(model_path, control_option)

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return CommandLineArgUtil.PROG_OK_EXIT_CODE


def main(args):
    """
    The main entry point for the discoverDomain tool.
    :param args: the command-line arguments
    """
    _method_name = 'main'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        sys.exit(exit_code)

    try:
        model_path = model_context.get_trailing_argument(0)
        exit_code = print_help(model_path, model_context)
    except CLAException, ve:
        __logger.severe('WLSDPLY-10112', _program_name, ve.getLocalizedMessage(), error=ve,
                        class_name=_class_name, method_name=_method_name)
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    __logger.exiting(result=exit_code, class_name=_class_name, method_name=_method_name)
    sys.exit(exit_code)


if __name__ == '__main__' or __name__ == 'main':
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
