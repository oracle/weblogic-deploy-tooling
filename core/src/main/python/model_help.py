"""
Copyright (c) 2020, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the modelHelp tool.
"""
import sys

from oracle.weblogic.deploy.util import CLAException

# Jython tools don't require sys.path modification
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.modelhelp.model_help_interactive_printer import ModelHelpInteractivePrinter
from wlsdeploy.tool.modelhelp.model_help_printer import ModelHelpPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode

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
    CommandLineArgUtil.TARGET_SWITCH,
    CommandLineArgUtil.TARGET_MODE_SWITCH
]

__output_types = [
    CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH,
    CommandLineArgUtil.FOLDERS_ONLY_SWITCH,
    CommandLineArgUtil.RECURSIVE_SWITCH
]


def __process_args(args, is_encryption_supported):
    """
    Process the command-line arguments.
    :param args: the command-line arguments list
    :param is_encryption_supported: whether WDT encryption is supported by the JVM
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    _method_name = '__process_args'

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)

    # try parsing with a trailing argument (the model path), then without if that fails
    try:
        argument_map = cla_util.process_args(args, trailing_arg_count=1)
    except CLAException:
        argument_map = cla_util.process_args(args)

    # zero or one output type arguments should be set
    found = False
    for key in __output_types:
        if key in argument_map:
            if found:
                types_text = ', '.join(__output_types)
                ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
                                                           'WLSDPLY-10100', types_text)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            found = True

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

    aliases = Aliases(model_context, wlst_mode=model_context.get_target_wlst_mode())

    if model_path:
        printer = ModelHelpPrinter(model_context, aliases, __logger)
        printer.print_model_help(model_path, control_option)
    else:
        printer = ModelHelpInteractivePrinter(model_context, aliases, __logger)
        printer.interactive_help_main_loop()

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    return ExitCode.OK


def main(model_context):
    """
    The main entry point for the modelHelp tool.
    :param model_context: the model context object
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _exit_code = ExitCode.OK
    try:
        model_path = None
        trailing_args = model_context.get_trailing_arguments()
        if trailing_args:
            model_path = trailing_args[0]
        _exit_code = print_help(model_path, model_context)
    except CLAException, ve:
        __logger.severe('WLSDPLY-10112', _program_name, ve.getLocalizedMessage(), error=ve,
                        class_name=_class_name, method_name=_method_name)
        _exit_code = ExitCode.ERROR

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
