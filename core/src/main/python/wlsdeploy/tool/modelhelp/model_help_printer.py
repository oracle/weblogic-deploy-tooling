"""
Copyright (c) 2020, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re


from wlsdeploy.aliases.model_constants import CRD_MODEL_SECTIONS
from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.modelhelp.model_crd_section_printer import ModelCrdSectionPrinter
from wlsdeploy.tool.modelhelp.model_help_utils import PathOptions
from wlsdeploy.tool.modelhelp.model_sample_printer import ModelSamplePrinter
from wlsdeploy.util import model
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode

_class_name = "ModelHelpPrinter"
MODEL_PATH_PATTERN = re.compile(r'(^[a-zA-Z]+:?)?(/[a-zA-Z0-9#^/]+)?$')


class ModelHelpOutputBuffer(object):
    """
    Class for holding output bound for STDOUT until after processing is successful
    """

    def __init__(self):
        self._buffer = list()

    def clear(self):
        self._buffer = list()

    def get_buffer_contents(self):
        return list(self._buffer)

    def append(self, contents):
        self._buffer.extend(contents)

    def add_output(self, line=''):
        self._buffer.append(line)

    def add_message(self, key, *args):
        self._buffer.append(exception_helper.get_message(key, *args))

    def print_output(self):
        for line in self._buffer:
            print(line)
        self.clear()


class ModelHelpPrinter(object):
    """
    Class for printing the recognized model metadata to STDOUT.
    """

    def __init__(self, model_context, aliases, logger):
        """
        :param model_context: The model context
        :param aliases: A reference to an Aliases class instance
        :param logger: A reference to the platform logger to write to, if a log entry needs to be made
        """
        self._logger = logger
        self._aliases = aliases
        self._model_context = model_context
        self._output_buffer = ModelHelpOutputBuffer()

    def get_output_buffer(self):
        return self._output_buffer

    def print_model_help(self, model_path, control_option, print_output=True, path_option=PathOptions.ANY):
        """
        Prints out the help information for a given '''model_path'''. '''model_path''' needs to be specified
        using the following pattern:

                <model_section>[:/<section_folder>[/<section_subfolder>|...]]

        Examples:
                'domainInfo', 'domainInfo:' or 'domainInfo:/' (all 3 are equivalent)
                'topology:/Server'
                'resources:/JDBCSystemResource/JdbcResource/JDBCDriverParams'
                'appDeployments:/Application'

        :param model_path: a formatted string containing the model path
        :param control_option: a command-line switch that controls what is output
        :param print_output: determine if the result is printed to the output
        :param path_option: used to interpret the path as a folder, attribute, or either
        :raises CLAException: if a problem is encountered
        """

        model_path_tokens = self._parse_model_path(model_path)
        folder_path = '/'.join(model_path_tokens[1:])
        model_path = '%s:/%s' % (model_path_tokens[0], folder_path)

        # print format information
        self._output_buffer.add_output()
        if control_option == ControlOptions.RECURSIVE:
            self._output_buffer.add_output(_format_message('WLSDPLY-10102', model_path))
        elif control_option == ControlOptions.FOLDERS_ONLY:
            self._output_buffer.add_output(_format_message('WLSDPLY-10103', model_path))
        elif control_option == ControlOptions.ATTRIBUTES_ONLY:
            self._output_buffer.add_output(_format_message('WLSDPLY-10104', model_path))
        else:
            self._output_buffer.add_output(_format_message('WLSDPLY-10105', model_path))

        if model_path_tokens[0] in CRD_MODEL_SECTIONS:
            sample_printer = ModelCrdSectionPrinter(self._model_context, self._output_buffer)
            sample_printer.print_model_sample(model_path_tokens, control_option, path_option)
        else:
            sample_printer = ModelSamplePrinter(self._aliases, self._logger, self._output_buffer)
            sample_printer.print_model_sample(model_path_tokens, control_option, path_option)

        if print_output:
            self._output_buffer.print_output()

    def _parse_model_path(self, model_path):
        """
        Parse the specified model_path into a Python list of elements.
        The first element will be the section name.
        If not specified, the section name will be derived from the first path element.
        :param model_path: a string contain the model path to parse
        :return: a python list containing the section name, then each folder element
        :raises: CLAException if the path cannot be parsed, or the section name is invalid
        """
        _method_name = '_parse_model_path'

        self._logger.entering(model_path, class_name=_class_name, method_name=_method_name)

        match = MODEL_PATH_PATTERN.match(model_path)
        if match is None:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-10108', model_path)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        self._logger.finest('match.group(1)={0}, match.group(2)={1}', str_helper.to_string(match.group(1)),
                            str_helper.to_string(match.group(2)), class_name=_class_name, method_name=_method_name)

        section = match.group(1)
        path = match.group(2)

        folders = []
        if path is not None:
            for folder in path.split('/'):
                # trailing or duplicate slashes may cause empty folder name
                if len(folder) > 0:
                    folders.append(folder)

        if section is None:
            section = self._get_section_for_folder_list(folders)

        section = section.replace(':', '')

        top_level_keys = model.get_model_top_level_keys()

        # 'top' is a special case for listing the sections
        all_section_keys = ['top']
        all_section_keys.extend(top_level_keys)

        if section not in all_section_keys:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-10109', section,
                                                       str_helper.to_string(', '.join(top_level_keys)))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        model_path_tokens = [section]
        model_path_tokens.extend(folders)
        return model_path_tokens

    def _get_section_for_folder_list(self, folder_list):
        """
        Derive the section name from the first folder in the specified list.
        :param folder_list: the list of folders in the model path
        :return: the section name
        :raises: CLAException if the section name cannot be determined
        """
        _method_name = '_get_section_for_folder_list'
        top_folder = folder_list[0]

        for section in KNOWN_TOPLEVEL_MODEL_SECTIONS:
            folder_keys = self._aliases.get_model_section_top_level_folder_names(section)
            if top_folder in folder_keys:
                return section

        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-10101', top_folder)
        self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def _format_message(key, *args):
    """
    Format the specified message key with the specified arguments.
    :param key: the message key
    :return: the formatted text message
    """
    return exception_helper.get_message(key, *args)
