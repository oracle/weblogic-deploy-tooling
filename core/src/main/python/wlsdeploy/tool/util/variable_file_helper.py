"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import copy
import os

import java.lang.IllegalArgumentException as IllegalArgumentException
import java.lang.StringBuilder as StringBuilder
import wlsdeploy.util.dictionary_utils as dictionary_utils
import wlsdeploy.util.model as model_sections
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.aliases.wlst_modes import WlstModes

VARIABLE_HELPER_FILE_NAME = 'model_variable_helper.json'
VARIABLE_HELPER_FILE_NAME_ARG = 'variable_helper_file_name'
VARIABLE_HELPER_DICTIONARY_ARG = 'variable_helper_dictionary'
CUSTOM_KEYWORD = 'CUSTOM'

_keyword_to_file_map = {
    'PORT': 'port.properties',
    'TOPOLOGY_NAME': 'name.properties',
    'CREDENTIALS': 'credentials.properties',
    'URL': 'url.properties'
}
_class_name = 'variable_file_helper'
_logger = PlatformLogger('wlsdeploy.util')


class VariableFileHelper(object):

    def __init__(self, model, model_context=None, version=None):
        self.__model = model
        if version is not None:
            self.__aliases = Aliases(model_context, WlstModes.OFFLINE, version, None)
        else:
            self.__aliases = Aliases(model_context)
        self.__variable_file = None

    def replace_variables_file(self, variable_file_location, **kwargs):
        """
        Replace attribute values with variables and generate a variable file.
        The variable replacement is driven from the values in the model variable helper file.
        This file can either contain the name of a replacement file, or a list of pre-defined
        keywords for canned replacement files.
        :param model: the model to be massaged
        :param variable_file_location: location and name to store the generated variable file, else default
        :param kwargs: arguments used to override default for variable processing, typically used in test situations
        :return: True if any variable was inserted, False otherwise
        """
        _method_name = 'insert_variables'
        _logger.entering(variable_file_location, class_name=_class_name, method_name=_method_name)

        variables_inserted = False

        self.__open_variable_file(variable_file_location)
        if not self.__variable_file:
            _logger.warning('WLSDPLY-19404', variable_file_location)
            return variables_inserted

        if VARIABLE_HELPER_DICTIONARY_ARG in kwargs:
            variables_dictionary = kwargs[VARIABLE_HELPER_DICTIONARY_ARG]
        else:
            variable_helper_location = os.path.join(os.environ.get('WLSDEPLOY_HOME'), 'lib', VARIABLE_HELPER_FILE_NAME)
            if VARIABLE_HELPER_FILE_NAME_ARG in kwargs:
                variable_helper_location = kwargs[VARIABLE_HELPER_FILE_NAME_ARG]
            variables_dictionary = _load_variables_dictionary(variable_helper_location)

        variables_file_dictionary = self.replace_variables_dictionary(variables_dictionary)
        # now persist the dictionary even if empty

        self.__variable_file.close()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variables_inserted)
        return variables_inserted

    def replace_variables_dictionary(self, variables_dictionary):
        """
        Takes a variable keyword dictionary and returns a variables for file in a dictionary
        :param variables_dictionary:
        :return:
        """
        variable_file_entries = dict()
        if variables_dictionary:
            file_list = []
            if not dictionary_utils.is_empty_dictionary_element(variables_dictionary, CUSTOM_KEYWORD):
                file_list.append(variables_dictionary[CUSTOM_KEYWORD])
                _logger.fine('WLSDPLY-19401', file_list[0])
            else:
                for keyword in variables_dictionary:
                    if keyword in _keyword_to_file_map:
                        file_list.append(_keyword_to_file_map[keyword])
                    elif keyword != CUSTOM_KEYWORD:
                        _logger.warning('WLSDPLY-19403', keyword)
            for file_name in file_list:
                replacement_list = _load_replacement_list(file_name)
                if replacement_list:
                    entries = self.process_variable_replacement(replacement_list)
                    if entries:
                        # log that a set of entries was returned for the keywood
                        variable_file_entries.append(entries)
        return variable_file_entries

    def process_variable_replacement(self, replacement_list):
        _method_name = '__process_variable_replacement'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        variable_dict = dict()
        print 'replacement_list=', replacement_list
        if replacement_list:
            topology = self.__model[model_sections.get_model_topology_key()]
            if 'Name' in topology:
                domain_name = topology['Name']
            else:
                domain_name = 'mydomain'
            location = LocationContext()
            domain_token = self.__aliases.get_name_token(location)
            location.add_name_token(domain_token, domain_name)
            for replacement_entry in replacement_list:
                entries_dict = self.__process_variable(location, replacement_entry)
                if len(entries_dict) > 0:
                    variable_dict.update(entries_dict)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_dict)
        return variable_dict

    def __process_variable(self, location, replacement):

        variable_dict = dict()

        def _traverse_variables(model_section, mbean_list, attribute, variable_name=StringBuilder()):
            print 'mbean_list=', mbean_list
            if mbean_list:
                mbean = mbean_list.pop(0)
                if mbean in model_section:
                    next_model_section = model_section[mbean]
                    _append_to_variable_name(variable_name, mbean.lower())
                    location.append_location(mbean)
                    name_token = self.__aliases.get_name_token(location)
                    if self.__aliases.supports_multiple_mbean_instances(location):
                        for mbean_name in next_model_section:
                            continue_mbean_list = copy.copy(mbean_list)
                            location.add_name_token(name_token, mbean_name)
                            continue_variable_name = StringBuilder(variable_name.toString())
                            _append_to_variable_name(continue_variable_name, mbean_name)
                            _traverse_variables(next_model_section[mbean_name], continue_mbean_list, attribute,
                                                continue_variable_name)
                            location.remove_name_token(name_token)
                    else:
                        _traverse_variables(next_model_section, mbean_list, attribute, variable_name)
                    location.pop_location()
                else:
                    print 'invalid mbean in mbean_list ', mbean, ' : ', model_section
                    return False
            else:
                if attribute in model_section:
                    value = model_section[attribute]
                    if type(value) != str or not value.startswith('@@PROP:'):
                        _append_to_variable_name(variable_name, attribute.lower())
                        str_var = variable_name.toString()
                        model_section[attribute] = '@@PROP:%s@@' % str_var
                        variable_dict[str_var] = value
                else:
                    print 'attribute not in model'
                    _logger.finer('attribute not in the model')
            return True

        section, attribute, segment = _split_section(replacement)
        print section, ', ', attribute, ', ', segment
        if section and section in self.__model:
            start_mbean_list, attribute = _split_attribute_path(attribute)
            print start_mbean_list, ', ', attribute
            _traverse_variables(self.__model[section], start_mbean_list, attribute)
        print variable_dict
        return variable_dict

    def __open_variable_file(self, variable_file_name):
        _method_name = '_open_variable_file'
        _logger.entering(variable_file_name, class_name=_class_name, method_name=_method_name)
        if variable_file_name and os.path.isfile(variable_file_name):
            try:
                self.__variable_file = open(variable_file_name, 'w')
            except OSError, oe:
                _logger.warning('WLSDPLY-19405', variable_file_name, str(oe), class_name=_class_name,
                                 method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name)


