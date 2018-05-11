"""
Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import copy
import os
import re

import java.lang.IllegalArgumentException as IllegalArgumentException

import oracle.weblogic.deploy.util.VariableException as VariableException
import oracle.weblogic.deploy.aliases.AliasException as AliasException

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
VARIABLE_FILE_NAME_ARG = 'variable_file_name'
VARIABLE_FILE_NAME = 'variables.properties'
CUSTOM_KEYWORD = 'CUSTOM'

_segment_pattern = re.compile("\\[[\w.-]+\\]$")
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
        self.__original = copy.deepcopy(model)
        self.__model = model
        if version:
            self.__aliases = Aliases(model_context, WlstModes.OFFLINE, version, None)
        else:
            self.__aliases = Aliases(model_context)

    def replace_variables_file(self, **kwargs):
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
        _logger.entering(class_name=_class_name, method_name=_method_name)

        variable_helper_location_file = _get_variable_helper_file_name(**kwargs)
        variables_helper_dictionary = _load_variables_dictionary(variable_helper_location_file)

        variables_inserted = False
        return_model = dict()
        variable_file_location = None
        if variables_helper_dictionary:
            variable_file_location = _get_variable_file_name(variables_helper_dictionary, **kwargs)
            if not variable_file_location:
                _logger.warning('WLSDPLY-19420', variable_helper_location_file, class_name=_class_name,
                                method_name=_method_name)
            else:
                file_map = dict()
                variable_keywords_location_path = _get_keyword_files_location(**kwargs)
                for key, value in _keyword_to_file_map.iteritems():
                    file_map[key] = os.path.join(variable_keywords_location_path, value)

                variables_file_dictionary = self.replace_variables_dictionary(file_map, variables_helper_dictionary)
                variables_inserted = _write_variables_file(variables_file_dictionary, variable_file_location)
                if variables_inserted:
                    _logger.info('WLSDPLY-19418', variable_file_location, class_name=_class_name,
                                 method_name=_method_name)
                    return_model = self.__model
                else:
                    _logger.fine('WLSDPLY-19419', class_name=_class_name, method_name=_method_name)
                    return_model = self.__original
                    variable_file_location = None

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variables_inserted)
        return variables_inserted, return_model, variable_file_location

    def replace_variables_dictionary(self, keyword_map, variables_dictionary):
        """
        Takes a variable keyword dictionary and returns a variables for file in a dictionary
        :param variables_dictionary:
        :return:
        """
        _method_name = 'replace_variables_dictionary'
        _logger.entering(variables_dictionary, class_name=_class_name, method_name=_method_name)
        variable_file_entries = dict()
        if variables_dictionary:
            file_map = dict()
            if not dictionary_utils.is_empty_dictionary_element(variables_dictionary, CUSTOM_KEYWORD):
                file_map[CUSTOM_KEYWORD] = variables_dictionary[CUSTOM_KEYWORD]
                _logger.fine('WLSDPLY-19401', file_map[CUSTOM_KEYWORD], class_name=_class_name,
                             method_name=_method_name)
            else:
                for keyword in variables_dictionary:
                    if keyword in keyword_map:
                        file_map[keyword] = keyword_map[keyword]
                    elif keyword != CUSTOM_KEYWORD:
                        _logger.warning('WLSDPLY-19403', keyword, class_name=_class_name, method_name=_method_name)
            for keyword, file_name in file_map.iteritems():
                replacement_list = _load_replacement_list(file_name)
                if replacement_list:
                    entries = self.process_variable_replacement(replacement_list)
                    if entries:
                        _logger.finer('WLSDPLY-19413', keyword, class_name=_class_name, method_name=_method_name)
                        variable_file_entries.update(entries)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_file_entries)
        return variable_file_entries

    def process_variable_replacement(self, replacement_list):
        _method_name = '__process_variable_replacement'
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

        return variable_dict

    def __process_variable(self, location, replacement):
        _method_name = '__process_variable'
        _logger.entering(replacement, class_name=_class_name, method_name=_method_name)
        variable_dict = dict()
        section, start_mbean_list, attribute, segment, segment_name, replace_if_nosegment = _split_property(replacement)

        def _traverse_variables(model_section, mbean_list):
            if mbean_list:
                mbean = mbean_list.pop(0)
                if mbean in model_section:
                    _logger.finest('WLSDPLY-19414', mbean, class_name=_class_name, method_name=_method_name)
                    next_model_section = model_section[mbean]
                    location.append_location(mbean)
                    name_token = self.__aliases.get_name_token(location)
                    if self.__aliases.supports_multiple_mbean_instances(location):
                        for mbean_name in next_model_section:
                            continue_mbean_list = copy.copy(mbean_list)
                            location.add_name_token(name_token, mbean_name)
                            _traverse_variables(next_model_section[mbean_name], continue_mbean_list)
                            location.remove_name_token(name_token)
                    else:
                        _traverse_variables(next_model_section, mbean_list)
                    location.pop_location()
                else:
                    mbean_list = []
                    if len(location.get_folder_path()) > 1:
                        try:
                            mbean_list = self.__aliases.get_model_subfolder_names(location)
                        except AliasException, ae:
                            _logger.fine('AliasException {0}', ae.getLocalizedMessage())
                            pass
                    else:
                        try:
                            mbean_list = self.__aliases.get_model_top_level_folder_names()
                        except AliasException, ae:
                            _logger.fine('AliasException {0}', ae.getLocalizedMessage())
                            pass
                    _logger.fine('The mbean list from get model subfolder is {0}', mbean_list)
                    if mbean in mbean_list:
                        _logger.finer('WLSDPLY-19416', mbean, replacement, location.get_folder_path(),
                                      class_name=_class_name, method_name=_method_name)
                    else:
                        _logger.warning('WLSDPLY-19415', mbean, replacement, location.get_folder_path(),
                                        class_name=_class_name, method_name=_method_name)
                    return False
            else:
                if attribute in model_section:
                    # change this to be a loaded thing
                    variable_value = model_section[attribute]
                    if type(variable_value) != str or not variable_value.startswith('@@PROP:'):
                        variable_name = self.__format_variable_name(location, attribute)
                        attribute_value = '@@PROP:%s@@' % variable_name
                        if segment:
                            segment_attribute_value = attribute_value
                            segment_variable_name = variable_name
                            if segment_name:
                                segment_variable_name += segment_name
                                segment_attribute_value = '@@PROP:%s@@' % segment_variable_name
                            if isinstance(variable_value, dict):
                                segment_dict = variable_value
                                variable_value = None
                                for entry in segment_dict:
                                    if segment_dict != str or not segment_dict[entry].startswith('@@PROP:'):
                                        matcher = re.search(segment, entry)
                                        if matcher:
                                            variable_value = str(segment_dict[entry])
                                            segment_dict[entry] = segment_attribute_value
                                            variable_name = segment_variable_name
                                            attribute_value = segment_dict
                            elif isinstance(variable_value, list):
                                print ' need to refactor first'
                            else:
                                variable_value = str(variable_value)
                                replaced, attr_value, var_replaced = _replace_segment(segment, variable_value,
                                                                                      segment_attribute_value)
                                if replaced:
                                    variable_name = segment_variable_name
                                    variable_value = var_replaced
                                    attribute_value = attr_value
                                elif not replace_if_nosegment:
                                    _logger.finer('WLSDPLY-19424', segment, attribute, replacement,
                                                  location.get_folder_path, class_name=_class_name,
                                                  method_name=_method_name)
                                    variable_value = None

                        else:
                            variable_value = str(variable_value)
                        if variable_value:
                            _logger.fine('WLSDPLY-19425', attribute_value, attribute, variable_name, variable_value,
                                         class_name=_class_name, method_name=_method_name)
                            model_section[attribute] = attribute_value
                            variable_dict[variable_name] = variable_value
                else:
                    _logger.finer('WLSDPLY-19417', attribute, replacement, location.get_folder_path(),
                                  class_name=_class_name, method_name=_method_name)
            return True

        if section and section in self.__model:
            _traverse_variables(self.__model[section], start_mbean_list)
        else:
            _logger.finer('WLSDPLY-19423', section, replacement)
        _logger.exiting(class_name=_class_name, method_name=_method_name)
        return variable_dict

    def __format_variable_name(self, location, attribute):
        path = ''
        make_path = self.__aliases.get_model_folder_path(location)
        if make_path:
            make_path = make_path.split(':')
            if len(make_path) > 1 and len(make_path[1]) > 1:
                path = make_path[1]
        return path + '/' + attribute


def _get_variable_file_name(variables_helper_dictionary, **kwargs):
    if VARIABLE_FILE_NAME_ARG in variables_helper_dictionary:
        variable_file_location = variables_helper_dictionary[VARIABLE_FILE_NAME_ARG]
        del variables_helper_dictionary[VARIABLE_FILE_NAME_ARG]
        _logger.finer('WLSDPLY-19422', variable_file_location)
    elif VARIABLE_FILE_NAME_ARG in kwargs:
        variable_file_location = kwargs[VARIABLE_FILE_NAME_ARG]
        _logger.finer('WLSDPLY-19421', variable_file_location)
    else:
        variable_file_location = None
    return variable_file_location


def _get_variable_helper_file_name(**kwargs):
    variable_helper_file_name = VARIABLE_HELPER_FILE_NAME
    if VARIABLE_HELPER_FILE_NAME_ARG in kwargs:
        variable_helper_file_name = kwargs[VARIABLE_HELPER_FILE_NAME_ARG]
    if VARIABLE_HELPER_PATH_NAME_ARG in kwargs:
        return os.path.join(kwargs[VARIABLE_HELPER_PATH_NAME_ARG], variable_helper_file_name)
    else:
        return os.path.join(os.environ.get('WLSDEPLOY_HOME'), 'lib', variable_helper_file_name)


def _get_keyword_files_location(**kwargs):
    if VARIABLE_HELPER_PATH_NAME_ARG in kwargs:
        return kwargs[VARIABLE_HELPER_PATH_NAME_ARG]
    else:
        return os.path.join(os.environ.get('WLSDEPLOY_HOME'), 'etc')


def _load_replacement_list(replacement_file_name):
    _method_name = '_load_replacement_dictionary'
    _logger.entering(replacement_file_name, class_name=_class_name, method_name=_method_name)
    replacement_list = []
    if os.path.isfile(replacement_file_name):
        try:
            replacement_file = open(replacement_file_name, 'r')
            entry = replacement_file.readline()
            while entry:
                if entry != '\n':
                    _logger.finest('WLSDPLY-19411', entry, replacement_file_name, class_name=_class_name,
                                   method_name=_method_name)
                    replacement_list.append(entry.strip())
                entry = replacement_file.readline()
        except OSError, oe:
            _logger.warning('WLDPLY-19409', replacement_file_name, oe.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
    else:
        _logger.warning('WLSDPLY-19410', replacement_file_name, class_name=_class_name, method_name=_method_name)

    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return replacement_list


def _load_variables_dictionary(variable_helper_location):
    _method_name = '_load_variables_dictionary'
    _logger.entering(variable_helper_location, class_name=_class_name, method_name=_method_name)
    variables_dictionary = None
    if os.path.isfile(variable_helper_location):
        try:
            variables_dictionary = FileToPython(variable_helper_location).parse()
            _logger.fine('WLSDPLY-19400', variable_helper_location, class_name=_class_name, method_name=_method_name)
        except IllegalArgumentException, ia:
            _logger.warning('WLSDPLY-19402', variable_helper_location, ia.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return variables_dictionary


def _replace_segment(segment, variable_value, attribute_value):
    replaced = False
    replaced_value = None
    replacement_string = None
    pattern = re.compile(segment)
    matcher = pattern.search(variable_value)
    if matcher:
        replaced = True
        replaced_value = variable_value[matcher.start():matcher.end()]
        replacement_string = pattern.sub(attribute_value, variable_value)
    return replaced, replacement_string, replaced_value


def _split_property(attribute_path):
    """
    Split the section from the attribute path.
    :param attribute_path:
    :return:
    """
    section = None
    attribute = None
    mbean_list = None
    segment = None
    segment_name = None
    if_notfound_replace_full = None
    split_list = attribute_path.split(':', 1)
    if len(split_list) == 2 and split_list[0] in model_sections.get_model_top_level_keys():
        section = split_list[0]
        segment, segment_name, if_notfound_replace_full = _find_segment(split_list[1])
        attribute_path = _split_from_segment(split_list[1])
        mbean_list, attribute = _split_attribute_path(attribute_path)
    return section, mbean_list, attribute, segment, segment_name, if_notfound_replace_full


def _split_attribute_path(attribute_path):
    mbean_list = attribute_path.split('.')
    attribute = None
    if len(mbean_list) > 0:
        attribute = mbean_list.pop()
    return mbean_list, attribute


def _split_from_segment(attribute_path):
    return re.split('[\[\(].+[\]\)]$', attribute_path)[0]


def _find_segment(attribute_path):
    segment = None
    segment_name = None
    if_notfound_replace_full = None
    matcher = re.search('[\[\(].+[\]\)]$', attribute_path)
    if matcher:
        if attribute_path[matcher.start()] == '(':
            if_notfound_replace_full = True
        else:
            if_notfound_replace_full = False
        segment = attribute_path[matcher.start()+1:matcher.end()-1]
        matcher = re.search('\w*:', segment)
        if matcher:
            segment_name = segment[matcher.start():matcher.end()-1]
            segment = segment[matcher.end():]
    return segment, segment_name, if_notfound_replace_full


def _find_special_name(mbean):
    mbean_name_list = []
    matcher = re.search('(?<=\[).+(?=\])', mbean)
    if matcher:
        mbean_name = mbean[matcher.start():matcher.end()]
        for entry in mbean_name.split[',']:
            if entry:
                mbean_name_list.append(entry)
    return mbean_name_list


def _write_variables_file(variables_dictionary, variables_file_name):
    _method_name = '_write_variables_file'
    _logger.entering(variables_dictionary, variables_file_name, class_name=_class_name, method_name=_method_name)
    written = False
    if variables_dictionary:
        try:
            variables.write_variables(variables_dictionary, variables_file_name)
            written = True
        except VariableException, ve:
            _logger.warning('WLSDPLY-19407', variables_file_name, ve.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
    _logger.exiting(class_name=_class_name, method_name=_method_name, result=written)
    return written
