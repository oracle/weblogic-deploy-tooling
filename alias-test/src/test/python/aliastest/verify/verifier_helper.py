"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import java.io.IOException as IOException
import java.lang.Boolean as Boolean
import java.lang.Double as Double
import java.lang.Integer as Integer
import java.lang.Long as Long
import java.lang.NumberFormatException as NumberFormatException
import java.util.logging.Level as Level

from oracle.weblogic.deploy.aliases import AliasException
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
import wlsdeploy.aliases.alias_constants as alias_constants

import aliastest.util.all_utils as all_utils
from aliastest.util.helper import TestHelper

NUMBER_TYPES = [alias_constants.INTEGER, alias_constants.LONG, alias_constants.DOUBLE]
LIST_TYPES = [alias_constants.LIST, alias_constants.JARRAY]
CONVERT_TO_DELIMITED_TYPES = [alias_constants.LIST, alias_constants.JARRAY,
                              alias_constants.ALIAS_MAP_TYPES, alias_constants.DICTIONARY]
CONVERT_TO_BOOLEAN_TYPES = [alias_constants.INTEGER, alias_constants.STRING, all_utils.UNKNOWN]

VERIFY_RANGE = range(1000, 1999)
WARN_RANGE = range(5000, 5999)
ERROR_RANGE = range(2000, 8999)
UNKNOWN_ERROR = range(2000, 2999)
MBEAN_ERROR_RANGE = range(3000, 3999)
ATTRIBUTE_ERROR_RANGE = range(4000, 4999)

TESTED_MBEAN_FOLDER = 1000

WARN_MBEAN_NOT_NO_NAME_0 = 5101
WARN_ATTRIBUTE_DEPRECATED = 5502

ERROR_FAILURE_ATTRIBUTE_LIST = 2000
ERROR_FAILURE_ATTRIBUTE_UNEXPECTED = 2001

ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER = 3001
ERROR_USING_REFERENCE_AS_FOLDER = 3002
ERROR_CANNOT_TEST_MBEAN_UNSPECIFIED = 3003
ERROR_ALIAS_FOLDER_NOT_IN_WLST = 3004
ERROR_FLATTENED_MBEAN_HAS_ATTRIBUTES = 3005
ERROR_CANNOT_TEST_MBEAN_CD = 3006
ERROR_SINGLE_UNPREDICTABLE = 3007

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
ERROR_ATTRIBUTE_IN_IGNORE_LIST = 4021
ERROR_ATTRIBUTE_PATH_TOKEN_REQUIRED = 4022
ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE = 4023
ERROR_ATTRIBUTE_MUST_BE_NO_NAME = 4024

WARN_ATTRIBUTE_HAS_UNKNOWN_TYPE = 5500
WARN_ALIAS_FOLDER_NOT_IMPLEMENTED = 5501

MSG_MAP = {
    TESTED_MBEAN_FOLDER:                           'Verified',
    WARN_ALIAS_FOLDER_NOT_IMPLEMENTED:             'Folder not implemented',
    WARN_MBEAN_NOT_NO_NAME_0:                      'MBean can be named other than NO_NAME_0',
    WARN_ATTRIBUTE_DEPRECATED:                     'Attribute is deprecated',
    WARN_ATTRIBUTE_HAS_UNKNOWN_TYPE:               'Unable to determine the WLST attribute type',
    ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER:           'Unable to generate information for MBean',
    ERROR_ALIAS_FOLDER_NOT_IN_WLST:                'Alias Folder not an mbean',
    ERROR_SINGLE_UNPREDICTABLE:                    'Alias Folder not marked single unpredictable',
    ERROR_FLATTENED_MBEAN_HAS_ATTRIBUTES:          'Alias flattened Folder has attributes',
    ERROR_USING_REFERENCE_AS_FOLDER:               'Reference attribute used as folder mbean',
    ERROR_ATTRIBUTE_ALIAS_NOT_FOUND:               'Attribute not found',
    ERROR_ATTRIBUTE_INCORRECT_CASE:                'Attribute case incorrect',
    ERROR_ATTRIBUTE_ALIAS_NOT_FOUND_IS_READONLY:   'Readonly attribute not found',
    ERROR_ATTRIBUTE_READONLY:                      'Attribute is marked readwrite',
    ERROR_ATTRIBUTE_NOT_READONLY_VERSION:          'Attribute is marked readonly or is invalid version range',
    ERROR_ATTRIBUTE_NOT_READONLY:                  'Attribute is not marked readwrite',
    ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE:           'Attribute wrong default value',
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
    ERROR_ATTRIBUTE_IN_IGNORE_LIST:                'Alias attribute is WLST attribute in the ignore list',
    ERROR_ATTRIBUTE_NOT_IN_WLST:                   'Alias attribute not in MBean',
    ERROR_FAILURE_ATTRIBUTE_LIST:                  'Invalid Alias attribute list',
    ERROR_CANNOT_TEST_MBEAN_UNSPECIFIED:           'Unspecified problem',
    ERROR_CANNOT_TEST_MBEAN_CD:                    'Cannot create MBean',
    ERROR_FAILURE_ATTRIBUTE_UNEXPECTED:            'Unexpected condition for attribute',
    ERROR_ATTRIBUTE_PASSWORD_NOT_MARKED:           'Attribute not marked as password'
}
MSG_ID = 'id'
LOCATION = 'location'
MESSAGE = 'message'
ATTRIBUTE = 'attribute'

_logger = PlatformLogger('test.aliases.verify', resource_bundle_name='aliastest_rb')
_logger.set_level(Level.FINER)
CLASS_NAME = 'VerifierHelper'


