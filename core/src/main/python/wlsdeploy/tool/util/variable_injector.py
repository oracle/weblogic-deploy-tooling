"""
Copyright (c) 2018, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import os
import re
import shutil

import java.io.FileInputStream as FileInputStream
import java.io.FileOutputStream as FileOutputStream
import java.io.IOException as IOException
import java.lang.Boolean as Boolean
import java.lang.IllegalArgumentException as IllegalArgumentException
import java.util.Properties as Properties

import oracle.weblogic.deploy.aliases.AliasException as AliasException
import oracle.weblogic.deploy.json.JsonException as JsonException
import oracle.weblogic.deploy.util.PyOrderedDict as OrderedDict
import oracle.weblogic.deploy.util.VariableException as VariableException
import wlsdeploy.tool.util.variable_injector_functions as variable_injector_functions
import wlsdeploy.util.model as model_sections
import wlsdeploy.util.variables as variables
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import path_utils
import wlsdeploy.util.unicode_helper as str_helper

WEBLOGIC_DEPLOY_HOME_TOKEN = '@@WLSDEPLOY@@'

VARIABLE_INJECTOR_FILE_NAME = 'model_variable_injector.json'
VARIABLE_KEYWORDS_FILE_NAME = 'variable_keywords.json'

VARIABLE_FILE_APPEND = 'append'
VARIABLE_FILE_UPDATE = 'update'
VARIABLE_FILE_APPEND_VALS = [VARIABLE_FILE_APPEND, VARIABLE_FILE_UPDATE]

# custom keyword in model injector file
CUSTOM_KEYWORD = 'CUSTOM'
KEYWORD_FILES = 'file-list'

# location for model injector file, keyword file and injector files
INJECTORS_LOCATION = 'injectors'

# should these injector json keywords be included in the keyword file
REGEXP = 'regexp'
REGEXP_SUFFIX = 'suffix'
REGEXP_PATTERN = 'pattern'
FORCE = 'force'
VARIABLE_VALUE = 'variable_value'

VARIABLE_SEP = '.'
SUFFIX_SEP = '--'

MANAGED_SERVERS = 'MANAGED_SERVERS'
ADMIN_SERVER = 'ADMIN_SERVER'

# This could be changed into a loaded file so that others can add their own bits of code to
# selectively identify which names in an mbean list should be injected with properties
USER_KEYWORD_DICT = {
    MANAGED_SERVERS: 'managed_server_list',
    ADMIN_SERVER: 'admin_server_list'
}

STANDARD_PASSWORD_INJECTOR = {
    VARIABLE_VALUE: ''
}

# global variables for functions in VariableInjector
_find_special_names_pattern = re.compile('[\[\]]')
_fake_name_marker = 'fakename'
_split_around_special_names = re.compile('([\w]+\[[\w\.,]+\])|\.')

_class_name = 'variable_injector'
_logger = PlatformLogger('wlsdeploy.tool.util')


class VariableInjector(object):

    def __init__(self, program_name, model, model_context, version=None, variable_dictionary=None):
        """
        Construct an instance of the injector with the model and information used by the injector.
        :param program_name: name of the calling tool
        :param model: to be updated with variables
        :param model_context: context with command line information
        :param version: of model if model context is not provided
        :param variable_dictionary: optional, a pre-populated map of variables
        """
        self.__program_name = program_name
        self.__original = copy.deepcopy(model)
        self.__model = model
        self.__model_context = model_context
        if self.__model_context:
            self.__wlst_mode = self.__model_context.get_target_wlst_mode()
        else:
            self.__wlst_mode = WlstModes.OFFLINE
        self.__section_keys = model_sections.get_model_top_level_keys()
        self.__section_keys.remove(model_sections.get_model_domain_info_key())

        if version:
            self.__aliases = Aliases(model_context, wlst_mode=self.__wlst_mode, wls_version=version)
        else:
            self.__aliases = Aliases(model_context)
        self.__variable_dictionary = variable_dictionary

    def get_variable_cache(self):
        """
        This caches all variable information, both from running as a tool, and collected during special
        processing while discovering the domain. DiscoverDomain methods should use a common variable injector
        and call the method variable_info to add to the cache outside of the tool.
        :return: variable dictionary containing token name and variable value
        """
        if self.__variable_dictionary is None:
            # ordered dictionary required to keep a multi-part variable in correct order for tokenizing
            self.__variable_dictionary = OrderedDict()
        return self.__variable_dictionary

    def get_aliases(self):
        """
        Get the aliases object
        :return: the aliases object
        """
        return self.__aliases

    def add_to_cache(self, dictionary=None, token_name=None, token_value=None):
        """
        Must pass either a dictionary containing token names and token values or a single token name and token
        value, or both. If the dictionary is not None, will update the cache with the dictionary. If the
        token name is not None, insert the token and value into the cache. If a token name (passed in either
        fashion) already exists in the cache, the value will be overwritten in the cache with the passed value.
        The dictionary is applied first, and then the token name, token value.
        :param dictionary: containing one or more token names and token values to add to the cache.
        :param token_name: single token name to insert into the cache
        :param token_value: value to insert into the cache with the provided token name
        """
        cache = self.get_variable_cache()
        if dictionary is not None and len(dictionary) > 0:
            cache.update(dictionary)
        if token_name is not None:
            cache[token_name] = token_value
        return cache

    def remove_from_cache(self, location, attribute_name):
        """
        For special circumstances, when scrubbing data from the model, remove the property from the cache.
        :param location: context for current location. This does not work for segmented properties.
        :param attribute_name: attribute for which to remove property from the cache.
        :return:
        """
        _method_name = 'remove_from_cache'
        _logger.entering(attribute_name, class_name=_class_name, method_name=_method_name)
        cache = self.get_variable_cache()
        if len(cache) > 0:
            property_name = self.get_variable_name(location, attribute_name)
            if property_name in cache:
                _logger.fine('WLSDPLY-19545', property_name, class_name=_class_name, method_name=_method_name)
                del cache[property_name]
        _logger.exiting(class_name=_class_name, method_name=_method_name)

    def custom_injection(self, model, attribute, location, injector_values=OrderedDict()):
        """
        Used by external processes to add to the  variable cache prior to persisting to the variables file. A token
        or tokens are created for the attribute based on the language provided in the injector values.
        The resulting variable name and value value is placed into the cache, and the model has the token injected
        into the attribute value.
        :param model: to tokenize attribute values with a token and extracting the attribute value
        :param attribute: name of the attribute to tokenize in the model
        :param location: current location context for the attribute
        :param injector_values: list of language to apply to the attribute
        :return: dictionary containing variable name(s) and value(s)
        """
        if attribute in model:
            variable_dictionary = self._add_variable_info(model, attribute, location, injector_values)
            self.add_to_cache(dictionary=variable_dictionary)

    def inject_variables_keyword_file(self, append_option=None):
        """
        Replace attribute values with variables and generate a variable dictionary.
        The variable replacement is driven from the values in the model variable helper file.
        This file can either contain the name of a replacement file, or a list of pre-defined
        keywords for canned replacement files.
        Return the variable dictionary with the variable name inserted into the model, and the value
        that the inserted variable replaced.
        :param append_option: 'append', 'update', or None
        :return: flag indicating insertion, the revised model, and variable file path
        """
        _method_name = 'inject_variables_keyword_file'
        _logger.entering(class_name=_class_name, method_name=_method_name)

        if self.__model_context.is_targetted_config():
            # this is mostly used for logging, so put the target config path here
            variable_injector_location_file = self.__model_context.get_target_configuration_file()
        else:
            # check for file location overrides from command line
            injector_file_override = self.__model_context.get_variable_injector_file()
            if injector_file_override is not None:
                variable_injector_location_file = injector_file_override
                _logger.info('WLSDPLY-19600', injector_file_override, class_name=_class_name, method_name=_method_name)
            else:
                variable_injector_location_file = path_utils.find_config_path(VARIABLE_INJECTOR_FILE_NAME)

        keywords_file_override = self.__model_context.get_variable_keywords_file()
        if keywords_file_override is not None:
            variable_keywords_location_file = keywords_file_override
            _logger.info('WLSDPLY-19601', keywords_file_override, class_name=_class_name, method_name=_method_name)
        else:
            variable_keywords_location_file = path_utils.find_config_path(VARIABLE_KEYWORDS_FILE_NAME)

        # discover may have passed -variable_file; inject variables may have passed -variable_properties_file
        variable_file_override = self.__model_context.get_variable_file()
        properties_file_override = self.__model_context.get_variable_properties_file()

        if variable_file_override is not None:
            variable_file_location = variable_file_override
        elif properties_file_override is not None:
            variable_file_location = properties_file_override
            _logger.info('WLSDPLY-19602', properties_file_override, class_name=_class_name, method_name=_method_name)
        else:
            variable_file_location = variables.get_default_variable_file_name(self.__model_context)

        if variable_file_location:
            variable_file_location = self._replace_tokens(variable_file_location)

        variables_injector_dictionary = self._load_variable_injector_file(variable_injector_location_file)
        keywords_dictionary = _load_keywords_file(variable_keywords_location_file)

        return_model = self.__original
        variables_inserted = False
        if not variable_file_location:
            _logger.warning('WLSDPLY-19520', variable_injector_location_file, class_name=_class_name,
                            method_name=_method_name)
        else:
            append, stage_dictionary = _load_variable_file(variable_file_location, append_option)
            self.add_to_cache(stage_dictionary)
            if variables_injector_dictionary and keywords_dictionary:
                _logger.info('WLSDPLY-19533', variable_injector_location_file, class_name=_class_name,
                             method_name=_method_name)

                injector_file_list = _create_injector_file_list(variables_injector_dictionary, keywords_dictionary)

                # perform the actual replacement of value with token variables
                variables_file_dictionary = self.inject_variables_keyword_dictionary(injector_file_list)
                if variables_file_dictionary:
                    self.add_to_cache(variables_file_dictionary)
            else:
                _logger.fine('WLSDPLY-19532', variable_injector_location_file, class_name=_class_name,
                             method_name=_method_name)

            variable_dictionary = self.get_variable_cache()
            if variable_dictionary is not None and len(variable_dictionary) > 0:
                # change variable_file_location to output_dir for target operation
                if self.__model_context.get_target() is not None:
                    new_variable_file_location = os.path.join(self.__model_context.get_output_dir(),
                                                              os.path.basename(variable_file_location))
                    if variable_file_location is not None and os.path.exists(variable_file_location):
                        # copy the original file first
                        append = True
                        if variable_file_location != new_variable_file_location:
                            shutil.copyfile(variable_file_location, new_variable_file_location)
                        self._filter_duplicate_properties(new_variable_file_location, variable_dictionary)
                    variable_file_location = new_variable_file_location

                variables_inserted = self._write_variables_file(variable_dictionary, variable_file_location, append)
            if variables_inserted:
                _logger.info('WLSDPLY-19518', variable_file_location, class_name=_class_name,
                             method_name=_method_name)
                return_model = self.__model
            else:
                _logger.info('WLSDPLY-19519', class_name=_class_name, method_name=_method_name)
                variable_file_location = None

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variables_inserted)
        return variables_inserted, return_model, variable_file_location

    def _filter_duplicate_properties(self, variable_file_location, variable_dictionary):
        """
        Remove the keys of variables that will be re-added to the file, to avoid duplicates.
        :param variable_file_location: the file to be modified
        :param variable_dictionary: keys to remove
        """
        _method_name = '_filter_duplicate_properties'
        _logger.entering(class_name=_class_name, method_name=_method_name)
        try:
            fis = FileInputStream(variable_file_location)
            prop = Properties()
            prop.load(fis)
            fis.close()

            for key in variable_dictionary:
                if prop.get(key) is not None:
                    prop.remove(key)

            fos = FileOutputStream(variable_file_location)
            prop.store(fos, None)
            fos.close()
        except IOException, e:
            _logger.warning('WLSDPLY-05803', e.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name)


    def inject_variables_keyword_dictionary(self, injector_file_list):
        """
        Takes a variable keyword dictionary and returns a variables for file in a dictionary
        :param injector_file_list: list of injector files for processing variable injection
        :return: variables_dictionary containing the variable properties to persist to the variable file
        """
        _method_name = 'inject_variables_keyword_dictionary'
        _logger.entering(injector_file_list, class_name=_class_name, method_name=_method_name)
        variable_dictionary = OrderedDict()
        for filename in injector_file_list:
            injector_dictionary = _load_injector_file(self._replace_tokens(filename))
            entries = self.inject_variables(injector_dictionary)
            if entries:
                _logger.finer('WLSDPLY-19513', filename, class_name=_class_name, method_name=_method_name)
                variable_dictionary.update(entries)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_dictionary)
        return variable_dictionary

    def inject_variables(self, injector_dictionary):
        """
        Iterate through the injector dictionary that was loaded from the file for the model
        injector file keyword.
        :param injector_dictionary:
        :return: variable dictionary containing the variable string and model value entries
        """
        variable_dict = OrderedDict()
        if injector_dictionary:
            location = LocationContext()
            domain_token = self.__aliases.get_name_token(location)
            location.add_name_token(domain_token, _fake_name_marker)
            for injector, injector_values in injector_dictionary.iteritems():
                entries_dict = self.__inject_variable(location, injector, injector_values)
                if len(entries_dict) > 0:
                    variable_dict.update(entries_dict)

        return variable_dict

    def __inject_variable(self, location, injector, injector_values):
        _method_name = '__inject_variable'
        _logger.entering(injector, class_name=_class_name, method_name=_method_name)
        variable_dict = OrderedDict()
        start_mbean_list, attribute = _split_injector(injector)

        def _traverse_variables(model_section, mbean_list):
            if mbean_list:
                mbean = mbean_list.pop(0)
                mbean, mbean_name_list = self._find_special_name(mbean)
                _logger.finer('WLSDPLY-19523', mbean, location.get_folder_path(), class_name=_class_name,
                              method_name=_method_name)
                if mbean in model_section:
                    _logger.finest('WLSDPLY-19514', mbean, class_name=_class_name, method_name=_method_name)
                    next_model_section = model_section[mbean]
                    location.append_location(mbean)
                    name_token = self.__aliases.get_name_token(location)
                    if not mbean_name_list:
                        if self.__aliases.supports_multiple_mbean_instances(location):
                            mbean_name_list = next_model_section
                        else:
                            self._check_name_token(location, name_token)
                    else:
                        _logger.fine('WLSDPLY-19506', mbean_name_list, attribute, location.get_folder_path(),
                                     class_name=_class_name, method_name=_method_name)
                    if mbean_name_list:
                        for mbean_name in mbean_name_list:
                            if mbean_name in next_model_section:
                                continue_mbean_list = copy.copy(mbean_list)
                                location.add_name_token(name_token, mbean_name)
                                _traverse_variables(next_model_section[mbean_name], continue_mbean_list)
                                location.remove_name_token(name_token)
                    else:
                        _traverse_variables(next_model_section, mbean_list)
                    location.pop_location()
                else:
                    self._log_mbean_not_found(mbean, injector, location)
                    return False
            else:
                self._check_insert_attribute_model(location, model_section, attribute, injector_values)
                if attribute in model_section:
                    returned_dict = self._add_variable_info(model_section, attribute, location, injector_values)
                    if returned_dict:
                        variable_dict.update(returned_dict)
                else:
                    _logger.finer('WLSDPLY-19517', attribute, injector, location.get_folder_path(),
                                  class_name=_class_name, method_name=_method_name)
            return True

        section = self.__model
        if start_mbean_list:
            # Find out in what section is the mbean top folder so can move to that section in the model
            top_mbean, __ = self._find_special_name(start_mbean_list[0])
            for entry in self.__section_keys:
                if entry in self.__model and top_mbean in self.__model[entry]:
                    section = self.__model[entry]
                    break
        else:
            # This is a domain attribute
            section = self.__model[model_sections.get_model_topology_key()]
        # if it wasn't found, will log appropriately in the called method
        # This also will allow someone to put the section in the injector string
        _traverse_variables(section, start_mbean_list)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_dict)

        return variable_dict

    def get_folder_short_name(self, location):
        """
        Return the short name for the MBean at the provided location
        :param location: location context for the current folder
        :return: Short name, or None if no short name
        """
        _method_name = 'get_folder_short_name'
        short_name = self.__aliases.get_folder_short_name(location)
        if short_name is not None:
            _logger.finer('WLSDPLY-19546', location.get_folder_path(), short_name,
                          class_name=_class_name, method_name=_method_name)
        return short_name

    def _add_variable_info(self, model, attribute, location, injector_values):
        # add code here to put in model if force in injector values
        if REGEXP in injector_values:
            return self._process_regexp(model, attribute, location, injector_values)
        else:
            return self._process_attribute(model, attribute, location, injector_values)

    def _check_tokenized(self, attribute_value):
        """
        Return True if the specified attribute value is already tokenized.
        Subclasses may perform any additional processing to clean up variables that will be overwritten.
        :param attribute_value: the value to be checked
        """
        return variables.is_variable_string(attribute_value)

    def _process_attribute(self, model, attribute, location, injector_values):
        _method_name = '_process_attribute'
        _logger.entering(attribute, location.get_folder_path(), class_name=_class_name,
                         method_name=_method_name)
        variable_dict = OrderedDict()
        variable_name = None
        variable_value = None
        attribute_value = model[attribute]
        if not self._check_tokenized(attribute_value):
            variable_name = self.get_variable_name(location, attribute)
            variable_value = _format_variable_value(attribute_value)
            model[attribute] = self.get_variable_token(attribute, variable_name)

            _logger.fine('WLSDPLY-19525', variable_name, attribute_value, attribute, variable_value,
                         class_name=_class_name, method_name=_method_name)
        else:
            _logger.finer('WLSDPLY-19526', attribute_value, attribute, str_helper.to_string(location),
                          class_name=_class_name, method_name=_method_name)

        if variable_value is not None:
            variable_dict[variable_name] = self._check_replace_variable_value(location, attribute,
                                                                              variable_value, injector_values)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_dict

    def get_variable_name(self, location, attribute, suffix=None):
        """
        Return the variable name for use in the cache, and in the variable token.
        The default behavior is to return the concatenated location paths, with invalid characters cleared.
        Sub-classes may extend this for other types of tokens, such as @@SECRET.
        :param location: the location to be used
        :param attribute: the attribute to be examined
        :param suffix: optional suffix for name
        :return: the derived name, such as JDBC.Generic1.PasswordEncrypted
        """
        path = variable_injector_functions.format_variable_name(location, attribute, self.__aliases)
        if suffix:
            return path + SUFFIX_SEP + suffix
        return path

    def get_variable_token(self, attribute, variable_name):
        """
        Return the correct token for the specified attribute, based on the variable name.
        The default behavior is to return a property token with a corrected name.
        Sub-classes may extend this for other types of tokens, such as @@SECRET.
        :param attribute: the attribute to be examined (used by sub-classes)
        :param variable_name: the variable name, such as JDBC.Generic1.PasswordEncrypted
        :return: the complete token name, such as @@PROP:JDBC.Generic1.PasswordEncrypted@@
        """
        return '@@PROP:%s@@' % variable_name

    def _process_regexp(self, model, attribute, location, injector_values):
        if isinstance(model[attribute], dict):
            return self._process_patterns_dictionary(attribute, model[attribute], location, injector_values)
        elif type(model[attribute]) == list:
            return self._process_patterns_list(attribute, model[attribute], location, injector_values)
        else:
            return self._process_patterns_string(model, attribute, location, injector_values)

    def _process_patterns_string(self, model, attribute, location, injector_values):
        variable_dict = OrderedDict()
        regexp_list = injector_values[REGEXP]
        for dictionary in regexp_list:
            pattern = None
            suffix = None
            if REGEXP_PATTERN in dictionary:
                pattern = dictionary[REGEXP_PATTERN]
            if REGEXP_SUFFIX in dictionary:
                suffix = dictionary[REGEXP_SUFFIX]
            variable_name, variable_value = self._process_pattern_string(model, attribute, location, pattern, suffix)
            if variable_value:
                variable_dict[variable_name] = self._check_replace_variable_value(location, attribute, variable_value,
                                                                                  injector_values)
        return variable_dict

    def _process_pattern_string(self, model, attribute, location, pattern, suffix):
        _method_name = '_process_regexp_string'
        _logger.entering(attribute, location.get_folder_path(), pattern, suffix, class_name=_class_name,
                         method_name=_method_name)
        attribute_value, variable_name, variable_value = self._find_segment_in_string(attribute, model[attribute],
                                                                                      location, pattern, suffix)
        if variable_value:
            _logger.finer('WLSDPLY-19529', variable_name, attribute_value, attribute, variable_value,
                          class_name=_class_name, method_name=_method_name)
            model[attribute] = attribute_value
        # elif replace_if_nosegment:
        #     check_value = model[attribute]
        #     if not _already_property(check_value):
        #         variable_value = check_value
        #         variable_name = self.__format_variable_name(location, attribute)
        #         model[attribute] = _format_as_property(variable_name)
        #         _logger.finer('WLSDPLY-19530', attribute, model[attribute], class_name=_class_name,
        #                       method_name=_method_name)
        else:
            _logger.finer('WLSDPLY-19524', pattern, attribute, model[attribute],
                          location.get_folder_path, class_name=_class_name,
                          method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _find_segment_in_string(self, attribute, attribute_value, location, pattern, suffix):
        variable_name = None
        variable_value = None
        if not self._check_tokenized(attribute_value):
            variable_name = self.get_variable_name(location, attribute, suffix=suffix)
            attribute_value, variable_value = self._replace_segment(pattern, _format_variable_value(attribute_value),
                                                               self.get_variable_token(attribute, variable_name))
        return attribute_value, variable_name, variable_value

    def _replace_segment(self, regexp, variable_value, attribute_value):
        replaced_value = None
        replacement_string = variable_value
        pattern = _compile_pattern(regexp)
        if pattern:
            matcher = pattern.search(variable_value)
            if matcher:
                temp_value = variable_value[matcher.start():matcher.end()]
                if not self._check_tokenized(temp_value):
                    replacement_string = pattern.sub(attribute_value, variable_value)
                    replaced_value = temp_value
        return replacement_string, replaced_value

    def _process_patterns_list(self, attribute, attribute_value, location, injector_values):
        variable_dict = OrderedDict()
        regexp_list = injector_values[REGEXP]
        for dictionary in regexp_list:
            pattern = None
            suffix = None
            if REGEXP_PATTERN in dictionary:
                pattern = dictionary[REGEXP_PATTERN]
            if REGEXP_SUFFIX in dictionary:
                suffix = dictionary[REGEXP_SUFFIX]
            variable_name, variable_value = self._process_pattern_list(attribute, attribute_value, location, pattern,
                                                                       suffix)
            if variable_value:
                variable_dict[variable_name] = self._check_replace_variable_value(location, attribute, variable_value,
                                                                                  injector_values)
        return variable_dict

    def _process_pattern_list(self, attribute_name, attribute_list, location, pattern, suffix):
        _method_name = '_process_regexp_list'
        _logger.entering(attribute_name, attribute_list, location.get_folder_path(), pattern, suffix,
                         class_name=_class_name, method_name=_method_name)
        variable_name = None
        variable_value = None
        idx = 0
        for entry in attribute_list:
            attribute_value, seg_var_name, seg_var_value = self._find_segment_in_string(attribute_name, entry, location,
                                                                                        pattern, suffix)
            if seg_var_value:
                _logger.finer('WLSDPLY-19528', variable_name, attribute_name, variable_value, class_name=_class_name,
                              method_name=_method_name)
                attribute_list[idx] = attribute_value
                variable_name = seg_var_name
                variable_value = seg_var_value

            idx += 1
            # don't break, continue replacing any in dictionary, return the last variable value found
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _process_patterns_dictionary(self, attribute, attribute_dict, location, injector_values):
        variable_dict = OrderedDict()
        regexp_list = injector_values[REGEXP]
        for dictionary in regexp_list:
            pattern = None
            suffix = None
            if REGEXP_PATTERN in dictionary:
                pattern = dictionary[REGEXP_PATTERN]
            if REGEXP_SUFFIX in dictionary:
                suffix = dictionary[REGEXP_SUFFIX]
            variable_name, variable_value = self._process_pattern_dictionary(attribute, attribute_dict, location,
                                                                             pattern, suffix)
            if variable_value:
                variable_dict[variable_name] = self._check_replace_variable_value(location, attribute, variable_value,
                                                                                  injector_values)
        return variable_dict

    def _process_pattern_dictionary(self, attribute_name, attribute_dict, location, regexp, suffix):
        _method_name = '_process_regexp_dictionary'
        _logger.entering(attribute_name, attribute_dict, location.get_folder_path(), regexp, suffix,
                         class_name=_class_name, method_name=_method_name)
        variable_name = self.get_variable_name(location, attribute_name, suffix=suffix)
        variable_value = None
        pattern = _compile_pattern(regexp)
        if pattern:
            replacement = self.get_variable_token(attribute_name, variable_name)
            for entry in attribute_dict:
                if not self._check_tokenized(attribute_dict[entry]):
                    matcher = pattern.search(entry)
                    if matcher:
                        _logger.finer('WLSDPLY-19527', attribute_name, replacement, class_name=_class_name,
                                      method_name=_method_name)
                        variable_value = _format_variable_value(attribute_dict[entry])
                        attribute_dict[entry] = replacement
                    # don't break, continue replacing any in dictionary, return the last variable value found
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variable_value)
        return variable_name, variable_value

    def _check_name_token(self, location, name_token):
        if self.__aliases.requires_unpredictable_single_name_handling(location):
            location.add_name_token(name_token, _fake_name_marker)

    def _replace_tokens(self, path_string):
        result = path_string
        if path_string.startswith(WEBLOGIC_DEPLOY_HOME_TOKEN):
            wlsdeploy_location = path_utils.get_wls_deploy_path()
            result = path_string.replace(WEBLOGIC_DEPLOY_HOME_TOKEN, wlsdeploy_location)
        elif path_string and self.__model_context:
            result = self.__model_context.replace_token_string(path_string)
        return result

    def _log_mbean_not_found(self, mbean, replacement, location):
        _method_name = '_log_mbean_not_found'
        code = ValidationCodes.INVALID
        try:
            code, __ = self.__aliases.is_valid_model_folder_name(location, mbean)
        except AliasException:
            pass
        if code == ValidationCodes.INVALID:
            _logger.warning('WLSDPLY-19515', mbean, replacement, location.get_folder_path(),
                            class_name=_class_name, method_name=_method_name)
        else:
            _logger.finer('WLSDPLY-19516', mbean, replacement, location.get_folder_path(),
                          class_name=_class_name, method_name=_method_name)

    def _write_variables_file(self, variables_dictionary, variables_file_name, append):
        _method_name = '_write_variables_file'
        _logger.entering(variables_dictionary, variables_file_name, class_name=_class_name, method_name=_method_name)

        written = False
        if variables_dictionary is not None:
            try:
                variables.write_sorted_variables(self.__program_name, variables_dictionary, variables_file_name, append)
                written = True
            except VariableException, ve:
                _logger.warning('WLSDPLY-19507', variables_file_name, ve.getLocalizedMessage(), class_name=_class_name,
                                method_name=_method_name)
        _logger.exiting(class_name=_class_name, method_name=_method_name, result=written)
        return written

    def _find_special_name(self, mbean):
        mbean_name = mbean
        mbean_name_list = []
        name_list = _find_special_names_pattern.split(mbean)
        if name_list and len(name_list) > 1:
            mbean_name = name_list[0]
            mbean_name_list = name_list[1].split(',')
        if mbean_name_list:
            new_list = []
            for entry in mbean_name_list:
                if entry in USER_KEYWORD_DICT:
                    _logger.fine('WLSDPLY-19538', entry, mbean)
                    try:
                        method = getattr(variable_injector_functions, USER_KEYWORD_DICT[entry])
                        append_list = method(self.__model)
                        new_list.extend(append_list)
                    except AttributeError, e:
                        _logger.warning('WLSDPLY-19539', entry, USER_KEYWORD_DICT[entry], e)
                        new_list = mbean_name_list
                        break
                else:
                    new_list.append(entry)
            mbean_name_list = new_list
        return mbean_name, mbean_name_list

    def _check_insert_attribute_model(self, location, model_section, attribute, injector_values):
        _method_name = '_check_insert_attribute_model'
        if attribute not in model_section and (FORCE in injector_values and Boolean(injector_values[FORCE])):
            value = self.__aliases.get_model_attribute_default_value(location, attribute)
            _logger.fine('WLSDPLY-19540', attribute, location.get_folder_path(), value,
                         class_name=_class_name, method_name=_method_name)
            model_section[attribute] = value

    def _check_replace_variable_value(self, location, attribute, variable_value, injector_values):
        _method_name = '_format_variable_value'
        value = variable_value
        if VARIABLE_VALUE in injector_values:
            value = injector_values[VARIABLE_VALUE]
            # might add code to call a method to populate the replacement value
            try:
                wlst_attribute_name = self.__aliases.get_wlst_attribute_name(location, attribute)
                __, check = self.__aliases.get_model_attribute_name_and_value(location, wlst_attribute_name, value)
                if check is not None:
                    value = check
                _logger.finer('WLSDPLY-19542', value, variable_value, attribute, location.get_folder_path(),
                              class_name=_class_name, method_name=_method_name)
            except AliasException, ae:
                _logger.finer('WLSDPLY-19541', value, attribute, location, ae.getLocalizedMessage(),
                              class_name=_class_name, method_name=_method_name)
        return value

    def _load_variable_injector_file(self, variable_injector_location):
        _method_name = '_load_variable_injector_file'
        _logger.entering(variable_injector_location, class_name=_class_name, method_name=_method_name)
        variables_dictionary = None

        # If -target is presence, it take precedence

        if self.__model_context is not None and self.__model_context.is_targetted_config():
            variables_dictionary = self.__model_context.get_target_configuration().get_variable_injectors()
        else:
            if os.path.isfile(variable_injector_location):
                try:
                    variables_dictionary = JsonToPython(variable_injector_location).parse()
                    _logger.fine('WLSDPLY-19500', variable_injector_location, class_name=_class_name, method_name=_method_name)
                except (IllegalArgumentException, JsonException), e:
                    _logger.warning('WLSDPLY-19502', variable_injector_location, e.getLocalizedMessage(),
                                    class_name=_class_name, method_name=_method_name)

        _logger.exiting(class_name=_class_name, method_name=_method_name, result=variables_dictionary)
        return variables_dictionary


def _load_variable_file(variable_file_location, append_option):
    """
    Load the variable dictionary from the file, and determine if append or update.
    :param variable_file_location: the location of the variable file
    :param append_option: 'append', 'update', or None
    :return: tuple with append True or False, and the existing variable dictionary
    """
    _method_name = '_load_variable_file'
    append = False
    variable_dictionary = OrderedDict()
    if append_option in VARIABLE_FILE_APPEND_VALS:
        if append_option == VARIABLE_FILE_APPEND:
            _logger.fine('WLSDPLY-19536', variable_file_location, class_name=_class_name, method_name=_method_name)
            append = True
        elif append_option == VARIABLE_FILE_UPDATE and os.path.isfile(variable_file_location):
            _logger.fine('WLSDPLY-19534', variable_file_location, class_name=_class_name, method_name=_method_name)
            try:
                variable_dictionary = variables.load_variables(variable_file_location)
            except VariableException, ve:
                _logger.warning('WLSDPLY-19537', variable_file_location, ve.getLocalizedMessage(),
                                class_name=_class_name, method_name=_method_name)
        else:
            _logger.fine('WLSDPLY-19535', variable_file_location, class_name=_class_name, method_name=_method_name)
    return append, variable_dictionary


def _load_keywords_file(variable_keywords_location):
    _method_name = '_load_keywords_file'
    _logger.entering(variable_keywords_location, class_name=_class_name, method_name=_method_name)
    keywords_dictionary = None
    if os.path.isfile(variable_keywords_location):
        try:
            keywords_dictionary = JsonToPython(variable_keywords_location).parse()
            _logger.finer('WLSDPLY-19504', variable_keywords_location, class_name=_class_name, method_name=_method_name)
        except (IllegalArgumentException, JsonException), e:
            _logger.warning('WLSDPLY-19505', variable_keywords_location, e.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)

    _logger.exiting(class_name=_class_name, method_name=_method_name, result=keywords_dictionary)
    return keywords_dictionary


def _create_injector_file_list(variables_dictionary, keyword_dictionary):
    _method_name = '_create_file_dictionary'
    injector_file_list = []

    if CUSTOM_KEYWORD in variables_dictionary:
        if KEYWORD_FILES in variables_dictionary[CUSTOM_KEYWORD]:
            injector_file_list = variables_dictionary[CUSTOM_KEYWORD][KEYWORD_FILES]
            if type(injector_file_list) != list:
                injector_file_list = injector_file_list.split(',')
            _logger.fine('WLSDPLY-19501', injector_file_list, class_name=_class_name, method_name=_method_name)
        else:
            _logger.info('WLSDPLY-19512', class_name=_class_name, method_name=_method_name)
        del variables_dictionary[CUSTOM_KEYWORD]

    for keyword in variables_dictionary:
        if keyword in keyword_dictionary:
            filename = keyword_dictionary[keyword]
            if filename and filename not in injector_file_list:
                if not os.path.isabs(filename):
                    filename = path_utils.find_config_path(os.path.join(INJECTORS_LOCATION, filename))
                injector_file_list.append(filename)
                _logger.finer('WLSDPLY-19508', filename, keyword, class_name=_class_name, method_name=_method_name)
        else:
            _logger.warning('WLSDPLY-19503', keyword, class_name=_class_name, method_name=_method_name)
    return injector_file_list


def _load_injector_file(injector_file_name):
    _method_name = '_load_injector_file'
    _logger.entering(injector_file_name, class_name=_class_name, method_name=_method_name)
    injector_dictionary = OrderedDict()
    if os.path.isfile(injector_file_name):
        try:
            injector_dictionary = JsonToPython(injector_file_name).parse()
            __temporary_fix(injector_dictionary)
        except (IllegalArgumentException, JsonException), e:
            _logger.warning('WLDPLY-19409', injector_file_name, e.getLocalizedMessage(), class_name=_class_name,
                            method_name=_method_name)
    else:
        _logger.warning('WLSDPLY-19510', injector_file_name, class_name=_class_name, method_name=_method_name)

    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return injector_dictionary


def _format_variable_value(value):
    if type(value) == bool:
        if value:
            return 'True'
        return 'False'
    else:
        return str_helper.to_string(value)


def _compile_pattern(pattern):
    try:
        return re.compile(pattern)
    except Exception, e:
        _logger.warning('WLSDPLY-19511', pattern, e, class_name=_class_name, method_name='_compile_pattern')
    return None


def _split_injector(injector_path):
    """
    Split the injector path into an mbean list and an attribute name from the injector path string
    :param injector_path:
    :return: attribute name:mbean list of mbean folder nodes
    """
    _method_name = '_split_injector'
    attr = None
    ml = _split_around_special_names.split(injector_path)
    mbean_list = []
    if len(ml) > 0:
        attr = ml.pop()
        for mbean_item in ml:
            if mbean_item:
                start = 0
                end = len(mbean_item)
                if mbean_item.startswith('\.'):
                    start += 1
                if mbean_item.endswith('\.'):
                    end -= 1
                mbean_list.append(mbean_item[start:end])
    _logger.finer('WLSDPLY-19543', mbean_list, attr, class_name=_class_name, method_name=_method_name)
    return mbean_list, attr


def __temporary_fix(injector_dictionary):
    # this is very dangerous - for now, if you want to escape a backslash, need to do 4 backslash.
    _method_name = '__temporary_fix'
    for value in injector_dictionary.itervalues():
        if REGEXP in value:
            for dict_entry in value[REGEXP]:
                if REGEXP_PATTERN in dict_entry:
                    pattern = dict_entry[REGEXP_PATTERN]
                    listsplit = re.split('\\\\(?!\\\\)', pattern)
                    if listsplit:
                        newpattern = ''
                        for split in listsplit:
                            newpattern += split[:len(split)]
                        dict_entry[REGEXP_PATTERN] = newpattern
                _logger.fine('Pattern after temporary fix {0}', dict_entry[REGEXP_PATTERN], class_name=_class_name,
                             method_name=_method_name)
