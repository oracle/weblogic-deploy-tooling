"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from oracle.weblogic.deploy.exception import ExceptionHelper
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.tool.modelhelp import model_help_utils
from wlsdeploy.tool.modelhelp.model_help_utils import ControlOptions
from wlsdeploy.tool.modelhelp.model_sample_printer import ModelSamplePrinter
from wlsdeploy.util import model
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.alias_helper import AliasHelper

_class_name = "ModelHelpPrinter"
MODEL_PATH_PATTERN = re.compile(r'^([a-zA-Z]+:?)?((/[a-zA-Z0-9]+)*)?$')


class ModelHelpPrinter(object):
    """
    Class for printing the recognized model metadata to STDOUT.
    """

    def __init__(self, aliases, logger):
        """
        :param aliases: A reference to an Aliases class instance
        :param logger: A reference to the platform logger to write to, if a log entry needs to be made
        """
        self._logger = logger
        self._alias_helper = AliasHelper(aliases, self._logger, ExceptionType.CLA)

    def print_model_help(self, model_path, control_option, as_sample=False):
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
        :param as_sample: specifies that a model sample should be output
        :raises CLAException: if a problem is encountered
        """

        # print filter information, if not NORMAL
        if control_option == ControlOptions.RECURSIVE:
            print
            print _format_message('WLSDPLY-10102')
        elif control_option == ControlOptions.FOLDERS_ONLY:
            print
            print _format_message('WLSDPLY-10103')
        elif control_option == ControlOptions.ATTRIBUTES_ONLY:
            print
            print _format_message('WLSDPLY-10104')

        model_path_tokens = self._parse_model_path(model_path)

        section_name = model_path_tokens[0]
        valid_section_folder_keys = self._alias_helper.get_model_section_top_level_folder_names(section_name)

        if as_sample:
            sample_printer = ModelSamplePrinter(self._alias_helper, self._logger)
            sample_printer.print_model_sample(model_path_tokens, control_option)
        else:
            if model_path_tokens[0] == 'top':
                self._print_model_top_level_help()
            elif len(model_path_tokens) == 1:
                self._print_model_section_help(section_name, valid_section_folder_keys, control_option)
            else:
                self._print_model_folder_help(model_path_tokens, valid_section_folder_keys, control_option)

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
            ex = exception_helper.create_cla_exception('WLSDPLY-10108', model_path)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        self._logger.finest('match.group(1)={0}, match.group(2)={1}', str(match.group(1)), str(match.group(2)),
                            class_name=_class_name, method_name=_method_name)

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
            ex = exception_helper.create_cla_exception('WLSDPLY-10109', section, str(', '.join(top_level_keys)))
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
            folder_keys = self._alias_helper.get_model_section_top_level_folder_names(section)
            if top_folder in folder_keys:
                return section

        ex = exception_helper.create_cla_exception('WLSDPLY-10101', top_folder)
        self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    def _print_model_top_level_help(self):
        """
        Prints out all the valid section names for a model.
        The -recursive flag is disregarded for this case.
        """
        _method_name = '_print_model_top_level_help'
        self._logger.finest('sections={0}', KNOWN_TOPLEVEL_MODEL_SECTIONS, class_name=_class_name,
                            method_name=_method_name)

        title = _format_message('WLSDPLY-10113')

        # Print 'All Sections:' header
        print
        _print_indent(title, 0)
        print

        for section in KNOWN_TOPLEVEL_MODEL_SECTIONS:
            _print_indent(section, 1)

    def _print_model_section_help(self, section_name, valid_section_folder_keys, control_option):
        """
        Prints the help for a section of a model, when just the section_name[:] is provided
        :param section_name: the name of the model section
        :param valid_section_folder_keys: list of the valid top folders in the specified section
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        _method_name = '_print_model_section_help'

        self._logger.finest('1 section_name={0}', section_name, class_name=_class_name, method_name=_method_name)

        location_path = '%s:' % section_name
        self._logger.finest('1 location_path={0}', location_path, class_name=_class_name, method_name=_method_name)

        model_section = _format_message('WLSDPLY-10106', location_path)

        # Print 'Section: <model_section>' label and field
        print
        _print_indent(model_section, 0)

        if model_help_utils.show_attributes(control_option):
            attributes_location = self._alias_helper.get_model_section_attribute_location(section_name)
            if attributes_location is not None:
                self._print_attributes_help(attributes_location, 1)

        if model_help_utils.show_folders(control_option):
            print
            _print_indent(_format_message('WLSDPLY-10107'), 1)
            valid_section_folder_keys.sort()

            for section_folder_key in valid_section_folder_keys:
                _print_indent(section_folder_key, 2)

                if control_option == ControlOptions.RECURSIVE:
                    model_location = LocationContext().append_location(section_folder_key)
                    self._print_subfolders_help(model_location, control_option, 2)

    def _print_model_folder_help(self, model_path_tokens, valid_section_folder_keys, control_option):
        """
        Prints the help for a folder in a model, when more than just the section_name[:] is provided.
        The section name in the first token was already validated.
        :param model_path_tokens: a Python list of path elements built from model path
        :param valid_section_folder_keys: A list of valid folder names for the model section in the path
        :param control_option: A command-line switch that controls what is output to STDOUT
        """
        _method_name = '_print_model_folder_help'

        self._logger.finest('1 model_path_tokens={0}, control_option={1}, valid_section_folder_keys={0}',
                            str(model_path_tokens), ControlOptions.from_value(control_option),
                            str(valid_section_folder_keys), class_name=_class_name, method_name=_method_name)

        section_name = model_path_tokens[0]
        top_folder = model_path_tokens[1]
        if top_folder not in valid_section_folder_keys:
            ex = exception_helper.create_cla_exception('WLSDPLY-10110', section_name + ':', top_folder,
                                                       ', '.join(valid_section_folder_keys))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        # Populate the location context using model_path_tokens[1:]
        model_location = LocationContext()
        for folder_key in model_path_tokens[1:]:
            model_location.append_location(folder_key)
            name_token = self._alias_helper.get_name_token(model_location)
            if name_token is not None:
                model_location.add_name_token(name_token, '%s-0' % folder_key)

            self._logger.finest('2 model_location={0}', model_location, class_name=_class_name,
                                method_name=_method_name)

        folder_path = '/'.join(model_path_tokens[1:])
        model_path = _format_message('WLSDPLY-10105', '%s:/%s' % (section_name, folder_path))
        type_name = self._get_folder_type_name(model_location)
        if type_name is not None:
            model_path += " (" + type_name + ")"

        # Print 'Path: <model_section>' header
        print
        _print_indent(model_path, 0)

        if model_help_utils.show_attributes(control_option):
            # Print the attributes associated with location context
            self._print_attributes_help(model_location, 1)

        if model_help_utils.show_folders(control_option):
            # Print the folders associated with location context
            print
            _print_indent(_format_message('WLSDPLY-10107'), 1)
            self._print_subfolders_help(model_location, control_option, 1)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return

    def _print_subfolders_help(self, model_location, control_option, indent_level):
        """
        Prints the help for the folders in a model location, without header or leading space.
        :param model_location: the model location being worked on
        :param control_option: a command-line switch that controls what is output to STDOUT
        :param indent_level: the level to indent by, before printing output
        """
        _method_name = '_print_subfolders_help'

        valid_subfolder_keys = self._alias_helper.get_model_subfolder_names(model_location)
        self._logger.finest('3 aliases.get_model_subfolder_names(model_location) returned: {0}',
                            str(valid_subfolder_keys), class_name=_class_name, method_name=_method_name)

        if not valid_subfolder_keys:
            return

        valid_subfolder_keys.sort()

        for key in valid_subfolder_keys:
            model_location.append_location(key)
            name_token = self._alias_helper.get_name_token(model_location)
            if name_token is not None:
                model_location.add_name_token(name_token, '%s-0' % key)

            self._logger.finest('3 model_location={0}', model_location, class_name=_class_name,
                                method_name=_method_name)

            text = key
            type_name = self._get_folder_type_name(model_location)
            if type_name is not None:
                text += " (" + type_name + ")"

            _print_indent(text, indent_level + 1)

            if control_option == ControlOptions.RECURSIVE:
                # Call this method recursively
                self._print_subfolders_help(model_location, control_option, indent_level + 1)

            model_location.pop_location()

    def _print_attributes_help(self, model_location, indent_level):
        """
        Prints out the help for the attributes in a model location
        :param model_location: An object containing data about the model location being worked on
        :param indent_level: The level to indent by, before printing output
        """
        _method_name = '_print_attributes_help'

        attr_infos = self._alias_helper.get_model_attribute_names_and_types(model_location)
        self._logger.finer('WLSDPLY-05012', str(model_location), str(attr_infos),
                           class_name=_class_name, method_name=_method_name)

        # Print 'Valid Attributes:' area label
        print
        _print_indent(_format_message('WLSDPLY-10111'), indent_level)

        if attr_infos:
            maxlen = 0
            for key in attr_infos:
                if len(key) > maxlen:
                    maxlen = len(key)
            formatted_string = '%-' + str(maxlen) + 's\t%s'

            attr_list = attr_infos.keys()
            attr_list.sort()
            for attr_name in attr_list:
                msg = formatted_string % (attr_name, attr_infos[attr_name])
                _print_indent(msg, indent_level + 1)

    def _get_folder_type_name(self, location):
        """
        Return text indicating the type of a folder, such as "multiple".
        :param location: the location to be checked
        :return: name of the folder type to be displayed, or None
        """
        if self._alias_helper.is_artificial_type_folder(location):
            return None
        if self._alias_helper.supports_multiple_mbean_instances(location):
            return "multiple"
        return None


def _format_message(key, *args):
    """
    Format the specified message key with the specified arguments.
    :param key: the message key
    :return: the formatted text message
    """
    return ExceptionHelper.getMessage(key, list(args))


def _print_indent(msg, level=1):
    """
    Print a message at the specified indent level.
    :param msg: the message to be printed
    :param level: the indent level
    """
    result = ''
    i = 0
    while i < level:
        result += '  '
        i += 1
    print '%s%s' % (result, msg)
