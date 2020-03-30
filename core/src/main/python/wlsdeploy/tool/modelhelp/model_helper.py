"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.util import model
from wlsdeploy.util.enum import Enum
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.alias_helper import AliasHelper

_class_name = "ModelHelper"
MODEL_PATH_PATTERN = re.compile(r'^([a-zA-Z]+:?)?((/[a-zA-Z0-9]+)*)?$')


class ModelHelper(object):
    """
    Class for printing the recognized model metadata to STDOUT.
    """
    ControlOptions = Enum(['NORMAL', 'RECURSIVE', 'FOLDERS_ONLY', 'ATTRIBUTES_ONLY'])

    def __init__(self, aliases, logger):
        """
        :param aliases: A reference to an Aliases class instance
        :param logger: A reference to the platform logger to write to, if a log entry needs to be made
        """
        self._logger = logger
        self._alias_helper = AliasHelper(aliases, self._logger, ExceptionType.VALIDATE)

    def print_model_path_usage(self, model_path, control_option):
        """
        Prints out the usage information for a given '''model_path'''. '''model_path''' needs to be specified
        using the following pattern:

                <model_section>[:/<section_folder>[/<section_subfolder>|...]]

        Examples:
                'domainInfo', 'domainInfo:' or 'domainInfo:/' (all 3 are equivalent)
                'topology:/Server'
                'resources:/JDBCSystemResource/JdbcResource/JDBCDriverParams'
                'appDeployments:/Application'

        :param model_path: A forward-slash delimited string contain the model path to print usage for
        :param control_option: A command-line switch that controls what is output to STDOUT
        :raises ValidationException: if an AliasException is raised during an invocation of an aliases API call.
        """

        # print filter information, if not NORMAL
        if control_option == self.ControlOptions.RECURSIVE:
            validation_utils.print_blank_lines()
            print validation_utils.format_message('WLSDPLY-10102')
        elif control_option == self.ControlOptions.FOLDERS_ONLY:
            validation_utils.print_blank_lines()
            print validation_utils.format_message('WLSDPLY-10103')
        elif control_option == self.ControlOptions.ATTRIBUTES_ONLY:
            validation_utils.print_blank_lines()
            print validation_utils.format_message('WLSDPLY-10104')

        model_path_tokens = self.__create_model_path_tokens(model_path)

        top_level_key = model_path_tokens[0]

        section_name = model_path_tokens[0]
        valid_section_folder_keys = self._alias_helper.get_model_section_top_level_folder_names(section_name)

        if model_path_tokens[0] == 'top':
            self.__print_model_top_level_help(control_option)
        elif len(model_path_tokens) == 1:
            self.__print_model_section_help(top_level_key, valid_section_folder_keys, control_option)
        else:
            self.__print_model_folder_help(model_path_tokens, valid_section_folder_keys, control_option)

        return

    def __create_model_path_tokens(self, model_path):
        """
        Creates a Python list from the elements in the specified model_path.
        The first element will be the section name.
        :param model_path: a string contain the model path to parse
        :return: a python list containing the section name, then each folder element
        """
        _method_name = '__create_model_path_tokens'

        self._logger.entering(model_path, class_name=_class_name, method_name=_method_name)

        match = MODEL_PATH_PATTERN.match(model_path)
        if match is None:
            ex = exception_helper.create_validate_exception('WLSDPLY-10108', model_path)
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        self._logger.finest('match.group(1)={0}, match.group(2)={1}',
                            str(match.group(1)), str(match.group(2)),
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
            section = self._get_section_for_folders(folders)

        section = section.replace(':', '')

        top_level_keys = model.get_model_top_level_keys()

        # 'top' is a special case for listing the sections
        all_section_keys = ['top']
        all_section_keys.extend(top_level_keys)

        if section not in all_section_keys:
            ex = exception_helper.create_validate_exception('WLSDPLY-10109', section, str(', '.join(top_level_keys)))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        model_path_tokens = [section]
        model_path_tokens.extend(folders)
        return model_path_tokens

    def _get_section_for_folders(self, folders):
        _method_name = '_get_section_for_folders'
        top_folder = folders[0]

        for section in KNOWN_TOPLEVEL_MODEL_SECTIONS:
            folder_keys = self._alias_helper.get_model_section_top_level_folder_names(section)
            if top_folder in folder_keys:
                return section

        ex = exception_helper.create_validate_exception('WLSDPLY-10101', top_folder)
        self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    def __print_model_top_level_help(self, control_option):
        pass

    def __print_model_section_help(self, top_level_key, valid_section_folder_keys, control_option):
        """
        Prints out the usage for a section of a model, when just the section_name[:[/}} is provided

        :param top_level_key: The name of one of the model sections
        :param valid_section_folder_keys: Python list of the valid model section names
        :param control_option: A command-line switch that controls what is output to STDOUT
        :return:
        """

        _method_name = '__print_model_section_help'

        self._logger.finest('1 top_level_key={0}', top_level_key,
                            class_name=_class_name, method_name=_method_name)

        location_path = '%s:' % top_level_key
        self._logger.finest('1 location_path={0}', location_path,
                            class_name=_class_name, method_name=_method_name)

        model_section = validation_utils.format_message('WLSDPLY-10106', location_path)

        # Print 'Section: <model_section>' label and field
        validation_utils.print_indent(model_section, 0)
        validation_utils.print_blank_lines()

        validation_location = LocationContext()
        attributes_location = self._alias_helper.get_model_section_attribute_location(top_level_key)

        if attributes_location is not None:
            self.__print_attributes_usage(attributes_location, 1)

        if control_option == self.ControlOptions.FOLDERS_ONLY:
            validation_utils.print_indent(validation_utils.format_message('WLSDPLY-10107'), 1)
            valid_section_folder_keys.sort()

        for section_folder_key in valid_section_folder_keys:
            if control_option == self.ControlOptions.FOLDERS_ONLY:
                validation_utils.print_indent(section_folder_key, 2)

            elif control_option == self.ControlOptions.RECURSIVE:
                validation_location.append_location(section_folder_key)

                name_token = self._alias_helper.get_name_token(validation_location)
                if name_token is not None:
                    validation_location.add_name_token(name_token, '%s-0' % section_folder_key)

                self._logger.finest('1 validation_location={0}', validation_location,
                                    class_name=_class_name, method_name=_method_name)

                location_path = '%s:%s' % (top_level_key, validation_location.get_folder_path())
                model_path = validation_utils.format_message('WLSDPLY-10105', location_path)

                validation_utils.print_blank_lines()
                validation_utils.print_indent(model_path, 0)
                validation_utils.print_blank_lines()

                self.__print_folders_usage(validation_location, control_option, 1)
                validation_location.pop_location()
        return

    def __print_model_folder_help(self, model_path_tokens, valid_section_folder_keys, control_option):
        """
        Prints out the usage for a section of a model, when more than just the section_name[:[/}} is provided

        :param model_path_tokens: A Python list of path elements built from model path
        :param valid_section_folder_keys: A list of valid folder names for the model section the
        usage is being printed for
        :param control_option: A command-line switch that controls what is output to STDOUT
        :return:
        """

        _method_name = '__print_model_folder_help'

        self._logger.finest('1 model_path_tokens={0}, control_option={1}',
                            str(model_path_tokens), self.ControlOptions.from_value(control_option),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('1 valid_section_folder_keys={0}', str(valid_section_folder_keys),
                            class_name=_class_name, method_name=_method_name)

        self.__validate_section_folder_path(model_path_tokens, valid_section_folder_keys)

        validation_location = LocationContext()

        model_path = validation_utils.format_message('WLSDPLY-10105',
                                                     '%s:/%s' % (model_path_tokens[0], '/'.join(model_path_tokens[1:])))

        # Print 'Path: <model_section>' header
        validation_utils.print_indent(model_path, 0)
        validation_utils.print_blank_lines()

        # Populate the location context using model_path_tokens[1:]
        for folder_key in model_path_tokens[1:]:
            validation_location.append_location(folder_key)
            name_token = self._alias_helper.get_name_token(validation_location)
            if name_token is not None:
                validation_location.add_name_token(name_token, '%s-0' % folder_key)

            self._logger.finest('2 validation_location={0}', validation_location,
                                class_name=_class_name, method_name=_method_name)

        # Print the attributes associated with location context
        self.__print_attributes_usage(validation_location, 1)

        if control_option != self.ControlOptions.ATTRIBUTES_ONLY:
            # Print the folders associated with location context
            self.__print_folders_usage(validation_location, control_option, 1)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)
        return

    def __print_folders_usage(self, validation_location, control_option, indent_level):
        """
        Prints out the usage for the folders in a model location

        :param validation_location: An object containing data about the model location being worked on
        :param control_option: A command-line switch that controls what is output to STDOUT
        :param indent_level: The level to indent by, before printing output
        :return:
        """

        _method_name = '__print_folders_usage'

        valid_subfolder_keys = self._alias_helper.get_model_subfolder_names(validation_location)
        self._logger.finest('3 aliases.get_model_subfolder_names(validation_location) returned: {0}',
                            str(valid_subfolder_keys),
                            class_name=_class_name, method_name=_method_name)

        if not valid_subfolder_keys:
            return

        validation_utils.print_indent(validation_utils.format_message('WLSDPLY-10107'), indent_level)
        valid_subfolder_keys.sort()

        for key in valid_subfolder_keys:
            validation_location.append_location(key)
            name_token = self._alias_helper.get_name_token(validation_location)
            if name_token is not None:
                validation_location.add_name_token(name_token, '%s-0' % key)

            self._logger.finest('3 validation_location={0}', validation_location,
                                class_name=_class_name, method_name=_method_name)

            validation_utils.print_indent(key, indent_level + 1)

            if control_option != self.ControlOptions.FOLDERS_ONLY:
                self.__print_attributes_usage(validation_location, indent_level + 2)

            if control_option == self.ControlOptions.RECURSIVE:
                # Call this __print_folders_usage() function recursively
                self.__print_folders_usage(validation_location, control_option, indent_level + 2)

            validation_location.pop_location()

        return

    def __print_attributes_usage(self, validation_location, indent_level):
        """
        Prints out the usage for the attributes in a model location

        :param validation_location: An object containing data about the model location being worked on
        :param indent_level: The level to indent by, before printing output
        :return:
        """
        _method_name = '__print_attributes_usage'

        attr_infos = self._alias_helper.get_model_attribute_names_and_types(validation_location)
        self._logger.finer('WLSDPLY-05012', str(validation_location), str(attr_infos),
                           class_name=_class_name, method_name=_method_name)

        _print_attr_infos(attr_infos, indent_level)
        return

    def __validate_section_folder_path(self, model_path_tokens, valid_section_folder_keys):
        """
        Verifies that a model path element is in the specified valid_section_folder_keys list.

        :param model_path_tokens: A Python list of path elements built from model path
        :param valid_section_folder_keys: A Python list of folder names
        :return:
        """
        _method_name = '__validate_section_folder_path'

        if model_path_tokens[1] not in valid_section_folder_keys:
            ex = exception_helper.create_validate_exception('WLSDPLY-10110', '%s:/' % model_path_tokens[0],
                                                            '%s' % '/'.join(model_path_tokens[1:]),
                                                            '%s' % ', '.join(valid_section_folder_keys))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        return


def _print_attr_infos(attr_infos, indent_level):
    """
    Prints out the attribute names and data types

    :param attr_infos: A Python dict containing the attribute names and data types
    :param indent_level: The level to indent by, before printing output
    :return:
    """

    if attr_infos:
        maxlen = 0
        for key in attr_infos:
            if len(key) > maxlen:
                maxlen = len(key)
        formatted_string = '%-' + str(maxlen) + 's\t%s'
        # Print 'Valid Attributes are :-' area label
        validation_utils.print_indent(validation_utils.format_message('WLSDPLY-10111'), indent_level)
        attr_list = attr_infos.keys()
        attr_list.sort()
        for attr_name in attr_list:
            msg = formatted_string % (attr_name, attr_infos[attr_name])
            validation_utils.print_indent(msg, indent_level + 1)

        validation_utils.print_blank_lines()
    return
