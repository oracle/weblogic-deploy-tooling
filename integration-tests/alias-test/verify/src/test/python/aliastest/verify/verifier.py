"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import java.io.IOException as IOException
import java.lang.Boolean as Boolean

from oracle.weblogic.deploy.aliases import AliasException

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.aliases.alias_constants as alias_constants
from wlsdeploy.aliases.wlst_modes import WlstModes

from aliastest.verify.alias_helper import AliasHelper
import aliastest.verify.utils as verify_utils

ADDITIONAL_RECHECK = "additional"
ATTRIBUTES = 'attributes'
CMO_DEFAULT = 'cmo_default'
CMO_READ_TYPE = 'cmo_read_type'
CMO_TYPE = 'cmo_wlst_type'
DEPRECATED = 'deprecated'
DERIVED_DEFAULT = 'derived_default'
GET_DEFAULT = 'get_default'
GET_TYPE = 'get_wlst_type'
INSTANCE_TYPE = 'instance'
LSA_DEFAULT = 'lsa_default'
LSA_TYPE = 'lsa_wlst_type'
MULTIPLE = 'multiple'
ONLINE_REFERENCE_ONLY = 'reference_only'
READ_ONLY = 'readonly'
READ_TYPE = 'read_type'
READ_WRITE = 'readwrite'
RECHECK = 'recheck'
RESTART = 'restart_required'
RESTART_NO_CHECK = 'none'
SINCE_VERSION = 'since_version'
SINGLE = 'single'
SINGLE_NO_NAME = 'single_no_name'
TYPE = 'wlst_type'
UNKNOWN = 'unknown'

NUMBER_TYPES = [alias_constants.INTEGER, alias_constants.LONG, alias_constants.DOUBLE]
LIST_TYPES = [alias_constants.LIST, alias_constants.JARRAY]
CONVERT_TO_DELIMITED_TYPES = [alias_constants.LIST, alias_constants.JARRAY,
                              alias_constants.ALIAS_MAP_TYPES, alias_constants.DICTIONARY]
CONVERT_TO_BOOLEAN_TYPES = [alias_constants.INTEGER, alias_constants.STRING, UNKNOWN]

VERIFY_RANGE = range(1000, 1999)
WARN_RANGE = range(5000, 5999)
ERROR_RANGE = range(2000, 8999)
UNKNOWN_ERROR = range(2000, 2999)
MBEAN_ERROR_RANGE = range(3000, 3999)
ATTRIBUTE_ERROR_RANGE = range(4000, 4999)

TESTED_MBEAN_FOLDER = 1000
INFO_ATTRIBUTE_IN_IGNORE_LIST = 1001

WARN_MBEAN_NOT_NO_NAME_0 = 5101
WARN_ATTRIBUTE_DEPRECATED = 5502
WARN_ATTRIBUTE_HAS_UNKNOWN_TYPE = 5500
WARN_ALIAS_FOLDER_NOT_IMPLEMENTED = 5501
WARN_NO_DERIVED_DEFAULT_IN_GENERATED = 5502


ERROR_FAILURE_ATTRIBUTE_LIST = 2000
ERROR_FAILURE_ATTRIBUTE_UNEXPECTED = 2001

ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER = 3001
ERROR_USING_REFERENCE_AS_FOLDER = 3002
ERROR_CANNOT_TEST_MBEAN_UNSPECIFIED = 3003
ERROR_ALIAS_FOLDER_NOT_IN_WLST = 3004
ERROR_FLATTENED_MBEAN_HAS_ATTRIBUTES = 3005
ERROR_CANNOT_TEST_MBEAN_CD = 3006
ERROR_SINGLE_UNPREDICTABLE = 3007
ERROR_FLATTENED_FOLDER_ERROR = 3008
ERROR_UNABLE_TO_VERIFY_NON_ALIAS_MBEAN_FOLDER = 3009

ERROR_ATTRIBUTE_ALIAS_NOT_FOUND = 4000
ERROR_ATTRIBUTE_ALIAS_NOT_FOUND_IS_READONLY = 4001
ERROR_ATTRIBUTE_INCORRECT_CASE = 4002
ERROR_ATTRIBUTE_INVALID_VERSION = 4003
ERROR_ATTRIBUTE_NOT_READONLY = 4004
ERROR_ATTRIBUTE_NOT_READONLY_VERSION = 4005
ERROR_ATTRIBUTE_READONLY = 4006
ERROR_ATTRIBUTE_PASSWORD_NOT_MARKED = 4007
ERROR_ATTRIBUTE_RESTART = 4008
ERROR_ATTRIBUTE_NOT_RESTART = 4009
ERROR_ATTRIBUTE_LSA_REQUIRED = 4011
ERROR_ATTRIBUTE_CMO_REQUIRED = 4010
ERROR_ATTRIBUTE_GET_REQUIRED = 4012
ERROR_ATTRIBUTE_WRONG_TYPE_FOR_GET = 4013
ERROR_ATTRIBUTE_SET_METHOD_MISSING = 4014
ERROR_ATTRIBUTE_WRONG_TYPE = 4015
ERROR_ATTRIBUTE_REQUIRES_PREFERRED_MODEL_TYPE = 4017
ERROR_ATTRIBUTE_NOT_IN_WLST = 4018
ERROR_ATTRIBUTE_CANNOT_CONVERT_BACK = 4019
ERROR_ATTRIBUTE_CANNOT_SET = 4020
ERROR_ATTRIBUTE_PATH_TOKEN_REQUIRED = 4022
ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE = 4023
ERROR_ATTRIBUTE_MUST_BE_NO_NAME = 4024
ERROR_FLATTENED_MBEAN_ATTRIBUTE_ERROR = 4025
ERROR_DERIVED_DEFAULT_DOES_NOT_MATCH = 4026

MSG_MAP = {
    TESTED_MBEAN_FOLDER:                           'Verified',
    WARN_ALIAS_FOLDER_NOT_IMPLEMENTED:             'Folder not implemented',
    WARN_MBEAN_NOT_NO_NAME_0:                      'MBean can be named other than NO_NAME_0',
    WARN_ATTRIBUTE_DEPRECATED:                     'Attribute is deprecated',
    WARN_ATTRIBUTE_HAS_UNKNOWN_TYPE:               'Unable to determine the WLST attribute type',
    WARN_NO_DERIVED_DEFAULT_IN_GENERATED:          'Generated file contained no derived default information',
    ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER:           'Unable to generate information for MBean',
    ERROR_UNABLE_TO_VERIFY_NON_ALIAS_MBEAN_FOLDER: 'Unable to generate information for non-alias MBean',
    ERROR_ALIAS_FOLDER_NOT_IN_WLST:                'Alias Folder not an mbean',
    ERROR_SINGLE_UNPREDICTABLE:                    'Alias Folder not marked single unpredictable',
    ERROR_FLATTENED_FOLDER_ERROR:                  'Alias Flattened Folder not found',
    ERROR_FLATTENED_MBEAN_HAS_ATTRIBUTES:          'Alias flattened Folder has attributes',
    ERROR_USING_REFERENCE_AS_FOLDER:               'Reference attribute used as folder mbean',
    ERROR_ATTRIBUTE_ALIAS_NOT_FOUND:               'Attribute not found in aliases',
    ERROR_ATTRIBUTE_INCORRECT_CASE:                'Attribute case incorrect',
    ERROR_ATTRIBUTE_ALIAS_NOT_FOUND_IS_READONLY:   'Readonly attribute not found in aliases',
    ERROR_ATTRIBUTE_READONLY:                      'Attribute is marked readwrite',
    ERROR_ATTRIBUTE_NOT_READONLY_VERSION:          'Attribute is marked readonly or is invalid version range',
    ERROR_ATTRIBUTE_NOT_READONLY:                  'Attribute is not marked readwrite',
    ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE:           'Attribute wrong default value',
    ERROR_DERIVED_DEFAULT_DOES_NOT_MATCH:          'Attribute does not match Alias derived_default',
    ERROR_ATTRIBUTE_INVALID_VERSION:               'Attribute invalid version',
    ERROR_ATTRIBUTE_GET_REQUIRED:                  'Attribute requires GET',
    ERROR_ATTRIBUTE_LSA_REQUIRED:                  'Attribute requires LSA',
    ERROR_ATTRIBUTE_CMO_REQUIRED:                  'Attribute requires CMO',
    ERROR_ATTRIBUTE_WRONG_TYPE:                    'Attribute has wrong type',
    ERROR_ATTRIBUTE_WRONG_TYPE_FOR_GET:            'Attribute marked as GET required and has wrong type for GET ',
    ERROR_ATTRIBUTE_SET_METHOD_MISSING:            'Attribute reference type missing set method',
    ERROR_ATTRIBUTE_REQUIRES_PREFERRED_MODEL_TYPE: 'Attribute requires preferred model type of dict',
    ERROR_ATTRIBUTE_CANNOT_CONVERT_BACK:           'Invalid default attribute',
    ERROR_ATTRIBUTE_RESTART:                       'Attribute not marked restart',
    ERROR_ATTRIBUTE_PATH_TOKEN_REQUIRED:           'Directory type requires use_path_tokens',
    ERROR_ATTRIBUTE_NOT_RESTART:                   'Attribute marked restart',
    ERROR_ATTRIBUTE_CANNOT_SET:                    'Cannot SET default value',
    ERROR_ATTRIBUTE_MUST_BE_NO_NAME:               'Attribute name must be set to NO_NAME_0',
    INFO_ATTRIBUTE_IN_IGNORE_LIST:                 'Alias attribute is WLST attribute in the ignore list',
    ERROR_ATTRIBUTE_NOT_IN_WLST:                   'Alias attribute not in MBean',
    ERROR_FAILURE_ATTRIBUTE_LIST:                  'Invalid Alias attribute list',
    ERROR_CANNOT_TEST_MBEAN_UNSPECIFIED:           'Unspecified problem',
    ERROR_CANNOT_TEST_MBEAN_CD:                    'Cannot create MBean',
    ERROR_FAILURE_ATTRIBUTE_UNEXPECTED:            'Unexpected condition for attribute',
    ERROR_ATTRIBUTE_PASSWORD_NOT_MARKED:           'Attribute not marked as password',
    ERROR_FLATTENED_MBEAN_ATTRIBUTE_ERROR:         'Attribute exists for flattened folder in aliases'
}
MSG_ID = 'id'
LOCATION = 'location'
MESSAGE = 'message'
ATTRIBUTE = 'attribute'

_logger = PlatformLogger('test.aliases.verify')
CLASS_NAME = 'Verifier'