class VerifierHelper:
    """
    Common methods and constants for the online and offline verification.
    """

    def __init__(self, model_context, dictionary):
        self._dictionary = dictionary
        self._model_context = model_context
        self._helper = TestHelper(model_context)
        self._error_dictionary = dict()
        self.__nbr_of_errs = 0
        self.__verify = 0
        self.__warn = 0
        self.__error = 0
        self.__mbean_error = 0
        self.__attr_error = 0
        self.__unspecified = 0

    def has_errors(self):
        """
        Print the verification report. Report to caller if errors are present.
        :return: True if errors and or warn were reported during verification
        """
        if self._error_dictionary:
            list_str = []
            for error in self._error_dictionary:
                msgid = self._error_dictionary[error][MSG_ID]
                self._tally_type(msgid)
                folder_path = self._error_dictionary[error][LOCATION]
                attribute = self._error_dictionary[error][ATTRIBUTE]
                extended = ''
                if MESSAGE in self._error_dictionary[error]:
                    extended = self._error_dictionary[error][MESSAGE]
                if attribute:
                    folder_path = folder_path + '/' + attribute
                message = '%04d %-125s %s' % (msgid, folder_path, extended)
                list_str.append(message)
            list_str.sort()
            report_file = None
            try:
                report_file = all_utils.open_file_for_write(
                    all_utils.filename(filename(), WlstModes.from_value(self._helper.mode()),
                                       self._model_context.get_target_wls_version().replace('.', '')))
                for entry in list_str:
                    new_entry = '%-60s ' % MSG_MAP[Integer(entry[:4]).intValue()] + entry[4:]
                    report_file.write(new_entry + '\n')
                report_file.write('\n\nNumber of MBeans tested %5d\n' % self.__verify)
                report_file.write('Number of Warning       %5d\n' % self.__warn)
                report_file.write('Number of Errors        %5d\n' % self.__error)
                report_file.write('       MBean Errors     %5d\n' % self.__mbean_error)
                report_file.write('       Attribute Errors %5d\n' % self.__attr_error)
                report_file.write('       Other Errors     %5d\n' % self.__unspecified)
            finally:
                if report_file:
                    all_utils.close_file(report_file)

        return self.__error > 0, self.__warn > 0

    def add_error(self, location, msg_id, message=None, attribute=None):
        """
        Add the error message to the report dictionary.
        :param location: Context of the current location
        :param msg_id: Id of the message in the message ID list which will return the message text
        :param message: Additional information to add the message
        :param attribute: Attribute name
        """
        dict_id = self._get_error_id()
        self._error_dictionary[dict_id] = dict()
        self._error_dictionary[dict_id][MSG_ID] = msg_id
        self._error_dictionary[dict_id][LOCATION] = LocationContext(location).get_folder_path()
        self._error_dictionary[dict_id][ATTRIBUTE] = attribute
        if message:
            self._error_dictionary[dict_id][MESSAGE] = message
        return

    def check_attributes(self):
        """
        Traverse through the generated attribute MBean list and verify the MBean and its attributes.
        Add verification information to the error dictionary encapsulated by this verification instance.
        """
        _method_name = 'check_attributes'

        def _check(dictionary, location, folder_map):
            _logger.entering(location.get_folder_path(), class_name=CLASS_NAME, method_name=_method_name)

            self.check_dictionary_against_model_list(location, dictionary, folder_map)
            for entry in dictionary:
                # is a entry is a folder, not in the ignore folders and is implemented
                folder_map_name = entry
                if self._do_this_subfolder(dictionary, entry):
                    attributes = attribute_list(dictionary[entry])
                    if attributes is None:
                        if all_utils.RECHECK in dictionary[entry]:
                            message = dictionary[entry][all_utils.RECHECK]
                            if all_utils.ADDITIONAL_RECHECK in dictionary[entry]:
                                message += ' : ' + dictionary[entry][all_utils.ADDITIONAL_RECHECK]
                            self.add_error(location, ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER,
                                           attribute=entry, message=message)
                        else:
                            _logger.fine('WLSDPLYST-01206', entry, folder_map, location.get_folder_path(),
                                         class_name=CLASS_NAME, method_name=_method_name)
                        continue
                    elif folder_map_name not in folder_map:
                        next_key = None
                        if len(dictionary[entry]) > 0:
                            key_list = dictionary[entry].keys()
                            if len(key_list) > 0:
                                if key_list[0] == all_utils.ATTRIBUTES and len(key_list[0]) > 1:
                                    next_key = key_list[1]
                                elif key_list[0] != all_utils.ATTRIBUTES:
                                    next_key = key_list[0]
                        if next_key and next_key in folder_map:
                            folder_map_name = next_key
                            _logger.fine('WLSDPLYST-01207', folder_map_name, class_name=CLASS_NAME,
                                         method_name=_method_name)
                        else:
                            _logger.fine('WLSDPLYST-01209', entry, folder_map, location.get_folder_path(),
                                         class_name=CLASS_NAME, method_name=_method_name)
                            if all_utils.DEPRECATED in dictionary[entry] and \
                                    dictionary[entry][all_utils.DEPRECATED] is not None:
                                message = 'MBean deprecated in version ' + dictionary[entry][all_utils.DEPRECATED]
                            elif all_utils.SINCE_VERSION in dictionary[entry]:
                                message = 'MBean since version ' + dictionary[entry][all_utils.SINCE_VERSION]
                            else:
                                message = ''
                            self.add_error(location, WARN_ALIAS_FOLDER_NOT_IMPLEMENTED,
                                           message=message, attribute=entry)
                            continue

                    # go_to_mbean = getattr(self, 'go_to_mbean')
                    # if go_to_mbean and not go_to_mbean(entry, location):
                    #     continue
                    location.append_location(folder_map[folder_map_name])
                    this_dictionary = dictionary[entry]
                    this_folder_map = folder_map[folder_map_name]
                    flattened_folder = False
                    if self._helper.aliases().get_wlst_flattened_folder_info(location) is not None:
                        _logger.finer('WLSDPLYST-01201', entry, location.get_folder_path(), class_name=CLASS_NAME,
                                      method_name=_method_name)
                        self._check_attribute_list_for_flattened(location, attributes)
                        this_dictionary = this_dictionary[this_dictionary.keys()[0]]
                        attributes = attribute_list(this_dictionary)
                        flattened_folder = True
                    self.check_single_folder(this_dictionary, location, flattened_folder)
                    # make this a message
                    _logger.finer('WLSDPLYST-01210', entry, class_name=CLASS_NAME, method_name=_method_name)
                    self._helper.build_location(location, this_folder_map)
                    self.verify_attributes(attributes, location)
                    subfolder_map = self._helper.get_subfolder_map(location)
                    if subfolder_map:
                        _check(this_dictionary, location, subfolder_map)
                    self._clean_up(location)
            _logger.exiting(class_name=CLASS_NAME, method_name=_method_name)

        top_location = LocationContext()
        top_location.add_name_token('DOMAIN', 'system_test_domain')
        top_folder_map = self._helper.get_top_folder_map(top_location)
        top_attributes = attribute_list(self._dictionary)
        self.verify_attributes(top_attributes, top_location)
        _check(self._dictionary, top_location, top_folder_map)

    def check_single_folder(self, dictionary, location, is_flattened_folder):
        """
        Check to see if the instance type matches, that a single folder is defined as a single folder and
        that the naming of the folder matches what can be named (i.e. NO_NAME_0 versus token name)
        Flattened folders are single by default, but are not marked in the alias definition.
        :param dictionary: generated dictionary of current mbean
        :param is_flattened_folder: if current mbean is a flattened and single folder
        :param location: current location context of mbean
        """
        if all_utils.INSTANCE_TYPE in dictionary:
            instance_type = dictionary[all_utils.INSTANCE_TYPE]
            is_multiple = self._helper.aliases().supports_multiple_mbean_instances(location)
            if is_flattened_folder:
                is_multiple = False
            if is_multiple:
                if instance_type != all_utils.MULTIPLE:
                    self.add_error(location, ERROR_SINGLE_UNPREDICTABLE)
            else:
                try:
                    token_name = self._helper.aliases().get_wlst_mbean_name(location)
                except AliasException:
                    self.add_error(location, ERROR_ATTRIBUTE_INVALID_VERSION)
                    return
                if instance_type == all_utils.SINGLE_NO_NAME:
                    if token_name != 'NO_NAME_0':
                        self.add_error(location, ERROR_ATTRIBUTE_MUST_BE_NO_NAME)
                else:
                    if token_name == 'NO_NAME_0':
                        self.add_error(location, WARN_MBEAN_NOT_NO_NAME_0)

    def verify_attributes(self, attributes, location):
        """
        Verify the attributes from the generated dictionary against the aliases MBean information at the
        current location.
        :param attributes: generated attribute dictionary
        :param location: current location in aliases
        """
        _method_name = 'verify_attributes'
        model_name_map = self._model_attribute_map(location)
        _logger.fine('WLSDPLYST-01211', location.get_folder_path(), model_name_map,
                     class_name=CLASS_NAME, method_name=_method_name)
        if model_name_map is None:
            _logger.fine('WLSDPLYST-01212', location.get_folder_path(),
                         class_name=CLASS_NAME, method_name=_method_name)
            self.add_error(location, ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER)
            return
        if model_name_map or attributes:
            attr_nbr = 0
            if attributes:
                attr_nbr = len(attributes)
            get_required_attribute_list = self._get_required_attribute_map(location)
            restart_attribute_list = self._restart_required_map(location)
            path_tokens_list = self._path_tokens_map(location)
            set_method_list = self._helper.aliases().get_model_mbean_set_method_attribute_names_and_types(
                location).keys()
            _logger.fine('WLSDPLYST-01213', location.get_folder_path(),
                         set_method_list, class_name=CLASS_NAME, method_name=_method_name)

            unprocessed_list = model_name_map.keys()
            _logger.finest('WLSDPLYST-01214', location.get_folder_path(), unprocessed_list,
                           class_name=CLASS_NAME, method_name=_method_name)
            if attributes:
                for attribute in attributes:
                    if attribute in unprocessed_list:
                        unprocessed_list.remove(attribute)

                    attribute_info = attributes[attribute]
                    _logger.finest('WLSDPLYST-01202', attribute, attribute_info, location, class_name=CLASS_NAME,
                                   method_name=_method_name)
                    exists, model_attribute = self.check_attribute_exists(location, attribute, attribute_info,
                                                                          model_name_map, get_required_attribute_list)
                    if exists:
                        alias_type = self._helper.aliases().get_model_attribute_type(location, model_attribute)
                        attr_default, attr_type = \
                            self.valid_attribute_value(location, attribute, attribute_info, model_attribute,
                                                       get_required_attribute_list)
                        self.valid_deprecated(location, attribute, attribute_info)
                        self.valid_restart_type(location, attribute, attribute_info, model_attribute,
                                                restart_attribute_list)
                        self.valid_path_token_type(location, attribute, attribute_info, attr_default, model_attribute,
                                                   path_tokens_list)
                        self.valid_attribute_type(location, attribute, attr_type, attr_default, attribute_info,
                                                  model_attribute,
                                                  alias_type, get_required_attribute_list, set_method_list)
                _logger.fine('WLSDPLYST-01215', location.get_folder_path(), unprocessed_list,
                             class_name=CLASS_NAME, method_name=_method_name)
            for unprocessed in unprocessed_list:
                if unprocessed in self._helper.aliases().get_ignore_attribute_names():
                    self.add_error(location, ERROR_ATTRIBUTE_IN_IGNORE_LIST, attribute=unprocessed)
                else:
                    message = ''
                    if all_utils.is_clear_text_password(unprocessed):
                        message = 'This attribute is a clear text password'
                    self.add_error(location, ERROR_ATTRIBUTE_NOT_IN_WLST, message=message, attribute=unprocessed)
        else:
            attr_nbr = 0
        self.add_error(location, TESTED_MBEAN_FOLDER, message=str(attr_nbr) + ' attributes')

    def check_attribute_exists(self, location, attribute, attribute_info, model_name_map, get_required_attribute_list):
        """
        Verify that the attribute found in weblogic in the generated list exists in the aliases for the current
        mbean.
        :param location: current location in the aliases
        :param attribute: name of the attribute to check in wlst format
        :param attribute_info: information about the attribute from the generated dictionary
        :param model_name_map: attribute map with model names from the aliases
        :param get_required_attribute_list: list of attributes that require GET
        :return: True if the attribute exists in the aliases: Model name for the attribute
        """
        _method_name = 'check_attribute'
        _logger.entering(location.get_folder_path(), attribute, class_name=CLASS_NAME, method_name=_method_name)
        exists, model_attribute = self.alias_attribute_exists(location, attribute, attribute_info, model_name_map)
        if exists:
            if model_attribute is None:
                # if the alias attribute is correctly identified as read-only, it's not an error, but we cannot
                # verify any of the other attribute information using aliases methods. And since its read-only
                # we don't really care about any of the attribute information. This is also true for clear
                # text password fields.
                exists = False
                # clear text attributes (don't have Encrypted on the end) are not defined in the definitions
                # they are only artificially known and ignored by alias definitions
                read_only = self.readonly(location, attribute, attribute_info, get_required_attribute_list)
                if read_only is not None:
                    if not read_only and not all_utils.is_clear_text_password(attribute):
                        message = None
                        if all_utils.CMO_READ_TYPE in attribute_info and \
                                attribute_info[all_utils.CMO_READ_TYPE] == all_utils.READ_ONLY:
                            message = 'LSA has READ_WRITE and CMO has READ_ONLY'
                        self.add_error(location, ERROR_ATTRIBUTE_NOT_READONLY_VERSION,
                                       message=message, attribute=attribute)
            else:
                if self.readonly(location, attribute, attribute_info, get_required_attribute_list):
                    self.add_error(location, ERROR_ATTRIBUTE_READONLY, attribute=attribute)
        _logger.exiting(result=all_utils.str_bool(exists), class_name=CLASS_NAME, method_name=_method_name)
        return exists, model_attribute

    def valid_attribute_value(self, location, attribute, attribute_info, model_attribute, get_required_attribute_list):
        """
        Verify that the type and default value for the generated attribute matches the aliases information.
        :param location: current location for the aliases
        :param attribute: attribute name in wlst format
        :param attribute_info: generated information about the attribute
        :param model_attribute: attribute model name from the aliases
        :param get_required_attribute_list: list from the aliases with GET is required for the MBean
        """
        _method_name = 'check_attribute_value'
        _logger.entering(location.get_folder_path(), attribute, model_attribute, class_name=CLASS_NAME,
                         method_name=_method_name)
        valid, attr_default, attr_type = \
            self.valid_default_type(location, attribute, attribute_info, get_required_attribute_list)
        if valid:
            __, model_default_value, wlst_default_value = self.valid_model_default_value(attribute, location,
                                                                                         model_attribute)
            self.check_default_value(location, attribute, attribute_info, attr_default, model_default_value)

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
        return attr_default, attr_type

    def alias_attribute_exists(self, location, attribute, attribute_info, model_name_map):
        """
        Verify that the generated attribute exists in the aliases. If it is not found in the aliases, attempt
        to determine if why it is not found in the aliases.
        :param location: current location in the aliases
        :param attribute: generated attribute name
        :param attribute_info: generated information about the information
        :param model_name_map: map of wlst attributes from the alias with model names to assist in determining reason
        :return: True if the attribute exists in aliases: aliases attribute model name
        """
        _method_name = 'alias_attribute_exists'
        _logger.entering(location.get_folder_path(), attribute, class_name=CLASS_NAME, method_name=_method_name)
        lower_case_list = model_name_map.values()
        exists = True
        model_attribute = None
        try:
            # no exception is thrown if it is found but read only, just returns empty model_attribute name
            model_attribute = self._helper.aliases().get_model_attribute_name(location, attribute)
        except AliasException:
            if all_utils.DEPRECATED not in attribute_info:
                message = None
                if all_utils.LSA_DEFAULT not in attribute_info:
                    message = 'Attribute is not found in LSA map'
                elif all_utils.SINCE_VERSION in attribute_info:
                    message = 'Since Version=', attribute_info[all_utils.SINCE_VERSION]
                if attribute.lower() in lower_case_list:
                    self.add_error(location, ERROR_ATTRIBUTE_INCORRECT_CASE, attribute=attribute)
                elif self.readonly(location, attribute, attribute_info):
                    self.add_error(location, ERROR_ATTRIBUTE_ALIAS_NOT_FOUND_IS_READONLY,
                                   attribute=attribute, message=message)
                else:
                    self.add_error(location, ERROR_ATTRIBUTE_ALIAS_NOT_FOUND,
                                   attribute=attribute, message=message)
            else:
                _logger.fine('WLSDPLYST-01205', attribute, location.get_folder_path(), class_name=CLASS_NAME,
                             method_name=_method_name)
            exists = False
        _logger.exiting(result=model_attribute, class_name=CLASS_NAME, method_name=_method_name)
        return exists, model_attribute

    def valid_model_default_value(self, attribute, location, model_attribute_name):
        """
        Return the model default value for the attribute, and the model value converted into wlst format by aliases.
        Using the default value found for the attribute in the aliases, convert the default value into wlst format
        to check that it can successfully be formatted.
        :param attribute: generated attribute name in wlst format
        :param location: current location in the aliases
        :param model_attribute_name: model name for the generated attribute from the aliases
        :return: True if the model default value is valid to the aliases: model default value
        """
        _method_name = 'valid_model_default_value'
        _logger.entering(attribute, location.get_folder_path(), model_attribute_name, class_name=CLASS_NAME,
                         method_name=_method_name)
        model_default_value = None
        valid = True
        try:
            model_default_value = self._helper.aliases().get_model_attribute_default_value(location,
                                                                                           model_attribute_name)
        except AliasException, ae:
            self.add_error(location, ERROR_FAILURE_ATTRIBUTE_UNEXPECTED, message=ae.getLocalizedMessage(),
                           attribute=attribute)
            valid = False
        wlst_default = None
        if valid:
            try:
                wlst_attr, wlst_default = self._helper.aliases().get_wlst_attribute_name_and_value(location,
                                                                                                   model_attribute_name,
                                                                                                   model_default_value)
            except AliasException, ae:
                self.add_error(location, ERROR_FAILURE_ATTRIBUTE_UNEXPECTED, message=ae.getLocalizedMessage(),
                               attribute=attribute)
                valid = False
        _logger.exiting(result=all_utils.str_bool(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid, model_default_value, wlst_default

    def valid_default_type(self, location, attribute, attribute_info, get_required_attribute_list):
        """
        Verify that the GET or LSA of the generated attribute is correct for the aliases attribute.
        Based on the GET or LSA in aliases, return the matching default value from the generated attribute information.
        :param location: current location in the aliases
        :param attribute: generated name of the attribute
        :param attribute_info: generated information for the attribute
        :param get_required_attribute_list: list from aliases for the MBean of those attributes with GET required
        :return: True if the default type is correct: Default value from the generated attribute information
        """
        _method_name = 'valid_default_type'
        _logger.entering(location.get_folder_path(), attribute, class_name=CLASS_NAME, method_name=_method_name)
        # Should we pass in the LSA list from aliases too to check that the lists from aliases are correct?
        attr_default = None
        attr_type = None
        valid = True

        if (all_utils.LSA_DEFAULT not in attribute_info and all_utils.GET_DEFAULT not in attribute_info) and \
                all_utils.CMO_DEFAULT in attribute_info:
            self.add_error(location, ERROR_ATTRIBUTE_CMO_REQUIRED, attribute=attribute)
            valid = False
            attr_default = attribute_info[all_utils.CMO_DEFAULT]
            attr_type = attribute_info[all_utils.CMO_TYPE]
        elif all_utils.GET_DEFAULT in attribute_info and all_utils.LSA_DEFAULT in attribute_info:
            _logger.finest('WLSDPLYST-01204', attribute, location.get_folder_path(), class_name=CLASS_NAME,
                           method_name=_method_name)
            if attribute in get_required_attribute_list:
                attr_default = attribute_info[all_utils.GET_DEFAULT]
                attr_type = attribute_info[all_utils.GET_TYPE]
            else:
                attr_default = attribute_info[all_utils.LSA_DEFAULT]
                attr_type = attribute_info[all_utils.LSA_TYPE]
        elif all_utils.GET_DEFAULT in attribute_info:
            attr_default = attribute_info[all_utils.GET_DEFAULT]
            attr_type = attribute_info[all_utils.GET_TYPE]
            if attribute not in get_required_attribute_list:
                message = 'Attribute is not in LSA map'
                self.add_error(location, ERROR_ATTRIBUTE_GET_REQUIRED, message=message, attribute=attribute)
                valid = False
        elif all_utils.LSA_DEFAULT in attribute_info:
            attr_default = attribute_info[all_utils.LSA_DEFAULT]
            attr_type = attribute_info[all_utils.LSA_TYPE]
            if attribute in get_required_attribute_list:
                message = ''
                if all_utils.CMO_DEFAULT not in attribute_info:
                    message = 'Attribute is not in the mbean info maps'
                self.add_error(location, ERROR_ATTRIBUTE_LSA_REQUIRED, message=message, attribute=attribute)
                valid = False
        if attr_default == "None":
            attr_default = None
        if attr_type == alias_constants.INTEGER and all_utils.CMO_TYPE in attribute_info and \
                attribute_info[all_utils.CMO_TYPE] == alias_constants.BOOLEAN:
            attr_type = alias_constants.BOOLEAN
        # if attr_type == all_utils.UNKNOWN:
        #     if all_utils.CMO_TYPE in attribute_info:
        #         attr_type = attribute_info[all_utils.CMO_TYPE]
        #     elif all_utils.GET_TYPE in attribute_info:
        #         attr_type = attribute_info[all_utils.GET_TYPE]
        #     elif all_utils.LSA_TYPE in attribute_info:
        #         attr_type = attribute_info[all_utils.LSA_TYPE]
        #     if attr_type == all_utils.UNKNOWN:
        #         _logger.fine('Unable to determine attribute {0} type', attribute,
        #                      class_name=CLASS_NAME, method_name=_method_name)
        #         valid = False

        _logger.exiting(result=all_utils.str_bool(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid, attr_default, attr_type

    def valid_attribute_type(self, location, attribute, attr_type, attr_value, attribute_info, model_name, alias_type,
                             get_required_attribute_list, set_method_list):
        """
        Verify that the type for the generated attribute matches the type for the attribute in the aliases.
        :param location: current location in the aliases
        :param attribute: generated attribute name
        :param attr_type: the attribute type specific to what value is being used
        :param attr_value: the attribute value to assist in checking the attribute type
        :param attribute_info: generated information about the attribute
        :param model_name: model attribute name from aliases
        :param alias_type: alias wlst type for the model attribute
        :param get_required_attribute_list: aliases list for the MBean of attributes requiring GET
        :param set_method_list: aliases list for the MBean of attributes with special set methods
        :return: True if the attribute type is correct
        """
        _method_name = 'valid_attribute_type'
        _logger.entering(location.get_folder_path(), attribute, model_name, class_name=CLASS_NAME,
                         method_name=_method_name)

        valid = False
        message = None
        if alias_type is not None and attr_type is not None:
            # if attr_type == all_utils.UNKNOWN and all_utils.CMO_TYPE in attribute_info:
            #     attr_type = attribute_info[all_utils.CMO_TYPE]
            # if alias_type == attr_type:
            #     _logger.finer('Attribute {0} alias type {1} matches WLST attribute type ', model_name, alias_type,
            #                   class_name=CLASS_NAME, method_name=_method_name)
            #     valid = True
            if alias_type in alias_constants.ALIAS_BOOLEAN_TYPES and \
                    _check_boolean_type(attribute, attribute_info, get_required_attribute_list):
                valid = True
                _logger.fine('Test attribute {0} type {1} with value {2} for valid conversion to alias type {3} ',
                             attribute, attr_type, attr_value, alias_type,
                             class_name=CLASS_NAME, method_name=_method_name)
            elif self.valid_primitive_type(location, attribute, attribute_info, attr_type, attr_value,
                                           alias_type, get_required_attribute_list):
                _logger.finer('Attribute [0} with alias type {0} passed special primitive test', model_name, alias_type,
                              class_name=CLASS_NAME, method_name=_method_name)
                valid = True
            elif alias_type == alias_constants.PROPERTIES and \
                self.valid_alias_property_type(location, attribute, attribute_info, alias_type, model_name,
                                               get_required_attribute_list):
                valid = True
            elif alias_type in alias_constants.ALIAS_LIST_TYPES and \
                    self.check_complex_type(location, attribute, attribute_info, alias_type, model_name,
                                            get_required_attribute_list):
                _logger.finer('Attribute {0} attribute type {1} is valid for alias type {2}',
                              model_name, attr_type, alias_type,
                              class_name=CLASS_NAME, method_name=_method_name)
                valid = True
            elif alias_type == alias_constants.STRING and object_type(attribute_info):
                valid = True
                if model_name not in set_method_list:
                    _logger.fine('WLSDPLYST-01216', attribute, set_method_list,
                                 class_name=CLASS_NAME, method_name=_method_name)
                    self.add_error(location, ERROR_ATTRIBUTE_SET_METHOD_MISSING, attribute=attribute)
            else:
                valid, attr_type, message = \
                    self._check_for_allowed_unknowns(location, attribute, attr_type, alias_type,
                                                     attribute_info, get_required_attribute_list, valid)
        if not valid:
            _logger.fine('No solution for attribute {0} with type {1} and full attribute info {2}', attribute,
                         attr_type, attribute_info, class_name=CLASS_NAME, method_name=_method_name)
            self.__add_invalid_type_error(
                location, attribute, attr_type, alias_type, get_required_attribute_list, message)

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name)

    def __add_invalid_type_error(self, location, attribute, wlst_type, alias_type, get_required_attribute_list,
                                 extra_blurb=''):
        _method_name = '__add_invalid_type_error'
        if extra_blurb is None:
            extra_blurb = ''
        if wlst_type == all_utils.UNKNOWN:
            _logger.fine('Change caller to pass an attribute type other than unknown for attribute {0}',
                         attribute, class_name=CLASS_NAME, method_name=_method_name)
        if len(extra_blurb) == 0 and attribute in get_required_attribute_list:
            extra_blurb = 'Alias has GET required'
        message = 'Attribute type %-10s :  Alias type %-30s  %s' % (wlst_type, alias_type, extra_blurb)
        self.add_error(location, ERROR_ATTRIBUTE_WRONG_TYPE, message=message, attribute=attribute)

    def valid_restart_type(self, location, attribute, attribute_info, model_name, restart_required_list):
        """
        Verify that the generated attribute requires restart type matches the aliases attribute information.
        :param location: current location in the aliases
        :param attribute: generated attribute name
        :param attribute_info: generated information about the attribute
        :param model_name: model name for the attribute from the aliases
        :param restart_required_list: aliases list for the MBean of attributes requiring restart
        :return: True if restart type is correct
        """
        _method_name = 'valid_restart_type'
        _logger.entering(location.get_folder_path(), attribute, model_name, class_name=CLASS_NAME,
                         method_name=_method_name)
        valid = True
        if model_name in restart_required_list:
            if all_utils.RESTART not in attribute_info or \
                    (attribute_info[all_utils.RESTART] != all_utils.RESTART_NO_CHECK and
                     attribute_info[all_utils.RESTART] != 'true'):
                self.add_error(location, ERROR_ATTRIBUTE_NOT_RESTART, attribute=model_name)
                valid = False
        elif all_utils.RESTART in attribute_info and attribute_info[all_utils.RESTART] == 'true':
            self.add_error(location, ERROR_ATTRIBUTE_RESTART, attribute=attribute)
            valid = False
        _logger.exiting(result=all_utils.str_bool(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def check_default_value(self, location, attribute, attribute_info, attr_default, model_default_value):
        """
        Verify that the default value for the generated attribute matches the default value for the attribute
        in the aliases.
        :param location: current location in the aliases
        :param attribute: generated attribute name
        :param attribute_info: generated structure with WLST information about the attribute
        :param attr_default: generated attribute default value
        :param model_default_value: default value from the aliases
        :return: True if default value is correct: aliases model name for the attribute: aliases model default value
        """
        _method_name = 'check_default_value'
        _logger.entering(location.get_folder_path(), attribute, attr_default, class_name=CLASS_NAME,
                         method_name=_method_name)
        check_attr = _massage_special(attribute, attribute_info, attr_default)
        match = True
        model_name = None
        model_value = None
        # aliases will automatically return None for a None in value
        if check_attr is not None:
            try:
                model_name, model_value = self._helper.aliases().get_model_attribute_name_and_value(location, attribute,
                                                                                                    check_attr)
            except TypeError, te:
                self.add_error(location, ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE, message=te,
                               attribute=attribute)
                match = False
            except (AliasException, IOException), ae:
                self.add_error(location, ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE, message=ae.getLocalizedMessage(),
                               attribute=attribute)
                match = False
        else:
            model_value = model_default_value

        if match and model_value is not None:
            match = False
            attr_type = type(check_attr)
            if all_utils.CMO_TYPE in attribute_info and \
                    (attribute_info[all_utils.CMO_TYPE] == alias_constants.BOOLEAN or
                     attribute_info[all_utils.CMO_TYPE] == alias_constants.JAVA_LANG_BOOLEAN) and \
                    check_attr is not None and (attr_type in [str, unicode, int]):
                check_attr = Boolean(check_attr)
            message = \
                'Attribute=%s  :  Alias=%s' % (str(check_attr), str(model_default_value))
            self.add_error(location, ERROR_ATTRIBUTE_WRONG_DEFAULT_VALUE, message=message,
                           attribute=attribute)
        _logger.exiting(result=all_utils.str_bool(match), class_name=CLASS_NAME, method_name=_method_name)
        return match, model_name, model_value

    def valid_primitive_type(self, location, attribute, attribute_info, attribute_type,
                             attribute_value, alias_type, get_required_attribute_list):
        """
        The attribute type is not the exact match to the alias type. Check to see if the attribute type is one
        whose value can be converted to a model value.There are only a small set of the primitives for which this
        makes sense.
        :param location: current location in the aliases
        :param attribute: attribute from the attribute_info
        :param attribute_info: Full information from the attribute_info
        :param attribute_type: type of the attribute value
        :param attribute_value: value that will be converted to a model value
        :param alias_type: type of the attribute in the aliases
        :param get_required_attribute_list: list of the alias attributes with GET required
        :return:
        """
        _method_name = 'valid_primitive_type'
        _logger.entering(attribute, attribute_type, attribute_value, alias_type,
                         class_name=CLASS_NAME, method_name=_method_name)
        valid = False
        if alias_type in alias_constants.ALIAS_PRIMITIVE_DATA_TYPES:
            if alias_type == attribute_type:
                valid = True
            elif (alias_type == alias_constants.STRING or alias_type == alias_constants.PASSWORD) and \
                    _is_of_type(attribute, alias_type, attribute_info, get_required_attribute_list):
                # simple primitive test
                valid = True
            elif alias_type == alias_constants.CREDENTIAL and \
                    _is_of_type(attribute, alias_constants.STRING, attribute_info, get_required_attribute_list):
                valid = True
            elif alias_type == alias_constants.LONG and attribute_type == alias_constants.INTEGER and \
                    attribute not in get_required_attribute_list:
                valid = True
                self.__add_invalid_type_error(location, attribute, attribute_type, alias_type,
                                              get_required_attribute_list,
                                              'Attribute requires GET for LONG value')
            elif alias_type in NUMBER_TYPES and \
                    _is_in_types(attribute, NUMBER_TYPES, attribute_info, get_required_attribute_list):
                _logger.fine('Test attribute {0} type {1} with value {2} for valid conversion to alias type {3} ',
                             attribute, attribute_type, attribute_value, alias_type,
                             class_name=CLASS_NAME, method_name=_method_name)
                valid = True
        _logger.exiting(result=Boolean(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def check_complex_type(self, location, attribute, attr_info, alias_type, model_name, get_required_attribute_list):
        """
        Check to see if the attribute type is consistent with an alias delimited type
        Check the delimited alias type to determine if it is a list of properties (dictionary) instead of straight
        string list.
        :param location: current location in the aliases
        :param attribute: attribute name
        :param attr_info: data structure containing the attribute information
        :param alias_type: the complex alias type for the check
        :param model_name: of the attribute to locate the alias attribute definition
        :param get_required_attribute_list: list of attributes that require GET for the MBean
        :return: True if the delimited type contains properties
        """
        _method_name = 'check_complex_type'
        _logger.entering(attribute, alias_type, model_name,
                         class_name=CLASS_NAME, method_name=_method_name)
        valid = False
        lsa_type, get_type, cmo_type = _get_attribute_types(attr_info)
        _logger.finest('Attribute {0} lsa_type {1} cmo_type {2} get_type {3} : alias_type {4} get required {5}',
                       attribute, lsa_type, cmo_type, get_type, alias_type,
                       Boolean(attribute in get_required_attribute_list),
                       class_name=CLASS_NAME, method_name=_method_name)
        if alias_type == alias_constants.SEMI_COLON_DELIMITED_STRING and \
                _is_of_type_with_lsa(attribute, alias_constants.PROPERTIES, attr_info, get_required_attribute_list):
            valid = True
            if self._helper.aliases().get_preferred_model_type(location, model_name) != alias_constants.DICTIONARY:
                self.__add_invalid_type_error(location, attribute, alias_constants.PROPERTIES, alias_type,
                                              'Attribute requires preferred model type')
        elif alias_type == alias_constants.JARRAY:
            if _is_of_type_with_get_required(attribute, alias_type, attr_info, get_required_attribute_list):
                valid = True
            elif _is_of_type_with_lsa(attribute, alias_type, attr_info, get_required_attribute_list):
                valid = True
                if self._helper.aliases().get_wlst_read_type(location, model_name) not in \
                        alias_constants.ALIAS_DELIMITED_TYPES:
                    self.__add_invalid_type_error(location, attribute, alias_constants.STRING, alias_type,
                                                  get_required_attribute_list, 'GET or WLST_READ_TYPE required')
        elif alias_type == alias_constants.LIST:
            if _is_of_type_with_get_required(attribute, alias_type, attr_info, get_required_attribute_list):
                valid = True
            elif _is_of_type_with_lsa(attribute, alias_type, attr_info, get_required_attribute_list):
                valid = True
                if self._helper.aliases().get_wlst_read_type(location, model_name) not in \
                        alias_constants.ALIAS_DELIMITED_TYPES:
                    self.__add_invalid_type_error(location, attribute, alias_constants.STRING, alias_type,
                                                  get_required_attribute_list, 'LSA GET_METHOD requires WLST_READ_TYPE')
        elif alias_type in alias_constants.ALIAS_DELIMITED_TYPES:
            if _is_any_string_type(attr_info):
                valid = True
                if _is_in_types_with_get_required(attribute, CONVERT_TO_DELIMITED_TYPES,
                                                  attr_info, get_required_attribute_list) and \
                        self._helper.aliases().get_wlst_read_type(location, model_name) not in \
                        CONVERT_TO_DELIMITED_TYPES:
                    self.__add_invalid_type_error(location, attribute, alias_constants.STRING, alias_type,
                                                  get_required_attribute_list, 'GET needs valid WLST_READ_TYPE')
                else:
                    _logger.finer('Attribute {0} type {1} is valid for delimited string',
                                  attribute, lsa_type, class_name=CLASS_NAME, method_name=_method_name)
        _logger.exiting(result=Boolean(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def valid_alias_property_type(self, location, attribute, attr_info, alias_type, model_name,
                                  get_required_attribute_list):
        """
        Determine if the WLST type can be converted into a dictionary type.
        :param location: Context for current location
        :param attribute: Attribute name
        :param attr_info: Information gathered about the attribute
        :param alias_type: Attribute type in the alias definition
        :param model_name: Model name in the alias definition used to test the get required list
        :param get_required_attribute_list: List of attributes for the MBean that require a WLST list
        :return: True if the is a type that can be converted to a dictionary
        """
        lsa_type, get_type, cmo_type = _get_attribute_types(attr_info)
        if attribute in get_required_attribute_list:
            valid = True
            attr_type = attribute_type_for_get_required(get_type, cmo_type)
            if attr_type != alias_constants.PROPERTIES:
                self.__add_invalid_type_error(location, attribute, attr_type, alias_type,
                                              'Alias has GET with wrong type')
        elif _is_any_string_type(attr_info) and self._helper.aliases().get_wlst_read_type(location, model_name) == \
                alias_constants.SEMI_COLON_DELIMITED_STRING:
            valid = True
        else:
            valid = True
            attr_type = attribute_type_for_lsa_required(attr_info)
            message = 'Attribute requires WLST_READ_TYPE of ' + alias_constants.SEMI_COLON_DELIMITED_STRING
            self.__add_invalid_type_error(
                location, attribute, attr_type, alias_type, get_required_attribute_list, message)

        if valid and \
                self._helper.aliases().get_preferred_model_type(location, model_name) != alias_constants.DICTIONARY:
            self.add_error(location, ERROR_ATTRIBUTE_REQUIRES_PREFERRED_MODEL_TYPE, attribute=attribute)

        return valid

    def valid_deprecated(self, location, attribute, attribute_info):
        """
        Check to see if the attribute found in the Aliases is actually deprecated.
        :param location: current location in the aliases
        :param attribute: generated attribute name
        :param attribute_info: generated attribute information
        :return: True if the generated attribute is defined as readonly
        """
        if all_utils.DEPRECATED in attribute_info:
            self.add_error(location, WARN_ATTRIBUTE_DEPRECATED, message=attribute_info[all_utils.DEPRECATED],
                           attribute=attribute)
            return False
        return True

    def readonly(self, location, attribute, attribute_info, get_required_attribute_list=None):
        """
        Determine whether the generated attribute is defined as readonly.
        :param location: current location in the aliases
        :param attribute: generated attribute name
        :param attribute_info: generated attribute information
        :param get_required_attribute_list: list of attributes that require GET
        :return: True if the generated attribute is defined as readonly
        """
        _method_name = 'readonly'

        if all_utils.READ_TYPE not in attribute_info and all_utils.CMO_READ_TYPE not in attribute_info:
            self.add_error(location, ERROR_FAILURE_ATTRIBUTE_UNEXPECTED,
                           message='Generated attribute has no read type', attribute=attribute)
            return None
        if get_required_attribute_list is not None and attribute in get_required_attribute_list and \
                all_utils.CMO_READ_TYPE in attribute_info:
            read_type = attribute_info[all_utils.CMO_READ_TYPE]
            _logger.finer('Using CMO read type {0} for attribute {1} which is in GET required list',
                          read_type, attribute,
                          class_name=CLASS_NAME, method_name=_method_name)
        elif all_utils.READ_TYPE in attribute_info:
            read_type = attribute_info[all_utils.READ_TYPE]
        else:
            _logger.finer('No LSA read type found, using the CMO read type for attribute {0} at location {1}',
                          attribute, location.get_folder_path(),
                          class_name=CLASS_NAME, method_name=_method_name)
            read_type = attribute_info[all_utils.CMO_READ_TYPE]

        _logger.fine('WLSDPLYST-01217', attribute, read_type,
                     class_name=CLASS_NAME, method_name=_method_name)
        return read_type == all_utils.READ_ONLY

    def valid_path_token_type(self, location, attribute, attribute_info,
                              attribute_default, model_name, path_tokens_map):
        """
        If the name indicates the attribute is a path type check to see if use_path_tokens is in the alias definition.

        :param location:  current location context
        :param attribute: name of attribute from generated file
        :param attribute_info: attribute information from generated file
        :param attribute_default: default for attribute
        :param model_name: model name for the generated attribute
        :param path_tokens_map: aliases in the mbean that have path tokens
        :return: True if the generated attribute indicates it needs a path token
        """
        _method_name = 'valid_path_token_type'
        _logger.entering(location.get_folder_path(), attribute, model_name, class_name=CLASS_NAME,
                         method_name=_method_name)
        valid = True

        if model_name not in path_tokens_map and \
                _is_any_string_type(attribute_info) and \
                _is_file_location_type(attribute):
            self.add_error(location, ERROR_ATTRIBUTE_PATH_TOKEN_REQUIRED, attribute=model_name,
                           message=attribute_default)
            valid = False
        _logger.exiting(result=all_utils.str_bool(valid), class_name=CLASS_NAME, method_name=_method_name)
        return valid

    def check_dictionary_against_model_list(self, location, dictionary, folder_map):
        """
        Verify the aliases MBeans for the current location for MBeans are in the generated dictionary.
        Add errors for any aliases MBeans that are not found in the generated dictionary.
        Skip the checking for a flattened folder as superficial and will not match the generated aliases.
        :param location: current location in the aliases.
        :param dictionary: generated dictionary for the current location
        :param folder_map: list of aliases folder for the current location
        """
        _method_name = 'check_dictionary_against_model_list'
        flattened_info = self._helper.aliases().get_wlst_flattened_folder_info(location)
        if flattened_info is not None:
            _logger.finer('WLSDPLYST-01203', location.get_folder_path(), class_name=CLASS_NAME,
                          method_name=_method_name)
        else:
            keys = folder_map.keys()
            lower_case_map = all_utils.get_lower_case_dict(dictionary.keys())
            _logger.finest('WLSDPLYST-01218', location.get_folder_path(), keys,
                           class_name=CLASS_NAME, method_name=_method_name)
            if keys is not None:
                for alias_name in keys:
                    found, mbean_info_name = self._helper.find_name_in_mbean_with_model_name(alias_name, lower_case_map)
                    if found:
                        _logger.fine('Alias mbean type {0} found in dictionary as {1}', alias_name, mbean_info_name,
                                     class_name=CLASS_NAME, method_name=_method_name)
                        if all_utils.ONLINE_REFERENCE_ONLY in dictionary[mbean_info_name] and \
                                dictionary[mbean_info_name][all_utils.ONLINE_REFERENCE_ONLY] == all_utils.TRUE:
                            _logger.fine('WLSDPLYST-01219', mbean_info_name, location.get_folder_path(),
                                         class_name=CLASS_NAME, method_name=_method_name)
                            self.add_error(location, ERROR_USING_REFERENCE_AS_FOLDER, attribute=mbean_info_name)
                            del dictionary[mbean_info_name]
                        elif all_utils.RECHECK in dictionary[mbean_info_name]:
                            message = dictionary[mbean_info_name][all_utils.RECHECK]
                            if all_utils.ADDITIONAL_RECHECK in dictionary[mbean_info_name]:
                                message += ' : ' + dictionary[mbean_info_name][all_utils.ADDITIONAL_RECHECK]
                            self.add_error(location, ERROR_UNABLE_TO_VERIFY_MBEAN_FOLDER,
                                           attribute=mbean_info_name, message=message)
                            _logger.fine('Remove alias folder {0} as it cannot be verified', alias_name,
                                         class_name=CLASS_NAME, method_name=_method_name)
                            del folder_map[alias_name]
                            del dictionary[mbean_info_name]
                        elif all_utils.TYPE in dictionary[mbean_info_name]:
                            self._process_security_provider(dictionary, mbean_info_name, folder_map, alias_name, location)

                    elif not self._helper.check_flattened_folder(location, alias_name):
                        # make this a message
                        _logger.fine('WLSDPLYST-01220', alias_name, location.get_folder_path(), dictionary.keys(),
                                     class_name=CLASS_NAME, method_name=_method_name)
                        self.add_error(location, ERROR_ALIAS_FOLDER_NOT_IN_WLST, attribute=alias_name)
                    else:
                        _logger.fine('Alias mbean type {0} not found in wlst dictionary {1}', dictionary.keys(),
                                     class_name=CLASS_NAME, method_name=_method_name)
            for item in dictionary:
                if all_utils.ONLINE_REFERENCE_ONLY in dictionary[item]:
                    # make this a real message
                    _logger.fine('WLSDPLYST-01221', item, location.get_folder_path(),
                                 class_name=CLASS_NAME, method_name=_method_name)
                    del dictionary[item]

    def _process_security_provider(self, dict, dict_name, alias_map, alias_name, location):
        del dict[dict_name][all_utils.TYPE]
        l2 = LocationContext(location)
        model_name = self._helper.aliases().get_model_subfolder_name(l2, alias_name)
        l2.append_location(model_name)
        alias_subfolders = self._helper.aliases().get_model_subfolder_names(l2)

        name_token = self._helper.aliases().get_name_token(l2)
        for provider in dict[dict_name].keys():
            l2.add_name_token(name_token, provider)
            model_provider = provider
            if '.' in provider:
                model_provider = provider[provider.rfind('.') + 1:]
            if model_provider is None or model_provider not in alias_subfolders:
                self.add_error(location, WARN_ALIAS_FOLDER_NOT_IMPLEMENTED, attribute=provider)
                continue

            l2.append_location(model_provider)
            next_dict=dict[dict_name][provider]
            attributes = attribute_list(next_dict)
            if attributes is None or len(attributes) == 0:
                continue
            self.verify_attributes(attributes, l2)
            l2.pop_location()

    def _clean_up(self, location):
        name_token = self._helper.aliases().get_name_token(location)
        if name_token:
            location.remove_name_token(name_token)
        location.pop_location()

    def _model_attribute_map(self, location):
        wlst_name_map = None
        try:
            model_name_list = self._helper.aliases().get_model_attribute_names(location)
            wlst_name_map = dict()
            if model_name_list:
                for model_name in model_name_list:
                    wlst_name = \
                        self._helper.aliases().get_wlst_attribute_name(location, model_name, check_read_only=False)
                    if wlst_name:
                        wlst_name_map[wlst_name] = wlst_name.lower()
        except AliasException:
            self.add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST)
        return wlst_name_map

    def _get_required_attribute_map(self, location):
        try:
            get_list = self._helper.aliases().get_wlst_get_required_attribute_names(location)
        except AliasException, ae:
            get_list = []
            self.add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST, message=ae.getLocalizedMessage())
        return get_list

    def _restart_required_map(self, location):
        try:
            restart_list = self._helper.aliases().get_model_restart_required_attribute_names(location)
        except AliasException, ae:
            restart_list = []
            self.add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST, message=ae.getLocalizedMessage())
        return restart_list

    def _path_tokens_map(self, location):
        try:
            token_list = self._helper.aliases().get_model_uses_path_tokens_attribute_names(location)
        except AliasException, ae:
            token_list = []
            self.add_error(location, ERROR_FAILURE_ATTRIBUTE_LIST, message=ae.getLocalizedMessage())
        return token_list

    def _get_error_id(self):
        self.__nbr_of_errs += 1
        return self.__nbr_of_errs

    def _tally_type(self, msgid):
        if msgid in VERIFY_RANGE:
            self.__verify += 1
        elif msgid in WARN_RANGE:
            self.__warn += 1
        elif msgid in ERROR_RANGE:
            self.__error += 1
            if msgid in MBEAN_ERROR_RANGE:
                self.__mbean_error += 1
            elif msgid in ATTRIBUTE_ERROR_RANGE:
                self.__attr_error += 1
            else:
                self.__unspecified += 1

    def _do_this_subfolder(self, dictionary, entry):
        if not isinstance(dictionary, dict) or entry not in dictionary:
            return False
        return not all_utils.ignore_mbean(entry) and \
            entry not in getattr(self, 'IGNORE_DICT_FOLDERS') and isinstance(dictionary[entry], dict)

    def _check_attribute_list_for_flattened(self, location, attributes):
        """
        Check the generated attribute list for an MBean that is flattened in the model. If there are
        attributes, the MBean should not be flattened and the attributes are reported as not in aliases.
        :param location: location for the current flattened folder
        :param attributes: generated dictionary to check for attributes
        """
        if len(attributes) > 0:
            self.add_error(location, ERROR_FLATTENED_MBEAN_HAS_ATTRIBUTES)
            for attribute in attributes:
                self.add_error(location, ERROR_ATTRIBUTE_ALIAS_NOT_FOUND, attribute=attribute)

    def _check_for_allowed_unknowns(self, location, attribute_name, wlst_type, alias_type, attribute_info,
                                    get_required_attribute_list, valid):
        _method_name = '_check_for_allowed_unknowns'
        _logger.entering(attribute_name, wlst_type, alias_type, Boolean(valid),
                         class_name=CLASS_NAME, method_name=_method_name)
        local_valid = valid
        message_type = wlst_type
        message = None
        lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
        if _is_unknown_type(attribute_name, alias_type, attribute_info, get_required_attribute_list):
            local_valid = True
        elif _is_of_type_with_get_required(attribute_name, alias_type, attribute_info, get_required_attribute_list):
            _logger.info('Need to improve the test for get required attribute {0} with GET type UNKNOWN and '
                         'CMO type {3} and '
                         'alias type {1} at location {2}', attribute_name, alias_type, location.get_folder_path(),
                         cmo_type, class_name=CLASS_NAME, method_name=_method_name)

            local_valid = True
        elif _is_of_type_with_lsa(attribute_info, all_utils, attribute_info, get_required_attribute_list):
            if message_type == alias_type:
                _logger.info('Need to improve the test for attribute {0} with LSA type UNKNOWN and '
                             'CMO type {3} and '
                             'alias type {1} at location {2}', attribute_name, alias_type, location.get_folder_path(),
                             cmo_type, class_name=CLASS_NAME, method_name=_method_name)
                local_valid = True
        elif wlst_type == all_utils.UNKNOWN:
            if attribute_name in get_required_attribute_list:
                if cmo_type is not None:
                    message_type = cmo_type
                elif get_type is not None and get_type != all_utils.UNKNOWN:
                    message_type = get_type
                message = 'Alias has GET required'
            else:
                if get_type in CONVERT_TO_DELIMITED_TYPES or cmo_type in CONVERT_TO_DELIMITED_TYPES:
                    message_type = 'delimited'
                message = 'Alias has LSA required'

        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=Boolean(local_valid))
        return local_valid, message_type, message

    def _can_convert_to_model_value(self, location, wlst_attribute, wlst_value):
        _method_name = '_can_convert_to_model_value'
        _logger.entering(wlst_attribute, wlst_value, class_name=CLASS_NAME, method_name=_method_name)
        try:
            self._helper.aliases().get_model_attribute_name_and_value(location, wlst_attribute, wlst_value)
            valid = True
        except TypeError, te:
            _logger.fine('Attribute {0} invalid attr_type {1} : {2}', wlst_attribute, wlst_value, str(te))
            valid = False
        _logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=Boolean(valid))
        return valid


def _check_boolean_type(attribute, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    valid = False
    if attribute in get_required_attribute_list and \
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


def _lsa_type_can_match(lsa_type, get_type, cmo_type, check_type):
    return lsa_type == check_type or \
        ((lsa_type is None or lsa_type == alias_constants.STRING or lsa_type == all_utils.UNKNOWN) and
            (cmo_type == check_type or get_type == check_type))


def _can_convert_string_to_number(attribute_type, attribute_value):
    _method_name = '_can_convert_string_to_number'
    _logger.entering(attribute_type, attribute_value, class_name=CLASS_NAME, method_name=_method_name)
    valid = True
    try:
        if attribute_type == alias_constants.INTEGER:
            Integer(attribute_value)
        elif attribute_type == alias_constants.LONG:
            Long(attribute_value)
        elif attribute_type == alias_constants.DOUBLE:
            Double(attribute_value)
    except NumberFormatException:
        valid = False
    _logger.exiting(result=Boolean(valid), class_name=CLASS_NAME, method_name=_method_name)
    return valid


def attribute_list(dictionary):
    """
    Return the attributes for the MBean from the generated file dictionary.
    :param dictionary: Contains the attribute information gathered from WLST
    :return: A list of the attribute names for the MBean
    """
    attributes = None
    if all_utils.ATTRIBUTES in dictionary:
        attributes = dictionary[all_utils.ATTRIBUTES]
        del dictionary[all_utils.ATTRIBUTES]
    return attributes


def object_type(attribute_info):
    """
    Determine if the attribute is an object or reference type in WLST.
    :param attribute_info: Information gathered about the attribute
    :return: True if the attribute is an object type in WLST
    """
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return lsa_type == alias_constants.OBJECT or \
        (unknown_type(lsa_type) and
            (get_type == alias_constants.OBJECT or (cmo_type == alias_constants.OBJECT)))


def unknown_type(check_type):
    """
    Determine if the attribute type does not have information to determine type.
    :param check_type: WLST attribute type from generated information; If None, the retrieval type
        does not exist and thus is not an unknown type. If the type is unknown, then the retrieval type exists
        but the attribute type cannot be determined.
    :return: True if retrieval type can be used to retrieve the attribute value, but the attribute information cannot
        provide information about the attribute type
    """
    return check_type is None or check_type == all_utils.UNKNOWN


def attribute_type_for_get_required(get_type, cmo_type):
    """
    Check that the attribute type is suitable for a WLST get by inspecting the type for the get and CMO.
    :param get_type: Type of the WLST.get returned from the type of the value or method.
    :param cmo_type: Type found in the MBeanInfo or MBI descriptors.
    :return: True if the attribute is suitable for a WLST.get()
    """
    if not unknown_type(get_type):
        return get_type
    if not unknown_type(cmo_type):
        return cmo_type
    return 'Unable to determine attribute type'


def attribute_type_for_lsa_required(attribute_info):
    """
    Check that the attribute type is suitable for parsing the attribute from the WLST ls attribute map.
    :param attribute_info: Information collected for the attribute
    :return: True if the attribute can be parsed from the "lsa" map
    """
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    if lsa_type is not None:
        if not unknown_type(lsa_type):
            return lsa_type
        return attribute_type_for_get_required(get_type, cmo_type)
    return lsa_type


def filename():
    """
    Name for the verify file. This could be overridden or changed.
    :return: Name to identify the verification file
    """
    return 'report'


def _massage_special(attribute, attr_type, attr_default):
    if attr_default is not None and attr_type == 'string':
        if _is_file_location_type(attribute):
            return attr_default.replace('\\', '/')
        elif attribute.endswith('Name') and '-' in attr_default:
            return None
    return attr_default


def _is_of_type(attribute, alias_type, attribute_info, get_required_attribute_list):
    return _is_of_type_with_get_required(attribute, alias_type, attribute_info, get_required_attribute_list) or \
        _is_of_type_with_lsa(attribute, alias_type, attribute_info, get_required_attribute_list)


def _is_of_type_with_get_required(attribute, alias_type, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return attribute in get_required_attribute_list and (get_type == alias_type or cmo_type == alias_type)


def _is_of_type_with_lsa(attribute, alias_type, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return attribute not in get_required_attribute_list and lsa_type is not None and \
        (lsa_type == alias_type or
         ((unknown_type(lsa_type) or lsa_type == alias_constants.STRING or lsa_type == alias_constants.INTEGER) and
          ((unknown_type(get_type) and cmo_type is None) or (get_type == alias_type or cmo_type == alias_type))))


def _is_in_types(attribute, alias_types, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return (attribute in get_required_attribute_list and (get_type in alias_types or cmo_type in alias_types)) or \
        lsa_type in alias_types or \
           ((lsa_type == alias_constants.STRING or lsa_type == all_utils.UNKNOWN or
             lsa_type == alias_constants.INTEGER) and
            (cmo_type in alias_types or get_type in alias_types))


def _is_in_types2(attribute, alias_types, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return (cmo_type in alias_types or get_type in alias_types) and \
           (attribute in get_required_attribute_list or (lsa_type in alias_types or
                                                         lsa_type == alias_constants.STRING or
                                                         lsa_type == all_utils.UNKNOWN or
                                                         lsa_type == alias_constants.INTEGER))


def _is_in_types_with_get_required(attribute, alias_types, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return attribute in get_required_attribute_list and (get_type in alias_types or cmo_type in alias_types)


def _is_in_types_with_lsa(attribute, alias_types, attribute_info, get_required_attribute_list):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return attribute not in get_required_attribute_list and \
        (lsa_type in alias_types or ((lsa_type == alias_constants.STRING or lsa_type == all_utils.UNKNOWN) and
                                     (cmo_type in alias_types or get_type in alias_types)))


def _is_any_string_type(attribute_info):
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    return (lsa_type == alias_constants.STRING or lsa_type == all_utils.UNKNOWN) and \
           (_type_can_be_lsa_string(get_type) or _type_can_be_lsa_string(cmo_type))


def _is_unknown_type(attribute, alias_type, attribute_info, get_required_attribute_list):
    _method_name = '_is_unknown_type'
    lsa_type, get_type, cmo_type = _get_attribute_types(attribute_info)
    is_unknown = (attribute in get_required_attribute_list and
                  get_type == all_utils.UNKNOWN and cmo_type is None) or \
                 (lsa_type == all_utils.UNKNOWN and get_type is None and cmo_type is None)
    if is_unknown:
        _logger.finer('Cannot definitively determine attribute type of attribute {0} with alias type {1} : {2}',
                      attribute, alias_type, attribute_info, class_name=CLASS_NAME, method_name=_method_name)
    return is_unknown


def _type_can_be_lsa_string(attribute_type):
    return attribute_type in [alias_constants.STRING, alias_constants.OBJECT, alias_constants.PASSWORD] or \
           attribute_type in alias_constants.ALIAS_LIST_TYPES or \
           attribute_type in alias_constants.ALIAS_MAP_TYPES


def _get_attribute_types(attribute_info):
    lsa_type = None
    get_type = None
    cmo_type = None
    if all_utils.LSA_TYPE in attribute_info:
        lsa_type = attribute_info[all_utils.LSA_TYPE]
    if all_utils.GET_TYPE in attribute_info:
        get_type = attribute_info[all_utils.GET_TYPE]
    if all_utils.CMO_TYPE in attribute_info:
        cmo_type = attribute_info[all_utils.CMO_TYPE]
    return lsa_type, get_type, cmo_type


def _is_file_location_type(attribute):
    return ('ClassPath' not in attribute and 'Path' in attribute) or 'Dir' in attribute


def _is_bool_type(attr_type):
    return attr_type == bool or attr_type in alias_constants.ALIAS_BOOLEAN_TYPES
