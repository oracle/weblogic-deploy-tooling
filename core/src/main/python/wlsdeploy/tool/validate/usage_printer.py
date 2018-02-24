"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import re

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.util import model
from wlsdeploy.util.enum import Enum
from wlsdeploy.tool.validate import validation_utils
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.alias_helper import AliasHelper

_class_name = "UsagePrinter"
MODEL_PATH_PATTERN = re.compile(r'^([a-zA-Z]+)(:((/[a-zA-Z0-9]+)*)/?)?$')


class UsagePrinter(object):
    """
    Class for printing the recognized metadata for a model file, to STDOUT. This output is referred to as the usage.
    """
    ControlOptions = Enum(['RECURSIVE', 'FOLDERS_ONLY', 'ATTRIBUTES_ONLY'])

    def __init__(self, aliases, logger):
        """

        :param aliases: A reference to an Aliases class instance
        :param logger: A reference to the platform logger to write to, if a log entry needs to be made
        """

        self._logger = logger
        self._aliases = aliases
        self._alias_helper = AliasHelper(self._aliases, self._logger, ExceptionType.VALIDATE)

    def print_model_path_usage(self, model_path, control_option):
        """
        Prints out the usage information for a given '''model_path'''. '''model_path''' needs to be specified
        using the following pattern:

                <model_section>[:/<section_folder>[/<section_subfolder>|...]]

        Examples:
                'domainInfo', 'domainInfo:' or 'domainInfo:/' (all 3 are rquivalent)
                'topology:/Server'
                'resources:/JDBCSystemResource/JdbcResource/JDBCDriverParams'
                'appDeployments:/Application'

        :param model_path: A forward-slash delimited string contain the model path to print usage for
        :param control_option: A command-line switch that controls what is output to STDOUT
        :return:
        :raises ValidationException: if an AliasException is raised during an invocation of an aliases API call.
        """

        model_path_tokens = self.__create_model_path_tokens(model_path)

        top_level_key = model_path_tokens[0]

        if control_option == self.ControlOptions.RECURSIVE:
            print validation_utils.format_message('WLSDPLY-05100')
        elif control_option == self.ControlOptions.FOLDERS_ONLY:
            print validation_utils.format_message('WLSDPLY-05101')
        elif control_option == self.ControlOptions.ATTRIBUTES_ONLY:
            print validation_utils.format_message('WLSDPLY-05102')

        validation_utils.print_blank_lines()

        valid_section_folder_keys = []

        if model_path_tokens[0] == model_constants.TOPOLOGY:
            valid_section_folder_keys = self._aliases.get_model_topology_top_level_folder_names()

        if model_path_tokens[0] == model_constants.RESOURCES:
            valid_section_folder_keys = self._aliases.get_model_resources_top_level_folder_names()

        if model_path_tokens[0] == model_constants.APP_DEPLOYMENTS:
            valid_section_folder_keys = self._aliases.get_model_app_deployments_top_level_folder_names()

        if len(model_path_tokens) == 1:
            if model_path_tokens[0] == model_constants.DOMAIN_INFO:
                self.__print_domain_info_usage(model_path_tokens)
            else:
                self.__print_top_level_usage(top_level_key, valid_section_folder_keys, control_option)
        else:
            self.__print_model_section_usage(model_path_tokens, valid_section_folder_keys, control_option)

        return

    def __print_domain_info_usage(self, model_path_tokens):
        """
        Prints out the usage for the domainInfo section of a model
        :param model_path_tokens: A Python list of path elements built from model path
        :return:
        """

        _method_name = '__print_domain_info_usage'
        self._logger.finest('1 model_path_tokens={0}', str(model_path_tokens),
                            class_name=_class_name, method_name=_method_name)

        model_path = validation_utils.format_message('WLSDPLY-05103', '%s:' % model_path_tokens[0])

        # Print 'Path: <model_section>' label and field
        validation_utils.print_indent(model_path, 0)
        validation_utils.print_blank_lines()

        attr_infos = self._alias_helper.get_model_domain_info_attribute_names_and_types()
        _print_attr_infos(attr_infos, 1)

        return

    def __print_top_level_usage(self, top_level_key, valid_section_folder_keys, control_option):
        """
        Prints out the usage for a section of a model, when just the section_name[:[/}} is provided

        :param top_level_key: The name of one of the model sections
        :param valid_section_folder_keys: Python list of the valid model section names
        :param control_option: A command-line switch that controls what is output to STDOUT
        :return:
        """

        _method_name = '__print_top_level_usage'

        self._logger.finest('1 top_level_key={0}', top_level_key,
                            class_name=_class_name, method_name=_method_name)

        location_path = '%s:' % top_level_key
        self._logger.finest('1 location_path={0}', location_path,
                            class_name=_class_name, method_name=_method_name)

        model_section = validation_utils.format_message('WLSDPLY-05104', location_path)

        # Print 'Section: <model_section>' label and field
        validation_utils.print_indent(model_section, 0)

        if control_option == self.ControlOptions.ATTRIBUTES_ONLY:
            # Doing an ATTRIBUTES_ONLY on a top level key is a no-op
            return

        validation_location = LocationContext()

        if control_option == self.ControlOptions.FOLDERS_ONLY:
            validation_utils.print_blank_lines()
            validation_utils.print_indent(validation_utils.format_message('WLSDPLY-05105'), 1)
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
                model_path = validation_utils.format_message('WLSDPLY-05103', location_path)

                validation_utils.print_blank_lines()
                validation_utils.print_indent(model_path, 0)
                validation_utils.print_blank_lines()

                self.__print_folders_usage(validation_location, control_option, 1)
                validation_location.pop_location()
        return

    def __print_model_section_usage(self, model_path_tokens, valid_section_folder_keys, control_option):
        """
        Prints out the usage for a section of a model, when more than just the section_name[:[/}} is provided

        :param model_path_tokens: A Python list of path elements built from model path
        :param valid_section_folder_keys: A list of valid folder names for the model section the
        usage is being printed for
        :param control_option: A command-line switch that controls what is output to STDOUT
        :return:
        """

        _method_name = '__print_model_section_usage'

        self._logger.finest('1 model_path_tokens={0}, control_option={1}',
                            str(model_path_tokens), self.ControlOptions.from_value(control_option),
                            class_name=_class_name, method_name=_method_name)
        self._logger.finest('1 valid_section_folder_keys={0}', str(valid_section_folder_keys),
                            class_name=_class_name, method_name=_method_name)

        self.__validate_section_folder_path(model_path_tokens, valid_section_folder_keys)

        validation_location = LocationContext()

        model_path = validation_utils.format_message('WLSDPLY-05103',
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

        validation_utils.print_indent(validation_utils.format_message('WLSDPLY-05105'), indent_level)
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

    def __create_model_path_tokens(self, model_path=''):
        """
        Creates a Python list from the elements in the specified model_path.

        :param model_path: A forward-slash delimited string contain the model path to print usage for
        :return:
        """
        _method_name = '__create_model_path_tokens'

        self._logger.entering(model_path, class_name=_class_name, method_name=_method_name)

        if model_path[-1:] != ':':
            m = MODEL_PATH_PATTERN.match(model_path)
            if m is None:
                ex = exception_helper.create_validate_exception('WLSDPLY-05106', model_path)
                self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

            self._logger.finest('m.group(1)={0}, m.group(3)={1}',
                                str(m.group(1)), str(m.group(3)),
                                class_name=_class_name, method_name=_method_name)

        # Replace any ':' in model_path with '', then split it on '/' into a list
        model_path_tokens = model_path.replace(':', '').split('/')

        # Remove any blank list items caused by the user entering
        # extraneous '/' characters.
        while '' in model_path_tokens:
            del model_path_tokens[model_path_tokens.index('')]

        recognized_top_level_keys = model.get_model_top_level_keys()
        self._logger.finest('recognized_top_level_keys={0}', str(recognized_top_level_keys),
                            class_name=_class_name, method_name=_method_name)

        top_level_key = model_path_tokens[0]

        if top_level_key not in recognized_top_level_keys:
            ex = exception_helper.create_validate_exception('WLSDPLY-05107', top_level_key,
                                                            '%s' % ', '.join(recognized_top_level_keys))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        return model_path_tokens

    def __validate_section_folder_path(self, model_path_tokens, valid_section_folder_keys):
        """
        Verifies that a model path element is in the specified valid_section_folder_keys list.

        :param model_path_tokens: A Python list of path elements built from model path
        :param valid_section_folder_keys: A Python list of folder names
        :return:
        """
        _method_name = '__validate_section_folder_path'

        if model_path_tokens[1] not in valid_section_folder_keys:
            ex = exception_helper.create_validate_exception('WLSDPLY-05108', '%s:/' % model_path_tokens[0],
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
        validation_utils.print_indent(validation_utils.format_message('WLSDPLY-05109'), indent_level)
        attr_list = attr_infos.keys()
        attr_list.sort()
        for attr_name in attr_list:
            msg = formatted_string % (attr_name, attr_infos[attr_name])
            validation_utils.print_indent(msg, indent_level + 1)

        validation_utils.print_blank_lines()
    return