def _append_to_variable_name(builder, value):
    if builder.length() > 0:
        builder.append('-')
    builder.append(value)


def _load_replacement_list(replacement_file_name):
    _method_name = '_load_replacement_dictionary'
    _logger.entering(replacement_file_name, class_name=_class_name, method_name=_method_name)
    replacement_list = []
    if os.path.isfile(replacement_file_name):
        replacement_file = open(replacement_file_name, 'r')
        entry = replacement_file.readline()
        while entry:
            if entry != '\n':
                replacement_list.append(entry)
            entry = replacement_file.readline()

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=replacement_list)
    return replacement_list


def _load_variables_dictionary(variable_helper_location):
    _method_name = '_load_variables_dictionary'
    variables_dictionary = None
    if os.path.isfile(variable_helper_location):
        try:
            variables_dictionary = FileToPython(variable_helper_location).parse()
            _logger.fine('WLSDPLY-19400', variable_helper_location, class_name=_class_name,
                           method_name=_method_name)
        except IllegalArgumentException, ia:
            _logger.warning('WLSDPLY-19402', variable_helper_location, ia.getLocalizedMessage(),
                             class_name=_class_name, method_name=_method_name)
    return variables_dictionary


def _split_section(attribute_path):
    """
    Split the section from the attribute path.
    :param attribute_path:
    :return:
    """
    split_list = attribute_path.split(':', 1)
    section = None
    attribute = None
    segment = None
    if len(split_list) == 2 and split_list[0] in model_sections.get_model_top_level_keys():
        section = split_list[0]
        attribute_split_list = split_list[1].split('${')
        attribute = attribute_split_list[0]
        if len(attribute_split_list) == 2:
            segment = attribute_split_list[1][:len(attribute_split_list[1])-1]
    return section, attribute, segment


def _split_attribute_path(attribute_path):
    mbean_list = attribute_path.split('.')
    attribute = None
    if len(mbean_list) > 0:
        attribute = mbean_list.pop()
    return mbean_list, attribute



