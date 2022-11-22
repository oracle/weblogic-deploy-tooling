"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import copy
import re

import os
import pprint
import unittest

from oracle.weblogic.deploy.aliases import VersionUtils
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import FileUtils

from oracle.weblogic.deploy.util import PyRealBoolean
from wlsdeploy.aliases.alias_constants import ChildFoldersTypes
from wlsdeploy.aliases.alias_constants import PATH_TOKEN
from wlsdeploy.aliases.alias_constants import SINGLE
from wlsdeploy.aliases.alias_entries import AliasEntries
from wlsdeploy.aliases.wlst_modes import WlstModes

from wlsdeploy.aliases.alias_constants import ACCESS
from wlsdeploy.aliases.alias_constants import ALIAS_DATA_TYPES
from wlsdeploy.aliases.alias_constants import ATTRIBUTES
from wlsdeploy.aliases.alias_constants import CHILD_FOLDERS_TYPE
from wlsdeploy.aliases.alias_constants import CONTAINS
from wlsdeploy.aliases.alias_constants import DEFAULT_NAME_VALUE
from wlsdeploy.aliases.alias_constants import DEFAULT_VALUE
from wlsdeploy.aliases.alias_constants import DERIVED_DEFAULT
from wlsdeploy.aliases.alias_constants import FLATTENED_FOLDER_DATA
from wlsdeploy.aliases.alias_constants import FOLDER_ORDER
from wlsdeploy.aliases.alias_constants import FOLDER_PARAMS
from wlsdeploy.aliases.alias_constants import FOLDERS
from wlsdeploy.aliases.alias_constants import GET
from wlsdeploy.aliases.alias_constants import GET_MBEAN_TYPE
from wlsdeploy.aliases.alias_constants import GET_METHOD
from wlsdeploy.aliases.alias_constants import LSA
from wlsdeploy.aliases.alias_constants import MERGE
from wlsdeploy.aliases.alias_constants import NAME_VALUE
from wlsdeploy.aliases.alias_constants import NONE
from wlsdeploy.aliases.alias_constants import ONLINE_BEAN
from wlsdeploy.aliases.alias_constants import PREFERRED_MODEL_TYPE
from wlsdeploy.aliases.alias_constants import RESTART_REQUIRED
from wlsdeploy.aliases.alias_constants import SET_MBEAN_TYPE
from wlsdeploy.aliases.alias_constants import SET_METHOD
from wlsdeploy.aliases.alias_constants import SHORT_NAME
from wlsdeploy.aliases.alias_constants import USES_PATH_TOKENS
from wlsdeploy.aliases.alias_constants import VERSION
from wlsdeploy.aliases.alias_constants import WLST_ATTRIBUTES_PATH
from wlsdeploy.aliases.alias_constants import WLST_CREATE_PATH
from wlsdeploy.aliases.alias_constants import WLST_LIST_PATH
from wlsdeploy.aliases.alias_constants import WLST_MODE
from wlsdeploy.aliases.alias_constants import WLST_NAME
from wlsdeploy.aliases.alias_constants import WLST_PATH
from wlsdeploy.aliases.alias_constants import WLST_PATHS
from wlsdeploy.aliases.alias_constants import WLST_READ_TYPE
from wlsdeploy.aliases.alias_constants import WLST_SUBFOLDERS_PATH
from wlsdeploy.aliases.alias_constants import WLST_TYPE

from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.attribute_setter import AttributeSetter
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_context import ModelContext


