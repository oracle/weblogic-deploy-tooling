"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import copy
import os

import java.lang.IllegalArgumentException as IllegalArgumentException

import oracle.weblogic.deploy.util.VariableException as VariableException

import wlsdeploy.util.dictionary_utils as dictionary_utils
import wlsdeploy.util.model as model_sections
import wlsdeploy.util.variables as variables
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.model_translator import FileToPython

VARIABLE_HELPER_FILE_NAME = 'model_variable_helper.json'
VARIABLE_HELPER_PATH_NAME_ARG = 'variable_helper_path_name'
VARIABLE_HELPER_FILE_NAME_ARG = 'variable_helper_file_name'
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
        Replace attribute values with variables and generate a variable dictionary.
        The variable replacement is driven from the values in the model variable helper file.
        This file can either contain the name of a replacement file, or a list of pre-defined
        keywords for canned replacement files.
        Return the variable dictionary with the variable name inserted into the model, and the value
        that the inserted variable replaced.
        :param variable_file_location: location and name to store the generated variable file, else default
        :param kwargs: arguments used to override default for variable processing, typically used in test situations
        :return: variable dictionary containing
        """
        _method_name = 'insert_variables'
        _logger.entering(variable_file_location, class_name=_class_name, method_name=_method_name)

        variables_inserted = False

        self.__open_variable_file(variable_file_location)
        if not self.__variable_file:
            _logger.warning('WLSDPLY-19404', variable_file_location)
            return variables_inserted

        variable_helper_file_name = VARIABLE_HELPER_FILE_NAME
        if VARIABLE_HELPER_FILE_NAME_ARG in kwargs:
            variable_helper_file_name = kwargs[VARIABLE_HELPER_FILE_NAME_ARG]
        if VARIABLE_HELPER_PATH_NAME_ARG in kwargs:
            variable_helper_location_path = kwargs[VARIABLE_HELPER_PATH_NAME_ARG]
            variable_helper_location_file = os.path.join(variable_helper_location_path, variable_helper_file_name)
        else:
            variable_helper_location_path = os.path.join(os.environ.get('WLSDEPLOY_HOME'), 'lib')
            variable_helper_location_file = os.path.join(variable_helper_location_path, variable_helper_file_name)
        file_map = dict()
        for key, value in _keyword_to_file_map.iteritems():
            file_map[key] = os.path.join(variable_helper_location_path, value)
        print file_map

        variables_helper_dictionary = _load_variables_dictionary(variable_helper_location_file)
        print 'variables_helper_dictionary=', variables_helper_dictionary

        variables_file_dictionary = self.replace_variables_dictionary(file_map, variables_helper_dictionary)
        if variables_file_dictionary:
            variables_inserted = True

            for entry in variables_file_dictionary:
                self.__variable_file.write(entry)

        # now persist the dictionary even if empty
        self.__variable_file.close()
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variables_inserted)
        return variables_inserted

    def replace_variables_dictionary(self, keyword_map, variables_dictionary):
        """
        Takes a variable keyword dictionary and returns a variables for file in a dictionary
        :param variables_dictionary:
        :return:
        """
        print 'keyword map=', keyword_map
        variable_file_entries = dict()
        if variables_dictionary:
            file_list = []
            if not dictionary_utils.is_empty_dictionary_element(variables_dictionary, CUSTOM_KEYWORD):
                file_list.append(variables_dictionary[CUSTOM_KEYWORD])
                _logger.fine('WLSDPLY-19401', file_list[0])
            else:
                for keyword in variables_dictionary:
                    print 'find keyword in var dict ', keyword
                    if keyword in keyword_map:
                        file_list.append(keyword_map[keyword])
                    elif keyword != CUSTOM_KEYWORD:
                        print 'keyword not understood ', keyword
                        _logger.warning('WLSDPLY-19403', keyword)
            print 'file_list=', file_list
            for file_name in file_list:
                replacement_list = _load_replacement_list(file_name)
                print 'replacement_list=', replacement_list
                if replacement_list:
                    entries = self.process_variable_replacement(replacement_list)
                    if entries:
                        # log that a set of entries was returned for the keywood
                        variable_file_entries.update(entries)
        print variable_file_entries
        return variable_file_entries

    def process_variable_replacement(self, replacement_list):
        _method_name = '__process_variable_replacement'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        variable_dict = dict()
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

        def _traverse_variables(model_section, mbean_list, attribute):
            if mbean_list:
                mbean = mbean_list.pop(0)
                if mbean in model_section:
                    next_model_section = model_section[mbean]
                    location.append_location(mbean)
                    name_token = self.__aliases.get_name_token(location)
                    if self.__aliases.supports_multiple_mbean_instances(location):
                        for mbean_name in next_model_section:
                            continue_mbean_list = copy.copy(mbean_list)
                            location.add_name_token(name_token, mbean_name)
                            _traverse_variables(next_model_section[mbean_name], continue_mbean_list, attribute)
                            location.remove_name_token(name_token)
                    else:
                        _traverse_variables(next_model_section, mbean_list, attribute)
                    location.pop_location()
                else:
                    print 'invalid mbean in mbean_list ', mbean, ' : ', model_section
                    return False
            else:
                if attribute in model_section:
                    value = model_section[attribute]
                    if type(value) != str or not value.startswith('@@PROP:'):
                        # change this to be a loaded thing
                        var_name, var_value = self.__insert_variable(location, attribute, value)
                        model_section[attribute] = '@@PROP:%s@@' % var_name
                        variable_dict[var_name] = var_value
                else:
                    print 'attribute not in model'
                    _logger.finer('attribute not in the model')
            return True

        section, attr, segment = _split_section(replacement)
        if section and section in self.__model:
            start_mbean_list, start_attribute = _split_attribute_path(attr)
            _traverse_variables(self.__model[section], start_mbean_list, start_attribute)
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

    def __insert_variable(self, location, attribute, value):
        path = ''
        make_path = self.__aliases.get_model_folder_path(location)
        if make_path:
            make_path = make_path.split(':')
            if len(make_path) > 1 and len(make_path[1]) > 1:
                path = make_path[1]
        return path + '/' + attribute, value


def _load_replacement_list(replacement_file_name):
    _method_name = '_load_replacement_dictionary'
    _logger.entering(replacement_file_name, class_name=_class_name, method_name=_method_name)
    replacement_list = []
    if os.path.isfile(replacement_file_name):
        replacement_file = open(replacement_file_name, 'r')
        entry = replacement_file.readline()
        while entry:
            print 'entry=', entry
            if entry != '\n':
                replacement_list.append(entry.strip())
            entry = replacement_file.readline()
    else:
        print 'file is not a file', replacement_file_name

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=replacement_list)
    return replacement_list


def _load_variables_dictionary(variable_helper_location):
    _method_name = '_load_variables_dictionary'
    variables_dictionary = None
    if os.path.isfile(variable_helper_location):
        try:
            variables_dictionary = FileToPython(variable_helper_location).parse()
            _logger.fine('WLSDPLY-19400', variable_helper_location, class_name=_class_name, method_name=_method_name)
        except IllegalArgumentException, ia:
            _logger.warning('WLSDPLY-19402', variable_helper_location, ia.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
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
            segment = attribute_split_list[1][:len(attribute_split_list[1]) - 1]
    return section, attribute, segment


def _split_attribute_path(attribute_path):
    mbean_list = attribute_path.split('.')
    attribute = None
    if len(mbean_list) > 0:
        attribute = mbean_list.pop()
    return mbean_list, attribute

def _write_variables_file(variables_dictionary, variables_file_name):
    _method_name = '_write_variables_file'
    _logger.entering(variables_dictionary, variables_file_name, class_name=_class_name, method_name=_method_name)
    try:
        variables.write_variables(variables_dictionary, variables_file_name)
    except VariableException, ve:
