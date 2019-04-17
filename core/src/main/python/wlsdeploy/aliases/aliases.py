"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from java.lang import String

from oracle.weblogic.deploy.aliases import TypeUtils
from oracle.weblogic.deploy.aliases import VersionUtils
from oracle.weblogic.deploy.encrypt import EncryptionException
from oracle.weblogic.deploy.encrypt import EncryptionUtils

from wlsdeploy.aliases.alias_constants import ChildFoldersTypes
from wlsdeploy.aliases.alias_entries import AliasEntries
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases import password_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper

from wlsdeploy.aliases.alias_constants import ACCESS
from wlsdeploy.aliases.alias_constants import ALIAS_LIST_TYPES
from wlsdeploy.aliases.alias_constants import ALIAS_MAP_TYPES
from wlsdeploy.aliases.alias_constants import ATTRIBUTES
from wlsdeploy.aliases.alias_constants import DEFAULT
from wlsdeploy.aliases.alias_constants import FLATTENED_FOLDER_DATA
from wlsdeploy.aliases.alias_constants import FOLDERS
from wlsdeploy.aliases.alias_constants import GET
from wlsdeploy.aliases.alias_constants import GET_MBEAN_TYPE
from wlsdeploy.aliases.alias_constants import GET_METHOD
from wlsdeploy.aliases.alias_constants import JARRAY
from wlsdeploy.aliases.alias_constants import LIST
from wlsdeploy.aliases.alias_constants import LSA
from wlsdeploy.aliases.alias_constants import MBEAN
from wlsdeploy.aliases.alias_constants import MERGE
from wlsdeploy.aliases.alias_constants import MODEL_NAME
from wlsdeploy.aliases.alias_constants import PASSWORD
from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.alias_constants import PREFERRED_MODEL_TYPE
from wlsdeploy.aliases.alias_constants import PROPERTIES
from wlsdeploy.aliases.alias_constants import RESTART_REQUIRED
from wlsdeploy.aliases.alias_constants import SET_MBEAN_TYPE
from wlsdeploy.aliases.alias_constants import SET_METHOD
from wlsdeploy.aliases.alias_constants import USES_PATH_TOKENS
from wlsdeploy.aliases.alias_constants import VALUE
from wlsdeploy.aliases.alias_constants import WLST_NAME
from wlsdeploy.aliases.alias_constants import WLST_TYPE
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER


