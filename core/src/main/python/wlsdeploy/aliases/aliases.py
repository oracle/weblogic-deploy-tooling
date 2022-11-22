"""
Copyright (c) 2017, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import String
from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.aliases import TypeUtils
from oracle.weblogic.deploy.aliases import VersionUtils
from oracle.weblogic.deploy.encrypt import EncryptionException
from oracle.weblogic.deploy.encrypt import EncryptionUtils

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases import password_utils
from wlsdeploy.aliases.alias_constants import ACCESS
from wlsdeploy.aliases.alias_constants import ALIAS_LIST_TYPES
from wlsdeploy.aliases.alias_constants import ALIAS_MAP_TYPES
from wlsdeploy.aliases.alias_constants import ATTRIBUTES
from wlsdeploy.aliases.alias_constants import ChildFoldersTypes
from wlsdeploy.aliases.alias_constants import DEFAULT_VALUE
from wlsdeploy.aliases.alias_constants import DERIVED_DEFAULT
from wlsdeploy.aliases.alias_constants import FLATTENED_FOLDER_DATA
from wlsdeploy.aliases.alias_constants import FOLDERS
from wlsdeploy.aliases.alias_constants import GET
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
from wlsdeploy.aliases.alias_constants import RO
from wlsdeploy.aliases.alias_constants import ROD
from wlsdeploy.aliases.alias_constants import SET_MBEAN_TYPE
from wlsdeploy.aliases.alias_constants import SET_METHOD
from wlsdeploy.aliases.alias_constants import STRING
from wlsdeploy.aliases.alias_constants import USES_PATH_TOKENS
from wlsdeploy.aliases.alias_constants import WLST_NAME
from wlsdeploy.aliases.alias_constants import WLST_READ_TYPE
from wlsdeploy.aliases.alias_constants import WLST_TYPE
from wlsdeploy.aliases.alias_entries import AliasEntries
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import string_utils
from wlsdeploy.util import unicode_helper as str_helper


class Aliases(object):
    """
    The public interface into the aliases subsystem that abstracts out the WLST knowledge base from the
    rest of the tooling.
    """
    _class_name = 'Aliases'

    def __init__(self, model_context, wlst_mode=WlstModes.OFFLINE, wls_version=None,
                 exception_type=ExceptionType.ALIAS):
        """
        Create an Aliases instance with the specified arguments.
        :param model_context: used for tokenizing and encryption
        :param wlst_mode: offline or online, default is offline
        :param wls_version: the WLS version to use, default is to Oracle Home version
        :param exception_type: the exception type to be thrown
        """
        self._model_context = model_context
        self._wlst_mode = wlst_mode
        self._exception_type = exception_type
        self._logger = PlatformLogger('wlsdeploy.aliases')

        if wls_version is None:
            self._wls_version = self._model_context.get_target_wls_version()
        else:
            self._wls_version = wls_version

        self._alias_entries = AliasEntries(wlst_mode, self._wls_version)

    ###########################################################################
    #              Model folder navigation-related methods                    #
    ###########################################################################

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

    def get_model_section_top_level_folder_names(self, section_name):
        """
        Returns a list of the recognized top-level model folders in the specified section corresponding to the
        known WLST top-level folders.
        :return: a list of the recognized top-level model folder names
        """
        return self._alias_entries.get_model_section_subfolder_names(section_name)

    def get_model_section_attribute_location(self, section_name):
        """
        Get the location containing the attributes for a model section (topology, domainInfo, etc.)
        :return: a location, or None of the section does not have attributes.
        """
        return self._alias_entries.get_model_section_attribute_location(section_name)

    def get_model_subfolder_names(self, location):
        """
        Get the list of model folder names for subfolders of the specified location.
        :param location: the location
        :return: list[string]: the list of model subfolder names or an empty list if there are none
        :raises: Tool type exception: if an error occurs while getting or processing the folders for the specified
                                      location
        """
        _method_name = 'get_model_subfolder_names'

        try:
            return self._alias_entries.get_model_subfolder_names_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19000', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_name_token(self, location):
        """
        Get the name token for the specified location.
        :param location: the location
        :return: the name token or None, if no new name token is required
        :raises: Tool type exception: if an error occurs while getting the name for the specified location
        """
        _method_name = 'get_name_token'
        try:
            return self._alias_entries.get_name_token_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19001', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_model_folder_path(self, location):
        """
        Get a slash delimited string of the path in the model to the specified location.
        :param location: the location
        :return: the model path string
        :raises Tool type exception: if an error occurs while getting the path for the specified location
        """
        _method_name = 'get_model_folder_path'
        try:
            return self._alias_entries.get_model_folder_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19002', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_folder_short_name(self, location):
        """
        Return the short name for the folder at the provided location or an empty
        string if the short name is not defined for the folder in the alias
        definition.
        :param location: location context for the folder
        :return: short name or empty string if not found
        """
        return self._alias_entries.get_folder_short_name_for_location(location)

    def get_online_bean_name(self, location):
        """
        Get the online bean name for the specified location
        :param location: the location to use
        :return: the online bean name
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        return self._alias_entries.get_online_bean_name_for_location(location)

    ###########################################################################
    #                      WLST Path-related methods                          #
    ###########################################################################

    def get_wlst_attributes_path(self, location):
        """
        Get the WLST path where the attributes for the specified location are found.
        :return: the WLST path
        :raises Tool type exception: if the location is missing required name tokens or
                                     the alias data for the location is bad
        """
        _method_name = 'get_wlst_attributes_path'
        try:
            return self._alias_entries.get_wlst_attribute_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19003', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_subfolders_path(self, location):
        """
        Get the WLST path where the subfolders for the specified location are found.
        :param location: the location to use
        :return: the WLST path
        :raises Tool type exception: if the location is missing required name tokens or
                                     the alias data for the location is bad
        """
        _method_name = 'get_wlst_subfolders_path'
        try:
            return self._alias_entries.get_wlst_subfolders_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19004', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_list_path(self, location):
        """
        Get the WLST path where to list the existing instances of the type corresponding to the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises Tool type exception: if the location is missing required name tokens or
                                     the alias data for the location is bad
        """
        _method_name = 'get_wlst_list_path'
        try:
            return self._alias_entries.get_wlst_list_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19005', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_create_path(self, location):
        """
        Get the WLST path where to create new instances of the type corresponding to the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises Tool type exception: if the location is missing required name tokens or
                                     the alias data for the location is bad
        """
        _method_name = 'get_wlst_create_path'
        try:
            return self._alias_entries.get_wlst_create_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19006', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_flattened_folder_list_path(self, location):
        """
        Get the WLST path where to list the existing instances of the flattened type corresponding to
        the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises Tool type exception: if the location is missing required name tokens or
                                     the alias data for the location is bad
        """
        _method_name = 'get_wlst_flattened_folder_list_path'
        try:
            return self._alias_entries.get_wlst_flattened_folder_list_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19007', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_flattened_folder_create_path(self, location):
        """
        Get the WLST path where to create new instances of the flattened type corresponding to the specified location.
        :param location: the location to use
        :return: the WLST path
        :raises Tool type exception: if the location is missing required name tokens or
                                     the alias data for the location is bad
        """
        _method_name = 'get_wlst_flattened_folder_create_path'
        try:
            return self._alias_entries.get_wlst_flattened_folder_create_path_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19007', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    ###########################################################################
    #                    Child folder-related methods                         #
    ###########################################################################

    def requires_unpredictable_single_name_handling(self, location):
        """
        Does the location folder specified require unpredicatable single name handling?
        :param location: the location
        :return: True, if the location requires unpredicatable single name handling, False otherwise
        :raises: Tool type exception: if an error occurs while getting the folder for the location or if the
                                      specified type doesn't match and the actual type is 'none'
        """
        _method_name = 'requires_unpredictable_single_name_handling'

        try:
            return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.SINGLE)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19021', location.get_current_model_folder(),
                                  location.get_folder_path(), ae.getLocalizedMessage())

    def supports_multiple_mbean_instances(self, location):
        """
        Does the location folder specified support multiple MBean instances of the parent node type?
        :param location: the location
        :return: True, if the location supports multiple named child nodes, False otherwise
        :raises: Tool type exception: if an error occurs while getting the folder for the location or if the
                                      specified type doesn't match and the actual type is 'none'
        """
        _method_name = 'supports_multiple_mbean_instances'

        try:
            return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.MULTIPLE)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19008', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_subfolders_in_order(self, location):
        """
        Return the sub-folder names that have an order in the order defined.
        :param location: location of the ordered sub-folders
        :return: list of sub-folder names in order
        """
        _method_name = 'get_subfolders_in_order'
        try:
            return self._alias_entries.get_folders_in_order_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19044',
                                  location.get_folder_path(), ae.getLocalizedMessage())

    def requires_artificial_type_subfolder_handling(self, location):
        """
        Does the location folder specified both support multiple MBean instances of the parent node type
        and require the use of a subtype, defined by an contained subfolder, to create the MBeans?
        :param location: the location
        :return: True, if so, False otherwise
        :raises: Tool type exception: if an error occurs while getting the folder for the location or if the
                                      specified type doesn't match and the actual type is 'none'
        """
        _method_name = 'requires_artificial_type_subfolder_handling'

        try:
            return self._alias_entries.is_location_child_folder_type(location,
                                                                     ChildFoldersTypes.MULTIPLE_WITH_TYPE_SUBFOLDER)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19024', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def is_artificial_type_folder(self, location):
        """
        Is the location folder specified an artificial subtype folder?
        :param location: the location
        :return: True, if so, False otherwise
        :raises: Tool type exception: if an error occurs while getting the folder for the location
        """
        _method_name = 'is_artificial_type_folder'

        try:
            return self._alias_entries.is_location_child_folder_type(location, ChildFoldersTypes.NONE)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19026', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def is_custom_folder_allowed(self, location):
        """
        Returns true if the specified location allows custom, user-defined folder types.
        This currently corresponds to all MULTIPLE_WITH_TYPE_SUBFOLDER entries.
        This will need to be refined if new custom types are added, or additional distinctions are required.
        :param location: the location to be checked
        :return: True if the location allows custom folder types, False otherwise
        :raises: Tool type exception: if an error occurs while getting the folder for the location
        """
        _method_name = 'is_custom_folder_allowed'

        try:
            return self._alias_entries.is_location_child_folder_type(location,
                                                                     ChildFoldersTypes.MULTIPLE_WITH_TYPE_SUBFOLDER)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19035', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def is_security_provider_type(self, location):
        """
        Returns true if the specified location is a security provider type, such as AuthenticationProvider.
        This currently corresponds to all MULTIPLE_WITH_TYPE_SUBFOLDER entries.
        This will need to be refined if new custom types are added, or additional distinctions are required.
        :param location: the location to be checked
        :return: True if the location is a security provider type, False otherwise
        :raises: Tool type exception: if an error occurs while getting the folder for the location
        """
        _method_name = 'is_security_provider_type'

        try:
            return self._alias_entries.is_location_child_folder_type(location,
                                                                     ChildFoldersTypes.MULTIPLE_WITH_TYPE_SUBFOLDER)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19036', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    ###########################################################################
    #                     WLST Folder create-related methods                  #
    ###########################################################################

    def get_wlst_mbean_name(self, location):
        """
        Get the WLST MBean name for the specified location
        :param location: the location to use
        :return: the WLST MBean name
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_mbean_name'

        try:
            return self._alias_entries.get_wlst_mbean_name_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19009', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_mbean_type(self, location):
        """
        Get the WLST MBean type for the specified location
        :param location: the location to use
        :return: the WLST MBean type
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_mbean_type'

        try:
            return self._alias_entries.get_wlst_mbean_type_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19010', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_wlst_flattened_folder_info(self, location):
        """
        Get the information used to create the flattened folder.
        :param location: the location
        :return: a FlattenedFolder object, or None if the location does not have a flattened folder
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_flattened_mbean_info'

        try:
            return self._alias_entries.get_wlst_flattened_folder_info_for_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19013', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    ###########################################################################
    #                   WLST attribute-related methods                        #
    ###########################################################################

    def get_wlst_attribute_name_and_value(self, location, model_attribute_name, model_attribute_value,
                                          existing_wlst_value=None, masked=False):
        """
        Returns the WLST attribute name and value for the specified model attribute name and value.

        wlst_attribute_value should return the correct type and value, even if the value
        is the default value for model_attribute_name.
        :param location: the location to use
        :param model_attribute_name: string
        :param model_attribute_value: value of the appropriate type
        :param existing_wlst_value: existing value of the appropriate type
        :param masked: if True, attribute value will be hidden in logging
        :return: the WLST name and value (which may be None)
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_attribute_name_and_value'

        try:
            wlst_attribute_name = None
            wlst_attribute_value = None

            module_folder = self._alias_entries.get_dictionary_for_location(location)
            if not module_folder:
                self._logger.fine('WLSDPLY-08410', location.get_current_model_folder(),
                                  location.get_parent_folder_path(), WlstModes.from_value(self._wlst_mode),
                                  self._wls_version)
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

            if attribute_info and not self.__is_wlst_attribute_read_only(location, attribute_info):
                wlst_attribute_name = attribute_info[WLST_NAME]
                uses_path_tokens = USES_PATH_TOKENS in attribute_info and \
                    string_utils.to_boolean(attribute_info[USES_PATH_TOKENS])

                data_type = attribute_info[WLST_TYPE]
                if data_type == 'password':
                    try:
                        wlst_attribute_value = self.decrypt_password(model_attribute_value)

                        # the attribute name may change for special cases, check against decrypted value
                        password_attribute_name = \
                            password_utils.get_wlst_attribute_name(attribute_info, wlst_attribute_value,
                                                                   self._wlst_mode)

                        if password_attribute_name is not None:
                            wlst_attribute_name = password_attribute_name

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
                        elif merge:
                            model_val = alias_utils.convert_to_type(LIST, model_attribute_value,
                                                                    delimiter=MODEL_LIST_DELIMITER)

                            if uses_path_tokens and model_val is not None:
                                for index, item in enumerate(model_val):
                                    item_value = self._model_context.replace_token_string(str_helper.to_string(item))
                                    model_val[index] = item_value

                            _read_type, read_delimiter = \
                                alias_utils.compute_read_data_type_and_delimiter_from_attribute_info(
                                    attribute_info, existing_wlst_value)

                            existing_val = alias_utils.convert_to_type(LIST, existing_wlst_value,
                                                                       delimiter=read_delimiter)
                            location_path = self.get_model_folder_path(location)
                            merged_value = \
                                alias_utils.merge_model_and_existing_lists(model_val, existing_val,
                                                                           location_path=location_path,
                                                                           attribute_name=model_attribute_name)
                        else:
                            merged_value = model_attribute_value

                        if data_type == JARRAY:
                            subtype = 'java.lang.String'
                            if SET_MBEAN_TYPE in attribute_info:
                                subtype = attribute_info[SET_MBEAN_TYPE]
                            wlst_attribute_value = \
                                alias_utils.convert_to_type(data_type, merged_value, subtype=subtype,
                                                            delimiter=MODEL_LIST_DELIMITER)
                        else:
                            wlst_attribute_value = alias_utils.convert_to_type(data_type, merged_value,
                                                                               delimiter=MODEL_LIST_DELIMITER)
                    else:
                        if uses_path_tokens:
                            model_attribute_value = self._model_context.replace_token_string(model_attribute_value)

                        wlst_attribute_value = alias_utils.convert_to_type(data_type, model_attribute_value,
                                                                           delimiter=MODEL_LIST_DELIMITER)

            return wlst_attribute_name, wlst_attribute_value
        except AliasException, ae:
            value = model_attribute_value
            if masked:
                value = '<masked>'

            self._raise_exception(ae, _method_name, 'WLSDPLY-19014', model_attribute_name, value,
                                  str_helper.to_string(location), ae.getLocalizedMessage())

    def get_wlst_attribute_name(self, location, model_attribute_name, check_read_only=True):
        """
        Returns the WLST attribute name and value for the specified model attribute name and value.

        wlst_attribute_value should return the correct type and value, even if the value
        is the default value for model_attribute_name.
        :param location:
        :param model_attribute_name:
        :param check_read_only: Defaults to True. If false, return name even if alias definition is read only
        :return: the WLST attribute name or None, if it is not relevant
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_attribute_name'
        self._logger.entering(str_helper.to_string(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)

        try:
            wlst_attribute_name = None
            alias_attr_dict = \
                self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)

            if alias_attr_dict is not None and (not check_read_only or not
                                                self.__is_wlst_attribute_read_only(location, alias_attr_dict)):
                if WLST_NAME in alias_attr_dict:
                    wlst_attribute_name = alias_attr_dict[WLST_NAME]
                else:
                    ex = exception_helper.create_alias_exception('WLSDPLY-07108', model_attribute_name, location,
                                                                 WLST_NAME)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

            return wlst_attribute_name
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19015', model_attribute_name,
                                  str_helper.to_string(location), ae.getLocalizedMessage())

    def get_wlst_get_required_attribute_names(self, location):
        """
        Get the list of attribute names that have their get_method specified as GET.
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_get_required_attribute_names'

        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19020', location.get_current_model_folder(),
                                  location.get_folder_path(), ae.getLocalizedMessage())

    def get_wlst_access_rod_attribute_names(self, location):
        """
        Get the list of attribute names that have their ACCESS type set to ROD (readonly but discover)
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_wlst_access_rod_attribute_names'

        try:
            wlst_attribute_names = []

            module_folder = self._alias_entries.get_dictionary_for_location(location)

            if ATTRIBUTES not in module_folder:
                ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            for key, value in module_folder[ATTRIBUTES].iteritems():
                if ACCESS in value and value[ACCESS] == ROD:
                    wlst_attribute_names.append(value[WLST_NAME])

            return wlst_attribute_names
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19046', location.get_current_model_folder(),
                                  location.get_folder_path(), ae.getLocalizedMessage())
                                  
    ###########################################################################
    #                    Model folder-related methods                         #
    ###########################################################################

    def get_model_subfolder_name(self, location, wlst_subfolder_name):
        """
        Get the model folder name for the WLST subfolder name at the specified location.
        :param location: the location
        :param wlst_subfolder_name: the WLST folder name
        :return: the model folder name, or None if the folder is not needed for the model.
        :raises: Tool type exception: if an error occurs due to a bad location or bad alias data
        """
        _method_name = 'get_model_subfolder_name'
        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19022', wlst_subfolder_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())

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
        _method_name = 'is_version_valid_location'

        try:
            return self._alias_entries.is_version_valid_location(location)
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19033', location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def is_valid_model_folder_name(self, location, model_folder_name):
        """
        Return whether or not location's model folders list has a subfolder
        with the name assigned to the model_folder_name parameter.

        :param location: the location
        :param model_folder_name: the model folder name
        :return: ValidationCode, message
        :raises: Tool type exception: if an error occurred
        """
        _method_name = 'is_valid_model_folder_name'
        self._logger.entering(str_helper.to_string(location), model_folder_name,
                              class_name=self._class_name, method_name=_method_name)
        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19018', model_folder_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())

    ###########################################################################
    #                  Model attribute-related methods                        #
    ###########################################################################

    def get_model_password_type_attribute_names(self, location):
        """
        Get the attributes in the current location whose types are passwords.
        :param location: the location
        :return: list of the attribute names
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_password_type_attribute_names'

        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19016', location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_model_restart_required_attribute_names(self, location):
        """
        :param location: Model folder name
        :return: list[string] Model attribute names at specified location
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_restart_required_attribute_names'

        try:
            restart_attribute_names = []

            module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)

            if ATTRIBUTES not in module_folder:
                ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            for key, value in module_folder[ATTRIBUTES].iteritems():
                if RESTART_REQUIRED in value:
                    restart_required = alias_utils.convert_boolean(value[RESTART_REQUIRED])
                    if restart_required:
                        restart_attribute_names.append(key)

            return restart_attribute_names
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19023', location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_model_lsa_required_attribute_names(self, location):
        """
        Get the model attribute names that require the use of LSA to get the accurate value from WLST.
        :param location: the location
        :return: the list of attribute names
        :raises: Tool type exception: if an error occurs
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

    def model_mbean_has_set_mbean_type_attribute_name(self, location, model_name):
        """
        Determine if the attribute for model_name has the set_mbean type value.
        :param location: the location
        :param model_name: the attribute name
        :return: True if the attribute has the set method value
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'model_mbean_has_set_mbean_type_attribute_name'

        try:
            module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)
            if ATTRIBUTES not in module_folder:
                ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            set_mbean_type = False

            if model_name in module_folder[ATTRIBUTES] and \
                SET_MBEAN_TYPE in module_folder[ATTRIBUTES][model_name]:

                    set_mbean_type = True

            return set_mbean_type
        except AliasException, ae:

            self._raise_exception(ae, _method_name, 'WLSDPLY-19017', location.get_folder_path(),
                          ae.getLocalizedMessage())

    def get_model_mbean_set_method_attribute_names_and_types(self, location):
        """
        Get the list of model attribute names and types where the set method requires an MBean.
        :param location: the location
        :return: a dictionary keyed by model attribute names with the set_method and set_mbean_type fields set
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_mbean_set_method_attribute_names_and_types'

        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19017', location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_model_merge_required_attribute_names(self, location):
        """
        Get the list of attribute names where merging the new and old values is required.
        :param location: the location
        :return: a list of the model attribute names
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_merge_required_attribute_names'

        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19027', location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def is_model_password_attribute(self, location, model_name):
        """
        Determine if the attribute with the specified model_name is a password attribute.
        :param location: current location context
        :param model_name: specified model name to check if password
        :return: True if the wlst type is password
        """
        _method_name = 'is_model_password_attribute'

        try:
            is_password = False
            module_folder = self._alias_entries.get_dictionary_for_location(location, resolve=False)

            if ATTRIBUTES not in module_folder:
                ex = exception_helper.create_alias_exception('WLSDPLY-08400', location.get_folder_path())
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            if model_name in module_folder[ATTRIBUTES] and WLST_TYPE in module_folder[ATTRIBUTES][model_name] and \
                    module_folder[ATTRIBUTES][model_name][WLST_TYPE] == PASSWORD:
                is_password = True

            return is_password
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19040', model_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_model_uses_path_tokens_attribute_names(self, location):
        """
        Get the list of attribute names that "use path tokens" (i.e., ones whose values are file system paths).
        :param location: the location
        :return: a list of the model attribute names
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_uses_path_tokens_attribute_names'

        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19030', location.get_current_model_folder(),
                                  location.get_folder_path(), ae.getLocalizedMessage())

    def get_model_attribute_name_and_value(self, location, wlst_attribute_name, wlst_attribute_value):
        """
        Returns the model attribute name and value for the specified WLST attribute name and value.

        model_attribute_value will be set to None, if value assigned to wlst_attribute_value arg
        is the default value for model_attribute_name.
        :param location: the location
        :param wlst_attribute_name: the WLST attribute name
        :param wlst_attribute_value: the WLST attribute value
        :return: the name and value
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_attribute_name_and_value'
        self._logger.entering(str_helper.to_string(location), wlst_attribute_name, wlst_attribute_value,
                              class_name=self._class_name, method_name=_method_name)

        try:
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

                converted_value = alias_utils.convert_to_model_type(model_type, wlst_attribute_value,
                                                                    delimiter=delimiter)

                model_attribute_name = attribute_info[MODEL_NAME]
                default_value = attribute_info[DEFAULT_VALUE]

                #
                # The logic below to compare the str() representation of the converted value and the default value
                # only works for lists/maps if both the converted value and the default value are the same data type...
                #
                if (model_type in ALIAS_LIST_TYPES or model_type in ALIAS_MAP_TYPES) \
                        and not (default_value == '[]' or default_value is None):
                    # always the model delimiter
                    default_value = alias_utils.convert_to_type(model_type, default_value,
                                                                delimiter=MODEL_LIST_DELIMITER)

                if attribute_info[WLST_TYPE] == STRING and default_value:
                    default_value = alias_utils.replace_tokens_in_path(location, default_value)

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
                    if default_value == '[]' or default_value is None:
                        model_attribute_value = None

                elif self._model_context is not None and USES_PATH_TOKENS in attribute_info:
                    if attribute_info[WLST_TYPE] == STRING:
                        model_attribute_value = self._model_context.tokenize_path(converted_value)
                    else:
                        model_attribute_value = self._model_context.tokenize_classpath(converted_value)
                    if model_attribute_value == default_value:
                        model_attribute_value = None

                elif default_value is None:
                    model_attribute_value = converted_value

                elif str_helper.to_string(converted_value) != str_helper.to_string(default_value):
                    if _strings_are_empty(converted_value, default_value):
                        model_attribute_value = None
                    else:
                        model_attribute_value = converted_value

            self._logger.exiting(class_name=self._class_name, method_name=_method_name,
                                 result={model_attribute_name: model_attribute_value})
            return model_attribute_name, model_attribute_value

        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19028', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_model_attribute_name(self, location, wlst_attribute_name, check_read_only=True):
        """
        Returns the model attribute name for the specified WLST attribute name and value. If the model attribute name
        is not valid for the version or the attribute is marked as read-only, return None

        :param location: the location
        :param wlst_attribute_name: the WLST attribute name
        :param check_read_only: Defaults to True. If False, return the WLST attribute name even if read only
        :return: matching model attribute name
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_attribute_name'

        try:
            self._logger.entering(str_helper.to_string(location), wlst_attribute_name,
                                  class_name=self._class_name, method_name=_method_name)
            model_attribute_name = None

            attribute_info = self._alias_entries.get_alias_attribute_entry_by_wlst_name(location, wlst_attribute_name)
            if attribute_info is not None and \
                    (not check_read_only or not self.__is_model_attribute_read_only(location, attribute_info)):
                model_attribute_name = attribute_info[MODEL_NAME]

            self._logger.exiting(class_name=self._class_name, method_name=_method_name,
                                 result=model_attribute_name)
            return model_attribute_name
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19039', str_helper.to_string(location),
                                  ae.getLocalizedMessage())

    def get_model_attribute_names(self, location):
        """
        Returns the model attribute names for the specified location.
        :param location: the location
        :return: the list of model attribute names
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_attribute_names'
        self._logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)

        try:
            attributes_dict = self._alias_entries.get_alias_attribute_entries_by_location(location)
            result = list(attributes_dict.keys())
            self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
            return result
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19029', location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_model_attribute_names_and_types(self, location):
        """
        Returns the model attribute name and type for the specified location.
        :param location: the location
        :return: a dictionary keyed on model attribute names with the type as the value
        :raises: Tool type exception: if an error occurs
        """
        _method_name = 'get_model_attribute_names_and_types'
        self._logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)

        try:
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
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19019', location.get_folder_path(),
                                  ae.getLocalizedMessage())

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
        :raises: Tool type exception: if an error occurred
        """
        _method_name = 'is_valid_model_attribute_name'
        self._logger.entering(str_helper.to_string(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)

        try:
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
                ex = exception_helper.create_alias_exception('WLSDPLY-08405', model_attribute_name, path,
                                                             self._wls_version, ValidationCodes.from_value(result))
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

            self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
            return result, message
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19031', model_attribute_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_model_attribute_type(self, location, model_attribute_name):
        """
        Get the wlst_type for the model attribute name at the specified location
        :param location:
        :param model_attribute_name:
        :return: WLST attribute type
        """
        _method_name = 'get_model_attribute_type'
        wlst_type = None
        try:
            attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
            if attribute_info is not None:
                wlst_type = attribute_info[WLST_TYPE]
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19015', model_attribute_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())

        return wlst_type

    def get_model_attribute_default_value(self, location, model_attribute_name):
        """
        Get the default value for the specified attribute
        :param location: the location
        :param model_attribute_name: the model attribute name
        :return: the default value converted to the type
        :raises: Tool type exception: if an error occurred
        """
        _method_name = 'get_model_attribute_default_value'
        self._logger.entering(str_helper.to_string(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)
        try:
            default_value = None
            attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
            if attribute_info is not None:
                default_value = attribute_info[DEFAULT_VALUE]
                data_type, delimiter = \
                    alias_utils.compute_read_data_type_and_delimiter_from_attribute_info(
                        attribute_info, default_value)

                default_value = alias_utils.convert_to_type(data_type, default_value, delimiter=delimiter)
            self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=default_value)
            return default_value
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19032', model_attribute_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())

    def get_ignore_attribute_names(self):
        """
        Return the list of attribute names that are ignored by the aliases and not defined in the alias category
        json files.
        :return: list of ignored attribute
        """
        _method_name = 'get_ignore_attribute_names'
        names = self._alias_entries.IGNORE_FOR_MODEL_LIST
        self._logger.finest('WLSDPLY-19038', names, class_name=self._class_name, method_name=_method_name)
        return names

    def get_preferred_model_type(self, location, model_attribute_name):
        """
        Return the preferred model type, if present, for the alias attribute definition.
        :param location: current location context
        :param model_attribute_name: name of the attribute to look up in model representation
        :return: alias attribute preferred model type or None if not present or attribute not found
        :raises: Tool Exception if an AliasException encountered
        """
        _method_name = 'get_preferred_model_type'
        self._logger.entering(str_helper.to_string(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)

        result = None
        try:
            attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
            if attribute_info is not None and PREFERRED_MODEL_TYPE in attribute_info:
                result = attribute_info[PREFERRED_MODEL_TYPE]
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19042', model_attribute_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_wlst_read_type(self, location, model_attribute_name):
        """
        Return the aliases attribute WLST_READ_TYPE, which overrides the WLST_TYPE when retrieving the attribute value.
        :param location: The context for the current location in WLST
        :param model_attribute_name: the model name for the WLST attribute
        :return: WLST_READ_TYPE or None if not defined for the attribute in the alias definitions
        :raises: Tool Exception when AliasException occurs retrieving read type
        """
        _method_name = 'get_wlst_read_type'
        self._logger.entering(str_helper.to_string(location), model_attribute_name,
                              class_name=self._class_name, method_name=_method_name)

        result = None
        try:
            attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute_name)
            if attribute_info is not None and WLST_READ_TYPE in attribute_info:
                result = attribute_info[WLST_READ_TYPE]
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19043', model_attribute_name, location.get_folder_path(),
                                  ae.getLocalizedMessage())
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def decrypt_password(self, text):
        """
        Decrypt the specified password if model encryption is used and the password is encrypted.
        :param text: the text to check and decrypt, if needed
        :return: the clear text
        :raises EncryptionException: if an error occurs while decrypting the password
        """
        if text is None or len(str_helper.to_string(text)) == 0 or \
                (self._model_context and not self._model_context.is_using_encryption()) or \
                not EncryptionUtils.isEncryptedString(text):

            rtnval = text
        else:
            passphrase = self._model_context.get_encryption_passphrase()
            rtnval = EncryptionUtils.decryptString(text, String(passphrase).toCharArray())
            if rtnval:
                rtnval = String.valueOf(rtnval)

        return rtnval

    def is_derived_default(self, location, model_attribute):
        """
        Return whether the default is derived by WLST.
        :param location: current location
        :param model_attribute: model name of attribute to check
        :return: True if the default is derived, False otherwise
        """
        _method_name = "is_derived_default"
        self._logger.entering(model_attribute, class_name=self._class_name, method_name=_method_name)

        result = False
        try:
            attribute_info = self._alias_entries.get_alias_attribute_entry_by_model_name(location, model_attribute)
            if attribute_info is not None and DERIVED_DEFAULT in attribute_info:
                result = attribute_info[DERIVED_DEFAULT]
                if result is None:
                    result = False
                elif isinstance(result, basestring):
                    if result == 'true':
                        result = True
                    else:
                        result = False
        except AliasException, ae:
            self._raise_exception(ae, _method_name, 'WLSDPLY-19045', model_attribute, location.get_folder_path(),
                                  ae.getLocalizedMessage())

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    ###########################################################################
    #                          Convenience Methods                            #
    ###########################################################################

    def get_exception_type(self):
        """
        Get the exception type for this Aliases instance.
        :return: the exception type
        """
        return self._exception_type

    def get_wlst_mbean_type_and_name(self, location):
        """
        Get the MBean type and name from the specified location.
        :param location: the location
        :return: the WLST type and name that should be used to create new MBean instances
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        type_name = self.get_wlst_mbean_type(location)
        if type_name is not None:
            value = self.get_wlst_mbean_name(location)
        else:
            value = None
        return type_name, value

    def get_model_type_and_name(self, location):
        """
        Get the location type and name.
        :param location: the location
        :return: type and name
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        folders = location.get_model_folders()
        if len(folders) == 0:
            return None, None

        key = folders[-1]

        name = None
        if self.supports_multiple_mbean_instances(location):
            token = self.get_name_token(location)
            if token is not None:
                name = location.get_name_for_token(token)

        return key, name

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
        if ACCESS in attribute_info and attribute_info[ACCESS] == RO:
            self._logger.finer('WLSDPLY-08409', attribute_info[MODEL_NAME], location.get_folder_path(),
                               WlstModes.from_value(self._wlst_mode),
                               class_name=self._class_name, method_name=_method_name)
            rtnval = True

        return rtnval

    def __is_wlst_attribute_read_only(self, location, attribute_info):
        """
        Is the wlst attribute read-only?
        :param location: the location
        :param attribute_info: the attribute tuple
        :return: True if the attribute is read-only, False otherwise
        """
        _method_name = '__is_wlst_attribute_read_only'
        rtnval = False
        if ACCESS in attribute_info and attribute_info[ACCESS] in (RO, ROD):
            self._logger.finer('WLSDPLY-08411', attribute_info[MODEL_NAME], location.get_folder_path(),
                               WlstModes.from_value(self._wlst_mode),
                               class_name=self._class_name, method_name=_method_name)
            rtnval = True

        return rtnval

    def _raise_exception(self, error, method_name, message_key, *args):
        """
        Throw an exception matching the declared tool type, after logging the exception.
        :param error: the error being raised
        :param method_name: the method name of the caller
        :param message_key: the key of the message
        :param args: arguments for the message
        """
        ex = exception_helper.create_exception(self._exception_type, message_key, error=error, *args)
        self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
        raise ex


def _convert_to_string(value):
    if type(value) in [str, unicode]:
        str_converted_value = value
    else:
        str_converted_value = str_helper.to_string(value)
    return str_converted_value


def _strings_are_empty(converted_value, default_value):
    """
    Test converted and default values to see if they are both either None or an empty string
    :param converted_value: the converted value
    :param default_value: the default value
    :return:
    """
    str_converted_value = _convert_to_string(converted_value)
    str_default_value = _convert_to_string(default_value)

    if str_default_value == 'None':
        str_default_value = None

    return string_utils.is_empty(str_converted_value) and string_utils.is_empty(str_default_value)
