"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import java.util.logging.Level as Level
from oracle.weblogic.deploy.aliases import AliasException

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.verify.utils as verify_utils

TOP_FOLDERS_TO_IGNORE = ['UnixMachine']


class AliasHelper(object):
    __logger = PlatformLogger('test.aliases')

    def __init__(self, model_context):
        self.__class_name__ = self.__class__.__name__
        self.__model_context = model_context
        self.__aliases = Aliases(self.__model_context, self.__model_context.get_target_wlst_mode(),
                                 self.__model_context.get_target_wls_version())

    def get_top_folder_map(self, location):
        top_folder_names = [folder for folder in self.__aliases.get_model_top_level_folder_names()
                            if folder not in TOP_FOLDERS_TO_IGNORE]

        return self.get_folder_map(top_folder_names, location)

    def get_subfolder_map(self, location):
        return self.get_folder_map(self.__aliases.get_model_subfolder_names(location), location)

    def get_folder_map(self, model_folder_list, base_location):
        _method_name = 'get_folder_map'

        location = LocationContext(base_location)
        folder_map = dict()
        for name in model_folder_list:
            if name is None:
                self.__logger.warning('Have a problem with the list at location {0} : {1}', location.get_folder_path(),
                                      model_folder_list, class_name=self.__class_name__, method_name=_method_name)
            else:
                location.append_location(name)
                self.__logger.finer('Checking the folder {0} for flattened and type', location.get_folder_path(),
                                    class_name=self.__class_name__, method_name=_method_name)
                flattened_info = None
                if not location.get_folder_path().startswith('/NMProperties') and not location.get_folder_path() == '/':
                    flattened_info = self.__aliases.get_wlst_flattened_folder_info(location)
                if flattened_info is not None:
                    # make a message
                    self.__logger.fine('The mbean type {0} at location {1} is a flattened folder ', name,
                                       location.get_folder_path(),
                                       class_name=self.__class_name__, method_name=_method_name)
                    wlst_mbean = flattened_info.get_mbean_type()
                else:
                    wlst_mbean = self.__aliases.get_wlst_mbean_type(location)
                if wlst_mbean is None:
                    # create a message for this
                    self.__logger.finer(
                        'Mbean folder {0} at location {1} is not implemented in aliases for version {2}}',
                        name, location.get_folder_path(), self.__model_context.get_target_wls_version(),
                        class_name=self.__class_name__, method_name=_method_name)
                else:
                    folder_map[wlst_mbean] = name
                location.pop_location()
        return folder_map

    def get_wlst_flattened_folder_info(self, location):
        return self.__aliases.get_wlst_flattened_folder_info(location)

    def get_model_attribute_names(self, location):
        return self.__aliases.get_model_attribute_names(location)

    def get_wlst_attribute_name(self, location, attribute_name, check_read_only=True):
        return self.__aliases.get_wlst_attribute_name(location, attribute_name, check_read_only)

    def get_wlst_get_required_attribute_names(self, location):
        return self.__aliases.get_wlst_get_required_attribute_names(location)

    def get_model_restart_required_attribute_names(self, location):
        return self.__aliases.get_model_restart_required_attribute_names(location)

    def get_model_uses_path_tokens_attribute_names(self, location):
        return self.__aliases.get_model_uses_path_tokens_attribute_names(location)

    def get_model_mbean_set_method_attribute_names_and_types(self, location):
        return self.__aliases.get_model_mbean_set_method_attribute_names_and_types(location)

    def get_model_attribute_name(self, location, generated_attribute):
        return self.__aliases.get_model_attribute_name(location, generated_attribute)

    def get_model_attribute_type(self, location, model_attribute_name):
        return self.__aliases.get_model_attribute_type(location, model_attribute_name)

    def get_model_attribute_default_value(self, location, model_attribute_name):
        return self.__aliases.get_model_attribute_default_value(location, model_attribute_name)

    def get_wlst_attribute_name_and_value(self, location, model_attribute_name, model_default_value):
        return self.__aliases.get_wlst_attribute_name_and_value(location, model_attribute_name, model_default_value)

    def get_model_attribute_name_and_value(self, location, generated_attribute, generated_default):
        return self.__aliases.get_model_attribute_name_and_value(location, generated_attribute, generated_default)

    def get_ignore_attribute_names(self):
        return self.__aliases.get_ignore_attribute_names()

    def get_model_subfolder_name(self, location, alias_name):
        return self.__aliases.get_model_subfolder_name(location, alias_name)

    def get_model_subfolder_names(self, location):
        return self.__aliases.get_model_subfolder_names(location)

    def get_name_token(self, location):
        return self.__aliases.get_name_token(location)

    def check_flattened_folder(self, location, folder):
        """
        Determine from aliases if an MBean is a flattened folder in the aliases model.
        :param location: location constructed with mbean information
        :param folder: mbean to check against aliases
        :return: True if the mbean at the location is a flattened folder in the model
        """
        flattened_info = self.__aliases.get_wlst_flattened_folder_info(location)
        if flattened_info is not None:
            mbean_type = flattened_info.get_mbean_type()
            if mbean_type == folder:
                return True
        return False

    def supports_multiple_mbean_instances(self, location):
        return self.__aliases.supports_multiple_mbean_instances(location)

    def get_wlst_mbean_name(self, location):
        return self.__aliases.get_wlst_mbean_name(location)

    def add_name_token_to_location(self, location, model_name):
        name_token = self.__aliases.get_name_token(location)
        if name_token:
            location.add_name_token(name_token, verify_utils.mbean_name(model_name)[0])
        return name_token

    def get_preferred_model_type(self, location, model_name):
        return self.__aliases.get_preferred_model_type(location, model_name)

    def get_wlst_read_type(self, location, model_name):
        return self.__aliases.get_wlst_read_type(location, model_name)

    def is_derived_default(self, location, model_name):
        return self.__aliases.is_derived_default(location, model_name)

    def get_wlst_access_rod_attribute_names(self, location):
        return self.__aliases.get_wlst_access_rod_attribute_names(location)
  