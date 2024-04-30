"""
Copyright (c) 2020, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re
import sys

from oracle.weblogic.deploy.util import CLAException

from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.modelhelp.model_help_printer import ModelHelpPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.modelhelp.model_help_utils import PathOptions
from wlsdeploy.util import model
from wlsdeploy.util import string_utils
from wlsdeploy.util.exit_code import ExitCode

_class_name = 'ModelHelpInteractivePrinter'
SIMPLE_COMMAND_REGEX = re.compile(r'^top$|^(cd|ls|cat)(?:\s+(\.\.(?:/[a-zA-Z0-9#.]+)*/?))?$')
LIST_COMMANDS = ['ls', 'cat']

class ModelHelpInteractivePrinter(ModelHelpPrinter):
    def __init__(self, model_context, aliases, logger):
        ModelHelpPrinter.__init__(self, model_context, aliases, logger)

    def interactive_help_main_loop(self):
        _method_name = 'interactive_help_main_loop'

        self._logger.entering(class_name=_class_name, method_name=_method_name)

        # setup starting history
        history = ['top']

        model_path = 'top'

        # initial command (seeded from the command line)
        command_str = 'cd %s' % model_path

        self._output_buffer.add_output()
        self._interactive_help_print_short_instructions()
        self._output_buffer.add_output()
        self._output_buffer.add_message('WLSDPLY-10119', model_path)

        # JLine requires Java 1.8.0
        reader = None
        if string_utils.is_java_version_or_above('1.8.0'):
            from org.jline.terminal import TerminalBuilder
            from org.jline.reader import LineReaderBuilder
            from org.jline.reader.impl.completer import StringsCompleter

            completer = StringsCompleter(['cat', 'cd', 'ls', 'top', 'exit'])
            terminal = TerminalBuilder.terminal()
            reader = LineReaderBuilder.builder().terminal(terminal).completer(completer).build()

        while True:
            if command_str == 'exit':
                break

            if reader:
                reader.getHistory().add(command_str)

            # the "process command" prints the help (or error) for the command_str
            # plus appends a new path to the history if the str specifies a successful directory change

            self._interactive_help_process_command(history[-1], command_str, history)
            self._output_buffer.add_output()
            self._output_buffer.print_output()

            command_str = _interactive_help_prompt(history[-1], reader)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

    def _interactive_help_process_command(self, model_path, command_str, history):
        """
        Process an interactive help command.
        :param model_path: current model path before applying command
        :param history: current history, a new model path added is added if command changes it
        :param command_str: the command
        """

        command_str = command_str.strip()
        try:
            if command_str == 'help':
                self._interactive_help_print_full_instructions()

            elif command_str == 'history':
                self._output_buffer.add_output('')
                for line in history:
                    self._output_buffer.add_output(line)

            elif len(command_str.split()) > 2:
                self._output_buffer.clear()
                self._output_buffer.add_output()
                self._output_buffer.add_message('WLSDPLY-10117', command_str)
                self._output_buffer.add_output()
                self._interactive_help_print_short_instructions()

            elif command_str == 'cd' or command_str == 'top' or command_str.startswith('cd '):
                canonical_path = self._parse_dir_command_all(model_path, command_str)
                model_path = _model_path_from_canonical_path(canonical_path)
                self._handle_cd(model_path, history)

            elif command_str == 'ls' or command_str.startswith('ls '):
                canonical_path = self._parse_dir_command_all(model_path, command_str)
                model_path = _model_path_from_canonical_path(canonical_path)
                self._handle_ls(model_path)

            elif command_str == 'cat' or command_str.startswith('cat '):
                canonical_path = self._parse_dir_command_all(model_path, command_str)
                model_path = _model_path_from_canonical_path(canonical_path)
                self._handle_cat(model_path)

            elif command_str:
                self._output_buffer.clear()
                self._output_buffer.add_output()
                self._output_buffer.add_message('WLSDPLY-10120', command_str)
                self._output_buffer.add_output()
                self._interactive_help_print_short_instructions()
        except CLAException, ex:
            self._handle_error_message('WLSDPLY-10121', ex.getLocalizedMessage())
            self._interactive_help_print_short_instructions()

    def _parse_dir_command_all(self, model_path, command_str):
        """
        helper function to process interactive help commands 'cd [path]', 'cd ../Server', 'cd', 'top', or 'ls ../..'
        :param model_path: the starting model path before the command
        :param command_str: the command
        :return: the resulting path (an absolute canonical path)
        """

        matcher = SIMPLE_COMMAND_REGEX.match(command_str)
        if matcher is not None:
            return _parse_dir_command_simple(model_path, matcher)
        else:
            return self._parse_dir_command_cd_path(model_path, command_str) # handle 'cd [path] and ls [path]'

    def _parse_dir_command_cd_path(self, model_path, command_str):
        """
        helper function to process interactive help command 'cd [path]'
        :param model_path: the starting model path before the command
        :param command_str: the 'cd' command
        :return: the resulting path (an absolute canonical path)
        """
        space_index = command_str.index(' ')
        ret_path = command_str[space_index:].replace(':','').strip()
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
            return self._add_section_if_missing(ret_path, tokens[1])

        # this is a relative path, so append it to the current path

        canonical_path = _canonical_path_from_model_path(model_path)

        if canonical_path == '/':
            return '/%s' % ret_path

        return '%s/%s' % (canonical_path, ret_path)

    def _add_section_if_missing(self, canonical_path, token):
        """
        helper function to try find and prepend section if missing
        :param canonical_path: candidate canonical path starting with "/"
        :param token: first token in canonical_path
        :return: potentially updated canonical path
        """

        if token not in model.get_model_top_level_keys():
            for section_name in model.get_model_top_level_keys():
                if token in self._aliases.get_model_section_top_level_folder_names(section_name):
                    return '/' + section_name + canonical_path

        return canonical_path

    def _handle_cd(self, model_path, history):
        try:
            if history[-1] != model_path:
                # This is kind of hacky.  Instead of trying to separate out the validation
                # code to validate the model_path, just call the code that would do the work
                # and throw away the output if it returns successfully.
                #
                lines = self._output_buffer.get_buffer_contents()
                # disallow cd to an attribute
                self.print_model_help(model_path, ControlOptions.NORMAL, print_output=False,
                                      path_option=PathOptions.FOLDER)
                self._output_buffer.clear()
                self._output_buffer.append(lines)
                history.append(model_path)
        except CLAException, ex:
            self._handle_error_message('WLSDPLY-10122', model_path, ex.getLocalizedMessage())
            self._interactive_help_print_short_instructions()

    def _handle_ls(self, model_path):
        """
        Prints help for the given model_path, or an error message.
        :param model_path: the model path
        """
        try:
            self.print_model_help(model_path, ControlOptions.NORMAL)
        except CLAException, ex:
            self._handle_error_message('WLSDPLY-10123', model_path, ex.getLocalizedMessage())
            self._interactive_help_print_short_instructions()

    def _handle_cat(self, model_path):
        """
        Prints attribute help for the given model_path, or an error message.
        :param model_path: the model path
        """
        try:
            self.print_model_help(model_path, ControlOptions.NORMAL, path_option=PathOptions.ATTRIBUTE)
        except CLAException, ex:
            self._handle_error_message('WLSDPLY-10138', model_path, ex.getLocalizedMessage())
            self._interactive_help_print_short_instructions()

    def _interactive_help_print_full_instructions(self):
        """
        Prints full instructions for interactive help.
        """
        self._output_buffer.add_output()
        self._add_message('WLSDPLY-10124', suffix=':')
        self._output_buffer.add_output()
        self._add_message('WLSDPLY-10125', prefix='  ls                      - ')
        self._add_message('WLSDPLY-10126', prefix='  ls [path]               - ')
        self._add_message('WLSDPLY-10127', prefix='  top, cd, cd /, cd top   - ')
        self._add_message('WLSDPLY-10128', prefix='  cd [path]               - ')
        self._add_message('WLSDPLY-10140', prefix='  cat [path]              - ')
        self._add_message('WLSDPLY-10129', prefix='  history                 - ')
        self._add_message('WLSDPLY-10130', prefix='  exit                    - ')
        self._output_buffer.add_output()
        self._add_message('WLSDPLY-10131', prefix='  [path] ', suffix=':')
        self._add_message('WLSDPLY-10132', prefix='    x/y/z               - ')
        self._add_message('WLSDPLY-10132', prefix='    ../../a             - ')
        self._add_message('WLSDPLY-10133', prefix='    section[:[/a/b/c]]  - ')
        self._add_message('WLSDPLY-10134', prefix='    /a[/b[/c]]          - ')
        self._output_buffer.add_output()
        self._add_message('WLSDPLY-10135', suffix=':')
        self._output_buffer.add_output()
        self._output_buffer.add_output('  %s' % str(', '.join(model.get_model_top_level_keys())))
        self._output_buffer.add_output()
        self._add_message('WLSDPLY-10136', suffix=':')
        self._output_buffer.add_output()
        self._output_buffer.add_output('  cd topology')
        self._output_buffer.add_output('  cd topology:/Server/Log/StdoutSeverity')
        self._output_buffer.add_output('  cd /Server/Log/StdoutSeverity')
        self._output_buffer.add_output('  cd ../../../ServerTemplate/DynamicServers')
        self._output_buffer.add_output()

    def _handle_error_message(self, key, *args):
        self._output_buffer.clear()
        self._output_buffer.add_output()
        self._output_buffer.add_message(key, *args)
        self._output_buffer.add_output()

    def _interactive_help_print_short_instructions(self):
        """
        Prints short instructions for interactive help.
        """
        self._output_buffer.add_message('WLSDPLY-10118')

    def _add_message(self, key, *args, **kwargs):
        prefix = ''
        suffix = ''
        if 'prefix' in kwargs:
            prefix = kwargs['prefix']
        if 'suffix' in kwargs:
            suffix = kwargs['suffix']
        message = exception_helper.get_message(key, *args)
        self._output_buffer.add_output('%s%s%s' % (prefix, message, suffix))


def _interactive_help_prompt(model_path, reader):
    """
    Gets the next command from stdin or using JLine.
    :param model_path: a current model path
    :param reader: JLine reader, or None if JLine not supported
    :return: returns when user types 'exit'
    """
    prompt = '[%s] --> ' % model_path

    if reader:
        command_str = reader.readLine(prompt)
    else:
        # prompt using sys.stdout.write to avoid newline
        sys.stdout.write(prompt)
        sys.stdout.flush()
        command_str = raw_input('') # get command from stdin

    command_str = ' '.join(command_str.split()) # remove extra white-space
    return command_str


def _canonical_path_from_model_path(model_path):
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


def _model_path_from_canonical_path(canonical_path):
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


def _parse_dir_command_simple(model_path, matcher):
    """
    helper function to process interactive help commands 'cd ..', 'cd', 'top', or 'ls'
    :param model_path: the starting model path before the command
    :param matcher: the regular expression MatchObject of the command
    :return: the resulting path (an absolute canonical path)
    """

    canonical_path = _canonical_path_from_model_path(model_path)
    groups = matcher.groups()
    if len(groups) == 2:
        dot_dot_path = groups[1]
        if dot_dot_path is not None:
            new_path = _resolve_dot_dot_path(canonical_path, dot_dot_path)
        elif groups[0] in LIST_COMMANDS:
            new_path = canonical_path
        else:
            new_path = '/'
    elif len(groups) == 1 and groups[0] in LIST_COMMANDS:
        new_path = canonical_path
    else:
        # Either cd with no argument or top
        new_path = '/'
    return new_path


def _resolve_dot_dot_path(canonical_path, dot_dot_path):
    canonical_path_elements = canonical_path.split('/')
    new_path_elements = list()
    for canonical_path_element in canonical_path_elements:
        if canonical_path_element != '':
            new_path_elements.append(canonical_path_element)

    dot_dot_path_elements = dot_dot_path.split('/')
    if dot_dot_path_elements[-1] == '':
        dot_dot_path_elements.pop()
    for dot_dot_path_element in dot_dot_path_elements:
        if dot_dot_path_element == '..':
            if len(new_path_elements) > 0:
                new_path_elements.pop()
            else:
                ex = exception_helper.create_cla_exception(ExitCode.OK, 'WLSDPLY-10116', dot_dot_path,
                                                           _model_path_from_canonical_path(canonical_path))
                raise ex
        else:
            new_path_elements.append(dot_dot_path_element)
    return '/%s' % '/'.join(new_path_elements)
