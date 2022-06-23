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

def canonicalize_path(model_path):
    """
    canonicalize internally used model path so it:
    -  has no ':'
    -  always starts with '/'
    -  does not end with a slash unless at top
    -  converts 'top' to '/'
    :param model_path: the model path
    :return: canonicalized path
    """
    model_path = model_path.replace(':','')
    while model_path.endswith('/'):
      model_path = model_path[:-1]
    while model_path.startswith('/'):
      model_path = model_path[1:]
    if model_path == 'top':
      model_path = ''
    model_path = '/' + model_path
    return model_path

def interactive_help(model_path,printer):
    """
    Runs the interactive help.
    :param model_path: the model path to start with
    :param printer: a model help printer
    :return: returns when user types 'exit'
    """
    _method_name = 'interactive_help'

    __logger.entering(model_path, class_name=_class_name, method_name=_method_name)

    # list of all sections (not including 'top')
    top_level_keys = model.get_model_top_level_keys()

    # setup starting history
    if model_path == 'top':
      history = ['top']
    else:
      history = ['top', model_path]

    model_path = canonicalize_path(model_path)

    print "In interactive mode! Type 'help' for help."
    while True:

      model_prompt = history[-1]

      input = raw_input("[" + model_prompt + "] --> ")

      input = " ".join(input.split()) # remove extra white-space
      if input == 'help':
        print ''
        print 'Commands:'
        print ''
        print '  ls                      - list contents of current location'
        print '  top, cd, cd /, cd top   - go to "top"'
        print '  cd x[/[...]]            - relative change (go to child location x...)'
        print '  cd section[:/[...]]     - absolute change (go to exact section and location)'
        print '  cd ..                   - go up'
        print '  history                 - history of visited locations'
        print '  exit                    - exit'
        print ''
        print 'Sections:'
        print ''
        print '  ' + str(', '.join(top_level_keys))
        print ''
        print 'Example:'
        print ''
        print '  cd topology:/Server/Log/StdoutSeverity'
        print ''
        continue
      elif input == 'history':
        for line in history:
          print line
        continue
      elif input == 'exit':
        break
      elif input == 'ls':
        # jython requires something here, and sonar doesn't like dummy statements
        if model_path == 'Inconceivable!':
          print "You keep using that word. I do not think it means what you think it means."
      elif input == 'cd ..':
        model_path = model_path[:model_path.rfind('/')]
        if not model_path:
          model_path = '/'
      elif input == 'cd':
        model_path = '/'
      elif input == 'top':
        model_path = '/'
      elif input.count(' ') > 1:
        print "Syntax error '" + input + "'"
        print "In interactive mode! Type 'help' for help."
        continue
      elif input.startswith('cd '):
        input = input[3:]
        input = input.replace(':','')
        while input.endswith('/'):
          input = input[:-1]

        # if first token is a section name, make it an absolute path
        slash_pos = input.find('/') 
        if slash_pos == -1:
          first_token = input
        elif slash_pos > 0:
          first_token = input[:slash_pos]
        if first_token in top_level_keys:
          input = '/' + input

        # if first token is 'top' treat it like its starting absolute path
        if first_token == 'top':
          if slash_pos > 0:
            input = input[3:]
          else:
            input = '/'
          
        if not input:
          model_path = '/'
        elif input.startswith('/'):
          model_path = input
        elif model_path == '/':
          model_path = "/" + input
        else:
          model_path = model_path + "/" + input
      elif input:
        print "Unknown command '" + input + "'"
        print "In interactive mode! Type 'help' for help."
        continue
      else:
        # no input, just prompt again 
        continue

      try:
        # prompt and get help using the public path format

        model_prompt = model_path[1:]
        slashpos = model_prompt.find('/')
        if slashpos > 0:
          model_prompt = model_prompt[0:slashpos] + ':' + model_prompt[slashpos:]
        if not model_prompt:
          model_prompt = 'top'

        printer.print_model_help(model_prompt, ControlOptions.NORMAL)

        if not history[-1] == model_prompt:
          history.append(model_prompt)

      except CLAException, ex:
        print "Error getting '" + model_prompt + "': " + ex.getLocalizedMessage()
        print "In interactive mode! Type 'help' for help."
        model_path = history[-1]  # last successful path
        model_path = canonicalize_path(model_path)

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