class ListTestCase(unittest.TestCase):
    _resources_dir = '../../test-classes/'
    _test_json_files = [
        'Test'
    ]
    _test_category_file_map = dict()

    _required_category_folder_keys = [
        'copyright',
        'license'
    ]

    _required_folder_keys = [
        ATTRIBUTES,
        FOLDERS,
        WLST_ATTRIBUTES_PATH,
        WLST_PATHS,
        WLST_TYPE
    ]

    _optional_folder_keys = [
        CHILD_FOLDERS_TYPE,
        CONTAINS,
        DEFAULT_NAME_VALUE,
        DERIVED_DEFAULT,
        FLATTENED_FOLDER_DATA,
        FOLDER_ORDER,
        FOLDER_PARAMS,
        ONLINE_BEAN,
        SHORT_NAME,
        VERSION,
        WLST_CREATE_PATH,
        WLST_LIST_PATH,
        WLST_MODE,
        WLST_SUBFOLDERS_PATH
    ]

    _required_attribute_keys = [
        DEFAULT_VALUE,
        VERSION,
        WLST_MODE,
        WLST_NAME,
        WLST_PATH,
        WLST_TYPE
    ]

    _optional_attribute_keys = [
        ACCESS,
        DERIVED_DEFAULT,
        GET_MBEAN_TYPE,
        GET_METHOD,
        MERGE,
        PREFERRED_MODEL_TYPE,
        RESTART_REQUIRED,
        SET_MBEAN_TYPE,
        SET_METHOD,
        USES_PATH_TOKENS,
        WLST_READ_TYPE
    ]

    _known_child_folders_type_values = list()
    for value in ChildFoldersTypes.values():
        _known_child_folders_type_values.append(value.lower())

    _known_access_attribute_values = [
        'RO',
        'ROD'
    ]

    _known_get_method_attribute_values = [
        GET,
        LSA,
        NONE
    ]

    _known_wlst_mode_attribute_values = [
        'both',
        'offline',
        'online'
    ]

    _folder_attributes_invalid_in_folder_params = [
        ATTRIBUTES,
        FOLDERS
    ]

    _token_pattern = re.compile("^%([\\w-]+)%$")
    _base_wlst_path_name = 'WP001'

    def setUp(self):
        self.alias_entries = AliasEntries(wls_version='12.2.1.3')
        self.online_alias_entries = AliasEntries(wls_version='12.2.1.3', wlst_mode=WlstModes.ONLINE)
        self.category_file_map = self.alias_entries._unit_test_only_get_category_map_files()
        for testfile in self._test_json_files:
            category_file_path = os.path.join(self._resources_dir, '%s.json' % testfile)
            self._test_category_file_map[testfile] = category_file_path

    def testForJsonFileTypos(self):
        category_results = dict()
        category_names = self.category_file_map.keys()
        category_names.sort()
        for category_name in category_names:
            category_file_path = self.category_file_map[category_name]
            category_dict = self._load_category_file(category_file_path)
            results = self._scan_category_dict_for_unknown_fields(category_name, category_dict)
            if len(results) > 0:
                category_results[category_name] = results
        message = 'Messages:\n' + pprint.pformat(category_results)
        self.assertEqual(len(category_results), 0, message)

    def testTestFilesForJsonFileTypos(self):
        category_results = dict()
        for category_name, category_file_path in self._test_category_file_map.iteritems():
            category_dict = self._load_test_category_file(category_file_path)
            results = self._scan_category_dict_for_unknown_fields(category_name, category_dict)
            if len(results) > 0:
                category_results[category_name] = results
        message = 'Messages:\n' + pprint.pformat(category_results)
        self.assertEqual(len(category_results), 0, message)

    def _load_category_file(self, category_file_path):
        category_input_stream = FileUtils.getResourceAsStream(category_file_path)
        self.assertNotEquals(category_input_stream, None)
        json_translator = JsonStreamTranslator(category_file_path, category_input_stream)
        return json_translator.parse()

    def _load_test_category_file(self, category_file_path):
        category_input_stream = FileUtils.getFileAsStream(category_file_path)
        self.assertNotEquals(category_input_stream, None)
        json_translator = JsonStreamTranslator(category_file_path, category_input_stream)
        return json_translator.parse()

    def _scan_category_dict_for_unknown_fields(self, category_name, category_dict):
        return self._process_folder(category_name, category_dict, True)

    def _process_folder(self, folder_path, folder_dict, top_level_folder=False, parent_path=""):
        result = []

        folder_keys = folder_dict.keys()
        if top_level_folder:
            # This method removes those special keys from the keys list to allow
            # the processing below to not have to know about them.
            result.extend(self._verify_required_category_keys(folder_path, folder_keys))

        result.extend(self._verify_required_folder_attributes(folder_path, folder_dict))
        for key in folder_keys:
            if key in self._required_folder_keys:
                # already checked these, will traverse dictionary types later
                continue
            elif key in self._optional_folder_keys:
                verify_function_name = '_verify_folder_%s_attribute_value' % key
                verify_function = getattr(self, verify_function_name)
                result.extend(verify_function(folder_path, folder_dict[key]))
            else:
                result.append(self._get_unknown_folder_key_message(folder_path, key))

        result.extend(self._check_folder_type(folder_path, folder_dict, parent_path))
        wlst_paths = dictionary_utils.get_dictionary_element(folder_dict, WLST_PATHS)
        next_parent = dictionary_utils.get_element(wlst_paths, self._base_wlst_path_name)
        if next_parent is None:
            result.append("Folder at path %s does not have %s entry named \"%s\"" %
                          (folder_path, WLST_PATHS, self._base_wlst_path_name))

        #
        # Now, verify the dictionary attribute types
        #
        subfolders = folder_dict[FOLDERS]
        for subfolder_name, subfolder_value in subfolders.iteritems():
            new_folder_path = folder_path + '/' + FOLDERS
            if type(subfolder_value) is not dict:
                result.append(self._get_invalid_dictionary_type_message(new_folder_path, subfolder_name,
                                                                        subfolder_value))
            else:
                new_folder_path += '/' + subfolder_name
                result.extend(self._process_folder(new_folder_path, subfolder_value, parent_path=next_parent))

        attributes = folder_dict[ATTRIBUTES]
        for attribute_name, attribute_value in attributes.iteritems():
            result.extend(self._process_attribute(folder_path, attribute_name, attribute_value))

        return result

    def _process_attribute(self, folder_path, attribute_name, attribute_value):
        result = []

        if type(attribute_value) is not list:
            result.append(self._get_invalid_list_type_message(folder_path, attribute_name, attribute_value))
        else:
            new_folder_path = folder_path + '/' + ATTRIBUTES
            attr_list_element = 0
            for attr_element_dict in attribute_value:
                new_attribute_name = attribute_name + '[' + str(attr_list_element) + ']'
                if type(attr_element_dict) is not dict:
                    result.append(self._get_invalid_dictionary_type_message(new_folder_path, new_attribute_name,
                                                                            attr_element_dict))
                else:
                    result.extend(self._process_attribute_entry(new_folder_path, new_attribute_name, attr_element_dict))

                attr_list_element += 1

            # after all syntax checks, check for overlapping version ranges
            result.extend(self._check_version_ranges(attribute_value, new_folder_path, attribute_name))

        return result

    def _process_attribute_entry(self, folder_path, attribute_name, attribute_value):
        result = []

        if type(attribute_value) is not dict:
            result.append(self._get_invalid_dictionary_type_message(folder_path, attribute_name, attribute_value))
        else:
            result.extend(self._verify_required_attribute_attributes(folder_path, attribute_name, attribute_value))
            for key in attribute_value:
                if key in self._required_attribute_keys:
                    # already checked these
                    pass
                elif key in self._optional_attribute_keys:
                    verify_function_name = '_verify_attribute_%s_attribute_value' % key
                    verify_function = getattr(self, verify_function_name)
                    result.extend(verify_function(folder_path, attribute_name, attribute_value[key]))
                else:
                    result.append(self._get_unknown_attribute_key_message(folder_path, attribute_name, key))

        return result

    def _verify_required_category_keys(self, category_name, category_keys):
        result = []
        for key in self._required_category_folder_keys:
            if key not in category_keys:
                result.append(self._get_missing_required_category_message(category_name, key))
            else:
                category_keys.remove(key)
        return result

    def _verify_required_folder_attributes(self, folder_name, folder_dict):
        result = []
        for key in self._required_folder_keys:
            if key not in folder_dict:
                result.append(self._get_missing_required_folder_key_message(folder_name, key))
            else:
                verify_function_name = '_verify_folder_%s_attribute_type' % key
                verify_function = getattr(self, verify_function_name)
                result.extend(verify_function(folder_name, folder_dict[key]))

        return result

    def _verify_required_attribute_attributes(self, folder_name, attribute_name, attribute_dict):
        result = []

        for key in self._required_attribute_keys:
            if key not in attribute_dict:
                result.append(self._get_missing_required_attribute_key_message(folder_name, attribute_name, key))
            else:
                verify_function_name = '_verify_attribute_%s_attribute_value' % key
                verify_function = getattr(self, verify_function_name)
                result.extend(verify_function(folder_name, attribute_name, attribute_dict[key]))

        return result

    ###########################################################################
    #    Dynamically-invoked folder attribute verification helpers            #
    ###########################################################################

    def _verify_folder_attributes_attribute_type(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not dict:
            result.append(self._get_invalid_dictionary_type_message(folder_name, ATTRIBUTES, attribute_value))
        return result

    def _verify_folder_folders_attribute_type(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not dict:
            result.append(self._get_invalid_dictionary_type_message(folder_name, FOLDERS, attribute_value))
        return result

    def _verify_folder_wlst_paths_attribute_type(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not dict:
            result.append(self._get_invalid_dictionary_type_message(folder_name, WLST_PATHS, attribute_value))
        return result

    def _verify_folder_wlst_type_attribute_type(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, WLST_TYPE, attribute_value))
        return result

    def _verify_folder_short_name_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, SHORT_NAME, attribute_value))
        return result

    def _verify_folder_online_bean_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, ONLINE_BEAN, attribute_value))
        return result

    def _verify_folder_folder_order_attribute_value(self, folder_name, attribute_value):
        result = []
        if (type(attribute_value) is not long and type(attribute_value) is not int) or \
                attribute_value < 0:
            result.append(self._get_invalid_attribute_value_message(folder_name, FOLDER_ORDER, attribute_value))
        return result

    def _verify_folder_wlst_attributes_path_attribute_type(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, WLST_ATTRIBUTES_PATH, attribute_value))
        return result

    def _verify_folder_child_folders_type_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, CHILD_FOLDERS_TYPE, attribute_value))
        elif attribute_value not in self._known_child_folders_type_values:
            result.append(self._get_invalid_attribute_value_message(folder_name, CHILD_FOLDERS_TYPE, attribute_value))
        return result

    def _verify_folder_contains_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not list:
            result.append(self._get_invalid_list_type_message(folder_name, CONTAINS, attribute_value))
        else:
            for ref in attribute_value:
                if ref not in self.category_file_map:
                    result.append(self._get_invalid_contains_reference_message(folder_name, ref))
        return result

    def _verify_folder_default_name_value_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, DEFAULT_NAME_VALUE, attribute_value))
        return result

    def _verify_folder_flattened_folder_data_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not dict:
            result.append(self._get_invalid_dictionary_type_message(folder_name, FLATTENED_FOLDER_DATA,
                                                                    attribute_value))
        else:
            if WLST_TYPE not in attribute_value:
                new_folder_name = folder_name + '/' + FLATTENED_FOLDER_DATA
                result.append(self._get_missing_required_folder_key_message(new_folder_name, WLST_TYPE))
            elif type(attribute_value[WLST_TYPE]) is not str:
                new_folder_name = folder_name + '/' + FLATTENED_FOLDER_DATA
                result.append(self._get_invalid_string_type_message(new_folder_name, WLST_TYPE,
                                                                    attribute_value[WLST_TYPE]))

            if NAME_VALUE not in attribute_value:
                new_folder_name = folder_name + '/' + FLATTENED_FOLDER_DATA
                result.append(self._get_missing_required_folder_key_message(new_folder_name, NAME_VALUE))
            elif type(attribute_value[NAME_VALUE]) is not str:
                new_folder_name = folder_name + '/' + FLATTENED_FOLDER_DATA
                result.append(self._get_invalid_string_type_message(new_folder_name, NAME_VALUE,
                                                                    attribute_value[NAME_VALUE]))

            if PATH_TOKEN not in attribute_value:
                new_folder_name = folder_name + '/' + FLATTENED_FOLDER_DATA
                result.append(self._get_missing_required_folder_key_message(new_folder_name, PATH_TOKEN))
            elif type(attribute_value[PATH_TOKEN]) is not str:
                new_folder_name = folder_name + '/' + FLATTENED_FOLDER_DATA
                result.append(self._get_invalid_string_type_message(new_folder_name, PATH_TOKEN,
                                                                    attribute_value[PATH_TOKEN]))
        return result

    def _verify_folder_folder_params_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not list or (len(attribute_value) > 0 and
                                                 type(attribute_value[0]) is not dict):
            result.append(self._get_invalid_list_of_dict_type_message(folder_name, FOLDER_PARAMS,
                                                                      attribute_value))
        else:
            # Make sure version is in each folder param
            folder_params = copy.deepcopy(attribute_value)
            for folder_param in folder_params:
                if VERSION not in folder_param:
                    result.extend(self._get_missing_required_attribute_key_message(folder_name,
                                                                                   VERSION, FOLDER_PARAMS))

                for key in folder_param:
                    if key in self._folder_attributes_invalid_in_folder_params:
                        result.append(self._get_invalid_folder_param_attribute(folder_name, key))
                    elif key == VERSION:
                        result.extend(self._verify_folder_version_attribute_value(folder_name, folder_param[VERSION]))
                    elif key == WLST_MODE:
                        result.extend(self._verify_folder_wlst_mode_attribute_value(folder_name, folder_param[key]))
                    elif key in self._required_folder_keys:
                        verify_function_name = '_verify_folder_%s_attribute_type' % key
                        verify_function = getattr(self, verify_function_name)
                        result.extend(verify_function(folder_name, folder_param[key]))
                    else:
                        result.append(self._get_unknown_folder_key_message(folder_name, key))

        return result

    def _verify_folder_version_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, VERSION, attribute_value))
        return result

    def _verify_folder_wlst_mode_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, folder_name,
                                                                      WLST_MODE, attribute_value)
            result.append(message)
        else:
            # curly braces not allowed in wlst_mode
            if attribute_value not in self._known_wlst_mode_attribute_values:
                message = self._get_invalid_wlst_mode_message(folder_name, attribute_value)
                result.append(message)
        return result

    def _verify_folder_wlst_create_path_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, WLST_CREATE_PATH, attribute_value))
        return result

    def _verify_folder_wlst_list_path_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, WLST_LIST_PATH, attribute_value))
        return result

    def _verify_folder_wlst_subfolders_path_attribute_value(self, folder_name, attribute_value):
        result = []
        if type(attribute_value) is not str:
            result.append(self._get_invalid_string_type_message(folder_name, WLST_SUBFOLDERS_PATH, attribute_value))
        return result

    ###########################################################################
    # Dynamically-invoked attribute dictionary attribute verification helpers #
    ###########################################################################

    def _verify_attribute_access_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      ACCESS, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_constrained_values(folder_name, attribute_name, ACCESS, alias_attribute_value,
                                                          self._known_access_attribute_values, True))
        return result

    def _verify_attribute_get_mbean_type_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      GET_MBEAN_TYPE, alias_attribute_value)
            result.append(message)
        return result

    def _verify_attribute_get_method_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      GET_METHOD, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_constrained_values(folder_name, attribute_name, GET_METHOD,
                                                          alias_attribute_value,
                                                          self._known_get_method_attribute_values, False))

        return result

    def _verify_attribute_merge_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        return self._verify_boolean_value(folder_name, attribute_name, MERGE, alias_attribute_value)

    def _verify_attribute_preferred_model_type_attribute_value(self, folder_name, attribute_name,
                                                               alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      PREFERRED_MODEL_TYPE, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_constrained_values(folder_name, attribute_name, PREFERRED_MODEL_TYPE,
                                                          alias_attribute_value, ALIAS_DATA_TYPES, False))

        return result

    def _verify_attribute_restart_required_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        return self._verify_boolean_value(folder_name, attribute_name, RESTART_REQUIRED, alias_attribute_value)

    def _verify_attribute_set_mbean_type_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      SET_MBEAN_TYPE, alias_attribute_value)
            result.append(message)

        return result

    def _verify_attribute_set_method_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      SET_METHOD, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_attribute_set_method(folder_name, attribute_name, WlstModes.OFFLINE,
                                                            alias_attribute_value, self.alias_entries))
            result.extend(self._verify_attribute_set_method(folder_name, attribute_name, WlstModes.ONLINE,
                                                            alias_attribute_value, self.online_alias_entries))
        return result

    def _verify_attribute_set_method(self, folder_name, attribute_name, wlst_mode, attribute_value, aliases):
        result = []
        resolved_attribute = aliases._resolve_curly_braces(attribute_value)
        if resolved_attribute:
            if not resolved_attribute.startswith('MBEAN'):
                message = self._get_invalid_alias_attribute_value_message(folder_name, attribute_name, SET_METHOD,
                                                                          WlstModes.from_value(wlst_mode),
                                                                          resolved_attribute,
                                                                          'it does not start with MBEAN')
                result.append(message)
            else:
                set_method_value_components = resolved_attribute.split('.')
                if len(set_method_value_components) == 2:
                    invoker = set_method_value_components[1]

                    model_context = ModelContext("test", {})
                    instance = AttributeSetter(model_context, aliases, ExceptionType.ALIAS, wlst_mode)
                    try:
                        getattr(instance, invoker)
                    except AttributeError:
                        result.append(self.set_method_not_found_message(folder_name, attribute_name,
                                                                        WlstModes.from_value(wlst_mode), invoker))
        return result

    def _verify_attribute_uses_path_tokens_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        return self._verify_boolean_value(folder_name, attribute_name, USES_PATH_TOKENS, alias_attribute_value)

    def _verify_attribute_default_value_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        # nothing to verify - default_value can be any type or null
        return []

    def _verify_attribute_derived_default_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        return []

    def _verify_attribute_version_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      VERSION, alias_attribute_value)
            result.append(message)

        return result

    def _verify_attribute_wlst_mode_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      WLST_MODE, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_constrained_values(folder_name, attribute_name, WLST_MODE,
                                                          alias_attribute_value,
                                                          self._known_wlst_mode_attribute_values, False))
        return result

    def _verify_attribute_wlst_name_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      WLST_NAME, alias_attribute_value)
            result.append(message)

        return result

    def _verify_attribute_wlst_path_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      WLST_PATH, alias_attribute_value)
            result.append(message)

        return result

    def _verify_attribute_wlst_read_type_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      WLST_READ_TYPE, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_constrained_values(folder_name, attribute_name, WLST_READ_TYPE,
                                                          alias_attribute_value, ALIAS_DATA_TYPES, False))

        return result

    def _verify_attribute_wlst_type_attribute_value(self, folder_name, attribute_name, alias_attribute_value):
        result = []
        if type(alias_attribute_value) is not str:
            message = self._get_invalid_attribute_string_type_message(folder_name, attribute_name,
                                                                      WLST_TYPE, alias_attribute_value)
            result.append(message)
        else:
            result.extend(self._verify_constrained_values(folder_name, attribute_name, WLST_TYPE,
                                                          alias_attribute_value, ALIAS_DATA_TYPES, False))

        return result

    ###########################################################################
    #                            Helper methods                               #
    ###########################################################################

    def _verify_boolean_value(self, folder_name, attribute_name, alias_attribute_name, alias_attribute_value):
        result = []
        constrained_string_values = ['true', 'false']
        if type(alias_attribute_value) is str:
            if alias_attribute_value.lower() not in constrained_string_values:
                result.append(self._get_invalid_attribute_boolean_string_value_message(folder_name, attribute_name,
                                                                                       alias_attribute_name,
                                                                                       alias_attribute_value))
            else:
                pass
        elif type(alias_attribute_value) is bool:
            pass
        elif isinstance(alias_attribute_value, PyRealBoolean):
            pass
        else:
            result.append(self._get_invalid_attribute_boolean_type_message(folder_name, attribute_name,
                                                                           alias_attribute_name, alias_attribute_value))
        return result

    def _verify_constrained_values(self, folder_name, attribute_name, alias_attribute_name,
                                   alias_attribute_value, constrained_values, empty_allowed=True):
        result = []
        if alias_attribute_value is None or len(alias_attribute_value) == 0:
            if empty_allowed:
                return result
            else:
                result.append(self._get_empty_constrained_value_message(folder_name, attribute_name,
                                                                        alias_attribute_name))
        else:
            offline_value = self.alias_entries._resolve_curly_braces(alias_attribute_value)
            result.extend(self._process_constrained_value_value(folder_name, attribute_name, alias_attribute_name,
                                                                offline_value, constrained_values, 'offline',
                                                                empty_allowed))

            online_value = self.online_alias_entries._resolve_curly_braces(alias_attribute_value)
            if offline_value != online_value:
                result.extend(self._process_constrained_value_value(folder_name, attribute_name, alias_attribute_name,
                                                                    online_value, constrained_values, 'online',
                                                                    empty_allowed))

        return result

    def _process_constrained_value_value(self, folder_name, attribute_name, alias_attribute_name,
                                         alias_attribute_value, constrained_values, wlst_mode, empty_allowed=True):
        result = []
        if alias_attribute_value is None or len(alias_attribute_value) == 0:
            if empty_allowed:
                return result
            else:
                result.append(self._get_empty_constrained_value_message(folder_name, attribute_name,
                                                                        alias_attribute_name, wlst_mode))
        elif alias_attribute_value not in constrained_values:
            result.append(self._get_constrained_value_error_message(folder_name, attribute_name,
                                                                    alias_attribute_name, alias_attribute_value,
                                                                    constrained_values, wlst_mode))
        return result

    def _check_folder_type(self, folder_path, folder_dict, parent_path):
        """
        Verify that the folder is correctly configured for the specified child folder type.
        All folder types should have tokens for folder names.
        Single MBean folders should have create_name, and a unique token at the end of each path.
        :param folder_path: the folder path, used for logging
        :param folder_dict: the dictionary for the folder
        :param parent_path: the WLST path of the parent folder
        :return: an array containing any error messages
        """
        result = []

        folders_type = dictionary_utils.get_element(folder_dict, CHILD_FOLDERS_TYPE)
        is_single_folder = folders_type in (SINGLE, None)
        required_last_token = folder_path.split('/')[-1].upper()
        tokens_found = False

        # verify that each wlst_path value has an alternating token pattern, such as:
        # /Folder1/%TOKEN1%/Folder2/%TOKEN2%/Folder3/%TOKEN3%
        wlst_paths = dictionary_utils.get_dictionary_element(folder_dict, WLST_PATHS)
        for key, wlst_path in wlst_paths.iteritems():
            # skip the first empty element, since path starts with /
            elements = wlst_path.split('/')[1:]

            # verify that each even-numbered element in each path is a token.
            last_token = None
            token_required = False
            for element in elements:
                if token_required:
                    matches = self._token_pattern.findall(element)
                    if len(matches) != 1:
                        result.append("Folder at path %s: %s %s has a name that should be a token: %s" %
                                      (folder_path, WLST_PATHS, key, element))
                    else:
                        last_token = matches[0]
                        tokens_found = True
                # toggle the token required flag
                token_required = not token_required

            if not wlst_path.startswith(parent_path):
                result.append("Folder at path %s: %s %s should start with \"%s\"" %
                              (folder_path, WLST_PATHS, key, parent_path))

            # for single folder, the final token in each wlst_path should correspond to the folder name.
            # this will ensure that the final token is unique in the path.
            if is_single_folder and (last_token is not None) and (last_token != required_last_token):
                result.append("Folder at path %s: %s %s last token should reflect folder name: %s" %
                              (folder_path, WLST_PATHS, key, required_last_token))

        # for single folder, if any tokens were found, a create name should be provided.
        if is_single_folder and tokens_found:
            default_name = dictionary_utils.get_element(folder_dict, DEFAULT_NAME_VALUE)
            if default_name is None:
                result.append("Folder at path %s: %s is required for single MBean folder with path tokens" %
                              (folder_path, DEFAULT_NAME_VALUE))

        return result

    def _check_version_ranges(self, attribute_value, new_folder_path, attribute_name):
        result = []

        for mode in ['offline', 'online']:
            wlst_modes = [mode, 'both']
            versions = []
            for attr_element_dict in attribute_value:
                if type(attr_element_dict) is dict:
                    wlst_mode = dictionary_utils.get_element(attr_element_dict, WLST_MODE)
                    if wlst_mode in wlst_modes:
                        version = dictionary_utils.get_element(attr_element_dict, VERSION)
                        versions.append(version)

            for index in range(len(versions) - 1):
                version_1 = versions[index]
                for nextIndex in range(index + 1, len(versions)):
                    version_2 = versions[nextIndex]
                    if VersionUtils.doVersionRangesOverlap(version_1, version_2):
                        result.append('Attribute %s at path %s: Version ranges for %s overlap: %s %s' %
                                      (attribute_name, new_folder_path, mode, version_1, version_2))
        return result

    ###########################################################################
    #                  Error messages helper methods                          #
    ###########################################################################

    def _get_missing_required_category_message(self, category_name, missing_key):
        return 'Category %s file is missing the required %s key' % (category_name, missing_key)

    def _get_unknown_folder_key_message(self, folder_name, unknown_key):
        return 'Folder at path %s has an unknown key %s' % (folder_name, unknown_key)

    def _get_unknown_attribute_key_message(self, folder_name, attribute_name, unknown_key):
        return 'Folder at path %s with defined attribute %s has an unknown key %s' % \
               (folder_name, attribute_name, unknown_key)

    def _get_missing_required_folder_key_message(self, folder_name, missing_key):
        return 'Folder at path %s is missing the required key %s' % (folder_name, missing_key)

    def _get_missing_required_attribute_key_message(self, folder_name, attribute_name, key):
        return 'Folder at path %s with defined attribute %s is missing the required key %s' % \
               (folder_name, attribute_name, key)

    def _get_invalid_folder_param_attribute(self, folder_name, attribute_name):
        text = 'Folder parameter at path %s contains an invalid folder param folder attribute %s'
        return text % (folder_name, attribute_name)

    def _get_invalid_dictionary_type_message(self, folder_name, attribute_name, attribute_value):
        return 'Folder at path %s has %s attribute that is expected to be a dictionary but is a %s instead' % \
               (folder_name, attribute_name, str(type(attribute_value)))

    def _get_invalid_list_type_message(self, folder_name, attribute_name, attribute_value):
        return 'Folder at path %s has %s attribute that is expected to be a list but is a %s instead' % \
               (folder_name, attribute_name, str(type(attribute_value)))

    def _get_invalid_list_of_dict_type_message(self, folder_name, attribute_name, attribute_value):
        return 'Folder at path %s has %s attribute that is expected to be a list of dict but is a %s instead' % \
               (folder_name, attribute_name, str(type(attribute_value)))

    def _get_invalid_string_type_message(self, folder_name, attribute_name, attribute_value):
        return 'Folder at path %s has %s attribute that is expected to be a string but is a %s instead' % \
               (folder_name, attribute_name, str(type(attribute_value)))

    def _get_invalid_attribute_value_message(self, folder_name, attribute_name, attribute_value):
        return 'Folder at path %s has %s attribute that has an invalid value %s' % \
               (folder_name, attribute_name, str(attribute_value))

    def _get_invalid_contains_reference_message(self, folder_name, ref):
        return 'Folder at path %s has contains attribute that references an invalid category %s' % (folder_name, ref)

    def _get_invalid_attribute_dictionary_type_message(self, folder_name, attribute_name,
                                                       alias_attribute_name, alias_attribute_value):
        text = 'Folder at path %s has a defined attribute %s with alias attribute %s that is expected to ' \
               'be a dictionary but is a %s instead'

        return  text % (folder_name, attribute_name, alias_attribute_name, str(type(alias_attribute_value)))

    def _get_invalid_attribute_string_type_message(self, folder_name, attribute_name,
                                                   alias_attribute_name, alias_attribute_value):
        text = 'Folder at path %s has a defined attribute %s with alias attribute %s that is expected to ' \
               'be a string but is a %s instead'

        return  text % (folder_name, attribute_name, alias_attribute_name, str(type(alias_attribute_value)))

    def _get_invalid_attribute_boolean_type_message(self, folder_name, attribute_name,
                                                     alias_attribute_name, alias_attribute_value):
        text = 'Folder at path %s has a defined attribute %s with alias attribute %s that is expected to ' \
               'be a boolean or a string but it was a %s instead'

        return  text % (folder_name, attribute_name, alias_attribute_name, str(type(alias_attribute_value)))

    def _get_invalid_attribute_boolean_string_value_message(self, folder_name, attribute_name,
                                                            alias_attribute_name, alias_attribute_value):
        text = 'Folder at path %s has a defined attribute %s with alias attribute %s that is expected to ' \
               'be a boolean but its string value %s is not a valid boolean value'

        return  text % (folder_name, attribute_name, alias_attribute_name, alias_attribute_value)


    def _get_invalid_wlst_mode_message(self, folder_name, alias_attribute_name):
        text = 'Folder at path %s has invalid wlst mode type of %s'
        result = text %(folder_name, alias_attribute_name)
        return result

    def _get_empty_constrained_value_message(self, folder_name, attribute_name, alias_attribute_name, wlst_mode=None):
        if wlst_mode is None:
            text = 'Folder at path %s has a defined attribute %s with alias attribute %s whose value was empty'
            result = text % (folder_name, attribute_name, alias_attribute_name)
        else:
            text = 'Folder at path %s has a defined attribute %s with alias attribute %s whose %s value was empty'
            result = text % (folder_name, attribute_name, alias_attribute_name, wlst_mode)
        return result

    def _get_constrained_value_error_message(self, folder_name, attribute_name, alias_attribute_name,
                                             alias_attribute_value, constrained_values, wlst_mode):
        text = 'Folder at path %s has a defined attribute %s with alias attribute %s whose %s ' \
               'value %s was not in the supported values list %s'
        return text % (folder_name, attribute_name, alias_attribute_name, wlst_mode,
                       alias_attribute_value, str(constrained_values))

    def _get_invalid_alias_attribute_value_message(self, folder_name, attribute_name, alias_attribute_name,
                                                   wlst_mode, alias_attribute_value, cause):
        text = 'Folder at path %s has a defined attribute %s with alias attribute %s whose ' \
               '%s value %s was not valid because %s'
        return text % (folder_name, attribute_name, alias_attribute_name, wlst_mode, alias_attribute_value, cause)

    def set_method_not_found_message(self, folder_name, attribute_name, wlst_mode, alias_attribute_value):
        text = 'Folder at path %s has a %s defined attribute %s whose set_method %s was not found in the' \
               ' attribute setter class'
        return text % (folder_name, attribute_name, wlst_mode, alias_attribute_value)
