"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import java.util.logging.Level as Level
from oracle.weblogic.deploy.aliases import AliasException

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.logging.platform_logger import PlatformLogger

import aliastest.util.all_utils as all_utils


# Change this to store stuff here and not in model_context
class TestHelper:
    """
    Common alias types of helper methods used for both generate and verify.
    """
    
    __logger = PlatformLogger('test.aliases', resource_bundle_name='aliastest_rb')
    __logger.set_level(Level.FINEST)

    def __init__(self, model_context):
        self.__class_name__ = self.__class__.__name__
        self.__model_context = model_context
        self.__aliases = Aliases(self.__model_context, self.__model_context.get_target_wlst_mode(),
                                 self.__model_context.get_target_wls_version())

    def mode(self):
        """
        Get the mode (online or offline) for the current processing
        :return: mode enum value
        """
        return self.__model_context.get_target_wlst_mode()

    def version(self):
        """
        Get the weblogic version for the oracle home in use
        :return: weblogic version
        """
        return self.__model_context.get_target_wls_version()

    def admin_url(self):
        """
        Get the URL for the admin server passed as an argument on the test.
        :return: Admin server URL
        """
        return self.__model_context.get_admin_url()

    def admin_user(self):
        """
        Get the admin user passed as an argument on the test.
        :return: Admin server userid
        """
        return self.__model_context.get_admin_user()

    def admin_password(self):
        """
        Get the admin password passed as an argument on the test.
        :return: Admin server password
        """
        return self.__model_context.get_admin_password()

    def oracle_home(self):
        """
        Get the location of the oracle home passed as an argument on the test.
        :return: oracle home location
        """
        return self.__model_context.get_oracle_home()

    def domain_home(self):
        """
        Get the location of the domain home passed as an argument on the test.
        :return: domain home location
        """
        return self.__model_context.get_domain_home()

    def domain_name(self):
        """
        Name of the domain at the domain home location.
        :return: domain name.
        """
        return self.__model_context.get_domain_name()

    def aliases(self):
        """
        Return the aliases instance encapsulated by the test.
        :return: aliases instance
        """
        return self.__aliases

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

    def get_top_folder_map(self, location):
        return self.get_folder_map(self.__aliases.get_model_top_level_folder_names(), location)

    def get_subfolder_map(self, location):
        return self.get_folder_map(self.__aliases.get_model_subfolder_names(location), location)

    def get_folder_map(self, model_folder_list, base_location):
        location = LocationContext(base_location)
        folder_map = dict()
        for name in model_folder_list:
            if name is None:
                self.__logger.warning('have a problem with the list at location {0} : {1}', location.get_folder_path(),
                                model_folder_list)
            else:
                location.append_location(name)
                self.__logger.finer('Checking the folder {0} for flattened and type', location.get_folder_path())
                flattened_info = None
                if not location.get_folder_path().startswith('/NMProperties') and not location.get_folder_path() == '/':
                    flattened_info = self.__aliases.get_wlst_flattened_folder_info(location)
                if flattened_info is not None:
                    # make a message
                    self.__logger.fine('The mbean type {0} at location {1} is a flattened folder ', name,
                                 location.get_folder_path())
                    wlst_mbean = flattened_info.get_mbean_type()
                else:
                    wlst_mbean = self.__aliases.get_wlst_mbean_type(location)
                if wlst_mbean is None:
                    # create a message for this
                    self.__logger.finer('Mbean folder {0} at location {1} is not implemented in aliases for version {2}}',
                                  name, location.get_folder_path(), self.__model_context.get_target_wls_version())
                else:
                    folder_map[wlst_mbean] = name
                location.pop_location()
        return folder_map

    def build_location(self, location, model_name):

        name_token = self.__aliases.get_name_token(location)
        if name_token:
            location.add_name_token(name_token, all_utils.mbean_name(model_name)[0])
        return name_token

    def get_alias_get_required_attribute_list(self, location):
        get_required_list = []
        try:
            get_required_list = self.__aliases.get_wlst_get_required_attribute_names(location)
        except AliasException, ae:
            self.__logger.fine('WLSDPLYST-01130', location.get_folder_path(), ae.getLocalizedMessage(),
                               class_name=self.__class_name__, method_name='_method_name')
        return get_required_list

    def find_name_in_mbean_with_model_name(self, wlst_name, lower_case_map):
        """
        Find the mbean name or attribute name as known in WLST MBeanInfo, MBI and CMO methods.
        :param wlst_name: Name from the mentioned resources
        :param lower_case_map: map of the lower case names to original wlst names for the search
        :return: True if found in the map, name from the map
        """
        _method_name = '__find_attribute_name'
        self.__logger.entering(wlst_name, class_name=self.__class_name__, method_name=_method_name)
        result = wlst_name
        found = False

        if result in lower_case_map.keys():
            found = True
        else:
            lower_case = wlst_name.lower()
            result = _key_in_case_map(lower_case, lower_case_map)
            if result is None and lower_case.endswith('y'):
                result = _key_in_case_map(lower_case[:len(lower_case) - 1] + 'ies', lower_case_map)
            if result is None:
                result = _key_in_case_map(lower_case + 'es', lower_case_map)
            if result is None:
                result = _key_in_case_map(lower_case + 's', lower_case_map)
            if result is None:
                result = wlst_name
            else:
                found = True

        self.__logger.exiting(class_name=self.__class_name__, method_name=_method_name, result=result)
        return found, result


def _key_in_case_map(key, case_map):
    if key in case_map:
        return case_map[key]
    return None