class Aliases(object):
    """
    The public interface into the aliases subsystem that abstracts out the WLST knowledge base from the
    rest of the tooling.
    """
    _class_name = 'Aliases'

    def __init__(self, model_context, wlst_mode=WlstModes.OFFLINE, wls_version=None, logger=None):
        self._model_context = model_context
        self._wlst_mode = wlst_mode

        if logger is None:
            self._logger = PlatformLogger('wlsdeploy.aliases')
        else:
            self._logger = logger

        self._wls_helper = WebLogicHelper(self._logger)
        if wls_version is None:
            self._wls_version = self._wls_helper.wl_version_actual
        else:
            self._wls_version = wls_version

        self._alias_entries = AliasEntries(wlst_mode, self._wls_version)
        return

    ###########################################################################
    #              Model folder navigation-related methods                    #
    ###########################################################################

    def get_mode_string(self):
        """
        Return WlstModes ONLINE or OFFLINE in string representation for this Aliases.
        :return: 'ONLINE' or 'OFFLINE'
        """
        return WlstModes.from_value(self._wlst_mode)

    def get_mode_enum(self):
        """
        Return the WlstModes enum value for this Aliases.
        :return: WlstModes.ONLINE or WlstModes.OFFLINE
        """
        return self._wlst_mode

    def get_model_top_level_folder_names(self):
        """
        Returns a list of the recognized top-level model folders corresponding to the known WLST top-level folders.
        :return: a list of the recognized top-level model folder names
        """
        return self._alias_entries.get_model_domain_subfolder_names()

    def get_model_topology_top_level_folder_names(self):
        """
        Returns a list of the recognized top-level model folders in the topology section corresponding to the
        known WLST top-level folders.
        :return: a list of the recognized top-level model folder names
        """
        return self._alias_entries.get_model_topology_subfolder_names()

    def get_model_resources_top_level_folder_names(self):
        """
        Returns a list of the recognized top-level model folders in the resources section corresponding to the
        known WLST top-level folders.
        :return: a list of the recognized top-level model folder names
        """
        return self._alias_entries.get_model_resources_subfolder_names()

    def get_model_app_deployments_top_level_folder_names(self):
        """
        Returns a list of the recognized top-level model folders in the appDeployments section corresponding to the
        known WLST top-level folders.
        :return: a list of the recognized top-level model folder names
        """
        return self._alias_entries.get_model_app_deployments_subfolder_names()

    def get_model_subfolder_names(self, location):
        """
        Get the list of model folder names for subfolders of the specified location.
        :param location: the location
        :return: list[string]: the list of model subfolder names or an empty list if there are none
        :raises: AliasException: if an error occurs while getting or processing the folders for the specified location
        """
        return self._alias_entries.get_model_subfolder_names_for_location(location)

    def get_name_token(self, location):
        """
        Get the name token for the specified location.
        :param location: the location
        :return: the name token or None, if no new name token is required
        :raises: AliasException: if an error occurs while getting or processing the folder for the specified location
        """
        return self._alias_entries.get_name_token_for_location(location)

    def get_model_folder_path(self, location):
        """
        Get a slash delimited string of the path in the model to the specified location.
        :param location: the location
        :return: the model path string
        :raises: AliasException: if an error occurs while getting or processing the folders for the specified location
        """
        return self._alias_entries.get_model_folder_path_for_location(location)

    ###########################################################################
    #                      WLST Path-related methods                          #
    ###########################################################################

    def get_wlst_attributes_path(self, location):
        """
        Get the WLST path where the attributes for the specified location are found.
        :return: the WLST path
        :raises AliasException: if the location is missing required name tokens or
                                the alias data for the location is bad
        """
        return self._alias_entries.get_wlst_attribute_path_for_location(location)

    def get_wlst_subfolders_path(self, location):
        """
        Get the WLST path where the subfolders for the specified location are found.
        :param location: the location to use
        :return: the WLST path
        :raises AliasException: if the location is missing required name tokens or
                                the alias data for the location is bad
        """
        return self._alias_entries.get_wlst_subfolders_path_for_location(location)

    def get_wlst_list_path(self, location):
        """
        Get the WLST path where to list the existing instances of the type corresponding to the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises AliasException: if the location is missing required name tokens or
                                the alias data for the location is bad
        """
        return self._alias_entries.get_wlst_list_path_for_location(location)

    def get_wlst_create_path(self, location):
        """
        Get the WLST path where to create new instances of the type corresponding to the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises AliasException: if the location is missing required name tokens or
                                the alias data for the location is bad
        """
        return self._alias_entries.get_wlst_create_path_for_location(location)

    def get_wlst_flattened_folder_list_path(self, location):
        """
        Get the WLST path where to list the existing instances of the flattened type corresponding to
        the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises AliasException: if the location is missing required name tokens or
                                the alias data for the location is bad
        """
        return self._alias_entries.get_wlst_flattened_folder_list_path_for_location(location)

    def get_wlst_flattened_folder_create_path(self, location):
        """
        Get the WLST path where to create new instances of the flattened type corresponding to the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises AliasException: if the location is missing required name tokens or
                                the alias data for the location is bad
        """
        return self._alias_entries.get_wlst_flattened_folder_create_path_for_location(location)

    ###########################################################################
    #                    Child folder-related methods                         #
    ###########################################################################

    def requires_unpredictable_single_name_handling(self, location):
        """
        Does the location folder specified require unpredicatable single name handling?
        :param location: the location
        :return: True, if the location requires unpredicatable single name handling, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location or if the
                                 specified type doesn't match and the actual type is 'none'
        """
        return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.SINGLE_UNPREDICTABLE)

    def supports_multiple_mbean_instances(self, location):
        """
        Does the location folder specified support multiple MBean instances of the parent node type?
        :param location: the location
        :return: True, if the location supports multiple named child nodes, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location or if the
                                 specified type doesn't match and the actual type is 'none'
        """
        return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.MULTIPLE)

    def requires_artificial_type_subfolder_handling(self, location):
        """
        Does the location folder specified both support multiple MBean instances of the parent node type
        and require the use of a subtype, defined by an contained subfolder, to create the MBeans?
        :param location: the location
        :return: True, if so, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location or if the
                                 specified type doesn't match and the actual type is 'none'
        """
        return self._alias_entries.is_location_child_folder_type(location,
                                                                 ChildFoldersTypes.MULTIPLE_WITH_TYPE_SUBFOLDER)

    def supports_single_mbean_instance(self, location):
        """
        Does the location folder specified support only a single MBean instance of the parent node type?
        :param location: the location
        :return: True, if so, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location or if the
                                 specified type doesn't match and the actual type is 'none'
        """
        return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.SINGLE)

    def is_artificial_type_folder(self, location):
        """
        Is the location folder specified an artificial subtype folder?
        :param location: the location
        :return: True, if so, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location
        """
        return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.NONE)

    def is_custom_folder_allowed(self, location):
        """
        Returns true if the specified location allows custom, user-defined folder types.
        This currently corresponds to all MULTIPLE_WITH_TYPE_SUBFOLDER entries.
        This will need to be refined if new custom types are added, or additional distinctions are required.
        :param location: the location to be checked
        :return: True if the location allows custom folder types, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location
        """
        return self._alias_entries.is_location_child_folder_type(location,
                                                                 ChildFoldersTypes.MULTIPLE_WITH_TYPE_SUBFOLDER)

    def is_security_provider_type(self, location):
        """
        Returns true if the specified location is a security provider type, such as AuthenticationProvider.
        This currently corresponds to all MULTIPLE_WITH_TYPE_SUBFOLDER entries.
        This will need to be refined if new custom types are added, or additional distinctions are required.
        :param location: the location to be checked
        :return: True if the location is a security provider type, False otherwise
        :raises: AliasException: if an error occurs while getting the folder for the location
        """
        return self._alias_entries.is_location_child_folder_type(location,
                                                                 ChildFoldersTypes.MULTIPLE_WITH_TYPE_SUBFOLDER)

    ###########################################################################
    #                     WLST Folder create-related methods                  #
    ###########################################################################

    def get_wlst_mbean_name(self, location):
        """
        Get the WLST MBean name for the specified location
        :param location: the location to use
        :return: the WLST MBean name
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        return self._alias_entries.get_wlst_mbean_name_for_location(location)

    def get_wlst_mbean_type(self, location):
        """
        Get the WLST MBean type for the specified location
        :param location: the location to use
        :return: the WLST MBean type
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        return self._alias_entries.get_wlst_mbean_type_for_location(location)

    def is_flattened_folder(self, location):
        """
        Is the current location one that contains a flattened WLST folder?
        :param location: the location
        :return: True, if the specified location contains a flattened WLST tuple of folders, False otherwise
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        return self._alias_entries.location_contains_flattened_folder(location)

    def get_wlst_flattened_mbean_name(self, location):
        """
        Get the flattened WLST folder name.
        :param location: the location
        :return: the flattened folder name
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        return self._alias_entries.get_wlst_flattened_name_for_location(location)

    def get_wlst_flattened_mbean_type(self, location):
        """
        Get the flattened WLST folder type.
        :param location: the location
        :return: the flattened folder type
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        return self._alias_entries.get_wlst_flattened_type_for_location(location)

    ###########################################################################
    #                   WLST attribute-related methods                        #
    ###########################################################################

    def get_wlst_attribute_name_and_value(self, location, model_attribute_name, model_attribute_value,
                                          existing_wlst_value=None):
        """
        Returns the WLST attribute name and value for the specified model attribute name and value.

        wlst_attribute_value should return the correct type and value, even if the value
        is the default value for model_attribute_name.
        :param location: the location to use
        :param model_attribute_name: string
        :param model_attribute_value: value of the appropriate type
        :param existing_wlst_value: existing value of the appropriate type
        :return: the WLST name and value (which may be None)
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_attribute_name_and_value'

        wlst_attribute_name = None
        wlst_attribute_value = None

        module_folder = self._alias_entries.get_dictionary_for_location(location)
        if not module_folder:
            self._logger.fine('WLSDPLY-08410', location.get_current_model_folder(), location.get_parent_folder_path(),
                              WlstModes.from_value(self._wlst_mode), self._wls_version)
            return wlst_attribute_name, wlst_attribute_value

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if model_attribute_name not in module_folder[ATTRIBUTES]:
            ex = exception_helper.create_alias_exception('WLSDPLY-08401', model_attribute_name,
                                                         location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        attribute_info = module_folder[ATTRIBUTES][model_attribute_name]

        if attribute_info and not self.__is_model_attribute_read_only(location, attribute_info):
            password_attribute_name = \
                password_utils.get_wlst_attribute_name(attribute_info, model_attribute_value, self._wlst_mode)

            if password_attribute_name is not None:
                wlst_attribute_name = password_attribute_name
            else:
                wlst_attribute_name = attribute_info[WLST_NAME]

            if self._model_context and USES_PATH_TOKENS in attribute_info and \
                    string_utils.to_boolean(attribute_info[USES_PATH_TOKENS]):
                model_attribute_value = self._model_context.replace_token_string(model_attribute_value)

            data_type = attribute_info[WLST_TYPE]
            if data_type == 'password':
                try:
                    wlst_attribute_value = self.decrypt_password(model_attribute_value)
                except EncryptionException, ee:
                    ex = exception_helper.create_alias_exception('WLSDPLY-08402', model_attribute_name,
                                                                 location.get_folder_path(),
                                                                 ee.getLocalizedMessage(), error=ee)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
            else:
                if data_type in ALIAS_LIST_TYPES or data_type in ALIAS_MAP_TYPES:
                    merge = True
                    if MERGE in attribute_info:
                        merge = alias_utils.convert_boolean(attribute_info[MERGE])

                    if merge and data_type in ALIAS_MAP_TYPES:
                        model_val = TypeUtils.convertToType(PROPERTIES, model_attribute_value)
                        existing_val = TypeUtils.convertToType(PROPERTIES, existing_wlst_value)
                        merged_value = alias_utils.merge_model_and_existing_properties(model_val, existing_val)
                    elif merge and existing_wlst_value is not None and len(existing_wlst_value) > 0:
                        model_val = alias_utils.convert_to_type(LIST, model_attribute_value,
                                                                delimiter=MODEL_LIST_DELIMITER)

                        _read_type, read_delimiter = \
                            alias_utils.compute_read_data_type_and_delimiter_from_attribute_info(attribute_info,
                                                                                                 existing_wlst_value)
                        existing_val = alias_utils.convert_to_type(LIST, existing_wlst_value, delimiter=read_delimiter)
                        merged_value = alias_utils.merge_model_and_existing_lists(model_val, existing_val)
                    else:
                        merged_value = model_attribute_value

                    if data_type == JARRAY:
                        subtype = 'java.lang.String'
                        if SET_MBEAN_TYPE in attribute_info:
                            subtype = attribute_info[SET_MBEAN_TYPE]
                        wlst_attribute_value = alias_utils.convert_to_type(data_type, merged_value, subtype=subtype,
                                                                           delimiter=MODEL_LIST_DELIMITER)
                    else:
                        wlst_attribute_value = alias_utils.convert_to_type(data_type, merged_value,
                                                                           delimiter=MODEL_LIST_DELIMITER)
                else:
                    wlst_attribute_value = alias_utils.convert_to_type(data_type, model_attribute_value,
                                                                       delimiter=MODEL_LIST_DELIMITER)

        return wlst_attribute_name, wlst_attribute_value

    def get_wlst_attribute_name(self, location, model_attribute_name, check_read_only=True):
        """
        Returns the WLST attribute name and value for the specified model attribute name and value.

        wlst_attribute_value should return the correct type and value, even if the value
        is the default value for model_attribute_name.
        :param location:
        :param model_attribute_name:
        :param check_read_only: Defaults to True. If false, return name even if alias definition is read only
        :return: the WLST attribute name or None, if it is not relevant
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_attribute_name'

        self._logger.entering(str(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)
        wlst_attribute_name = None
        alias_attr_dict = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
        if alias_attr_dict is not None and (not check_read_only or not
                                            self.__is_model_attribute_read_only(location, alias_attr_dict)):
            if WLST_NAME in alias_attr_dict:
                wlst_attribute_name = alias_attr_dict[WLST_NAME]
            else:
                ex = exception_helper.create_alias_exception('WLSDPLY-07108', model_attribute_name, location, WLST_NAME)
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

        return wlst_attribute_name

    def get_wlst_get_required_attribute_names(self, location):
        """
        Get the list of attribute names that have their get_method specified as GET.
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_get_required_attribute_names'

        wlst_attribute_names = []

        module_folder = self._alias_entries.get_dictionary_for_location(location)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if GET_METHOD in value and value[GET_METHOD] == GET:
                wlst_attribute_names.append(value[WLST_NAME])

        return wlst_attribute_names

    def get_wlst_lsa_required_attribute_names(self, location):
        """
        Get the list of attribute names that have their get_method specified as LSA.
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_lsa_required_attribute_names'

        wlst_attribute_names = []

        module_folder = self._alias_entries.get_dictionary_for_location(location)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if GET_METHOD in value and value[GET_METHOD] == LSA:
                wlst_attribute_names.append(value[WLST_NAME])

        return wlst_attribute_names

    def get_wlst_get_returns_mbean_attribute_names_and_types(self, location):
        """
        Get the dictionary of attribute names and types that have their get_mbean_type specified.
        :param location: the location
        :return: dictionary: a dictionary with the attribute names as keys and the MBean types as values
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_get_returns_mbean_attribute_names_and_types'

        wlst_attribute_names = dict()

        module_folder = self._alias_entries.get_dictionary_for_location(location)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if GET_MBEAN_TYPE in value:
                wlst_attribute_names[value[WLST_NAME]] = value[GET_MBEAN_TYPE]
            else:
                wlst_attribute_names[value[WLST_NAME]] = None

        return wlst_attribute_names

    ###########################################################################
    #                    Model folder-related methods                         #
    ###########################################################################

    def get_model_subfolder_name(self, location, wlst_subfolder_name):
        """
        Get the model folder name for the WLST subfolder name at the specified location.
        :param location: the location
        :param wlst_subfolder_name: the WLST folder name
        :return: the model folder name, or None if the folder is not needed for the model.
        :raises: AliasException: if an error occurs due to a bad location or bad alias data
        """

        model_subfolder_name = None

        module_folder = self._alias_entries.get_dictionary_for_location(location)
        is_base_security_provider_type_location = alias_utils.is_base_security_provider_type_location(location)
        for key, value in module_folder[FOLDERS].iteritems():
            # value will be None if the folder is not the correct version
            if value is not None:
                wlst_type = value[WLST_TYPE]
                if (wlst_subfolder_name == wlst_type) or \
                        (FLATTENED_FOLDER_DATA in value and WLST_TYPE in value[FLATTENED_FOLDER_DATA] and
                         wlst_subfolder_name == value[FLATTENED_FOLDER_DATA][WLST_TYPE]):
                    model_subfolder_name = key
                    break
                elif is_base_security_provider_type_location:
                    model_subfolder_name = alias_utils.get_security_provider_model_folder_name(wlst_subfolder_name)
                    break

        return model_subfolder_name

    def is_version_valid_location(self, location):
        """
        Verify that the specified location is valid for the WLS version
        being used.

        Caller needs to determine what action (e.g. log, raise exception,
        continue processing, record validation item, etc.) to take, when
        return code is VERSION_INVALID.

        :param location: the location to be checked
        :return: A ValidationCodes Enum value of either VERSION_INVALID or VALID
        :return: A message saying which WLS version location is valid in, if
                return code is VERSION_INVALID
        """
        return self._alias_entries.is_version_valid_location(location)

    def is_valid_model_folder_name(self, location, model_folder_name):
        """
        Return whether or not location's model folders list has a subfolder
        with the name assigned to the model_folder_name parameter.

        :param location: the location
        :param model_folder_name: the model folder name
        :return: ValidationCode, message
        :raises: AliasException: if an error occurred
        """
        _method_name = 'is_valid_model_folder_name'

        self._logger.entering(str(location), model_folder_name,
                              class_name=self._class_name, method_name=_method_name)
        result, valid_version_range = \
            self._alias_entries.is_valid_model_folder_name_for_location(location, model_folder_name)

        if result == ValidationCodes.VALID:
            message = exception_helper.get_message('WLSDPLY-08403', model_folder_name,
                                                   location.get_folder_path(), self._wls_version)
        elif result == ValidationCodes.INVALID:
            message = exception_helper.get_message('WLSDPLY-08404', model_folder_name,
                                                   location.get_folder_path(), self._wls_version)
        elif result == ValidationCodes.VERSION_INVALID:
            message = \
                VersionUtils.getValidFolderVersionRangeMessage(model_folder_name, location.get_folder_path(),
                                                               self._wls_version, valid_version_range,
                                                               WlstModes.from_value(self._wlst_mode))
        else:
            ex = exception_helper.create_alias_exception('WLSDPLY-08405', model_folder_name,
                                                         location.get_folder_path(), self._wls_version,
                                                         ValidationCodes.from_value(result))
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result, message

    ###########################################################################
    #                  Model attribute-related methods                        #
    ###########################################################################

    def get_model_password_type_attribute_names(self, location):
        """
        Get the attributes in the current location whose types are passwords.
        :param location: the location
        :return: list of the attribute names
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_password_type_attribute_names'

        password_attribute_names = []
        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if WLST_TYPE in value and value[WLST_TYPE] == 'password':
                password_attribute_names.append(key)
        return password_attribute_names

    def get_model_restart_required_attribute_names(self, location):
        """
        :param location: Model folder name
        :return: list[string] Model attribute names at specified location
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_restart_required_attribute_names'

        restart_attribute_names = []

        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if RESTART_REQUIRED in value:
                restart_required_value = value[RESTART_REQUIRED]
                if "true" == restart_required_value.lower():
                    restart_attribute_names.append(key)

        return restart_attribute_names

    def get_model_get_required_attribute_names(self, location):
        """
        Get the list of attribute names that have their get_method specified as GET.
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_get_required_attribute_names'

        wlst_attribute_names = []

        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if GET_METHOD in value and value[GET_METHOD] == GET:
                wlst_attribute_names.append(key)

        return wlst_attribute_names

    def get_model_lsa_required_attribute_names(self, location):
        """
        Get the model attribute names that require the use of LSA to get the accurate value from WLST.
        :param location: the location
        :return: the list of attribute names
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_lsa_required_attribute_names'

        lsa_required_attribute_names = []

        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if GET_METHOD in value and LSA in value[GET_METHOD]:
                lsa_required_attribute_names.append(key)

        return lsa_required_attribute_names

    def get_model_get_returns_mbean_attribute_names_and_types(self, location):
        """
        Get the dictionary of attribute names and types that have their get_mbean_type specified.
        :param location: the location
        :return: dictionary: a dictionary with the attribute names as keys and the MBean types as values
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_get_returns_mbean_attribute_names_and_types'

        model_attribute_names = dict()

        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if GET_MBEAN_TYPE in value:
                model_attribute_names[key] = value[GET_MBEAN_TYPE]
            else:
                model_attribute_names[key] = None

        return model_attribute_names

    def get_model_mbean_set_method_attribute_names_and_types(self, location):
        """
        Get the list of model attribute names and types where the set method requires an MBean.
        :param location: the location
        :return: a dictionary keyed by model attribute names with the set_method and set_mbean_type fields set
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_mbean_set_method_attribute_names_and_types'

        model_attributes_dict = dict()

        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if SET_METHOD in value and value[SET_METHOD].startswith(MBEAN):
                attr_dict = dict()

                attr_set_method_name = None
                set_method_value_components = value[SET_METHOD].split('.')
                if len(set_method_value_components) == 2:
                    attr_set_method_name = set_method_value_components[1]

                attr_dict[SET_METHOD] = attr_set_method_name
                if SET_MBEAN_TYPE in value:
                    attr_dict[SET_MBEAN_TYPE] = value[SET_MBEAN_TYPE]
                else:
                    attr_dict[SET_MBEAN_TYPE] = None

                model_attributes_dict[key] = attr_dict

        return model_attributes_dict

    def get_model_merge_required_attribute_names(self, location):
        """
        Get the list of attribute names where merging the new and old values is required.
        :param location: the location
        :return: a list of the model attribute names
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_merge_required_attribute_names'

        model_attribute_names = list()

        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if WLST_TYPE in value and (value[WLST_TYPE] in ALIAS_LIST_TYPES or value[WLST_TYPE] in ALIAS_MAP_TYPES):
                merge = True
                if MERGE in value:
                    merge = alias_utils.convert_boolean(value[MERGE])
                if merge:
                    model_attribute_names.append(key)

        return model_attribute_names

    def get_model_password_attribute_names(self, location):
        """
        Get the list of attribute names for the current location that are marked as password.
        :param location: current location context
        :return: list of password attributes
        """
        _method_name = 'get_model_password_attribute_names'

        model_attribute_names = list()
        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if WLST_TYPE in value and value[WLST_TYPE] == PASSWORD:
                model_attribute_names.append(key)

        return model_attribute_names

    def get_model_uses_path_tokens_attribute_names(self, location):
        """
        Get the list of attribute names that "use path tokens" (i.e., ones whose values are file system paths).
        :param location: the location
        :return: a list of the model attribute names
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_uses_path_tokens_attribute_names'

        model_attribute_names = list()
        module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if USES_PATH_TOKENS in value and alias_utils.convert_boolean(value[USES_PATH_TOKENS]):
                model_attribute_names.append(key)

        return model_attribute_names

    def get_model_attribute_name_and_value(self, location, wlst_attribute_name, wlst_attribute_value):
        """
        Returns the model attribute name and value for the specified WLST attribute name and value.

        model_attribute_value will be set to None, if value assigned to wlst_attribute_value arg
        is the default value for model_attribute_name.
        :param location: the location
        :param wlst_attribute_name: the WLST attribute name
        :param wlst_attribute_value: the WLST attribute value
        :return: the name and value
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_attribute_name_and_value'

        self._logger.entering(str(location), wlst_attribute_name, wlst_attribute_value,
                              class_name=self._class_name, method_name=_method_name)
        model_attribute_name = None
        # Assume wlst_attribute_value is the same as default value of model_attribute_name
        model_attribute_value = None

        attribute_info = self._alias_entries.get_alias_attribute_entry_by_wlst_name(location, wlst_attribute_name)
        if attribute_info is not None and not self.__is_model_attribute_read_only(location, attribute_info):
            data_type, preferred_type, delimiter = \
                alias_utils.compute_read_data_type_for_wlst_and_delimiter_from_attribute_info(attribute_info,
                                                                                              wlst_attribute_value)
            model_type = data_type
            if preferred_type:
                model_type = preferred_type

            converted_value = alias_utils.convert_to_model_type(model_type, wlst_attribute_value, delimiter=delimiter)

            model_attribute_name = attribute_info[MODEL_NAME]
            default_value = attribute_info[VALUE][DEFAULT]

            #
            # The logic below to compare the str() representation of the converted value and the default value
            # only works for lists/maps if both the converted value and the default value are the same data type...
            #
            if (model_type in ALIAS_LIST_TYPES or model_type in ALIAS_MAP_TYPES) \
                    and not (default_value == '[]' or default_value == 'None'):
                # always the model delimiter
                default_value = alias_utils.convert_to_type(model_type, default_value, delimiter=MODEL_LIST_DELIMITER)

            if model_type == 'password':
                if string_utils.is_empty(wlst_attribute_value) or converted_value == default_value:
                    model_attribute_value = None
                else:
                    model_attribute_value = PASSWORD_TOKEN

            elif model_type == 'boolean':
                wlst_val = alias_utils.convert_boolean(converted_value)
                default_val = alias_utils.convert_boolean(default_value)
                if wlst_val == default_val:
                    model_attribute_value = None
                else:
                    model_attribute_value = converted_value

            elif (model_type in ALIAS_LIST_TYPES or data_type in ALIAS_MAP_TYPES) and \
                    (converted_value is None or len(converted_value) == 0):
                if default_value == '[]' or default_value == 'None':
                    model_attribute_value = None

            elif str(converted_value) != str(default_value):
                if _strings_are_empty(converted_value, default_value):
                    model_attribute_value = None
                else:
                    model_attribute_value = converted_value
                    if self._model_context and USES_PATH_TOKENS in attribute_info:
                        model_attribute_value = self._model_context.tokenize_path(model_attribute_value)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name,
                             result={model_attribute_name: model_attribute_value})
        return model_attribute_name, model_attribute_value

    def get_model_attribute_name(self, location, wlst_attribute_name, check_read_only=True):
        """
        Returns the model attribute name for the specified WLST attribute name and value. If the model attribute name
        is not valid for the version or the attribute is marked as read-only, return None

        :param location: the location
        :param wlst_attribute_name: the WLST attribute name
        :param check_read_only: Defaults to True. If False, return the WLST attribute name even if read only
        :return: matching model attribute name
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_attribute_name'

        self._logger.entering(str(location), wlst_attribute_name,
                              class_name=self._class_name, method_name=_method_name)
        model_attribute_name = None

        attribute_info = self._alias_entries.get_alias_attribute_entry_by_wlst_name(location, wlst_attribute_name)
        if attribute_info is not None and \
                (not check_read_only or not self.__is_model_attribute_read_only(location, attribute_info)):
            model_attribute_name = attribute_info[MODEL_NAME]

        self._logger.exiting(class_name=self._class_name, method_name=_method_name,
                             result=model_attribute_name)
        return model_attribute_name

    def get_model_attribute_names(self, location):
        """
        Returns the model attribute names for the specified location.
        :param location: the location
        :return: the list of model attribute names
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_attribute_names'

        self._logger.entering(str(location), class_name=self._class_name, method_name=_method_name)
        attributes_dict = self._alias_entries.get_alias_attribute_entries_by_location(location)
        result = list(attributes_dict.keys())
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_model_attribute_names_and_types(self, location):
        """
        Returns the model attribute name and type for the specified location.
        :param location: the location
        :return: a dictionary keyed on model attribute names with the type as the value
        :raises: AliasException: if an error occurs
        """
        _method_name = 'get_model_attribute_names_and_types'

        self._logger.entering(str(location), class_name=self._class_name, method_name=_method_name)
        result = {}
        attributes_dict = self._alias_entries.get_alias_attribute_entries_by_location(location)
        for key, value in attributes_dict.iteritems():
            if PREFERRED_MODEL_TYPE in value:
                result[key] = value[PREFERRED_MODEL_TYPE]
            elif WLST_TYPE in value:
                result[key] = value[WLST_TYPE]
            else:
                result[key] = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_model_domain_info_attribute_names_and_types(self):
        """
        Get the attribute names and types for the domainInfo section of the model
        :return: a dictionary keyed on model attribute names with the type as the value
        """
        return self._alias_entries.get_domain_info_attribute_names_and_types()

    def attribute_values_are_equal(self, location, model_attribute_name, model_attribute_value, wlst_attribute_value):
        """
        Returns whether or not the model and WLST values for a given model attribute,
        should be considered equal.

        :param location:
        :param model_attribute_name:
        :param model_attribute_value:
        :param wlst_attribute_value:
        :return: boolean
        :raises: AliasException: if an error occurs
        """

        _method_name = 'attribute_values_are_equal'

        result = False

        module_folder = self._alias_entries.get_dictionary_for_location(location)

        if ATTRIBUTES not in module_folder:
            ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        for key, value in module_folder[ATTRIBUTES].iteritems():
            if key == model_attribute_name:
                attribute_info = module_folder[ATTRIBUTES][key]
                if attribute_info and VALUE in attribute_info and DEFAULT in attribute_info[VALUE]:
                    result = (model_attribute_value == wlst_attribute_value and
                              model_attribute_value == attribute_info[VALUE][DEFAULT])

        return result

    def is_valid_model_attribute_name(self, location, model_attribute_name):
        """
        Return whether or not location's model folders list has an attribute
        with the name assigned to the model_attribute_name parameter.

        If so, it returns True and a message stating that value assigned to
        model_attribute_name parameter is supported in the specified WLST
        version. Otherwise, it returns False and a message stating which, if
        any, WLST version(s) the value assigned to the model_attribute_name
        parameter is supported in.

        :param location: the location
        :param model_attribute_name: the model attribute name
        :return: ValidationCode, message
        :raises: AliasException: if an error occurred
        """
        _method_name = 'is_wlst_version_model_attribute_name'

        self._logger.entering(str(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)
        result, valid_version_range = \
            self._alias_entries.is_valid_model_attribute_name_for_location(location, model_attribute_name)

        path = self.get_model_folder_path(location)
        if result == ValidationCodes.VALID:
            message = exception_helper.get_message('WLSDPLY-08407', model_attribute_name, path, self._wls_version)
        elif result == ValidationCodes.INVALID:
            message = exception_helper.get_message('WLSDPLY-08408', model_attribute_name, path, self._wls_version)
        elif result == ValidationCodes.VERSION_INVALID:
            message = \
                VersionUtils.getValidAttributeVersionRangeMessage(model_attribute_name, path,
                                                                  self._wls_version, valid_version_range,
                                                                  WlstModes.from_value(self._wlst_mode))
        else:
            ex = exception_helper.create_alias_exception('WLSDPLY-08405', model_attribute_name, path, self._wls_version,
                                                         ValidationCodes.from_value(result))
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result, message

    def get_model_attribute_default_value(self, location, model_attribute_name):
        """
        Get the default value for the specified attribute
        :param location: the location
        :param model_attribute_name: the model attribute name
        :return: the default value converted to the type
        :raises: AliasException: if an error occurred
        """
        _method_name = 'get_model_attribute_default_value'

        self._logger.entering(str(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)
        default_value = None
        attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
        if attribute_info is not None:
            default_value = attribute_info[VALUE][DEFAULT]
            if default_value == 'None':
                default_value = None
            else:
                data_type, delimiter = \
                    alias_utils.compute_read_data_type_and_delimiter_from_attribute_info(attribute_info, default_value)

                default_value = alias_utils.convert_to_type(data_type, default_value, delimiter=delimiter)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=default_value)
        return default_value

    def get_model_attribute_type(self, location, model_attribute_name):
        """
        Get the wlst_type for the model attribute name at the specified location
        :param location:
        :param model_attribute_name:
        :return:
        """
        wlst_type = None
        attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
        if attribute_info is not None:
            wlst_type = attribute_info[WLST_TYPE]
        return wlst_type

    def get_ignore_attribute_names(self):
        """
        Return the list of attribute names that are ignored by the aliases and not defined in the alias category
        json files.
        :return: list of ignored attribute
        """
        return self._alias_entries.IGNORE_FOR_MODEL_LIST

    def decrypt_password(self, text):
        """
        Encrypt the specified password if encryption is used and the password is encrypted.
        :param text: the text to check and decrypt, if needed
        :return: the clear text
        :raises EncryptionException: if an error occurs while decrypting the password
        """
        if text is None or len(str(text)) == 0 or \
                (self._model_context and not self._model_context.is_using_encryption()) or \
                not EncryptionUtils.isEncryptedString(text):

            rtnval = text
        else:
            passphrase = self._model_context.get_encryption_passphrase()
            rtnval = EncryptionUtils.decryptString(text, String(passphrase).toCharArray())
            if rtnval:
                rtnval = String.valueOf(rtnval)

        return rtnval

    ####################################################################################
    #
    # Private methods, private inner classes and static methods only, beyond here please
    #
    ####################################################################################

    def __is_model_attribute_read_only(self, location, attribute_info):
        """
        Is the model attribute read-only?
        :param location: the location
        :param attribute_info: the attribute tuple
        :return: True if the attribute is read-only, False otherwise
        """
        _method_name = '__is_model_attribute_read_only'
        rtnval = False
        if ACCESS in attribute_info and attribute_info[ACCESS] in ('RO', 'VO'):
            self._logger.finer('WLSDPLY-08409', attribute_info[MODEL_NAME], location.get_folder_path(),
                               WlstModes.from_value(self._wlst_mode),
                               class_name=self._class_name, method_name=_method_name)
            rtnval = True

        return rtnval


def _strings_are_empty(converted_value, default_value):
    """
    Test converted and default values to see if they are both either None or an empty string
    :param converted_value: the converted value
    :param default_value: the default value
    :return:
    """
    if type(converted_value) is str:
        str_converted_value = converted_value
    else:
        str_converted_value = str(converted_value)

    if type(default_value) is str:
        str_default_value = default_value
    else:
        str_default_value = str(default_value)

    if str_default_value == 'None':
        str_default_value = None

    return string_utils.is_empty(str_converted_value) and string_utils.is_empty(str_default_value)
