"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

import re

from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.util import model
from wlsdeploy.util.enum import Enum
from wlsdeploy.validation import validation_utils
from wlsdeploy.exception import exception_helper

import oracle.weblogic.deploy.aliases.AliasException as AliasException

_class_name = "UsagePrinter"
_model_path_pattern = re.compile(r'([a-zA-Z]+):([/a-zA-Z0-9]+)')


class UsagePrinter(object):
    """

    """
    ControlOptions = Enum(['RECURSIVE', 'FOLDERS_ONLY', 'ATTRIBUTES_ONLY'])

    def __init__(self, aliases, logger):
        """

        :param aliases: A reference to an Aliases class instance
        :param logger: A reference to the platform logger to write to, if a log entry needs to be made
        """

        self._aliases = aliases
        self._logger = logger

    def print_model_path_usage(self, model_path, control_option):
        """
        Prints out the usage information for a given '''model_path'''. '''model_path''' needs to be specified
        using the following pattern:

                <model_section>:[/<section_folder>[/<section_subfolder>|...]]

        Examples:
                'domainInfo'
                'topology/Server'
                'resources/JDBCSystemResource/JdbcResource/JDBCDriverParams'
                'appDeployments/Application'

        :param model_path: A forward-slash delimited string contain the model path to print usage for
        :param control_option: Switch to control what is output to STDOUT
        :return:
        """

        _method_name = 'print_model_path_usage'

        model_path_tokens = self.__create_model_path_tokens(model_path)

        top_level_key = model_path_tokens[0]

        # Print 'Using <control_option> as the print usage control option...' label
        print validation_utils.format_message('WLSDPLY-03233', self.ControlOptions.from_value(control_option))
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
        :param model_path_tokens: A Python list of strings built from model path
        :return:
        """

        _method_name = '__print_domain_info_usage'

        self._logger.finer('1 model_path_tokens={0}', str(model_path_tokens),
                           class_name=_class_name, method_name=_method_name)

        model_path = validation_utils.format_message('WLSDPLY-03215', '%s:' % model_path_tokens[0])

        # Print 'Path: <model_section>' label and field
        validation_utils.print_indent(model_path, 0)
        validation_utils.print_blank_lines()

        attr_infos = validation_utils.get_domain_info_data_types()

        self.__print_attr_infos(attr_infos, 1)

        return

    def __print_top_level_usage(self, top_level_key, valid_section_folder_keys, control_option):
        """

        :param top_level_key:
        :param valid_section_folder_keys:
        :param control_option:
        :return:
        """

        _method_name = '__print_top_level_usage'

        self._logger.finer('1 top_level_key={0}', top_level_key,
                           class_name=_class_name, method_name=_method_name)

        location_path = '%s:' % top_level_key
        self._logger.finer('1 location_path={0}', location_path,
                           class_name=_class_name, method_name=_method_name)

        model_section = validation_utils.format_message('WLSDPLY-03214', location_path)

        # Print 'Section: <model_section>' label and field
        validation_utils.print_indent(model_section, 0)

        if control_option == self.ControlOptions.ATTRIBUTES_ONLY:
            # Doing an ATTRIBUTES_ONLY on a top level key is a no-op
            return

        validation_location = LocationContext()

        if control_option == self.ControlOptions.FOLDERS_ONLY:
            validation_utils.print_blank_lines()
            validation_utils.print_indent(validation_utils.format_message('WLSDPLY-03156'), 1)
            valid_section_folder_keys.sort()

        for section_folder_key in valid_section_folder_keys:
            if control_option == self.ControlOptions.FOLDERS_ONLY:
                validation_utils.print_indent(section_folder_key, 2)

            elif control_option == self.ControlOptions.RECURSIVE:
                validation_location.append_location(section_folder_key)

                try:
                    name_token = self._aliases.get_name_token(validation_location)
                    if name_token is not None:
                        validation_location.add_name_token(name_token, '%s-0' % section_folder_key)

                    self._logger.finer('1 validation_location={0}', validation_location,
                                       class_name=_class_name, method_name=_method_name)

                    location_path = '%s:%s' % (top_level_key, validation_location.get_folder_path())
                    model_path = validation_utils.format_message('WLSDPLY-03215', location_path)

                    validation_utils.print_blank_lines()
                    validation_utils.print_indent(model_path, 0)
                    validation_utils.print_blank_lines()

                    self.__print_folders_usage(validation_location, control_option, 1)
                    validation_location.pop_location()

                except AliasException, ae:
                    raise exception_helper.create_validate_exception(error=ae)

    def __print_model_section_usage(self, model_path_tokens, valid_section_folder_keys, control_option):
        """
        :param model_path_tokens: A Python list of strings built from model path
        :param valid_section_folder_keys: A list of valid folder names for the model section the
        usage is being printed for
        :param control_option: Switch to control what is output to STDOUT
        :return:
        """

        _method_name = '__print_model_section_usage'

        self._logger.finer('1 model_path_tokens={0}, control_option={1}',
                           str(model_path_tokens), self.ControlOptions.from_value(control_option),
                           class_name=_class_name, method_name=_method_name)
        self._logger.finer('1 valid_section_folder_keys={0}', str(valid_section_folder_keys),
                           class_name=_class_name, method_name=_method_name)

        self.__validate_section_folder_path(model_path_tokens, valid_section_folder_keys)

        validation_location = LocationContext()

        model_path = validation_utils.format_message('WLSDPLY-03215',
                                                     '%s:/%s' % (model_path_tokens[0], '/'.join(model_path_tokens[1:])))

        # Print 'Path: <model_section>' header
        validation_utils.print_indent(model_path, 0)
        validation_utils.print_blank_lines()

        try:
            # Populate the location context using model_path_tokens[1:]
            for folder_key in model_path_tokens[1:]:
                validation_location.append_location(folder_key)
                name_token = self._aliases.get_name_token(validation_location)
                if name_token is not None:
                    validation_location.add_name_token(name_token, '%s-0' % folder_key)

                self._logger.finer('2 validation_location={0}', validation_location,
                                   class_name=_class_name, method_name=_method_name)

            # Print the attributes associated with location context
            self.__print_attributes_usage(validation_location, 1)

            if control_option != self.ControlOptions.ATTRIBUTES_ONLY:
                # Print the folders associated with location context
                self.__print_folders_usage(validation_location, control_option, 1)

        except AliasException, ae:
            raise exception_helper.create_validate_exception(ae)

        self._logger.exiting(class_name=_class_name, method_name=_method_name)

        return

    def __print_folders_usage(self, validation_location, control_option, indent_level):
        """

        :param validation_location:
        :param control_option:
        :param indent_level:
        :return:
        """

        _method_name = '__print_folders_usage'

        valid_subfolder_keys = self._aliases.get_model_subfolder_names(validation_location)
        self._logger.finer('3 aliases.get_model_subfolder_names(validation_location) returned: {0}',
                           str(valid_subfolder_keys),
                           class_name=_class_name, method_name=_method_name)

        if not valid_subfolder_keys:
            return

        validation_utils.print_indent(validation_utils.format_message('WLSDPLY-03156'), indent_level)
        valid_subfolder_keys.sort()

        for key in valid_subfolder_keys:
            validation_location.append_location(key)
            name_token = self._aliases.get_name_token(validation_location)
            if name_token is not None:
                validation_location.add_name_token(name_token, '%s-0' % key)

            self._logger.finer('3 validation_location={0}', validation_location,
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

        :param validation_location:
        :param indent_level:
        :return:
        """
        _method_name = '__print_attributes_usage'

        attr_infos = self._aliases.get_model_attribute_names_and_types(validation_location)
        self._logger.finer('aliases.get_model_attribute_names_and_types(validation_location) returned: {0}',
                           str(attr_infos),
                           class_name=_class_name, method_name=_method_name)

        self.__print_attr_infos(attr_infos, indent_level)

        return

    def __print_attr_infos(self, attr_infos, indent_level):
        """

        :param attr_infos:
        :param indent_level:
        :return:
        """
        _method_name = '__print_attr_infos'

        if attr_infos:
            maxlen = 0
            for key in attr_infos:
                if len(key) > maxlen:
                    maxlen = len(key)
            formatted_string = '%-' + str(maxlen) + 's\t%s'
            # Print 'Valid Attributes are :-' area label
            validation_utils.print_indent(validation_utils.format_message('WLSDPLY-03157'), indent_level)
            attr_list = attr_infos.keys()
            attr_list.sort()
            for attr_name in attr_list:
                msg = formatted_string % (attr_name, attr_infos[attr_name])
                validation_utils.print_indent(msg, indent_level + 1)

            validation_utils.print_blank_lines()
        return

    def __create_model_path_tokens(self, model_path=''):
        _method_name = '__create_model_path_tokens'

        self._logger.finer('model_path={0}', model_path,
                           class_name=_class_name, method_name=_method_name)

        if model_path[-1:] != ':':
            m = _model_path_pattern.match(model_path)
            if m is None:
                ex = exception_helper.create_validate_exception('WLSDPLY-03234', model_path)
                self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

            self._logger.finer('m.group(1)={0}, m.group(2)={1}',
                               str(m.group(1)), str(m.group(2)),
                               class_name=_class_name, method_name=_method_name)

        # Replace any ':' in model_path with '', then split it on '/' into a list
        model_path_tokens = model_path.replace(':', '').split('/')

        # Remove any blank list items caused by the user entering
        # extraneous '/' characters.
        while '' in model_path_tokens:
            del model_path_tokens[model_path_tokens.index('')]

        recognized_top_level_keys = model.get_model_top_level_keys()

        self._logger.finer('recognized_top_level_keys={0}', str(recognized_top_level_keys),
                           class_name=_class_name, method_name=_method_name)

        top_level_key = model_path_tokens[0]

        if top_level_key not in recognized_top_level_keys:
            ex = exception_helper.create_validate_exception('WLSDPLY-03154', top_level_key,
                                                            '%s' % ', '.join(recognized_top_level_keys))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        return model_path_tokens

    def __validate_section_folder_path(self, model_path_tokens, valid_section_folder_keys):
        _method_name = '__validate_section_folder_path'

        if model_path_tokens[1] not in valid_section_folder_keys:
            ex = exception_helper.create_validate_exception('WLSDPLY-03235', '%s:/' % model_path_tokens[0],
                                                            '%s' % '/'.join(model_path_tokens[1:]),
                                                            '%s' % ', '.join(valid_section_folder_keys))
            self._logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        return
