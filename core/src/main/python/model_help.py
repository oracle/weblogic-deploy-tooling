"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the modelHelp tool.
"""
import os
import sys

from oracle.weblogic.deploy.util import CLAException

# Jython tools don't require sys.path modification
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.modelhelp.model_help_printer import ModelHelpPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import model
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
    CommandLineArgUtil.INTERACTIVE_MODE_SWITCH,
    CommandLineArgUtil.TARGET_SWITCH
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
                ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
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

def add_section_if_missing(aliases, canonical_path, token):
    """
    helper function to try find and prepend section if missing
    :param aliases: aliases
    :param canonical_path: candidate canonical path starting with "/"
    :param token: first token in canonical_path
    :return: potentially updated canonical path
    """

    if token not in model.get_model_top_level_keys():
      for section_name in model.get_model_top_level_keys():
        if token in aliases.get_model_section_top_level_folder_names(section_name):
          return '/' + section_name + canonical_path

    return canonical_path

def parse_dir_command_cd_path(aliases, model_path, command_str):
    """
    helper function to process interactive help command 'cd [path]'
    :param aliases: aliases
    :param model_path: the starting model path before the command
    :param command_str: the 'cd' command
    :return: the resulting path (an absolute canonical path)
    """

    print("Parsing")

    ret_path = command_str[3:].replace(':','').strip()
    while ret_path.endswith('/'):
      ret_path = ret_path[:-1]
    while ret_path.replace('//','/') != ret_path:
      ret_path = ret_path.replace('//','/')
    if ret_path.startswith('top/'):
      ret_path = ret_path[3:]
    while ret_path.startswith('/top/'):
      ret_path = ret_path[4:]

    if not ret_path or ret_path == 'top' or ret_path == '/':
      return '/'

    tokens = ret_path.split('/')

    if tokens[0] in model.get_model_top_level_keys():
      # if first token is a section name, make it an absolute path
      return '/' + ret_path

    if ret_path.startswith('/'):
      # user specified an absolute path '/token1[/...]'
      # (starts with '/' so there must be a second token (tokens[1]))
      return add_section_if_missing(aliases, ret_path, tokens[1])

    # this is a relative path, so append it to the current path

    canonical_path = canonical_path_from_model_path(model_path)

    if canonical_path == "/":
      return "/" + ret_path

    return canonical_path + "/" + ret_path


def parse_dir_command_all(aliases, model_path, command_str):
    """
    helper function to process interactive help commands 'cd [path]', 'cd ..', 'cd', 'top', or 'ls'
    :param aliases: aliases
    :param model_path: the starting model path before the command
    :param command_str: the command
    :return: the resulting path (an absolute canonical path)
    """

    if command_str == 'cd ..' or command_str == 'cd' or command_str == 'top' or command_str == 'ls':
      return parse_dir_command_simple(model_path, command_str)
    else:
      return parse_dir_command_cd_path(aliases, model_path, command_str) # handle 'cd [path]'


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
      print("")
      print("Error getting '" + model_path + "': " + ex.getLocalizedMessage())
      print("")
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
    print("  cd /folder[/...]        - find section that contains the folder and go there")
    print("  cd ..                   - go up")
    print("  history                 - history of visited locations")
    print("  exit                    - exit")
    print("")
    print("Sections:")
    print("")
    print("  " + str(', '.join(model.get_model_top_level_keys())))
    print("")
    print("Examples:")
    print("")
    print("  cd topology")
    print("  cd topology:/Server/Log/StdoutSeverity")
    print("  cd /Server/Log/StdoutSeverity")
    print("")


def interactive_help_process_command(aliases, printer, model_path, command_str, history):
    """
    Process an interactive help command.
    :param aliases: aliases
    :param printer: a model help printer
    :param model_path: current model path before applying command
    :param history: current history, a new model path added is added if command changes it
    :param command_str: the command
    """

    if command_str == 'help':
      interactive_help_print_full_instructions()

    elif command_str == 'history':
      for line in history:
        print("")
        print(line)

    elif command_str.count(' ') > 1:
      print("")
      print("Syntax error '" + command_str + "'")
      print("")
      interactive_help_print_short_instructions()

    elif command_str == 'ls' or command_str == 'cd' or command_str == 'top' or command_str.startswith('cd '):
      canonical_path = parse_dir_command_all(aliases, model_path, command_str)
      model_path = model_path_from_canonical_path(canonical_path)
      interactive_help_print_path(printer, model_path, history)

    elif command_str:
      print("")
      print("Unknown command '" + command_str + "'")
      print("")
      interactive_help_print_short_instructions()


def interactive_help_main_loop(aliases, model_path, printer):
    """
    Runs the interactive help.
    :param aliases: aliases
    :param model_path: the model path to start with
    :param printer: a model help printer
    :return: returns when user types 'exit'
    """
    _method_name = 'interactive_help_main_loop'

    __logger.entering(model_path, class_name=_class_name, method_name=_method_name)

    # setup starting history
    history = ['top']

    # optionally get input from file instead of stdin (undocumented feature)
    input_file_name = os.environ.get('WDT_INTERACTIVE_MODE_INPUT_FILE')
    input_file = None
    if input_file_name:
      input_file = open(input_file_name, "r")

    # initial command (seeded from the command line)
    command_str = "cd " + model_path

    print("")
    interactive_help_print_short_instructions()
    print("")
    print("Starting with '" + command_str + "'.")

    while True:
      if command_str == 'exit':
        break

      # the "process command" prints the help (or error) for the command_str
      # plus appends a new path to the history if the str specifies a successful directory change

      interactive_help_process_command(aliases, printer, history[-1], command_str, history)
      print("")

      # get the next command (from either stdin, or the input_file if input_file is set)

      command_str = interactive_help_prompt(history[-1], input_file)

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
    printer = ModelHelpPrinter(model_context, aliases, __logger)

    if model_context.get_interactive_mode_option():
      interactive_help_main_loop(aliases, model_path, printer)
    else:
      printer.print_model_help(model_path, control_option)

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
        model_path = model_context.get_trailing_argument(0)
        _exit_code = print_help(model_path, model_context)
    except CLAException, ve:
        __logger.severe('WLSDPLY-10112', _program_name, ve.getLocalizedMessage(), error=ve,
                        class_name=_class_name, method_name=_method_name)
        _exit_code = ExitCode.ERROR

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
