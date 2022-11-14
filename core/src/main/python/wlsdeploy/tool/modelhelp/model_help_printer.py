"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from oracle.weblogic.deploy.exception import ExceptionHelper

from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.modelhelp.model_kubernetes_printer import ModelKubernetesPrinter
from wlsdeploy.tool.modelhelp.model_sample_printer import ModelSamplePrinter
from wlsdeploy.util import model
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode

_class_name = "ModelHelpPrinter"
MODEL_PATH_PATTERN = re.compile(r'(^[a-zA-Z]+:?)?(/[a-zA-Z0-9^/]+)?$')


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

    def print_model_help(self, model_path, control_option):
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
        :raises CLAException: if a problem is encountered
        """

        model_path_tokens = self._parse_model_path(model_path)
        folder_path = '/'.join(model_path_tokens[1:])
        model_path = '%s:/%s' % (model_path_tokens[0], folder_path)

        # print format information
        print("")
        if control_option == ControlOptions.RECURSIVE:
            print(_format_message('WLSDPLY-10102', model_path))
        elif control_option == ControlOptions.FOLDERS_ONLY:
            print(_format_message('WLSDPLY-10103', model_path))
        elif control_option == ControlOptions.ATTRIBUTES_ONLY:
            print( _format_message('WLSDPLY-10104', model_path))
        else:
            print(_format_message('WLSDPLY-10105', model_path))

        if model_path_tokens[0] == KUBERNETES:
            sample_printer = ModelKubernetesPrinter(self._model_context)
            sample_printer.print_model_sample(model_path_tokens, control_option)
        else:
            sample_printer = ModelSamplePrinter(self._aliases, self._logger)
            sample_printer.print_model_sample(model_path_tokens, control_option)

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
    return ExceptionHelper.getMessage(key, list(args))
