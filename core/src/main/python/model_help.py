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


def parse_dir_command_simple(model_path, command_str):
    """
    helper function to process interactive help commands 'cd ..', 'cd', 'top', or 'ls'
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

    if command_str == 'ls':
      return canonical_path

    # must be 'top' or 'cd'
    return '/'


def parse_dir_command_cd_path(model_path, command_str):
    """
    helper function to process interactive help command 'cd [path]'
    :param model_path: the starting model path before the command
    :param command_str: the command
    :return: the resulting path (an absolute canonical path)
    """

    canonical_path = canonical_path_from_model_path(model_path)

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


def parse_dir_command_all(model_path, command_str):
    """
    helper function to process interactive help commands 'cd [path]', 'cd ..', 'cd', 'top', or 'ls'
    :param model_path: the starting model path before the command
    :param command_str: the command
    :return: the resulting path (an absolute canonical path)
    """

    if command_str == 'cd ..' or command_str == 'cd' or command_str == 'top' or command_str == 'ls':
      return parse_dir_command_simple(model_path, command_str)
    else:
      return parse_dir_command_cd_path(model_path, command_str) # handle 'cd [path]'


def interactive_help_prompt(model_path, input_file):
    """
    Gets the next command from stdin or a file.
    :param model_path: a current model path
    :param input_file: specify a file to get input from file instead of stdin.
    :param printer: a model help printer
    :return: returns when user types 'exit'
    """

    # prompt using sys.stdout.write to avoid newline
    sys.stdout.write("[" + model_path + "] --> ")
    sys.stdout.flush()

    if not input_file:
      command_str = raw_input("") # get command from stdin 

    else:
      # get command from file instead of stdin (undocumented feature)
      command_str = input_file.readline()
      if not command_str:
        command_str = 'exit' # reached EOF
      else:
        command_str = command_str.rstrip(os.linesep)

      # show retrieved command_str right after the prompt
      print(command_str)

    command_str = " ".join(command_str.split()) # remove extra white-space
    return command_str


def interactive_help_print_path(printer, model_path, history):
    """
    Prints help for the given model_path, or an error message.
    Also updates the help history on success.
    :param model_path: the model path 
    :param history: history of successful model paths
    :param printer: a model help printer
    """
    try:
      printer.print_model_help(model_path, ControlOptions.NORMAL)

      # the print_model_help succeeded, add successful path to the history
      if history[-1] != model_path:
        history.append(model_path)

    except CLAException, ex:
      print("Error getting '" + model_path + "': " + ex.getLocalizedMessage())
      interactive_help_print_short_instructions()


def interactive_help_print_short_instructions():
    """
    Prints short instructions for interactive help.
    """
    print("In interactive mode! Type 'help' for help.")


def interactive_help_print_full_instructions():
    """
    Prints full instructions for interactive help.
    """
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


def interactive_help_process_command(printer, model_path, command_str, history):
    """
    Process an interactive help command.
    :param printer: a model help printer
    :param model_path: current model path before applying command
    :param history: current history, a new model path added is added if command changes it
    :param command_str: the command
    """

    if command_str == 'help':
      interactive_help_print_full_instructions()

    elif command_str == 'history':
      for line in history:
        print(line)

    elif command_str.count(' ') > 1:
      print("Syntax error '" + command_str + "'")
      interactive_help_print_short_instructions()

    elif command_str == 'ls' or command_str == 'cd' or command_str == 'top' or command_str.startswith('cd '):
      canonical_path = parse_dir_command_all(model_path, command_str)
      model_path = model_path_from_canonical_path(canonical_path)
      interactive_help_print_path(printer, model_path, history)

    elif command_str:
      print("Unknown command '" + command_str + "'")
      interactive_help_print_short_instructions()


def interactive_help_main_loop(model_path, printer):
    """
    Runs the interactive help.
    :param model_path: the model path to start with
    :param printer: a model help printer
    :return: returns when user types 'exit'
    """
    _method_name = 'interactive_help_main_loop'

    __logger.entering(model_path, class_name=_class_name, method_name=_method_name)

    # setup starting history
    history = ['top']
    if history[-1] != model_path:
      history.append(model_path)

    # optionally get input from file instead of stdin (undocumented feature)
    input_file_name = os.environ.get('WDT_INTERACTIVE_MODE_INPUT_FILE')
    input_file = None
    if input_file_name:
      input_file = open(input_file_name, "r")

    interactive_help_print_short_instructions()

    while True:

      command_str = interactive_help_prompt(model_path, input_file)

      if command_str == 'exit':
        break

      interactive_help_process_command(printer, model_path, command_str, history)

      model_path = history[-1]

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
      interactive_help_main_loop(model_path, printer)
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
