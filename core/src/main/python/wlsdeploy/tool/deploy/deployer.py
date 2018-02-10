"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
from oracle.weblogic.deploy.util import PyWLSTException

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy import log_helper
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.util.attribute_setter import AttributeSetter
from wlsdeploy.tool.util.wlst_helper import WlstHelper
import wlsdeploy.util.dictionary_utils as dictionary_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class Deployer(object):
    """
    The base class for deployers.
    Maintains model, model context, WLST mode, etc.
    Has common methods for deployers.
    """
    _class_name = "Deployer"

    def __init__(self, model, model_context, aliases, wlst_mode=WlstModes.OFFLINE):
        self.name = self._class_name
        self.model = model
        self.wlst_mode = wlst_mode
        self.model_context = model_context
        self.aliases = aliases
        self.logger = PlatformLogger('wlsdeploy.deploy')
        self.alias_helper = AliasHelper(aliases, self.logger, ExceptionType.DEPLOY)
        self.wls_helper = WebLogicHelper(self.logger)
        self.wlst_helper = WlstHelper(self.logger, ExceptionType.DEPLOY)
        self.attribute_setter = AttributeSetter(self.aliases, self.logger, ExceptionType.DEPLOY, wlst_mode=wlst_mode)

    def _add_named_elements(self, type_name, model_nodes, location):
        """
        Add each named element from the specified nodes in WLST and set its attributes.
        Sub-folders are processed in a generic manner if present.
        It is assumed that there are no attributes or sub-folders with special processing.
        :param type_name: the type name of the child nodes
        :param model_nodes: the child nodes of a model element
        :param location: the location where elements should be added
        """
        _method_name = '_add_named_elements'

        if len(model_nodes) == 0:
            return

        parent_type, parent_name = self.get_location_type_and_name(location)
        location = LocationContext(location).append_location(type_name)
        if not self._check_location(location):
            return

        deployer_utils.check_flattened_folder(location, self.alias_helper)
        existing_names = deployer_utils.get_existing_object_list(location, self.alias_helper)

        token = self.alias_helper.get_name_token(location)
        for name in model_nodes:
            is_add = name not in existing_names
            log_helper.log_updating_named_folder(type_name, name, parent_type, parent_name, is_add, self._class_name,
                                                 _method_name)

            if token is not None:
                location.add_name_token(token, name)
            deployer_utils.create_and_cd(location, existing_names, self.alias_helper)

            child_nodes = dictionary_utils.get_dictionary_element(model_nodes, name)
            self.set_attributes(location, child_nodes)
            self._add_subfolders(child_nodes, location)
        return

    def _add_subfolders(self, model_nodes, location, excludes=None):
        """
        Add each model sub-folder from the specified nodes and set its attributes.
        :param model_nodes: the child nodes of a model element
        :param location: the location where sub-folders should be added
        :param excludes: optional list of sub-folder names to be excluded from processing
        """
        location = LocationContext(location)
        model_subfolder_names = self.alias_helper.get_model_subfolder_names(location)

        for subfolder in model_nodes:
            key_excluded = (excludes is not None) and (subfolder in excludes)
            if subfolder in model_subfolder_names and not key_excluded:
                subfolder_nodes = model_nodes[subfolder]
                if len(subfolder_nodes) != 0:
                    sub_location = LocationContext(location).append_location(subfolder)
                    if self.alias_helper.supports_multiple_mbean_instances(sub_location):
                        self._add_named_elements(subfolder, subfolder_nodes, location)
                    else:
                        self._add_model_elements(subfolder, subfolder_nodes, location)
        return

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

        deployer_utils.check_flattened_folder(location, self.alias_helper)
        existing_subfolder_names = deployer_utils.get_existing_object_list(location, self.alias_helper)

        mbean_name = deployer_utils.get_mbean_name(location, existing_subfolder_names, self.alias_helper)
        is_add = mbean_name not in existing_subfolder_names
        log_helper.log_updating_folder(type_name, parent_type, parent_name, is_add, self._class_name, _method_name)

        deployer_utils.create_and_cd(location, existing_subfolder_names, self.alias_helper)

        self.set_attributes(location, model_nodes)
        self._add_subfolders(model_nodes, location)
        return

    def set_attributes(self, location, model_nodes, excludes=None):
        """
        Set all the attributes in the model_nodes list. Exclude items that are sub-folders.
        :param location: the location of the attributes to be set
        :param model_nodes: a map of model nodes with attributes to be set
        :param excludes: a list of items that should not be set
        """
        _method_name = 'set_attributes'
        attribute_names = self.alias_helper.get_model_attribute_names_and_types(location)
        restart_attribute_names = self.alias_helper.get_model_restart_required_attribute_names(location)
        set_method_map = self.alias_helper.get_model_mbean_set_method_attribute_names_and_types(location)

        for key in model_nodes:
            key_excluded = (excludes is not None) and (key in excludes)
            if key in attribute_names and not key_excluded:
                value = model_nodes[key]
                if not self._skip_setting_attribute(key, value, restart_attribute_names) and \
                        (not self.set_special_attribute(location, key, value, set_method_map)):
                    try:
                        deployer_utils.set_attribute(location, key, value, self.alias_helper)
                    except PyWLSTException, pwe:
                        loc_type, loc_name = self.get_location_type_and_name(location)
                        ex = exception_helper.create_deploy_exception('WLSDPLY-09133', key, loc_type, loc_name,
                                                                      pwe.getLocalizedMessage(), error=pwe)
                        self.logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                        raise ex
        return

    def _skip_setting_attribute(self, key, value, restart_attribute_names):
        """
        For the case where a change to an attribute will require restart, verify that the new value is different
        from the current value in WLST.
        :param key: the attribute key
        :param value: the attribute value from the model
        :param restart_attribute_names: a list of attribute names that require system restart
        :return: True if the attribute does not need to be set
        """
        # if model_key in restart_attribute_names:
        #     if wlst_helper.requires_set(model_key, model_value, wlst_param, lsa_required_param_names):
        #         return True

        return False

    def get_location_type_and_name(self, location):
        """
        Returns location type and name of the last element in the location for logging purposes.
        This wrapper was added to the base class to allow overrides by sub-classes for special cases.
        :param location:the location to be examined
        :return: the type and name of the last element in the location
        """
        return self.alias_helper.get_model_type_and_name(location)

    def get_location_type(self, location):
        """
        Returns location type of the last element in the location.
        :param location:the location to be examined
        :return: the type of the last element in the location
        """
        folders = location.get_model_folders()
        if len(folders) == 0:
            return None
        return folders[-1]

    def set_special_attribute(self, location, key, value, set_method_map):
        method_name = 'set_special_attribute'
        set_method_info = dictionary_utils.get_dictionary_element(set_method_map, key)
        set_method_name = dictionary_utils.get_element(set_method_info, 'set_method')

        if set_method_name is not None:
            try:
                set_method = getattr(self.attribute_setter, set_method_name)
                set_method(location, key, value)
                return True
            except AttributeError, e:
                location_text = '/'.join(location.get_model_folders())
                ex = exception_helper.create_deploy_exception('WLSDPLY-09120', set_method_name, key, location_text,
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
        if self.alias_helper.get_wlst_mbean_type(location) is None:
            the_type = self.get_location_type(location)
            self.logger.warning('WLSDPLY-09112', the_type, self.wls_helper.get_weblogic_version(),
                                class_name=self._class_name, method_name=_method_name)
            return False
        return True
