"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import copy

from array import array
from java.lang import Class
from oracle.weblogic.deploy.util import PyWLSTException
from wlsdeploy.aliases.model_constants import ABSOLUTE_PLAN_PATH
from wlsdeploy.aliases.model_constants import ABSOLUTE_SOURCE_PATH
from wlsdeploy.aliases.model_constants import APP_DEPLOYMENTS
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import PLAN_PATH
from wlsdeploy.aliases.model_constants import SOURCE_PATH
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.util import model_helper
from wlsdeploy.tool.deploy import log_helper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.util.attribute_setter import AttributeSetter
from wlsdeploy.tool.util.topology_helper import TopologyHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
import wlsdeploy.util.dictionary_utils as dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class Deployer(object):
    """
    The base class for deployers.
    Maintains model, model context, WLST mode, etc.
    Has common methods for deployers.
    """
    _class_name = "Deployer"

    _mbean_interface = Class.forName('weblogic.management.configuration.ConfigurationMBean')
    _object_name_class = Class.forName('javax.management.ObjectName')
    _list_interface = Class.forName('java.util.List')

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        self.name = self._class_name
        self.model = model
        self.wlst_mode = wlst_mode
        self.model_context = model_context
        self.aliases = aliases
        self.logger = PlatformLogger('wlsdeploy.deploy')
        self.wls_helper = WebLogicHelper(self.logger)
        self.wlst_helper = WlstHelper(ExceptionType.DEPLOY)
        self.attribute_setter = AttributeSetter(model_context, self.aliases, ExceptionType.DEPLOY, wlst_mode=wlst_mode)
        self.topology_helper = TopologyHelper(self.aliases, ExceptionType.DEPLOY, self.logger)

        self.archive_helper = None
        archive_file_name = self.model_context.get_archive_file_name()
        if archive_file_name is not None:
            self.archive_helper = ArchiveHelper(archive_file_name, self.model_context.get_domain_home(), self.logger,
                                                exception_helper.ExceptionType.DEPLOY)

    def _add_named_elements(self, type_name, model_nodes, location, delete_now=True):
        """
        Add each named element from the specified nodes in WLST and set its attributes.
        Sub-folders are processed in a generic manner if present.
        It is assumed that there are no attributes or sub-folders with special processing.
        :param type_name: the type name of the child nodes
        :param model_nodes: the child nodes of a model element
        :param location: the location where elements should be added
        :param delete_now: Flag to determine whether to delay delete of element
        """
        _method_name = '_add_named_elements'

        if len(model_nodes) == 0:
            return

        parent_type, parent_name = self.get_location_type_and_name(location)
        location = LocationContext(location).append_location(type_name)
        if not self._check_location(location):
            return

        deployer_utils.check_flattened_folder(location, self.aliases)
        existing_names = deployer_utils.get_existing_object_list(location, self.aliases)

        token = self.aliases.get_name_token(location)
        for name in model_nodes:
            if model_helper.is_delete_name(name):
                if delete_now:
                    deployer_utils.delete_named_element(location, name, existing_names, self.aliases)
                continue

            is_add = name not in existing_names
            log_helper.log_updating_named_folder(type_name, name, parent_type, parent_name, is_add, self._class_name,
                                                 _method_name)

            if token is not None:
                location.add_name_token(token, name)
            deployer_utils.create_and_cd(location, existing_names, self.aliases)

            child_nodes = dictionary_utils.get_dictionary_element(model_nodes, name)
            self._set_attributes_and_add_subfolders(location, child_nodes)

    def _add_subfolders(self, model_nodes, location, excludes=None):
        """
        Add each model sub-folder from the specified nodes and set its attributes.
        :param model_nodes: the child nodes of a model element
        :param location: the location where sub-folders should be added
        :param excludes: optional list of sub-folder names to be excluded from processing
        """
        location = LocationContext(location)
        model_subfolder_names = self.aliases.get_model_subfolder_names(location)

        for subfolder in model_nodes:
            key_excluded = (excludes is not None) and (subfolder in excludes)
            if subfolder in model_subfolder_names and not key_excluded:
                subfolder_nodes = model_nodes[subfolder]
                if len(subfolder_nodes) != 0:
                    sub_location = LocationContext(location).append_location(subfolder)
                    if self.aliases.supports_multiple_mbean_instances(sub_location):
                        self._add_named_elements(subfolder, subfolder_nodes, location)
                    else:
                        self._add_model_elements(subfolder, subfolder_nodes, location)

    def _add_model_elements(self, type_name, model_nodes, location):
        """
        Add each model element from the specified nodes at the specified location and set its attributes.
        :param model_nodes: the child nodes of a model element
        :param location: the location where sub-folders should be added
        :param type_name: the name of the model folder to add
        """
        _method_name = '_add_model_elements'

        parent_type, parent_name = self.get_location_type_and_name(location)
        location = LocationContext(location).append_location(type_name)
        if not self._check_location(location):
            return

        deployer_utils.check_flattened_folder(location, self.aliases)
        existing_subfolder_names = deployer_utils.get_existing_object_list(location, self.aliases)

        mbean_name = deployer_utils.get_mbean_name(location, existing_subfolder_names, self.aliases)
        is_add = mbean_name not in existing_subfolder_names
        log_helper.log_updating_folder(type_name, parent_type, parent_name, is_add, self._class_name, _method_name)

        deployer_utils.create_and_cd(location, existing_subfolder_names, self.aliases)

        self._set_attributes_and_add_subfolders(location, model_nodes)

    def _set_attributes_and_add_subfolders(self, location, model_nodes):
        """
        Set the attributes and add sub-folders for the specified location.
        This method can be overridden for finer control of the ordering
        :param location: the location of the attributes and sub-folders
        :param model_nodes: a map of model nodes including attributes and sub-folders
        :raise: DeployException: if an error condition is encountered
        """
        self.set_attributes(location, model_nodes)
        self._add_subfolders(model_nodes, location)

    def set_attributes(self, location, model_nodes, excludes=None):
        """
        Set all the attributes in the model_nodes list. Exclude items that are sub-folders.
        :param location: the location of the attributes to be set
        :param model_nodes: a map of model nodes with attributes to be set
        :param excludes: a list of items that should not be set
        :raise: DeployException: if an error condition is encountered
        """
        _method_name = 'set_attributes'
        attribute_names = self.aliases.get_model_attribute_names(location)
        uses_path_tokens_attribute_names = self.aliases.get_model_uses_path_tokens_attribute_names(location)
        restart_attribute_names = self.aliases.get_model_restart_required_attribute_names(location)
        merge_attribute_names = self.aliases.get_model_merge_required_attribute_names(location)
        lsa_required_attribute_names = self.aliases.get_model_lsa_required_attribute_names(location)
        set_method_map = self.aliases.get_model_mbean_set_method_attribute_names_and_types(location)

        for key in model_nodes:
            key_excluded = (excludes is not None) and (key in excludes)
            if key in attribute_names and not key_excluded:
                value = model_nodes[key]
                if key in uses_path_tokens_attribute_names:
                    value = deployer_utils.extract_from_uri(self.model_context, value)
                    self._extract_from_archive_if_needed(location, key, value)

                wlst_merge_value = None
                if key in merge_attribute_names:
                    wlst_merge_value = self._get_existing_wlst_value(location, key, lsa_required_attribute_names)

                if not self._skip_setting_attribute(key, value, wlst_merge_value, restart_attribute_names) and \
                        (not self.set_special_attribute(location, key, value, wlst_merge_value, set_method_map)):
                    try:
                        self.attribute_setter.set_attribute(location, key, value, wlst_merge_value)
                    except PyWLSTException, pwe:
                        loc_type, loc_name = self.get_location_type_and_name(location)
                        ex = exception_helper.create_deploy_exception('WLSDPLY-09200', key, loc_type, loc_name,
                                                                      pwe.getLocalizedMessage(), error=pwe)
                        self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                        raise ex

    def _skip_setting_attribute(self, key, value, wlst_merge_value, restart_attribute_names):
        """
        For the case where a change to an attribute will require restart, verify that the new value is different
        from the current value in WLST.
        :param key: the attribute key
        :param value: the attribute value from the model
        :param wlst_merge_value: the WLST value to check for merge
        :param restart_attribute_names: a list of attribute names that require system restart
        :return: True if the attribute does not need to be set
        """

        # Needs implementation. Return true if model key in restart attribute_names,
        # and WLST helper determines that set is required,
        # based on model key, model value, and the WLST merge value
        return False

    def _get_existing_wlst_value(self, location, key, lsa_required_attribute_names):
        """
        Returns the existing value for the specified attribute key in the specified location.
        :param location: the location to be checked
        :param key: the attribute key
        :return: The value of the attribute in WLST
        """
        _method_name = '_get_existing_wlst_value'

        wlst_key = self.aliases.get_wlst_attribute_name(location, key)
        if wlst_key is None:
            return None

        # online WLST may return a default value, even if the attribute was not set.
        # don't merge with a value that was not set (example: JDBCDataSourceParams: JNDINames).
        if not self.wlst_helper.is_set(wlst_key):
            return None

        if key in lsa_required_attribute_names:
            attribute_map = self.wlst_helper.lsa()
            if wlst_key in attribute_map:
                wlst_value = attribute_map[wlst_key]
            else:
                path = self.aliases.get_model_folder_path(location)
                ex = exception_helper.create_deploy_exception('WLSDPLY-09201', key, path, wlst_key)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        else:
            wlst_value = self.wlst_helper.get(wlst_key)

        wlst_value = self._convert_if_mbean_list(wlst_value)

        return wlst_value

    def _convert_if_mbean_list(self, wlst_value):
        """
        Converts the specified WLST value to a list of names, if it represents a list of mbeans or object names.
        :param wlst_value: the value to be checked
        :return: a list of names, or the original value
        """
        if isinstance(wlst_value, (list, array, self._list_interface)) and len(wlst_value) > 0:
            first_list_item = wlst_value[0]

            if self._mbean_interface.isInstance(first_list_item):
                new_list = []
                for mbean in wlst_value:
                    new_list.append(mbean.getName())
                return new_list

            if self._object_name_class.isInstance(first_list_item):
                new_list = []
                for object_name in wlst_value:
                    new_list.append(object_name.getKeyProperty('Name'))
                return new_list

        return wlst_value

    def get_location_type_and_name(self, location):
        """
        Returns location type and name of the last element in the location for logging purposes.
        This wrapper was added to the base class to allow overrides by sub-classes for special cases.
        :param location:the location to be examined
        :return: the type and name of the last element in the location
        """
        return self.aliases.get_model_type_and_name(location)

    def get_location_type(self, location):
        """
        Returns location type of the last element in the location.
        :param location:the location to be examined
        :return: the type of the last element in the location
        """
        _method_name = 'get_location_type'
        self.logger.entering(str_helper.to_string(location), class_name=self._class_name, method_name=_method_name)

        folders = location.get_model_folders()
        if len(folders) == 0:
            return None
        return folders[-1]

    def set_special_attribute(self, location, key, value, wlst_merge_value, set_method_map):
        method_name = 'set_special_attribute'
        set_method_info = dictionary_utils.get_dictionary_element(set_method_map, key)
        set_method_name = dictionary_utils.get_element(set_method_info, 'set_method')

        if set_method_name is not None:
            try:
                set_method = getattr(self.attribute_setter, set_method_name)
                set_method(location, key, value, wlst_merge_value)
                return True
            except AttributeError, e:
                location_text = '/'.join(location.get_model_folders())
                ex = exception_helper.create_deploy_exception('WLSDPLY-09202', set_method_name, key, location_text,
                                                              error=e)
                self.logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex

        return False

    def _check_location(self, location):
        """
        Verify that the specified location in valid for the current WLS version.
        A warning is logged if the location is not valid.
        :param location: the location to be checked
        :return: True if the location is valid, False otherwise
        """
        _method_name = '_check_location'
        if self.aliases.get_wlst_mbean_type(location) is None:
            the_type = self.get_location_type(location)
            self.logger.warning('WLSDPLY-09203', the_type, self.wls_helper.get_weblogic_version(),
                                class_name=self._class_name, method_name=_method_name)
            return False
        return True

    def _extract_from_archive_if_needed(self, location, key, value):
        """
        Extract the file from the archive, if needed.
        :param location: the location
        :param key: the attribute name
        :param value: the attribute value
        :return: True if the file/directory was extracted, False otherwise
        :raise: DeployException: if an error occurs
        """
        _method_name = '_extract_from_archive_if_needed'
        self.logger.entering(str_helper.to_string(location), key, value,
                             class_name=self._class_name, method_name=_method_name)

        result = False
        short_value = deployer_utils.get_rel_path_from_uri(self.model_context, value)
        if deployer_utils.is_path_into_archive(short_value):
            if self.archive_helper is not None:
                result = self.__process_archive_entry(location, key, short_value)
            else:
                path = self.aliases.get_model_folder_path(location)
                ex = exception_helper.create_deploy_exception('WLSDPLY-09110', key, path, value)
                self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def __process_archive_entry(self, location, key, value):
        """
        Extract the archive entry, if needed.  Note that this method assumes the path has already been
        tested to verify that it points into the archive.
        :param location: the location
        :param key: the attribute name
        :param value: the attribute value
        :return: True if the artifact was extracted, False otherwise
        """
        _method_name = '__process_archive_entry'
        self.logger.entering(str_helper.to_string(location), key, value,
                             class_name=self._class_name, method_name=_method_name)

        result = False
        fullpath = os.path.join(self.model_context.get_domain_home(), value)
        if self.archive_helper.contains_file(value):
            if self.wlst_mode == WlstModes.OFFLINE:
                if value.endswith('/'):
                    result = self.__process_directory_entry(fullpath)
                else:
                    # In offline mode, just overwrite any existing file.
                    self.archive_helper.extract_file(value)
                    result = True
            else:
                if value.endswith('/'):
                    result = self.__process_directory_entry(fullpath)
                else:
                    if os.path.isfile(fullpath):
                        # If the file already exists in the file system,
                        # compare the hash values to determine if it needs
                        # to be extracted.
                        archive_hash = self.archive_helper.get_file_hash(value)
                        file_hash = deployer_utils.get_file_hash(fullpath)
                        if archive_hash != file_hash:
                            self.archive_helper.extract_file(value)
                            result = True
                    else:
                        # The file does not exist so extract it from the archive.
                        self.archive_helper.extract_file(value)
                        result = True
        elif self.archive_helper.contains_path(value):
            # contents should have been extracted elsewhere, such as for apps and shared libraries
            result = self.archive_helper.extract_directory(value)
        elif value.endswith('/'):
            # If the path is a directory in the wlsdeploy directory tree
            # but not in the archive, just create it to help the user.
            result = self.__process_directory_entry(fullpath)
        else:
            path = self.aliases.get_model_folder_path(location)
            ex = exception_helper.create_deploy_exception('WLSDPLY-09204', key, path, value,
                                                          self.model_context.get_archive_file_name())
            self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        self.logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def add_application_attributes_online(self, model, location):
        """
        Add attributes for online; the attributes that are added are not set during the online
        deploy WLST call.
        :param model: dictionary model
        :param location: current location
        """

        deploy = dictionary_utils.get_dictionary_element(model.get_model(), APP_DEPLOYMENTS)
        apps_deploy = dictionary_utils.get_dictionary_element(deploy, APPLICATION)
        apps = copy.deepcopy(apps_deploy)

        for app in apps:
            apps_slim = apps[app]
            deploy_info = [ PLAN_PATH, ABSOLUTE_PLAN_PATH, SOURCE_PATH, ABSOLUTE_SOURCE_PATH, TARGET]
            new_location = LocationContext(location)
            new_location.append_location(APPLICATION)
            new_location.add_name_token(self.aliases.get_name_token(new_location), app)
            path = self.aliases.get_wlst_attributes_path(new_location)
            if self.wlst_helper.path_exists(path):
                self.wlst_helper.cd(path)
                self.set_attributes(new_location, apps_slim, excludes=deploy_info)
                self._add_subfolders(apps_slim, location)

    def __process_directory_entry(self, path):
        """
        Create the directory (and any parent directories) if it does not already exist.
        :param path: the full path to the directory
        :return: True, if the directory was created, False otherwise
        """
        _method_name = '__process_directory_entry'
        self.logger.entering(str_helper.to_string(path), class_name=self._class_name, method_name=_method_name)

        result = False
        if not os.path.isdir(path):
            # No real need to extract directory, just make the directories
            os.makedirs(path)
            result = True
        return result
