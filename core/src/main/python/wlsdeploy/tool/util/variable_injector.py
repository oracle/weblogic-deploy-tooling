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

    def inject_variables_keyword_file(self, **kwargs):
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
        _method_name = 'inject_variables_keyword_file'
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

                variables_file_dictionary = self.inject_variables_keyword_dictionary(file_map, variables_helper_dictionary)
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

    def inject_variables_keyword_dictionary(self, keyword_map, variables_dictionary):
        """
        Takes a variable keyword dictionary and returns a variables for file in a dictionary
        :param variables_dictionary:
        :return:
        """
        _method_name = 'inject_variables_keyword_dictionary'
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
                    entries = self.inject_variables(replacement_list)
                    if entries:
                        _logger.finer('WLSDPLY-19413', keyword, class_name=_class_name, method_name=_method_name)
                        variable_file_entries.update(entries)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_file_entries)
        return variable_file_entries

    def inject_variables(self, replacement_list):
        _method_name = 'inject_variables'
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
                entries_dict = self.__inject_variable(location, replacement_entry)
                if len(entries_dict) > 0:
                    variable_dict.update(entries_dict)

        return variable_dict

    def __inject_variable(self, location, replacement):
        _method_name = '__process_variable'
        _logger.entering(replacement, class_name=_class_name, method_name=_method_name)
        variable_dict = dict()
        section, start_mbean_list, attribute, segment, segment_name, replace_if_nosegment = _split_property(replacement)

        def _traverse_variables(model_section, mbean_list):
            if mbean_list:
                mbean = mbean_list.pop(0)
                mbean, mbean_name_list = _find_special_name(mbean)
                if mbean in model_section:
                    _logger.finest('WLSDPLY-19414', mbean, class_name=_class_name, method_name=_method_name)
                    next_model_section = model_section[mbean]
                    location.append_location(mbean)
                    name_token = self.__aliases.get_name_token(location)
                    if not mbean_name_list and self.__aliases.supports_multiple_mbean_instances(location):
                        mbean_name_list = next_model_section
                    if mbean_name_list:
                        for mbean_name in mbean_name_list:
                            continue_mbean_list = copy.copy(mbean_list)
                            location.add_name_token(name_token, mbean_name)
                            _traverse_variables(next_model_section[mbean_name], continue_mbean_list)
                            location.remove_name_token(name_token)
                    else:
                        _traverse_variables(next_model_section, mbean_list)
                    location.pop_location()
                else:
                    self._log_mbean_not_found(mbean, replacement, location)
                    return False
            else:
                if attribute in model_section:
                    # change this to be a loaded thing
                    if segment:
                        variable_name, variable_value = self._process_segment(model_section, attribute, segment,
                                                                              segment_name, replace_if_nosegment,
                                                                              location)
                    else:
                        variable_name, variable_value = self._process_attribute(model_section, attribute, location)
                    if variable_value:
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

    def __format_variable_name_segment(self, location, attribute, segment_name):
        path = ''
        make_path = self.__aliases.get_model_folder_path(location)
        if make_path:
            make_path = make_path.split(':')
            if len(make_path) > 1 and len(make_path[1]) > 1:
                path = make_path[1]
        variable_name = path + '/' + attribute
        if segment_name:
            variable_name += segment_name
        return variable_name

    def _process_attribute(self, model, attribute, location):
        _method_name = '_process_attribute'
        _logger.entering(attribute, location.get_folder_path(), class_name=_class_name, method_name=_method_name)
        variable_name = None
        variable_value = None
        attribute_value = model[attribute]
        if not _already_property(attribute_value):
            variable_name = self.__format_variable_name(location, attribute)
            variable_value = str(model[attribute])
            model[attribute] = _format_as_property(variable_name)
        else:
            _logger.finer('WLSDPLY-19426', attribute_value, attribute, str(location), class_name=_class_name,
                          method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _process_segment(self, model, attribute, segment, segment_name, replace_if_nosegment, location):
        if isinstance(model[attribute], dict):
            return self._process_segment_in_dictionary(attribute, model[attribute], segment, segment_name, location)
        elif type(model[attribute]) == list:
            return self._process_segment_in_list(attribute, model[attribute], segment, segment_name, location)
        else:
            return self._process_segment_string(model, attribute, segment, segment_name,
                                                replace_if_nosegment, location)

    def _process_segment_string(self, model, attribute, segment, segment_name, replace_if_nosegment, location):
        _method_name = '_process_segment_string'
        _logger.entering(attribute, segment, segment_name, replace_if_nosegment, str(location))
        attribute_value, variable_name, variable_value = self._find_segment_in_string(attribute, model[attribute],
                                                                                      segment, segment_name, location)
        if variable_value:
            _logger.finer('WLSDPLY-19429', attribute, attribute_value, class_name=_class_name,
                          method_name=_method_name)
            model[attribute] = attribute_value
        elif replace_if_nosegment:
            check_value = model[attribute]
            if not _already_property(check_value):
                variable_value = check_value
                variable_name = self.__format_variable_name(location, attribute)
                model[attribute] = _format_as_property(variable_name)
                _logger.finer('WLSDPLY-19430', attribute, model[attribute], class_name=_class_name,
                              method_name=_method_name)
        else:
            _logger.finer('WLSDPLY-19424', segment, attribute, model[attribute],
                          location.get_folder_path, class_name=_class_name,
                          method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _find_segment_in_string(self, attribute, attribute_value, segment, segment_name, location):
        variable_name = None
        variable_value = None
        if not _already_property(attribute_value):
            variable_name = self.__format_variable_name_segment(location, attribute, segment_name)
            attribute_value, variable_value = _replace_segment(segment, str(attribute_value),
                                                               _format_as_property(variable_name))
        return attribute_value, variable_name, variable_value

    def _process_segment_in_list(self, attribute_name, attribute_list, segment, segment_name, location):
        _method_name = '_process_segment_in_dictionary'
        _logger.entering(attribute_name, attribute_list, segment, str(location), class_name=_class_name,
                         method_name=_method_name)
        variable_name = None
        variable_value = None
        idx = 0
        for entry in attribute_list:
            attribute_value, seg_var_name, seg_var_value = self._find_segment_in_string(attribute_name, entry, segment,
                                                                                        segment_name, location)
            if seg_var_value:
                _logger.finer('WLSDPLY-19429', attribute_name, attribute_value, class_name=_class_name,
                              method_name=_method_name)
                attribute_list[idx] = attribute_value
                variable_name = seg_var_name
                variable_value = seg_var_value

            idx += 1
            # don't break, continue replacing any in dictionary, return the last variable value found
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _process_segment_in_dictionary(self, attribute_name, attribute_dict, segment, segment_name, location):
        _method_name = '_process_segment_in_dictionary'
        _logger.entering(attribute_name, attribute_dict, segment, str(location), class_name=_class_name,
                         method_name=_method_name)
        variable_name = self.__format_variable_name_segment(location, attribute_name, segment_name)
        variable_value = None
        replacement = _format_as_property(variable_name)
        for entry in attribute_dict:
            if not _already_property(attribute_dict[entry]):
                matcher = re.search(segment, entry)
                if matcher:
                    _logger.finer('WLSDPLY-19427', attribute_name, replacement, class_name=_class_name,
                                  method_name=_method_name)
                    variable_value = str(attribute_dict[entry])
                    attribute_dict[entry] = replacement
                    # don't break, continue replacing any in dictionary, return the last variable value found
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _log_mbean_not_found(self, mbean, replacement, location):
        _method_name = '_log_mbean_not_found'
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
    replaced_value = None
    replacement_string = variable_value
    pattern = re.compile(segment)
    matcher = pattern.search(variable_value)
    if matcher:
        replaced_value = variable_value[matcher.start():matcher.end()]

        replacement_string = pattern.sub(attribute_value, variable_value)
    return replacement_string, replaced_value


def _already_property(check_string):
    return type(check_string) == str and check_string.startswith('@@PROP:')


def _format_as_property(prop_name):
    return '@@PROP:%s@@' % prop_name


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
    _logger.finest('WLSDPLY-19431', section, mbean_list, attribute, segment, segment_name, if_notfound_replace_full)
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
        matcher = re.search('(?<=`)\w*(?=`)', segment)
        if matcher:
            segment_name = segment[matcher.start():matcher.end()]
            segment = segment[matcher.end()+1:]
    return segment, segment_name, if_notfound_replace_full


def _find_special_name(mbean):
    mbean_name = mbean
    mbean_name_list = []
    name_list = re.split('[\{).+\}]', mbean)
    if name_list and len(name_list) > 1:
        mbean_name = name_list[0]
        mbean_name_list = name_list[1].split(',')
    return mbean_name, mbean_name_list


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
