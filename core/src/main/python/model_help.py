"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the modelHelp tool.
"""
import os
import sys
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion

# Jython tools don't require sys.path modification

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.modelhelp.model_help_printer import ModelHelpPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import model
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
    CommandLineArgUtil.INTERACTIVE_MODE_SWITCH
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
                ex = exception_helper.create_cla_exception(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE,
                                                           'WLSDPLY-10100', types_text)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            found = True

    return model_context_helper.create_context(_program_name, argument_map)


def canonical_path_from_model_path(model_path):
    """
    helper function for interactive help
    canonicalize a model path so it:
    -  has no ':'
    -  always starts with '/'
    -  does not end with a slash unless at top
    -  converts 'top' to '/'
    -  note: a standalone '/' implies "top"
    -  note: first string after first '/' is normally a section
    :param model_path: the model path
    :return: canonicalized path
    """
    ret_path = model_path.replace(':','')
    while ret_path.endswith('/'):
      ret_path = ret_path[:-1]
    while ret_path.startswith('/'):
      ret_path = ret_path[1:]
    if ret_path == 'top':
      ret_path = ''
    ret_path = '/' + ret_path
    return ret_path


def model_path_from_canonical_path(canonical_path):
    """
    helper function for interactive help
    returns "normal" model path based on canonicalized path
    :param canonical_path: the path in "/.../..." format
    :return: the model path with "section:/..." format or "top"
    """
    ret_path = canonical_path[1:]
    slashpos = ret_path.find('/')
    if slashpos > 0:
      ret_path = ret_path[0:slashpos] + ':' + ret_path[slashpos:]
    if not ret_path:
      ret_path = 'top'
    return ret_path


def parse_dir_command(model_path, command_str):
    """
    helper function to process interactive help commands 'cd [path]', 'cd ..', 'cd', 'top', or 'ls'
    :param model_path: the starting model path before the command
    :param command_str: the command
    :return: the resulting path (an absolute canonical path)
    """

    canonical_path = canonical_path_from_model_path(model_path)

    if command_str == 'cd ..':
      new_path = canonical_path[:canonical_path.rfind('/')]
      if not new_path:
        return '/'
      else:
        return new_path

    if command_str == 'cd' or command_str == 'top':
      return '/'

    if command_str == 'ls':
      return canonical_path

    # if we get this far, then the command string must begin with 'cd '

    command_str = command_str[3:]
    command_str = command_str.replace(':','')
    while command_str.endswith('/'):
      command_str = command_str[:-1]

    # if first token is a section name, make it an absolute path
    slash_pos = command_str.find('/')
    if slash_pos == -1:
      first_token = command_str
    elif slash_pos > 0:
      first_token = command_str[:slash_pos]
    if first_token in model.get_model_top_level_keys():
      command_str = '/' + command_str

    # if first token is 'top' treat it like its starting absolute path
    if first_token == 'top':
      if slash_pos > 0:
        command_str = command_str[3:]
      else:
        command_str = '/'

    if not command_str:
      return '/'

    if command_str.startswith('/'):
      return command_str

    if canonical_path == '/':
      return "/" + command_str

    return canonical_path + "/" + command_str


def interactive_help(model_path, printer):
    """
    Runs the interactive help.
    :param model_path: the model path to start with
    :param printer: a model help printer
    :return: returns when user types 'exit'
    """
    _method_name = 'interactive_help'

    __logger.entering(model_path, class_name=_class_name, method_name=_method_name)

    short_instructions = "In interactive mode! Type 'help' for help."

    # setup starting history
    if model_path == 'top':
      history = ['top']
    else:
      history = ['top', model_path]

    print(short_instructions)
    while True:

      model_path = history[-1]

      command_str = raw_input("[" + model_path + "] --> ")

      command_str = " ".join(command_str.split()) # remove extra white-space

      if command_str == 'help':
        print("")
        print("Commands:")
        print("")
        print("  ls                      - list contents of current location")
        print("  top, cd, cd /, cd top   - go to \"top\"")
        print("  cd x[/[...]]            - relative change (go to child location x...)")
        print("  cd section[:/[...]]     - absolute change (go to exact section and location)")
        print("  cd ..                   - go up")
        print("  history                 - history of visited locations")
        print("  exit                    - exit")
        print("")
        print("Sections:")
        print("")
        print("  " + str(', '.join(model.get_model_top_level_keys())))
        print("")
        print("Example:")
        print("")
        print("  cd topology:/Server/Log/StdoutSeverity")
        print("")
        continue

      if command_str == 'history':
        for line in history:
          print(line)
        continue

      if command_str == 'exit':
        break

      if command_str.count(' ') > 1:
        print("Syntax error '" + command_str + "'")
        print(short_instructions)
        continue

      if command_str == 'ls' or command_str == 'cd' or command_str == 'top' or command_str.startswith('cd '):
        canonical_path = parse_dir_command(model_path, command_str)
        model_path = model_path_from_canonical_path(canonical_path)

        try:
          printer.print_model_help(model_path, ControlOptions.NORMAL)

          # the print_model_help succeeded, add successful path to the history
          if not history[-1] == model_path:
            history.append(model_path)

        except CLAException, ex:
          print("Error getting '" + model_path + "': " + ex.getLocalizedMessage())
          print(short_instructions)

        continue

      if command_str:
        print("Unknown command '" + command_str + "'")
        print(short_instructions)
        continue

      # no command_str, just prompt again 
      continue

    # end of "while True"

    __logger.exiting(class_name=_class_name, method_name=_method_name)
    
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

    if model_context.get_interactive_mode_option():
      interactive_help(model_path,printer)
    else:
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