class Verifier(object):
    IGNORE_DICT_FOLDERS = []
    IGNORE_ALIAS_FOLDERS = []

    def __init__(self, model_context, generated_dictionary):
        self._generated_dictionary = generated_dictionary
        self._model_context = model_context
        self._alias_helper = AliasHelper(model_context)
        self._results = \
            VerifierResult(verify_utils.get_wlst_mode_as_string(model_context), model_context.get_target_wls_version())

    def verify(self):
        """
        Verify the aliases against the generated dictionary.
        :return: False
        """
        _method_name = 'verify'
        _logger.entering(class_name=CLASS_NAME, method_name=_method_name)

        self._verify_aliases()

        _logger.exiting(result=self._results.get_error_count(), class_name=CLASS_NAME, method_name=_method_name)
        return self._results

    def _verify_aliases(self):
        """
        Walk the tree of the generated dictionary and verify the alias entries.
        """
        _method_name = '_verify_aliases'
        _logger.entering(class_name=CLASS_NAME, method_name=_method_name)

        top_alias_location = LocationContext()
        top_alias_location.add_name_token('DOMAIN', 'system_test_domain')
        top_alias_folder_map = self._alias_helper.get_top_folder_map(top_alias_location)
        top_generated_attributes = \
            verify_utils.filter_generated_attributes(top_alias_location,
                                                     _get_generated_attribute_list(self._generated_dictionary))
        self._verify_attributes_at_location(top_generated_attributes, top_alias_location)
        self._verify_aliases_at_location(self._generated_dictionary, top_alias_location, top_alias_folder_map)

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name)

    def _verify_aliases_at_location(self, generated_dictionary, location, folder_map):
        """
        Verify the sub-folders at the specified location.  Note that this method calls itself recursively
        to traverse the entire subtree.
        :param generated_dictionary: the generated dictionary for this version of WebLogic
        :param location: the Alias Location object that represents the current place in the tree
        :param folder_map: the map of sub-folders
        """
        _method_name = '_verify_aliases_at_location'
        _logger.entering(location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)

        self._check_generated_against_alias_folders(location, generated_dictionary, folder_map)
        for entry in generated_dictionary:
            # a entry is a folder, not in ignore folders list and is implemented
            folder_map_name = entry
            if self._process_this_subfolder(generated_dictionary, entry):
                attributes = _get_generated_attribute_list(generated_dictionary[entry])
                if attributes is None:
                    if RECHECK in generated_dictionary[entry]:
                        message = generated_dictionary[entry][RECHECK]
                        if ADDITIONAL_RECHECK in generated_dictionary[entry]:
                            message += ' : ' + generated_dictionary[entry][ADDITIONAL_RECHECK]
                        self._add_missing_mbean(folder_map_name, location, message=message)
                    else:
                        _logger.fine('The wlst mbean {0} at location {2} is not in the folder map {1}',
                                     entry, folder_map, location.get_folder_path(),
                                     class_name=CLASS_NAME, method_name=_method_name)
                    continue
                elif folder_map_name not in folder_map:
                    next_key = None
                    if len(generated_dictionary[entry]) > 0:
                        key_list = generated_dictionary[entry].keys()
                        if len(key_list) > 0:
                            if key_list[0] == ATTRIBUTES and len(key_list) > 1:
                                next_key = key_list[1]
                            elif key_list[0] != ATTRIBUTES:
                                next_key = key_list[0]
                    if next_key and next_key in folder_map:
                        folder_map_name = next_key
                        _logger.fine('Found the next key {0} of the dictionary in the folder map',
                                     folder_map_name, class_name=CLASS_NAME, method_name=_method_name)
                    else:
                        _logger.fine('The wlst mbean {0} at location {2} is not in the folder map {1}',
                                     entry, folder_map, location.get_folder_path(),
                                     class_name=CLASS_NAME, method_name=_method_name)
                        if DEPRECATED in generated_dictionary[entry] and \
                                generated_dictionary[entry][DEPRECATED] is not None:
                            message = 'MBean deprecated in version ' + generated_dictionary[entry][DEPRECATED]
                        elif SINCE_VERSION in generated_dictionary[entry]:
                            message = 'MBean since version ' + generated_dictionary[entry][SINCE_VERSION]
                        else:
                            message = ''
                        self._add_warning(location, WARN_ALIAS_FOLDER_NOT_IMPLEMENTED, message=message, attribute=entry)
                        continue

                # go_to_mbean = getattr(self, 'go_to_mbean')
                # if go_to_mbean and not go_to_mbean(entry, location):
                #     continue
                location.append_location(folder_map[folder_map_name])
                this_dictionary = generated_dictionary[entry]
                this_folder_map = folder_map[folder_map_name]
                flattened_folder = False
                if self._alias_helper.get_wlst_flattened_folder_info(location) is not None:
                    _logger.finer('MBean {0} is flattened in the aliases at location {1}', entry,
                                  location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)
                    self._check_attribute_list_for_flattened(location, attributes)
                    # Swallow the intermediate layer that is not relevant in a flattened location
                    _logger.finer('MBean {0} now at dictionary {1}', entry, this_dictionary.keys(),
                                  class_name=CLASS_NAME, method_name=_method_name)
                    this_dictionary = self._get_next_entry(this_dictionary)

                    attributes = _get_generated_attribute_list(this_dictionary)
                    flattened_folder = True
                self._check_single_folder(this_dictionary, location, flattened_folder)
                # make this a message
                _logger.finer('Found the generated mbean {0} in the alias folder map', entry,
                              class_name=CLASS_NAME, method_name=_method_name)
                self._alias_helper.add_name_token_to_location(location, this_folder_map)
                self._verify_attributes_at_location(attributes, location)
                subfolder_map = self._alias_helper.get_subfolder_map(location)
                if subfolder_map:
                    self._verify_aliases_at_location(this_dictionary, location, subfolder_map)
                self._clean_up_location(location)

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name)

    def _get_next_entry(self, dictionary):
        keys = dictionary.keys()
        if len(keys) == 3:
            if ATTRIBUTES in keys[0] or INSTANCE_TYPE in keys[0]:
                if ATTRIBUTES in keys[2] or INSTANCE_TYPE in keys[2]:
                    next_entry = dictionary[keys[1]]
                else:
                    next_entry = dictionary[keys[2]]
            else:
                next_entry = dictionary[keys[0]]
        elif len(keys) == 1:
            next_entry = dictionary[keys[0]]
        else:
            return dictionary
        return next_entry

    def _check_generated_against_alias_folders(self, location, generated_dictionary, folder_map):
        """
        Verify the aliases MBeans for the current location for MBeans are in the generated dictionary.
        Add errors for any aliases MBeans that are not found in the generated dictionary.
        Skip the checking for a flattened folder as superficial and will not match the generated aliases.
        :param location: current location in the aliases.
        :param generated_dictionary: generated dictionary for the current location
        :param folder_map: list of aliases folder for the current location
        """
        _method_name = '_check_generated_against_alias_folders'

        flattened_info = self._alias_helper.get_wlst_flattened_folder_info(location)
        if flattened_info is not None:
            _logger.finer('MBean {0} folder is flattened in aliases and does not have a model list of attributes',
                          location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)
            path_token = flattened_info.get_path_token()
            mbean_name = flattened_info.get_mbean_name()
            location.add_name_token(path_token, mbean_name)
        else:
            keys = folder_map.keys()
            lower_case_map = verify_utils.get_lower_case_dict(generated_dictionary.keys())
            _logger.finest('The location {0} contains the following folders {1}', location.get_folder_path(), keys,
                           class_name=CLASS_NAME, method_name=_method_name)
            if keys is not None:
                for alias_name in keys:
                    if verify_utils.is_alias_folder_in_ignore_list(self._model_context, location, alias_name):
                        continue

                    found, mbean_info_name = verify_utils.find_name_in_mbean_with_model_name(alias_name, lower_case_map)
                    if found:
                        _logger.fine('Alias mbean type {0} found in dictionary as {1}', alias_name, mbean_info_name,
                                     class_name=CLASS_NAME, method_name=_method_name)
                        if ONLINE_REFERENCE_ONLY in generated_dictionary[mbean_info_name] and \
                                generated_dictionary[mbean_info_name][ONLINE_REFERENCE_ONLY] == 'true':
                            _logger.fine('Found a reference only {0} for folder {1}', mbean_info_name,
                                         location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)
                            self._add_error(location, ERROR_USING_REFERENCE_AS_FOLDER, attribute=mbean_info_name)
                            # TODO - commenting out deletions
                            del generated_dictionary[mbean_info_name]
                        elif RECHECK in generated_dictionary[mbean_info_name]:
                            message = generated_dictionary[mbean_info_name][RECHECK]
                            if ADDITIONAL_RECHECK in generated_dictionary[mbean_info_name]:
                                message += ' : ' + generated_dictionary[mbean_info_name][ADDITIONAL_RECHECK]
                            self._add_missing_mbean(mbean_info_name, location, message=message)
                            _logger.fine('Remove alias folder {0} as it cannot be verified', alias_name,
                                         class_name=CLASS_NAME, method_name=_method_name)
                            # Removing these results in duplicate errors
                            del folder_map[alias_name]
                            del generated_dictionary[mbean_info_name]
                        elif TYPE in generated_dictionary[mbean_info_name]:
                            self._process_security_provider(generated_dictionary, mbean_info_name, folder_map,
                                                            alias_name, location)

                    elif not self._alias_helper.check_flattened_folder(location, alias_name):
                        # make this a message
                        _logger.fine('The alias folder name {0} at location {1} is not in the generated list {2}',
                                     alias_name, location.get_folder_path(), generated_dictionary.keys(),
                                     class_name=CLASS_NAME, method_name=_method_name)
                        self._add_error(location, ERROR_ALIAS_FOLDER_NOT_IN_WLST, attribute=alias_name)
                    else:
                        _logger.fine('Alias mbean type {0} not found in wlst dictionary {1}',
                                     generated_dictionary.keys(), class_name=CLASS_NAME, method_name=_method_name)
            for item in generated_dictionary:
                if ONLINE_REFERENCE_ONLY in generated_dictionary[item]:
                    # make this a real message
                    _logger.fine('Reference item {0} not implemented as folder at location {1}', item,
                                 location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)
                    # TODO - commenting out deletions
                    del generated_dictionary[item]

    def _verify_attributes_at_location(self, generated_attributes, location):
        """
        Verify the aliases at the current location against the attributes from the generated dictionary.
        :param generated_attributes: generated attribute dictionary
        :param location: current location in aliases
        """
        _method_name = '_verify_attributes_at_location'

        alias_flattened_info = self._alias_helper.get_wlst_flattened_folder_info(location)
        if alias_flattened_info is not None:
            path_token = alias_flattened_info.get_path_token()
            mbean_name = alias_flattened_info.get_mbean_name()
            location.add_name_token(path_token, mbean_name)

        alias_attribute_name_map = self._get_alias_attribute_map_for_location(location)
        _logger.fine('The alias attribute name map at location {0} is {1}', location.get_folder_path(),
                     alias_attribute_name_map, class_name=CLASS_NAME, method_name=_method_name)
        if alias_attribute_name_map is None:
            _logger.fine('Unable to get an alias attribute name map from location {0}', location.get_folder_path(),
                         class_name=CLASS_NAME, method_name=_method_name)
            self._add_error(location, ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER)
            return

        if alias_attribute_name_map or generated_attributes:
            generated_number_of_attributes = 0
            if generated_attributes:
                generated_number_of_attributes = len(generated_attributes)
            get_required_attribute_list = self._get_alias_required_attribute_map(location)
            restart_attribute_list = self._get_alias_restart_required_map(location)
            path_tokens_list = self._get_alias_path_tokens_map(location)
            set_method_list = self._alias_helper.get_model_mbean_set_method_attribute_names_and_types(location).keys()
            _logger.fine('The list of mbeans with set methods at location {0} is {1}', location.get_folder_path(),
                         set_method_list, class_name=CLASS_NAME, method_name=_method_name)

            unprocessed_alias_list = alias_attribute_name_map.keys()
            _logger.finest('Alias attribute list for location {0}: {1}', location.get_folder_path(),
                           unprocessed_alias_list, class_name=CLASS_NAME, method_name=_method_name)

            if generated_attributes:
                for generated_attribute in generated_attributes:
                    if generated_attribute in unprocessed_alias_list:
                        unprocessed_alias_list.remove(generated_attribute)

                    generated_attribute_info = generated_attributes[generated_attribute]
                    _logger.finest('Attribute {0} generated information {1} at location {2}', generated_attribute,
                                   generated_attribute_info, location, class_name=CLASS_NAME, method_name=_method_name)
                    exists, model_attribute_name = \
                        self._check_attribute_exists(location, generated_attribute, generated_attribute_info,
                                                     alias_attribute_name_map, get_required_attribute_list)
                    if exists:
                        alias_type = self._alias_helper.get_model_attribute_type(location, model_attribute_name)
                        attr_default, attr_type = \
                            self._is_valid_attribute_type_and_value(location, generated_attribute,
                                                                    generated_attribute_info, model_attribute_name,
                                                                    get_required_attribute_list)
                        self._is_valid_deprecated(location, generated_attribute, generated_attribute_info)
                        self._is_valid_restart(location, generated_attribute, generated_attribute_info,
                                               model_attribute_name, restart_attribute_list)
                        self._is_valid_uses_path_token(location, generated_attribute, generated_attribute_info,
                                                       attr_default, model_attribute_name, path_tokens_list)
                        self._is_valid_type(location, generated_attribute, attr_type, attr_default,
                                            generated_attribute_info, model_attribute_name,
                                            alias_type, get_required_attribute_list, set_method_list)
                _logger.fine('Unprocessed list for location {0}: {1}', location.get_folder_path(),
                             unprocessed_alias_list, class_name=CLASS_NAME, method_name=_method_name)

            for unprocessed in unprocessed_alias_list:
                if unprocessed in self._alias_helper.get_ignore_attribute_names():
                    self._add_info(location, INFO_ATTRIBUTE_IN_IGNORE_LIST, attribute=unprocessed)
                else:
                    message = ''
                    if verify_utils.is_clear_text_password(unprocessed):
                        message = 'This attribute is a clear text password'
                    self._add_error(location, ERROR_ATTRIBUTE_NOT_IN_WLST, message=message, attribute=unprocessed)
        else:
            generated_number_of_attributes = 0

        self._add_info(location, TESTED_MBEAN_FOLDER, message=str(generated_number_of_attributes) + ' attributes')

    def _get_alias_attribute_map_for_location(self, location):
        wlst_name_map = None
        try:
            alias_attribute_name_list = \
                verify_utils.filter_attributes(location, self._alias_helper.get_model_attribute_names(location))
            wlst_name_map = dict()
            if alias_attribute_name_list:
                for alias_attribute_name in alias_attribute_name_list:
                    wlst_name = self._alias_helper.get_wlst_attribute_name(location, alias_attribute_name,
                                                                           check_read_only=False)
                    if wlst_name:
                        wlst_name_map[wlst_name] = wlst_name.lower()
        except AliasException:
            self._add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST)
        return wlst_name_map

    def _get_alias_required_attribute_map(self, location):
        try:
            get_list = self._alias_helper.get_wlst_get_required_attribute_names(location)
        except AliasException, ae:
            get_list = []
            self._add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST, message=ae.getLocalizedMessage())
        return get_list

    def _get_alias_restart_required_map(self, location):
        try:
            restart_list = self._alias_helper.get_model_restart_required_attribute_names(location)
        except AliasException, ae:
            restart_list = []
            self._add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST, message=ae.getLocalizedMessage())
        return restart_list

    def _get_alias_path_tokens_map(self, location):
        try:
            token_list = self._alias_helper.get_model_uses_path_tokens_attribute_names(location)
        except AliasException, ae:
            token_list = []
            self._add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST, message=ae.getLocalizedMessage())
        return token_list

    def _check_attribute_exists(self, location, generated_attribute, generated_attribute_info,
                                alias_name_map, alias_get_required_attribute_list):
        """
        Verify that the attribute found in the generated list exists in the aliases at the current location.
        :param location: current location in the aliases
        :param generated_attribute: name of the attribute to check in wlst format
        :param generated_attribute_info: information about the attribute from the generated dictionary
        :param alias_name_map: attribute map with model names from the aliases
        :param alias_get_required_attribute_list: list of attributes that require GET
        :return: True if the attribute exists in the aliases: Model name for the attribute
        """
        _method_name = '_check_attribute_exists'
        _logger.entering(location.get_folder_path(), generated_attribute,
                         class_name=CLASS_NAME, method_name=_method_name)

        exists, model_attribute_name, rod = \
            self._does_alias_attribute_exist(location, generated_attribute, generated_attribute_info, alias_name_map)
        if exists:
            if model_attribute_name is None or rod:
                # if the alias attribute is correctly identified as read-only, it's not an error, but we cannot
                # verify any of the other attribute information using aliases methods. And since its read-only
                # we don't really care about any of the attribute information. This is also true for clear
                # text password fields.
                if not rod:
                    exists = False
                # clear text attributes (don't have Encrypted on the end) are not defined in the definitions
                # they are only artificially known and ignored by alias definitions
                read_only = \
                    self._is_generated_attribute_readonly(location, generated_attribute, generated_attribute_info,
                                                          alias_get_required_attribute_list)
                if read_only is not None:
                    if not read_only and not _is_clear_text_password(generated_attribute):
                        if CMO_READ_TYPE in generated_attribute_info and \
                                generated_attribute_info[CMO_READ_TYPE] == READ_ONLY:
                            # if CMO_READ_TYPE is read only, no error...
                            pass
                        else:
                            self._add_error(location, ERROR_ATTRIBUTE_NOT_READONLY_VERSION,
                                            attribute=generated_attribute)
            else:
                if self._is_generated_attribute_readonly(location, generated_attribute, generated_attribute_info,
                                                         alias_get_required_attribute_list):
                    self._add_error(location, ERROR_ATTRIBUTE_READONLY, attribute=generated_attribute)

        _logger.exiting(result=verify_utils.bool_to_string(exists), class_name=CLASS_NAME, method_name=_method_name)
        return exists, model_attribute_name

    def _does_alias_attribute_exist(self, location, generated_attribute, generated_attribute_info, alias_name_map):
        """
        Verify that the generated attribute exists in the aliases. If it is not found in the aliases, attempt
        to determine why it is not found in the aliases.
        :param location: current location in the aliases
        :param generated_attribute: generated attribute name
        :param generated_attribute_info: generated information about the information
        :param alias_name_map: map of wlst attributes from the alias with model names to assist in determining reason
        :return: True if the attribute exists in aliases: aliases attribute model name
        """
        _method_name = '_does_alias_attribute_exist'
        _logger.entering(location.get_folder_path(), generated_attribute,
                         class_name=CLASS_NAME, method_name=_method_name)

        lower_case_list = alias_name_map.values()
        exists = True
        model_attribute = None
        rod = False
        try:
            # no exception is thrown if it is found but read only, just returns empty model_attribute name
            model_attribute = self._alias_helper.get_model_attribute_name(location, generated_attribute)
            # if value returned check to see if access type is ROD. If so change model_attribute to None
            if model_attribute is not None:
                wlst_attributes = self._alias_helper.get_wlst_access_rod_attribute_names(location)
                if wlst_attributes is not None and generated_attribute in wlst_attributes:
                    rod = True
        except AliasException, ae:
            exists = False

            if DEPRECATED not in generated_attribute_info:
                message = None
                if LSA_DEFAULT not in generated_attribute_info:
                    message = 'Attribute is not found in LSA map'
                elif SINCE_VERSION in generated_attribute_info:
                    message = 'Since Version=', generated_attribute_info[SINCE_VERSION]

                if generated_attribute.lower() in lower_case_list:
                    expected_wlst_name = _get_dict_key_from_value(alias_name_map, generated_attribute.lower())
                    message = 'WLST name in aliases is %s' % expected_wlst_name
                    self._add_error(location, ERROR_ATTRIBUTE_INCORRECT_CASE,
                                    message=message, attribute=generated_attribute)
                elif self._is_generated_attribute_readonly(location, generated_attribute, generated_attribute_info):
                    self._add_error(location, ERROR_ATTRIBUTE_ALIAS_NOT_FOUND_IS_READONLY,
                                    attribute=generated_attribute, message=message)
                elif location.get_folder_path().startswith('/SecurityConfiguration/Realm'):
                    # We are not fully implementing Security Providers and only intend to
                    # add attributes as customers need them so make these warnings.
                    #
                    self._add_warning(location, ERROR_ATTRIBUTE_ALIAS_NOT_FOUND,
                                      attribute=generated_attribute, message=message)
                else:
                    self._add_error(location, ERROR_ATTRIBUTE_ALIAS_NOT_FOUND,
                                    attribute=generated_attribute, message=message)
            else:
                _logger.fine('Attribute {0} was not found in aliases but is deprecated. From location {1}',
                             generated_attribute, location.get_folder_path(),
                             class_name=CLASS_NAME, method_name=_method_name)

        _logger.exiting(result=model_attribute, class_name=CLASS_NAME, method_name=_method_name)
        return exists,  model_attribute, rod

    def _is_generated_attribute_readonly(self, location, generated_attribute, generated_attribute_info,
                                         alias_get_required_attribute_list=None):
        """
        Determine whether the generated attribute is defined as readonly.
        :param location: current location in the aliases
        :param generated_attribute: generated attribute name
        :param generated_attribute_info: generated attribute information
        :param alias_get_required_attribute_list: list of attributes that require GET
        :return: True if the generated attribute is defined as readonly
        """
        _method_name = '_is_generated_attribute_readonly'
        _logger.entering(location.get_folder_path(), generated_attribute, str(generated_attribute_info),
                         str(alias_get_required_attribute_list), class_name=CLASS_NAME, method_name=_method_name)

        if READ_TYPE not in generated_attribute_info and CMO_READ_TYPE not in generated_attribute_info:
            self._add_error(location, ERROR_FAILURE_ATTRIBUTE_UNEXPECTED,
                            message='Generated attribute has no read type', attribute=generated_attribute)
            return None
        if alias_get_required_attribute_list is not None and \
                generated_attribute in alias_get_required_attribute_list and CMO_READ_TYPE in generated_attribute_info:
            read_type = generated_attribute_info[CMO_READ_TYPE]
            _logger.finer('Using CMO read type {0} for attribute {1} which is in GET required list',
                          read_type, generated_attribute, class_name=CLASS_NAME, method_name=_method_name)
        elif READ_TYPE in generated_attribute_info:
            read_type = generated_attribute_info[READ_TYPE]
            _logger.finer('Using read type {0} for attribute {1}', read_type, generated_attribute,
                          class_name=CLASS_NAME, method_name=_method_name)
        else:
            read_type = generated_attribute_info[CMO_READ_TYPE]
            _logger.finer('No LSA read type found, using the CMO read type {0} for attribute {1} at location {2}',
                          read_type, generated_attribute, location.get_folder_path(),
                          class_name=CLASS_NAME, method_name=_method_name)

        result = read_type == READ_ONLY

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=result)
        return result

    def _is_valid_attribute_type_and_value(self, location, generated_attribute, generated_attribute_info,
                                           model_attribute_name, alias_get_required_attribute_list):
        """
        Verify that the type and default value for the generated attribute matches the alias information.
        :param location: current location for the aliases
        :param generated_attribute: generated attribute name in wlst format
        :param generated_attribute_info: generated information about the attribute
        :param model_attribute_name: attribute model name from the aliases
        :param alias_get_required_attribute_list: list from the aliases with GET is required for the MBean
        """
        _method_name = '_is_valid_attribute_type_and_value'
        _logger.entering(location.get_folder_path(), generated_attribute, model_attribute_name,
                         class_name=CLASS_NAME, method_name=_method_name)

        valid, generated_attr_default, generated_attr_type = \
            self._is_valid_default_type(location, generated_attribute, generated_attribute_info,
                                        alias_get_required_attribute_list)
        if valid:
            __, model_default_value = \
                self._get_attribute_default_values(generated_attribute, location, model_attribute_name)
            self._is_valid_default_value(location, generated_attribute, generated_attribute_info,
                                         generated_attr_default, model_default_value)

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
        return generated_attr_default, generated_attr_type

    def _is_valid_default_type(self, location, generated_attribute, generated_attribute_info,
                               alias_get_required_attribute_list):
        """
        Verify that the GET or LSA of the generated attribute is correct for the aliases attribute.
        Based on the GET or LSA in aliases, return the matching default value from the generated attribute information.
        :param location: current location in the aliases
        :param generated_attribute: generated name of the attribute
        :param generated_attribute_info: generated information for the attribute
        :param alias_get_required_attribute_list: list from aliases for the MBean of those attributes with GET required
        :return: True if the default type is correct: Default value from the generated attribute information
        """
        _method_name = '_is_valid_default_type'
        _logger.entering(location.get_folder_path(), generated_attribute,
                         class_name=CLASS_NAME, method_name=_method_name)

        # Should we pass in the LSA list from aliases too to check that the lists from aliases are correct?
        attr_default = None
        attr_type = None
        valid = True

        if (LSA_DEFAULT not in generated_attribute_info and GET_DEFAULT not in generated_attribute_info) and \
                CMO_DEFAULT in generated_attribute_info:
            self._add_error(location, ERROR_ATTRIBUTE_CMO_REQUIRED, attribute=generated_attribute)
            valid = False
            attr_default = generated_attribute_info[CMO_DEFAULT]
            attr_type = generated_attribute_info[CMO_TYPE]
        elif GET_DEFAULT in generated_attribute_info and LSA_DEFAULT in generated_attribute_info:
            _logger.finest('WLST LSA and GET are both allowed on attribute {0} at location {1}', generated_attribute,
                           location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)
            if generated_attribute in alias_get_required_attribute_list:
                attr_default = generated_attribute_info[GET_DEFAULT]
                attr_type = generated_attribute_info[GET_TYPE]
            else:
                attr_default = generated_attribute_info[LSA_DEFAULT]
                attr_type = generated_attribute_info[LSA_TYPE]
        elif GET_DEFAULT in generated_attribute_info:
            attr_default = generated_attribute_info[GET_DEFAULT]
            attr_type = generated_attribute_info[GET_TYPE]
            if generated_attribute not in alias_get_required_attribute_list:
                message = 'Attribute is not in LSA map'
                self._add_error(location, ERROR_ATTRIBUTE_GET_REQUIRED, message=message, attribute=generated_attribute)
                valid = False
        elif LSA_DEFAULT in generated_attribute_info:
            attr_default = generated_attribute_info[LSA_DEFAULT]
            attr_type = generated_attribute_info[LSA_TYPE]
            if generated_attribute in alias_get_required_attribute_list:
                message = ''
                if CMO_DEFAULT not in generated_attribute_info:
                    message = 'Attribute is not in the mbean info maps'
                self._add_error(location, ERROR_ATTRIBUTE_LSA_REQUIRED, message=message, attribute=generated_attribute)
                valid = False

        if attr_type == alias_constants.INTEGER and CMO_TYPE in generated_attribute_info and \
                generated_attribute_info[CMO_TYPE] == alias_constants.BOOLEAN:
            attr_type = alias_constants.BOOLEAN

        _logger.exiting(result=verify_utils.bool_to_string(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid, attr_default, attr_type

    def _get_attribute_default_values(self, generated_attribute, location, model_attribute_name):
        """
        Return the model default value for the attribute, and the model value converted into wlst format by aliases.
        Using the default value found for the attribute in the aliases, convert the default value into wlst format
        to check that it can successfully be formatted.
        :param generated_attribute: generated attribute name in wlst format
        :param location: current location in the aliases
        :param model_attribute_name: model name for the generated attribute from the aliases
        :return: True if the model default value is valid in the aliases, model default value, and wlst default value
        """
        _method_name = '_get_attribute_default_values'
        _logger.entering(generated_attribute, location.get_folder_path(), model_attribute_name,
                         class_name=CLASS_NAME, method_name=_method_name)

        model_default_value = None
        valid = True
        try:
            model_default_value = self._alias_helper.get_model_attribute_default_value(location, model_attribute_name)
        except AliasException, ae:
            self._add_error(location, ERROR_FAILURE_ATTRIBUTE_UNEXPECTED, message=ae.getLocalizedMessage(),
                            attribute=generated_attribute)
            valid = False

        wlst_default_value = None
        if valid:
            try:
                wlst_attr = \
                    self._alias_helper.get_wlst_attribute_name(location, model_attribute_name)
            except AliasException, ae:
                self._add_error(location, ERROR_FAILURE_ATTRIBUTE_UNEXPECTED, message=ae.getLocalizedMessage(),
                                attribute=generated_attribute)
                valid = False

        _logger.exiting(result=verify_utils.bool_to_string(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid, model_default_value

    def _is_valid_default_value(self, location, generated_attribute, generated_attribute_info,
                                generated_default_value, model_default_value):
        """
        Verify that the default value for the generated attribute matches the default value for the attribute
        in the aliases.
        :param location: current location in the aliases
        :param generated_attribute: generated attribute name
        :param generated_attribute_info: generated structure with WLST information about the attribute
        :param generated_default_value: generated attribute default value
        :param model_default_value: default value from the aliases
        :return: True if default value is correct: aliases model name for the attribute: aliases model default value
        """
        _method_name = '_is_valid_default_value'
        _logger.entering(location.get_folder_path(), generated_attribute, generated_default_value,
                         class_name=CLASS_NAME, method_name=_method_name)

        generated_default = _adjust_default_value_for_special_cases(generated_attribute, generated_attribute_info,
                                                                    generated_default_value)
        match = True
        model_name = None
        model_value = None
        is_derived_default = False
        if generated_default is not None:
            try:
                _logger.finest('getting model name and value with generated_default ({0}) of "{1}"',
                               type(generated_default), generated_default,
                               class_name=CLASS_NAME, method_name=_method_name)

                # This code is sort of non-intuitive because the method was written for a different
                # purpose.  This get_model_attribute_name_and_value() function compared the value
                # we pass in with the alias default (accounting for type conversion).  If the value
                # passed in matches the alias default value, it returns None for model_value.
                # Otherwise, it returns the passed in value converted to the alias type, if necessary.
                #
                model_name, model_value = \
                    self._alias_helper.get_model_attribute_name_and_value(location, generated_attribute,
                                                                          generated_default)

                _logger.finest('aliases returned model_name {0} and model_value ({1}) of "{2}"', model_name,
                               type(model_value), model_value, class_name=CLASS_NAME, method_name=_method_name)

                is_derived_default = self._alias_helper.is_derived_default(location, model_name)
                if DERIVED_DEFAULT in generated_attribute_info:
                    generated_derived = generated_attribute_info[DERIVED_DEFAULT]
                    if isinstance(generated_derived, long):
                        generated_derived = bool(generated_derived)
                    elif not isinstance(generated_derived, bool):
                        val = str(generated_derived)
                        generated_derived = val.lower() == 'true'
                else:
                    # The generator was unable to find the information about the derived default
                    # so just assume that the alias is correct.
                    #
                    generated_derived = is_derived_default
                    if self._model_context.get_target_wlst_mode() == WlstModes.ONLINE:
                        _logger.finest('No information about derived_default in the generated file',
                                       class_name=CLASS_NAME, method_name=_method_name)
                        message = 'Alias %s' % str(is_derived_default)
                        self._add_warning(location, WARN_NO_DERIVED_DEFAULT_IN_GENERATED,
                                          message=message, attribute=generated_attribute)

                if is_derived_default != generated_derived:
                    _logger.finest('derived default value mismatch', class_name=CLASS_NAME, method_name=_method_name)
                    message = 'WLST: %s  :  Alias: %s' % (str(generated_derived), str(is_derived_default))
                    self._add_error(location, ERROR_DERIVED_DEFAULT_DOES_NOT_MATCH,
                                    message=message, attribute=generated_attribute)
                    match = False

                if match and model_value is not None and not is_derived_default:
                    # the alias code is not treating the strings or lists of strings as equal so test them here...
                    if isinstance(generated_default, basestring) and isinstance(model_value, basestring):
                        if str(generated_default) == str(model_value):
                            model_value = None
                    if model_value is not None:
                        wlst_read_type = self._alias_helper.get_wlst_read_type(location, model_name)
                        model_value = verify_utils.check_list_of_strings_equal(model_name, model_value,
                                                                               generated_default, wlst_read_type)

            except TypeError, te:
                self._add_error(location, ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE,
                                message=te, attribute=generated_attribute)
                match = False
            except (AliasException, IOException), ae:
                self._add_error(location, ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE, message=ae.getLocalizedMessage(),
                                attribute=generated_attribute)
                match = False
        else:
            model_value = model_default_value

        # This if statement will be true if the default values do not match and the alias attribute
        # is not marked as a derived_default.
        #
        if match and model_value is not None and not is_derived_default:
            if not verify_utils.is_attribute_value_test_anomaly(self._model_context, location, model_name, model_value):
                attr_type = type(generated_default)
                if CMO_TYPE in generated_attribute_info and \
                        (generated_attribute_info[CMO_TYPE] == alias_constants.BOOLEAN or
                         generated_attribute_info[CMO_TYPE] == alias_constants.JAVA_LANG_BOOLEAN) and \
                        generated_default is not None and (attr_type in [str, unicode, int]):
                    generated_default = Boolean(generated_default)
                message = 'WLST: %s / Alias: %s' % (str(generated_default), str(model_default_value))
                self._add_error(location, ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE,
                                message=message, attribute=generated_attribute)
                match = False

        _logger.exiting(result=verify_utils.bool_to_string(match), class_name=CLASS_NAME, method_name=_method_name)
        return match, model_name, model_value

    def _is_valid_deprecated(self, location, generated_attribute, generated_attribute_info):
        """
        Check to see if the attribute found in the Aliases is actually deprecated.
        :param location: current location in the aliases
        :param generated_attribute: generated attribute name
        :param generated_attribute_info: generated attribute information
        :return: True if the generated attribute is defined as readonly
        """
        if DEPRECATED in generated_attribute_info:
            self._add_warning(location, WARN_ATTRIBUTE_DEPRECATED, message=generated_attribute_info[DEPRECATED],
                              attribute=generated_attribute)
            return False
        return True

    def _is_valid_restart(self, location, generated_attribute, generated_attribute_info,
                          model_attribute_name, restart_required_list):
        """
        Verify that the generated attribute requires restart type matches the aliases attribute information.
        :param location: current location in the aliases
        :param generated_attribute: generated attribute name
        :param generated_attribute_info: generated information about the attribute
        :param model_attribute_name: model name for the attribute from the aliases
        :param restart_required_list: aliases list for the MBean of attributes requiring restart
        :return: True if restart type is correct
        """
        _method_name = '_is_valid_restart'
        _logger.entering(location.get_folder_path(), generated_attribute, model_attribute_name,
                         class_name=CLASS_NAME, method_name=_method_name)

        valid = True
        if model_attribute_name in restart_required_list:
            if RESTART not in generated_attribute_info or \
                    (generated_attribute_info[RESTART] != RESTART_NO_CHECK and
                     generated_attribute_info[RESTART] != 'true'):
                # TODO - temporary change to warning until we decide what to do about the restart attributes of the aliases.
                self._add_warning(location, ERROR_ATTRIBUTE_NOT_RESTART, attribute=model_attribute_name)
                valid = False
        elif RESTART in generated_attribute_info and generated_attribute_info[RESTART] == 'true':
            # TODO - temporary change to warning until we decide what to do about the restart attributes of the aliases.
            self._add_warning(location, ERROR_ATTRIBUTE_RESTART, attribute=generated_attribute)
            valid = False

        _logger.exiting(result=verify_utils.bool_to_string(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def _is_valid_uses_path_token(self, location, generated_attribute, generated_attribute_info,
                                  generated_default_value, model_name, path_tokens_map):
        """
        If the name indicates the attribute is a path type check to see if use_path_tokens is in the alias definition.

        :param location:  current location context
        :param generated_attribute: name of attribute from generated file
        :param generated_attribute_info: attribute information from generated file
        :param generated_default_value: default value for the attribute
        :param model_name: model name for the generated attribute
        :param path_tokens_map: aliases in the mbean that have path tokens
        :return: True if the generated attribute indicates it needs a path token
        """
        _method_name = '_is_valid_uses_path_token'
        _logger.entering(location.get_folder_path(), generated_attribute, model_name, path_tokens_map,
                         class_name=CLASS_NAME, method_name=_method_name)

        valid = True
        if model_name not in path_tokens_map and \
                _is_any_string_type(generated_attribute_info) and \
                _is_file_location_type(generated_attribute):
            self._add_error(location, ERROR_ATTRIBUTE_PATH_TOKEN_REQUIRED, attribute=model_name,
                            message=generated_default_value)
            valid = False

        _logger.exiting(result=verify_utils.bool_to_string(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def _is_valid_type(self, location, generated_attribute, generated_attr_type, generated_attr_value,
                       generated_attribute_info, model_name, alias_type, get_required_attribute_list, set_method_list):
        """
        Verify that the type for the generated attribute matches the type for the attribute in the aliases.
        :param location: current location in the aliases
        :param generated_attribute: generated attribute name
        :param generated_attr_type: the attribute type specific to what value is being used
        :param generated_attr_value: the attribute value to assist in checking the attribute type
        :param generated_attribute_info: generated information about the attribute
        :param model_name: model attribute name from aliases
        :param alias_type: alias wlst type for the model attribute
        :param get_required_attribute_list: aliases list for the MBean of attributes requiring GET
        :param set_method_list: aliases list for the MBean of attributes with special set methods
        :return: True if the attribute type is correct
        """
        _method_name = '_is_valid_type'
        _logger.entering(location.get_folder_path(), generated_attribute, model_name, class_name=CLASS_NAME,
                         method_name=_method_name)

        valid = False
        message = None
        if alias_type is not None and generated_attr_type is not None:
            if alias_type in alias_constants.ALIAS_BOOLEAN_TYPES and \
                    _check_boolean_type(generated_attribute, generated_attribute_info, get_required_attribute_list):
                valid = True
                _logger.fine('Test attribute {0} type {1} with value {2} for valid conversion to alias type {3} ',
                             generated_attribute, generated_attr_type, generated_attr_value, alias_type,
                             class_name=CLASS_NAME, method_name=_method_name)
            elif self._validate_primitive_type(location, generated_attribute, generated_attribute_info,
                                               generated_attr_type, generated_attr_value, alias_type,
                                               get_required_attribute_list):
                _logger.finer('Attribute [0} with alias type {0} passed special primitive test', model_name, alias_type,
                              class_name=CLASS_NAME, method_name=_method_name)
                valid = True
            elif alias_type == alias_constants.PROPERTIES and \
                    self._is_valid_alias_property_type(location, generated_attribute, generated_attribute_info,
                                                       alias_type, model_name, get_required_attribute_list):
                valid = True
            elif alias_type in alias_constants.ALIAS_LIST_TYPES and \
                    self._check_complex_type(location, generated_attribute, generated_attribute_info, alias_type,
                                             model_name, get_required_attribute_list):
                _logger.finer('Attribute {0} attribute type {1} is valid for alias type {2}',
                              model_name, generated_attr_type, alias_type,
                              class_name=CLASS_NAME, method_name=_method_name)
                valid = True
            elif alias_type == alias_constants.STRING and _is_object_type(generated_attribute_info):
                valid = True
                if self._model_context.is_wlst_online() and model_name not in set_method_list:
                    _logger.fine('Attribute {0} is an object but is not in the set method list {1}',
                                 generated_attribute, set_method_list, class_name=CLASS_NAME, method_name=_method_name)
                    self._add_error(location, ERROR_ATTRIBUTE_SET_METHOD_MISSING, attribute=generated_attribute)
            else:
                valid, generated_attr_type, message = \
                    _check_for_allowed_unknowns(location, generated_attribute, generated_attr_type, alias_type,
                                                generated_attribute_info, get_required_attribute_list, valid)
        if not valid:
            _logger.fine('No solution for attribute {0} with type {1} and full attribute info {2}', generated_attribute,
                         generated_attr_type, generated_attribute_info, class_name=CLASS_NAME, method_name=_method_name)
            self._add_invalid_type_error(location, generated_attribute, generated_attr_type, alias_type,
                                         get_required_attribute_list, message)

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=verify_utils.bool_to_string(valid))
        return valid

    def _process_security_provider(self, generated_dictionary, mbean_name, alias_map, alias_name, location):
        # TODO - commenting out deletions
        # del generated_dictionary[mbean_name][TYPE]
        l2 = LocationContext(location)
        model_name = self._alias_helper.get_model_subfolder_name(l2, alias_name)
        l2.append_location(model_name)
        alias_subfolders = self._alias_helper.get_model_subfolder_names(l2)

        name_token = self._alias_helper.get_name_token(l2)
        for provider in generated_dictionary[mbean_name].keys():
            l2.add_name_token(name_token, provider)
            model_provider = provider
            if '.' in provider:
                model_provider = provider[provider.rfind('.') + 1:]
            if model_provider is None or model_provider not in alias_subfolders:
                self._add_warning(location, WARN_ALIAS_FOLDER_NOT_IMPLEMENTED, attribute=provider)
                continue

            l2.append_location(model_provider)
            next_dict = generated_dictionary[mbean_name][provider]
            attributes = _get_generated_attribute_list(next_dict)
            if attributes is None or len(attributes) == 0:
                continue
            self._verify_attributes_at_location(attributes, l2)
            l2.pop_location()

    def _process_this_subfolder(self, dictionary, entry):
        if not isinstance(dictionary, dict) or entry not in dictionary:
            return False
        return entry not in getattr(self, 'IGNORE_DICT_FOLDERS') and isinstance(dictionary[entry], dict)

    def _check_attribute_list_for_flattened(self, location, attributes):
        """
        Check the generated attribute list for an MBean that is flattened in the model. If there are
        attributes, the MBean should not be flattened and the attributes are reported as not in aliases.
        :param location: location for the current flattened folder
        :param attributes: generated dictionary to check for attributes
        """
        if len(attributes) > 0:
            self._add_error(location, ERROR_FLATTENED_MBEAN_HAS_ATTRIBUTES)
            for attribute in attributes:
                message = 'Flattened location %s has attribute %s' % (location.get_folder_path(), attribute)
                self._add_error(location, ERROR_FLATTENED_MBEAN_ATTRIBUTE_ERROR, message=message, attribute=attribute)

    def _check_single_folder(self, dictionary, location, is_flattened_folder):
        """
        Check to see if the instance type matches, that a single folder is defined as a single folder and
        that the naming of the folder matches what can be named (i.e. NO_NAME_0 versus token name)
        Flattened folders are single by default, but are not marked in the alias definition.
        :param dictionary: generated dictionary of current mbean
        :param is_flattened_folder: if current mbean is a flattened and single folder
        :param location: current location context of mbean
        """
        _method_name = '_check_single_folder'
        _logger.entering(location.get_folder_path(), is_flattened_folder,
                         class_name=CLASS_NAME, method_name=_method_name)

        if INSTANCE_TYPE in dictionary:
            instance_type = dictionary[INSTANCE_TYPE]
            is_multiple = self._alias_helper.supports_multiple_mbean_instances(location)
            if is_flattened_folder:
                is_multiple = False
                token_name = self._alias_helper.get_name_token(location)
                location.add_name_token(token_name, 'foo')
            if is_multiple:
                if instance_type != MULTIPLE:
                    self._add_error(location, ERROR_SINGLE_UNPREDICTABLE)
            else:
                try:
                    _logger.finer('Calling get_wlst_mbean_name() on location {0}', location.get_folder_path(),
                                  class_name=CLASS_NAME, method_name=_method_name)
                    token_name = self._alias_helper.get_name_token(location)
                    location.add_name_token(token_name, 'foo')
                    token_name = self._alias_helper.get_wlst_mbean_name(location)
                except AliasException, e:
                    if is_flattened_folder:
                        self._add_error(location, ERROR_FLATTENED_FOLDER_ERROR, message=str(e))
                    else:
                        self._add_error(location, ERROR_ATTRIBUTE_INVALID_VERSION)
                    return

                if instance_type == SINGLE_NO_NAME:
                    if token_name != 'NO_NAME_0':
                        self._add_error(location, ERROR_ATTRIBUTE_MUST_BE_NO_NAME)
                else:
                    if token_name == 'NO_NAME_0':
                        self._add_warning(location, WARN_MBEAN_NOT_NO_NAME_0)

    def _add_invalid_type_error(self, location, generated_attribute, wlst_type, alias_type, get_required_attribute_list,
                                extra_blurb=''):
        _method_name = '_add_invalid_type_error'

        if extra_blurb is None:
            extra_blurb = ''
        if wlst_type == UNKNOWN:
            _logger.fine('Change caller to pass an attribute type other than unknown for attribute {0}',
                         generated_attribute, class_name=CLASS_NAME, method_name=_method_name)
        if len(extra_blurb) == 0 and generated_attribute in get_required_attribute_list:
            extra_blurb = 'Alias has GET required'
        message = 'WLST type: %s / Alias type: %s  (%s)' % (wlst_type, alias_type, extra_blurb)
        self._add_error(location, ERROR_ATTRIBUTE_WRONG_TYPE, message=message, attribute=generated_attribute)

    def _validate_primitive_type(self, location, generated_attribute, generated_attribute_info,
                                 generated_attribute_type, wlst_attribute_value, alias_type,
                                 get_required_attribute_list):
        """
        The attribute type is not the exact match to the alias type. Check to see if the attribute type is one
        whose value can be converted to a model value.There are only a small set of the primitives for which this
        makes sense.
        :param location: current location in the aliases
        :param generated_attribute: attribute from the attribute_info
        :param generated_attribute_info: Full information from the attribute_info
        :param generated_attribute_type: type of the attribute value
        :param wlst_attribute_value: value that will be converted to a model value
        :param alias_type: type of the attribute in the aliases
        :param get_required_attribute_list: list of the alias attributes with GET required
        :return:
        """
        _method_name = '_validate_primitive_type'
        _logger.entering(generated_attribute, generated_attribute_type, wlst_attribute_value, alias_type,
                         class_name=CLASS_NAME, method_name=_method_name)
        valid = False
        if alias_type in alias_constants.ALIAS_PRIMITIVE_DATA_TYPES:
            if alias_type == generated_attribute_type:
                valid = True
            elif (alias_type == alias_constants.STRING or alias_type == alias_constants.PASSWORD) and \
                    _is_of_type(generated_attribute, alias_type, generated_attribute_info, get_required_attribute_list):
                # simple primitive test
                valid = True
            elif alias_type == alias_constants.CREDENTIAL and \
                    _is_of_type(generated_attribute, alias_constants.STRING, generated_attribute_info,
                                get_required_attribute_list):
                valid = True
            elif alias_type == alias_constants.LONG and generated_attribute_type == alias_constants.INTEGER and \
                    generated_attribute not in get_required_attribute_list:
                valid = True
            elif alias_type in NUMBER_TYPES and \
                    _is_in_types(generated_attribute, NUMBER_TYPES, generated_attribute_info,
                                 get_required_attribute_list):
                _logger.fine('Test attribute {0} type {1} with value {2} for valid conversion to alias type {3} ',
                             generated_attribute, generated_attribute_type, wlst_attribute_value, alias_type,
                             class_name=CLASS_NAME, method_name=_method_name)
                valid = True
        _logger.exiting(result=Boolean(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def _check_complex_type(self, location, generated_attribute, generated_attr_info, alias_type, model_name,
                            get_required_attribute_list):
        """
        Check to see if the attribute type is consistent with an alias delimited type
        Check the delimited alias type to determine if it is a list of properties (dictionary) instead of straight
        string list.
        :param location: current location in the aliases
        :param generated_attribute: attribute name
        :param generated_attr_info: data structure containing the attribute information
        :param alias_type: the complex alias type for the check
        :param model_name: of the attribute to locate the alias attribute definition
        :param get_required_attribute_list: list of attributes that require GET for the MBean
        :return: True if the delimited type contains properties
        """
        _method_name = '_check_complex_type'
        _logger.entering(location.get_folder_path(), generated_attribute, alias_type, model_name,
                         class_name=CLASS_NAME, method_name=_method_name)

        valid = False
        lsa_type, get_type, cmo_type = _get_attribute_types(generated_attr_info)
        if _logger.is_finest_enabled():
            wlst_read_type = self._alias_helper.get_wlst_read_type(location, model_name)
            _logger.finest('Location {0} Attribute {1} with alias_type {2}: lsa_type={3} cmo_type={4}'
                           ' get_type={5} wlst_read_type={6}, get_required={7}',
                           location.get_folder_path(), generated_attribute, alias_type, lsa_type, cmo_type, get_type,
                           wlst_read_type, Boolean(generated_attribute in get_required_attribute_list),
                           class_name=CLASS_NAME, method_name=_method_name)

        if alias_type == alias_constants.SEMI_COLON_DELIMITED_STRING and \
                _is_of_type_with_lsa(generated_attribute, alias_constants.PROPERTIES, generated_attr_info,
                                     get_required_attribute_list):
            valid = True
            if self._alias_helper.get_preferred_model_type(location, model_name) != alias_constants.DICTIONARY:
                self._add_invalid_type_error(location, generated_attribute, alias_constants.PROPERTIES, alias_type,
                                             'Attribute requires preferred model type')
        elif alias_type == alias_constants.JARRAY:
            if _is_of_type_with_get_required(generated_attribute, alias_type, generated_attr_info,
                                             get_required_attribute_list):
                valid = True
                _logger.finer('alias type JARRAY has get_required for attribute {0}', generated_attribute,
                              class_name=CLASS_NAME, method_name=_method_name)
            elif _is_of_type_with_lsa(generated_attribute, alias_type, generated_attr_info,
                                      get_required_attribute_list):
                valid = True
                _logger.finer('alias type JARRAY is in lsa type for attribute {0}', generated_attribute,
                              class_name=CLASS_NAME, method_name=_method_name)
                if self._alias_helper.get_wlst_read_type(location, model_name) not in \
                        alias_constants.ALIAS_DELIMITED_TYPES:
                    self._add_invalid_type_error(location, generated_attribute, alias_constants.STRING, alias_type,
                                                 get_required_attribute_list, 'GET or WLST_READ_TYPE required')
            elif _is_wlst_read_type_compatible_list_type(generated_attribute, lsa_type,
                                                         self._alias_helper.get_wlst_read_type(location, model_name)):
                valid = True
        elif alias_type == alias_constants.LIST:
            if _is_of_type_with_get_required(generated_attribute, alias_type, generated_attr_info,
                                             get_required_attribute_list):
                valid = True
            elif _is_of_type_with_lsa(generated_attribute, alias_type, generated_attr_info,
                                      get_required_attribute_list):
                valid = True
                if self._alias_helper.get_wlst_read_type(location, model_name) not in \
                        alias_constants.ALIAS_DELIMITED_TYPES:
                    self._add_invalid_type_error(location, generated_attribute, alias_constants.STRING, alias_type,
                                                 get_required_attribute_list, 'LSA GET_METHOD requires WLST_READ_TYPE')
            elif _is_wlst_read_type_compatible_list_type(generated_attribute, lsa_type,
                                                         self._alias_helper.get_wlst_read_type(location, model_name)):
                valid = True
        elif alias_type in alias_constants.ALIAS_DELIMITED_TYPES:
            if _is_any_string_type(generated_attr_info):
                valid = True
                if _is_in_types_with_get_required(generated_attribute, CONVERT_TO_DELIMITED_TYPES,
                                                  generated_attr_info, get_required_attribute_list) and \
                        self._alias_helper.get_wlst_read_type(location, model_name) not in CONVERT_TO_DELIMITED_TYPES:
                    self._add_invalid_type_error(location, generated_attribute, alias_constants.STRING, alias_type,
                                                 get_required_attribute_list, 'GET needs valid WLST_READ_TYPE')
                else:
                    _logger.finer('Attribute {0} type {1} is valid for delimited string',
                                  generated_attribute, lsa_type, class_name=CLASS_NAME, method_name=_method_name)

        _logger.exiting(result=Boolean(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def _is_valid_alias_property_type(self, location, attribute, attr_info, alias_type, model_name,
                                      get_required_attribute_list):
        """
        Determine if the WLST type can be converted into a dictionary type.
        :param location: Context for current location
        :param attribute: Attribute name
        :param attr_info: Information gathered about the attribute
        :param alias_type: Attribute type in the alias definition
        :param model_name: Model name in the alias definition used to test the get required list
        :param get_required_attribute_list: List of attributes for the MBean that require a WLST list
        :return: True if the type is a type that can be converted to a dictionary
        """
        _method_name = '_is_valid_alias_property_type'
        _logger.entering(location.get_folder_path(), attribute, alias_type, model_name,
                         class_name=CLASS_NAME, method_name=_method_name)

        lsa_type, get_type, cmo_type = _get_attribute_types(attr_info)
        if attribute in get_required_attribute_list:
            _logger.finest('Attribute {0} in get_required_attribute_list', attribute,
                           class_name=CLASS_NAME, method_name=_method_name)
            valid = True
            attr_type = _is_attribute_type_for_get_required(get_type, cmo_type)
            if attr_type != alias_constants.PROPERTIES:
                self._add_invalid_type_error(location, attribute, attr_type, alias_type,
                                             'Alias has GET with wrong type')
        elif _is_any_string_type(attr_info) and self._alias_helper.get_wlst_read_type(location, model_name) == \
                alias_constants.SEMI_COLON_DELIMITED_STRING:
            _logger.finest('Attribute {0} is string type and WLST read type is a delimited string type', attribute,
                           class_name=CLASS_NAME, method_name=_method_name)
            valid = True
        else:
            _logger.finest('Attribute {0} is lsa_type {1}, get_type {2}, and cmo_type {3}', attribute, lsa_type,
                           get_type, cmo_type, class_name=CLASS_NAME, method_name=_method_name)
            valid = True
            attr_type = _is_attribute_type_for_lsa_required(attr_info)
            message = 'Attribute requires WLST_READ_TYPE of ' + alias_constants.SEMI_COLON_DELIMITED_STRING
            self._add_invalid_type_error(
                location, attribute, attr_type, alias_type, get_required_attribute_list, message)

        if valid and \
                self._alias_helper.get_preferred_model_type(location, model_name) != alias_constants.DICTIONARY:
            self._add_error(location, ERROR_ATTRIBUTE_REQUIRES_PREFERRED_MODEL_TYPE, attribute=attribute)

        return valid

    def _clean_up_location(self, location):
        name_token = self._alias_helper.get_name_token(location)
        if name_token:
            location.remove_name_token(name_token)
        location.pop_location()

    def _add_error(self, location, msg_id, message=None, attribute=None):
        """
        Add the error message to the warning dictionary.
        :param location: Context of the current location
        :param msg_id: id of the message in the message ID list which will return the message text
        :param message: Additional information to add the message
        :param attribute: Attribute name
        """
        self._results.add_error(location, msg_id, message, attribute)

    def _add_warning(self, location, msg_id, message=None, attribute=None):
        """
        Add the warning message to the warning dictionary.
        :param location: Context of the current location
        :param msg_id: id of the message in the message ID list which will return the message text
        :param message: Additional information to add the message
        :param attribute: Attribute name
        """
        self._results.add_warning(location, msg_id, message, attribute)

    def _add_info(self, location, msg_id, message=None, attribute=None):
        """
        Add the informational message to the info dictionary.
        :param location: Context of the current location
        :param msg_id: id of the message in the message ID list which will return the message text
        :param message: Additional information to add the message
        :param attribute: Attribute name
        """
        self._results.add_info(location, msg_id, message, attribute)

    def _add_missing_mbean(self, mbean_name, location, message=None):
        """
        Add a message identifying a missing MBean to the error result, or to the info result
        if there is no corresponding alias folder.
        :param mbean_name: the WLST name of the MBean to be checked
        :param location: context of the current location
        :param message: additional information to add the message
        """
        model_name = self._alias_helper.get_model_subfolder_name(location, mbean_name)
        if model_name:
            self._add_error(location, ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER, attribute=mbean_name, message=message)
        else:
            self._add_info(location, ERROR_UNABLE_TO_VERIFY_NON_ALIAS_MBEAN_FOLDER, attribute=mbean_name,
                           message=message)


def _get_generated_attribute_list(dictionary):
    """
    Return the attributes for the MBean from the generated file dictionary.
    :param dictionary: Contains the attribute information gathered from WLST
    :return: A list of the attribute names for the MBean
    """
    attributes = None
    if ATTRIBUTES in dictionary:
        attributes = dictionary[ATTRIBUTES]
        # TODO - commenting out deletions
        # del dictionary[ATTRIBUTES]
    return attributes


def _is_clear_text_password(attribute_name):
    """
    Any encrypted field that follows the pattern of containing a clear text representation of the encrypted value
    is not added to the generated dictionary.
    :param attribute_name: Name of the attribute to check. Each encrypted attribute that takes an encrypted value has
        Encrypted on the end of its name.
    :return: True if the name indicates that the encrypted attribute contains a clear text representation
    """
    # clear text password attributes are not in the alias definition and are skipped on discover or set
    # clear text do not have Encrypted on the end
    return ('Credential' in attribute_name or 'Pass' in attribute_name or 'Encrypted' in attribute_name) and \
           not attribute_name.endswith('Encrypted')


def _adjust_default_value_for_special_cases(attribute, attr_type, attr_default):
    if attr_default is not None and attr_type == 'string' and _is_file_location_type(attribute):
        return attr_default.replace('\\', '/')
    return attr_default


PATH_INCLUDES_TOKENS = ['Path', 'Dir']
PATH_EXCLUDES_TOKENS = ['ClassPath']
PATH_EXCLUDE_ATTRIBUTE_NAMES = ['Direction', 'ErrorPath', 'UriPath']


def _is_file_location_type(attribute):
    _method_name = '_is_file_location_type'
    _logger.entering(attribute, class_name=CLASS_NAME, method_name=_method_name)

    result = False
    for include_token in PATH_INCLUDES_TOKENS:
        if include_token in attribute:
            result = True
            break

    if result:
        for exclude_token in PATH_EXCLUDES_TOKENS:
            if exclude_token in attribute:
                result = False
                break

    if result and attribute in PATH_EXCLUDE_ATTRIBUTE_NAMES:
        result = False

    _logger.exiting(result=result, class_name=CLASS_NAME, method_name=_method_name)
    return result


def _get_attribute_types(attribute_info):
    lsa_type = None
    get_type = None
    cmo_type = None
    if LSA_TYPE in attribute_info:
        lsa_type = attribute_info[LSA_TYPE]
    if GET_TYPE in attribute_info:
        get_type = attribute_info[GET_TYPE]
    if CMO_TYPE in attribute_info:
        cmo_type = attribute_info[CMO_TYPE]
    return lsa_type, get_type, cmo_type


def _is_of_type_with_get_required(attribute, alias_type, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return attribute in get_required_attribute_list and (get_type == alias_type or cmo_type == alias_type)


def _is_of_type_with_lsa(attribute, alias_type, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)

    is_lsa_type = attribute not in get_required_attribute_list and lsa_type is not None
    is_lsa_and_alias_types_equal = lsa_type == alias_type
    is_lsa_type_unknown = _is_type_an_unknown_type(lsa_type)
    is_lsa_type_string_or_integer = lsa_type == alias_constants.STRING or lsa_type == alias_constants.INTEGER
    is_lsa_type_unknown_or_string_or_integer = is_lsa_type_unknown or is_lsa_type_string_or_integer
    is_lsa_type_unknown_and_cmo_type_is_none = _is_type_an_unknown_type(get_type) and cmo_type is None
    is_get_and_alias_types_equal = get_type == alias_type
    is_cmo_and_alias_types_equal = cmo_type == alias_type
    is_cmo_or_get_and_alias_types_equal = is_get_and_alias_types_equal or is_cmo_and_alias_types_equal
    is_alias_type_list_type = alias_type in LIST_TYPES

    return is_lsa_type and \
           (is_lsa_and_alias_types_equal or
            (is_lsa_type_unknown_or_string_or_integer and
             (is_lsa_type_unknown_and_cmo_type_is_none or is_cmo_or_get_and_alias_types_equal or is_alias_type_list_type)))


def _is_wlst_read_type_compatible_list_type(attribute, lsa_type, wlst_read_type):
    _method_name = '_is_wlst_read_type_compatible_list_type'
    _logger.entering(attribute, lsa_type, wlst_read_type, class_name=CLASS_NAME, method_name=_method_name)

    result = False
    if wlst_read_type is not None and lsa_type is not None:
        # if the lsa_type is 'string' and the wlst_read_type is 'delimited_string[*]', the types are a match
        result = wlst_read_type in alias_constants.ALIAS_DELIMITED_TYPES and lsa_type in wlst_read_type

    _logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=result)
    return result


def _is_in_types_with_get_required(attribute, alias_types, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return attribute in get_required_attribute_list and (get_type in alias_types or cmo_type in alias_types)


def _check_for_allowed_unknowns(location, generated_attribute, wlst_type, alias_type, generated_attr_info,
                                get_required_attribute_list, valid):
    _method_name = '_check_for_allowed_unknowns'
    _logger.entering(generated_attribute, wlst_type, alias_type, Boolean(valid),
                     class_name=CLASS_NAME, method_name=_method_name)

    local_valid = valid
    message_type = wlst_type
    message = None
    lsa_type, get_type, cmo_type = _get_attribute_types(generated_attr_info)
    if _is_unknown_type(generated_attribute, alias_type, generated_attr_info, get_required_attribute_list):
        local_valid = True
    elif _is_of_type_with_get_required(generated_attribute, alias_type, generated_attr_info,
                                       get_required_attribute_list):
        _logger.info('Need to improve the test for get required attribute {0} with GET type UNKNOWN and '
                     'CMO type {3} and alias type {1} at location {2}', generated_attribute, alias_type,
                     location.get_folder_path(), cmo_type, class_name=CLASS_NAME, method_name=_method_name)

        local_valid = True
    elif _is_of_type_with_lsa(generated_attribute, alias_type, generated_attr_info, get_required_attribute_list):
        if message_type == alias_type:
            _logger.info('Need to improve the test for attribute {0} with LSA type UNKNOWN and '
                         'CMO type {3} and alias type {1} at location {2}', generated_attribute, alias_type,
                         location.get_folder_path(), cmo_type, class_name=CLASS_NAME, method_name=_method_name)
            local_valid = True
    elif wlst_type == UNKNOWN:
        if generated_attribute in get_required_attribute_list:
            if cmo_type is not None:
                message_type = cmo_type
            elif get_type is not None and get_type != UNKNOWN:
                message_type = get_type
            message = 'Alias has GET required'
        else:
            if get_type in CONVERT_TO_DELIMITED_TYPES or cmo_type in CONVERT_TO_DELIMITED_TYPES:
                message_type = 'delimited'

                message = 'Alias has LSA required'
            if alias_type == alias_constants.STRING or alias_type == alias_constants.LIST:
                local_valid =True

    _logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=Boolean(local_valid))
    return local_valid, message_type, message


def _check_boolean_type(generated_attribute, generated_attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(generated_attribute_info)
    valid = False
    if generated_attribute in get_required_attribute_list and \
            (get_type in alias_constants.ALIAS_BOOLEAN_TYPES or
             (get_type in CONVERT_TO_BOOLEAN_TYPES and
              (cmo_type in alias_constants.ALIAS_BOOLEAN_TYPES or cmo_type is None))):
        valid = True
    elif lsa_type in alias_constants.ALIAS_BOOLEAN_TYPES or \
            (lsa_type in CONVERT_TO_BOOLEAN_TYPES and
             (get_type in alias_constants.ALIAS_BOOLEAN_TYPES or
              (get_type in CONVERT_TO_BOOLEAN_TYPES and
               (cmo_type in alias_constants.ALIAS_BOOLEAN_TYPES or cmo_type is None)))):
        valid = True
    elif cmo_type is None and (lsa_type == alias_constants.INTEGER or get_type == alias_constants.INTEGER):
        valid = True
    return valid


def _is_object_type(attribute_info):
    """
    Determine if the attribute is an object or reference type in WLST.
    :param attribute_info: Information gathered about the attribute
    :return: True if the attribute is an object type in WLST
    """
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return lsa_type == alias_constants.OBJECT or \
           (_is_type_an_unknown_type(lsa_type) and
            (get_type == alias_constants.OBJECT or (cmo_type == alias_constants.OBJECT)))


def _is_type_an_unknown_type(check_type):
    """
    Determine if the attribute type does not have information to determine type.
    :param check_type: WLST attribute type from generated information; If None, the retrieval type
        does not exist and thus is not an unknown type. If the type is unknown, then the retrieval type exists
        but the attribute type cannot be determined.
    :return: True if retrieval type can be used to retrieve the attribute value, but the attribute information cannot
        provide information about the attribute type
    """
    return check_type is None or check_type == UNKNOWN


def _is_unknown_type(attribute, alias_type, attribute_info, get_required_attribute_list):
    _method_name = '_is_unknown_type'
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    is_unknown = (attribute in get_required_attribute_list and
                  get_type == UNKNOWN and cmo_type is None) or \
                 (lsa_type == UNKNOWN and get_type is None and cmo_type is None)
    if is_unknown:
        _logger.finer('Cannot definitively determine attribute type of attribute {0} with alias type {1} : {2}',
                      attribute, alias_type, attribute_info, class_name=CLASS_NAME, method_name=_method_name)
    return is_unknown


def _is_attribute_type_for_get_required(get_type, cmo_type):
    """
    Check that the attribute type is suitable for a WLST get by inspecting the type for the get and CMO.
    :param get_type: Type of the WLST.get returned from the type of the value or method.
    :param cmo_type: Type found in the MBeanInfo or MBI descriptors.
    :return: True if the attribute is suitable for a WLST.get()
    """
    if not _is_type_an_unknown_type(get_type):
        return get_type
    if not _is_type_an_unknown_type(cmo_type):
        return cmo_type
    return 'Unable to determine attribute type'


def _is_attribute_type_for_lsa_required(attribute_info):
    """
    Check that the attribute type is suitable for parsing the attribute from the WLST ls attribute map.
    :param attribute_info: Information collected for the attribute
    :return: True if the attribute can be parsed from the "lsa" map
    """
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    if lsa_type is not None:
        if not _is_type_an_unknown_type(lsa_type):
            return lsa_type
        return _is_attribute_type_for_get_required(get_type, cmo_type)
    return lsa_type


def _is_of_type(attribute, alias_type, attribute_info, get_required_attribute_list):
    return _is_of_type_with_get_required(attribute, alias_type, attribute_info, get_required_attribute_list) or \
           _is_of_type_with_lsa(attribute, alias_type, attribute_info, get_required_attribute_list)


def _is_in_types(attribute, alias_types, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return (attribute in get_required_attribute_list and (get_type in alias_types or cmo_type in alias_types)) or \
        lsa_type in alias_types or ((lsa_type == alias_constants.STRING or lsa_type == UNKNOWN or
                                     lsa_type == alias_constants.INTEGER) and
                                    (cmo_type in alias_types or get_type in alias_types))


def _is_any_string_type(attribute_info):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return (lsa_type == alias_constants.STRING or lsa_type == UNKNOWN) and \
           (_type_can_be_lsa_string(get_type) or _type_can_be_lsa_string(cmo_type))


def _type_can_be_lsa_string(attribute_type):
    return attribute_type in [alias_constants.STRING, alias_constants.OBJECT, alias_constants.PASSWORD] or \
           attribute_type in alias_constants.ALIAS_LIST_TYPES or \
           attribute_type in alias_constants.ALIAS_MAP_TYPES


def _get_dict_key_from_value(alias_name_map, lower_case_value):
    result = None
    for key, value in alias_name_map.iteritems():
        if value == lower_case_value:
            result = key
            break
    return result


class VerifierResult(object):
    CLASS_NAME = 'VerifierResult'

    def __init__(self, wlst_mode_string, wls_version):
        self._wlst_mode = wlst_mode_string
        self._wls_version = wls_version
        self._error_dictionary = dict()
        self._warning_dictionary = dict()
        self._info_dictionary = dict()
        self._error_count = 0
        self._warning_count = 0
        self._info_count = 0

    def add_error(self, location, msg_id, message=None, attribute=None):
        _add_message(self._error_dictionary, location, msg_id, message, attribute)
        self._error_count += 1

    def add_warning(self, location, msg_id, message=None, attribute=None):
        _add_message(self._warning_dictionary, location, msg_id, message, attribute)
        self._warning_count += 1

    def add_info(self, location, msg_id, message=None, attribute=None):
        _add_message(self._info_dictionary, location, msg_id, message, attribute)
        self._info_count += 1

    def get_error_count(self):
        return self._error_count

    def get_warning_count(self):
        return self._warning_count

    def get_info_count(self):
        return self._info_count

    def get_exit_code(self):
        if self._error_count > 0:
            return 1
        return 0

    def write_report_file(self, report_file_name):
        with open(report_file_name, 'w') as report_file:
            self._write_error_header(report_file)
            self._write_errors(report_file)
            self._write_warning_header(report_file)
            self._write_warnings(report_file)
            self._write_info_header(report_file)
            self._write_infos(report_file)

    def write_to_logger(self, logger):
        self._write_errors_to_log(logger)
        self._write_warnings_to_log(logger)

    def _write_error_header(self, report_file):
        if self._error_count > 0:
            header = 'Verify %s for WebLogic Server %s reported %s error(s):\n' % \
                     (self._wlst_mode, self._wls_version, self._error_count)
        else:
            header = 'Verify %s for WebLogic Server %s reported 0 errors\n' % (self._wlst_mode, self._wls_version)
        report_file.write(header)

    def _write_warning_header(self, report_file):
        if self._warning_count > 0:
            header = 'Verify %s for WebLogic Server %s reported %s warning(s):\n' % \
                     (self._wlst_mode, self._wls_version, self._warning_count)
        else:
            header = 'Verify %s for WebLogic Server %s reported 0 warnings\n' % (self._wlst_mode, self._wls_version)
        report_file.write(header)

    def _write_info_header(self, report_file):
        if self._info_count > 0:
            header = 'Verify %s for WebLogic Server %s reported %s informational messages:\n' % \
                     (self._wlst_mode, self._wls_version, self._info_count)
        else:
            header = 'Verify %s for WebLogic Server %s reported 0 informational messages\n' % \
                     (self._wlst_mode, self._wls_version)
        report_file.write(header)

    def _write_errors(self, report_file):
        error_dict = verify_utils.sort_dict(self._error_dictionary)
        for location, error_list in error_dict.iteritems():
            error_number = 1
            report_file.write('\tFound %s error(s) at location "%s":\n' % (len(error_list), location))

            for error_dict in error_list:
                message = '\t\t%s\n' % _format_message(error_number, error_dict, location)
                report_file.write(message)
                error_number += 1
            report_file.write('\n')
        report_file.write('\n')

    def _write_warnings(self, report_file):
        warning_dict = verify_utils.sort_dict(self._warning_dictionary)
        for location, warning_list in warning_dict.iteritems():
            warning_number = 1
            report_file.write('\tFound %s warning(s) at location "%s":\n' % (len(warning_list), location))

            for warning_dict in warning_list:
                message = '\t\t%s\n' % _format_message(warning_number, warning_dict, location)
                report_file.write(message)
                warning_number += 1
            report_file.write('\n')
        report_file.write('\n')

    def _write_infos(self, report_file):
        info_dict = verify_utils.sort_dict(self._info_dictionary)
        for location, info_list in info_dict.iteritems():
            info_number = 1
            report_file.write('\tFound %s info message(s) at location "%s":\n' % (len(info_list), location))

            for info_dict in info_list:
                message = '\t\t%s\n' % _format_message(info_number, info_dict, location)
                report_file.write(message)
                info_number += 1
            report_file.write('\n')
        report_file.write('\n')

    def _write_errors_to_log(self, logger):
        _method_name = '_write_errors_to_log'

        if self._error_count == 0:
            logger.info('Verify {0} for WebLogic Server {1} found 0 errors', self._wlst_mode, self._wls_version,
                        class_name=self.CLASS_NAME, method_name=_method_name)
            return

        logger.severe('Verify {0} for WebLogic Server {1} found {2} error(s)', self._wlst_mode, self._wls_version,
                      self._error_count, class_name=self.CLASS_NAME, method_name=_method_name)
        for location, error_list in self._error_dictionary.iteritems():
            error_number = 1
            logger.severe('Found {0} error(s) at location "{1}":', len(error_list), location,
                          class_name=self.CLASS_NAME, method_name=_method_name)

            for error_dict in error_list:
                logger.severe(_format_message(error_number, error_dict, location),
                              class_name=self.CLASS_NAME, method_name=_method_name)
                error_number += 1

    def _write_warnings_to_log(self, logger):
        _method_name = '_write_warnings_to_log'

        if self._warning_count == 0:
            logger.info('Verify {0} for WebLogic Server {1} found 0 warnings', self._wlst_mode, self._wls_version,
                        class_name=self.CLASS_NAME, method_name=_method_name)
            return

        logger.warning('Verify {0} for WebLogic Server {1} found {2} warning(s)', self._wlst_mode, self._wls_version,
                       self._warning_count, class_name=self.CLASS_NAME, method_name=_method_name)
        for location, warning_list in self._warning_dictionary.iteritems():
            warning_number = 1
            logger.warning('Found {0} warning(s) at location "{1}":', len(warning_list), location,
                           class_name=self.CLASS_NAME, method_name=_method_name)

            for warning_dict in warning_list:
                logger.warning(_format_message(warning_number, warning_dict, location),
                               class_name=self.CLASS_NAME, method_name=_method_name)
                warning_number += 1


def _add_message(msg_dict, location, msg_id, message=None, attribute=None):
    location_path = LocationContext(location).get_folder_path()
    if location_path in msg_dict:
        msg_list = msg_dict[location_path]
    else:
        msg_list = list()
        msg_dict[location_path] = msg_list

    typed_msg_dict = dict()
    typed_msg_dict[MSG_ID] = msg_id
    if attribute is not None:
        typed_msg_dict[ATTRIBUTE] = attribute
    if message is not None:
        typed_msg_dict[MESSAGE] = message
    msg_list.append(typed_msg_dict)


def _format_message(message_number, message_dict, location):
    message = MSG_MAP[message_dict[MSG_ID]]

    if ATTRIBUTE in message_dict:
        attribute = message_dict[ATTRIBUTE]
    else:
        attribute = '<No Attribute>'

    if MESSAGE in message_dict:
        extra_message = message_dict[MESSAGE]
    else:
        extra_message = '<No Message>'
    return '%s.) %s (attribute: %s, message: %s, location: %s)' % \
           (message_number, message, attribute, extra_message, location)

