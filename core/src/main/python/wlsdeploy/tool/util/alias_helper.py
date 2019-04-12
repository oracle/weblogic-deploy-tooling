"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from oracle.weblogic.deploy.aliases import AliasException

from wlsdeploy.exception import exception_helper


class AliasHelper(object):
    """
    This class simply wraps the alias methods to catch exceptions and convert them into
    BundleAwareException of the specified types.
    """
    __class_name = 'AliasHelper'

    def __init__(self, aliases, logger, exception_type):
        self.__aliases = aliases
        self.__logger = logger
        self.__exception_type = exception_type
        return

    def get_model_attribute_name_and_value(self, location, wlst_name, wlst_value):
        """
        Convert the wlst attribute name and attribute value into the appropriate format for the model.
        :param location: context containing current location information
        :param wlst_name: attribute name in wlst
        :param wlst_value: value retrieved for the attribute from wlst
        :return: converted model name and value
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_attribute_name_and_value'
        try:
            model_name, model_value = self.__aliases.get_model_attribute_name_and_value(location, wlst_name, wlst_value)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19028', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return model_name, model_value

    def get_model_subfolder_names(self, location):
        """
        Get the model subfolder names for the specified location.
        :param location: the location
        :return: the list of model subfolder names, or an empty list if none exist
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_subfolder_names'

        try:
            model_subfolder_names = self.__aliases.get_model_subfolder_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19000', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return model_subfolder_names

    def get_name_token(self, location):
        """
        Get the name token, if any, for the specified location.
        :param location: the location
        :return: the name token or None, if no additional name token is required
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_name_token'

        try:
            token_name = self.__aliases.get_name_token(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19001', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return token_name

    def get_model_folder_path(self, location):
        """
        Get the model folder path for the specified location.
        :param location: the location
        :return: the model folder path (e.g., /topology/Server/AdminServer/SSL)
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_folder_path'

        try:
            path = self.__aliases.get_model_folder_path(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19002', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return path

    def get_wlst_attributes_path(self, location):
        """
        Get the WLST attribute path from the aliases for the specified location.
        :param location: the location
        :return: the WLST path where the attributes for the specified location are located
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_attributes_path'

        try:
            wlst_path = self.__aliases.get_wlst_attributes_path(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19003', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_path

    def get_wlst_subfolders_path(self, location):
        """
        Get the WLST subfolders path from the aliases for the specified location.
        :param location: the location
        :return: the WLST path where the subfolders for the specified location are located
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_subfolders_path'

        try:
            wlst_path = self.__aliases.get_wlst_subfolders_path(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19004', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_path

    def get_wlst_list_path(self, location):
        """
        Get the WLST list path from the aliases for the specified location.
        :param location: the location
        :return: the WLST path where the instances of the MBeans can be found
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_list_path'

        try:
            wlst_path = self.__aliases.get_wlst_list_path(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19005', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_path

    def get_wlst_create_path(self, location):
        """
        Get the WLST create path from the aliases for the specified location.
        :param location: the location
        :return: the WLST path where the new instances of the MBean can be created
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_create_path'

        try:
            wlst_path = self.__aliases.get_wlst_create_path(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19006', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_path

    def get_wlst_flattened_folder_create_path(self, location):
        """
        Get the WLST path where to list the existing instances of the flattened type corresponding to
        the specified location.
        :param location: the location
        :return: the WLST path where the new instances of the flattened MBean can be created
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_flattened_folder_create_path'

        try:
            result = self.__aliases.get_wlst_flattened_folder_create_path(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19007', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def requires_unpredictable_single_name_handling(self, location):
        """
        Does the location folder specified require unpredictable single name handling?
        :param location: the location
        :return: True, if the location requires unpredictable single name handling, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'requires_unpredictable_single_name_handling'

        try:
            result = self.__aliases.requires_unpredictable_single_name_handling(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19021',
                                                   location.get_current_model_folder(), location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def supports_multiple_mbean_instances(self, location):
        """
        Does the location folder specified support multiple MBean instances of the parent node type?
        :param location: the location
        :return: True, if the location supports multiple named child nodes, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'supports_multiple_mbean_instances'

        try:
            result = self.__aliases.supports_multiple_mbean_instances(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19008', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def requires_artificial_type_subfolder_handling(self, location):
        """
        Does the location folder specified require artificial subfolder type handling?
        :param location: the location
        :return: True, if the location requires artificial subfolder type handling, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'requires_artificial_type_subfolder_handling'

        try:
            result = self.__aliases.requires_artificial_type_subfolder_handling(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19024', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def supports_single_mbean_instance(self, location):
        """
        Does the location folder specified support only a single MBean instance of the parent node type?
        :param location: the location
        :return: True, if the location support only a single MBean instance of the parent node type, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'supports_single_mbean_instance'

        try:
            result = self.__aliases.supports_single_mbean_instance(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19025', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def is_artificial_type_folder(self, location):
        """
        Is the location folder specified an artificial type folder?
        :param location: the location
        :return: True, if the location is an artificial type folder, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'is_artificial_type_folder'

        try:
            result = self.__aliases.is_artificial_type_folder(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19026', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def is_custom_folder_allowed(self, location):
        """
        Returns true if the specified location allows custom, user-defined folder types.
        :param location: the location to be checked
        :return: True, if the location allows custom folder types, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'is_custom_folder_allowed'

        try:
            result = self.__aliases.is_custom_folder_allowed(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19035', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def is_security_provider_type(self, location):
        """
        Returns true if the specified location is a security provider type.
        :param location: the location to be checked
        :return: True, if the location is a security provider type, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'is_security_provider_type'

        try:
            result = self.__aliases.is_security_provider_type(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19036', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_wlst_mbean_name(self, location):
        """
        Get the MBean name to use to create it for the specified location.
        :param location: the location
        :return: the MBean name
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_mbean_name'

        try:
            wlst_mbean_name = self.__aliases.get_wlst_mbean_name(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19009', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_mbean_name

    def get_wlst_mbean_type(self, location):
        """
        Get the MBean type to use to create it for the specified location.
        :param location: the location
        :return: the MBean type
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_mbean_type'

        try:
            wlst_mbean_type = self.__aliases.get_wlst_mbean_type(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19010', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_mbean_type

    def is_flattened_folder(self, location):
        """
        Does the location contain a flattened folder?
        :param location: the location
        :return: True if the location has a flattened folder, False otherwise
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'is_flattened_folder'

        try:
            result = self.__aliases.is_flattened_folder(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19011', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_wlst_flattened_mbean_name(self, location):
        """
        Get the WLST MBean name for the flattened folder.
        :param location: the location
        :return: the WLST MBean name, or None if there isn't a flattened folder
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_flattened_mbean_name'

        try:
            result = self.__aliases.get_wlst_flattened_mbean_name(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19012', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_wlst_flattened_mbean_type(self, location):
        """
        Get the WLST MBean name for the flattened folder.
        :param location: the location
        :return: the WLST MBean name, or None if there isn't a flattened folder
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_flattened_mbean_type'

        try:
            result = self.__aliases.get_wlst_flattened_mbean_type(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19013', str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_wlst_attribute_name_and_value(self, location, model_name, model_value, existing_wlst_value=None,
                                          masked=False):
        """
        Get the WLST attribute name and value to use to call set.
        :param location: the location
        :param model_name: the model name
        :param model_value: the model value
        :param existing_wlst_value: the WLST value to be merged
        :param masked: whether or not to mask the value in the logs, default is False
        :return: the WLST name and value returned from the alias method
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_attribute_name_and_value'

        try:
            wlst_name, wlst_value = self.__aliases.get_wlst_attribute_name_and_value(location, model_name, model_value,
                                                                                     existing_wlst_value)
        except AliasException, ae:
            value = model_value
            if masked:
                value = '<masked>'
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19014', model_name,
                                                   value, str(location), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_name, wlst_value

    def get_wlst_attribute_name(self, location, model_name):
        """
        Get the WLST attribute name for the model attribute name.
        :param location: the location
        :param model_name: the model attribute name
        :return: the WLST attribute name, or None if the attribute is not relevant for the version of WLS
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_attribute_name'

        try:
            wlst_name = self.__aliases.get_wlst_attribute_name(location, model_name)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19015', model_name, str(location),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return wlst_name

    def get_model_password_type_attribute_names(self, location):
        """
        Get the attributes in the current location whose types are passwords.
        :param location: the location
        :return: list of the attribute names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_password_type_attribute_names'

        try:
            password_attribute_names = self.__aliases.get_model_password_type_attribute_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19016', location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return password_attribute_names

    def get_model_mbean_set_method_attribute_names_and_types(self, location):
        """
        Get the list of model attribute names and types where the set method requires an MBean.
        :param location: the location
        :return: a dictionary keyed by model attribute names with the set_method and set_mbean_type fields set
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_mbean_set_method_attribute_names_and_types'

        try:
            mbean_attribute_names = self.__aliases.get_model_mbean_set_method_attribute_names_and_types(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19017', location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return mbean_attribute_names

    def is_valid_model_folder_name(self, location, model_folder_name):
        """
        Return whether or not location's model folders list has a subfolder
        with the name assigned to the model_folder_name parameter.

        :param location: the location
        :param model_folder_name: the model folder name
        :return: ValidationCode, message
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'is_valid_model_folder_name'

        try:
            result, message = self.__aliases.is_valid_model_folder_name(location, model_folder_name)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19018', model_folder_name,
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result, message

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
            code, message = self.__aliases.is_version_valid_location(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19033',
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex

        return code, message

    def is_valid_model_attribute_name(self, location, model_attribute_name):
        """
        Return whether or not location's model folders list has an attribute
        with the name assigned to the model_attribute_name parameter.

        :param location: the location
        :param model_attribute_name: the model attribute name
        :return: ValidationCode, message
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'is_valid_model_attribute_name'

        try:
            result, message = self.__aliases.is_valid_model_attribute_name(location, model_attribute_name)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19031', model_attribute_name,
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result, message

    def get_model_topology_top_level_folder_names(self):
        """
        Get the model topology top-level folder names.
        :return: the list of top-level topology folders
        """
        return self.__aliases.get_model_topology_top_level_folder_names()

    def get_model_resources_top_level_folder_names(self):
        """
        Get the model resources top-level folder names.
        :return: the list of top-level resources folders
        """
        return self.__aliases.get_model_resources_top_level_folder_names()

    def get_model_app_deployments_top_level_folder_names(self):
        """
        Get the model app_deployments top-level folder names.
        :return: the list of top-level app_deployments folders
        """
        return self.__aliases.get_model_app_deployments_top_level_folder_names()

    def get_model_attribute_names(self, location):
        """
        Get the model attribute names.
        :param location: the location
        :return: list of model attribute names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_attribute_names'

        try:
            result = self.__aliases.get_model_attribute_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19029',
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_model_attribute_names_and_types(self, location):
        """
        Get the model attribute names and their types.
        :param location: the location
        :return: dictionary of model attribute names and their types
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_attribute_names_and_types'

        try:
            result = self.__aliases.get_model_attribute_names_and_types(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19019',
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_model_uses_path_tokens_attribute_names(self, location):
        """
        Get the list of attribute names that have their get_method specified as GET.
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_uses_path_tokens_attribute_names'

        try:
            result = self.__aliases.get_model_uses_path_tokens_attribute_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19030',
                                                   location.get_current_model_folder(), location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_wlst_get_required_attribute_names(self, location):
        """
        Get the list of attribute names that have their get_method specified as GET.
        :param location: the location
        :return: list[string]: the list of attribute names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_wlst_get_required_attribute_names'

        try:
            result = self.__aliases.get_wlst_get_required_attribute_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19020',
                                                   location.get_current_model_folder(), location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_model_subfolder_name(self, location, wlst_name):
        """
        Get the model folder name for the WLST subfolder name at the specified location.
        :param location: the location
        :param wlst_name: the WLST mbean name for the subfolder
        :return: the model folder name, or None if the folder is not needed for the model.
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_subfolder_name'
        try:
            result = self.__aliases.get_model_subfolder_name(location, wlst_name)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19022', wlst_name,
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_model_restart_required_attribute_names(self, location):
        """
        Get the names of attributes at the specified location that require a restart if changed.
        :param location: the location
        :return: a list of attribute names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_restart_required_attribute_names'
        try:
            result = self.__aliases.get_model_restart_required_attribute_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19023', location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_model_merge_required_attribute_names(self, location):
        """
        Get the names of attributes at the specified location that require merge with existing WLST values.
        :param location: the location
        :return: a list of attribute names
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_merge_required_attribute_names'
        try:
            result = self.__aliases.get_model_merge_required_attribute_names(location)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19027', location.get_folder_path(),
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def get_model_domain_info_attribute_names_and_types(self):
        """
        Get the attribute names and types for the domainInfo section of the model.
        :return: a dictionary keyed on model attribute names with the type as the value
        """
        return self.__aliases.get_model_domain_info_attribute_names_and_types()

    def get_model_attribute_default_value(self, location, model_attribute_name):
        """
        Get the default value for the specified attribute.
        :param location: the location
        :param model_attribute_name: the model attribute name
        :return: the default value converted to the type
        :raises: BundleAwareException of the specified type: if an error occurs
        """
        _method_name = 'get_model_attribute_default_value'

        try:
            result = self.__aliases.get_model_attribute_default_value(location, model_attribute_name)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19032', model_attribute_name,
                                                   location.get_folder_path(), ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    def decrypt_password(self, text):
        """
        Encrypt the specified password if encryption is used and the password is encrypted.
        :param text: the text to check and decrypt, if needed
        :return: the clear text
        :raises EncryptionException: if an error occurs while decrypting the password
        """
        _method_name = 'decrypt_password'

        try:
            result = self.__aliases.decrypt_password(text)
        except AliasException, ae:
            ex = exception_helper.create_exception(self.__exception_type, 'WLSDPLY-19037',
                                                   ae.getLocalizedMessage(), error=ae)
            self.__logger.throwing(ex, class_name=self.__class_name, method_name=_method_name)
            raise ex
        return result

    ###########################################################################
    #                          Convenience Methods                            #
    ###########################################################################

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
