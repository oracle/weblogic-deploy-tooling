"""
Copyright (c) 2021, 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.util import Properties

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import ALIAS_LIST_TYPES
from wlsdeploy.aliases.alias_constants import PROPERTIES
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import CRD_MODEL_SECTIONS
from wlsdeploy.aliases.model_constants import LIBRARY
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import model_helper
import wlsdeploy.util.unicode_helper as str_helper


class ModelComparer(object):
    """
    Class for comparing two WDT models.
    """
    _class_name = "ModelComparer"
    _logger = PlatformLogger('wlsdeploy.compare_model')

    SOURCE_PATH_FOLDERS = [APPLICATION, LIBRARY]

    def __init__(self, current_model_dict, past_model_dict, aliases, messages):
        """
        :param current_model_dict: the new dictionary being compared
        :param past_model_dict: the old dictionary being compared
        :param aliases: a reference to an Aliases class instance
        :param messages: a Set to be updated with messages
        """
        self._current_model_dict = current_model_dict
        self._past_model_dict = past_model_dict
        self._aliases = aliases
        self._messages = messages

    def compare_models(self):
        """
        Compare the current an past models from the top level.
        :return: a dictionary of differences between these models
        """
        self._messages.clear()
        location = None
        change_model_dict = self._compare_folders(self._current_model_dict, self._past_model_dict, location, location)
        return change_model_dict

    def _compare_folders(self, current_folder, past_folder, location, attributes_location):
        """
        Compare folders after determining if the folder has named sub-folders.
        :param current_folder: a folder in the current model
        :param past_folder: corresponding folder in the past model
        :param location: the location for the specified folders
        :param attributes_location: the attribute location for the specified folders
        :return: a dictionary of differences between these folders
        """

        # determine if the specified location has named folders, such as topology/Server
        has_named_folders = False
        has_security = False
        if (location is not None) and not self._aliases.is_artificial_type_folder(location):
            if self._aliases.supports_multiple_mbean_instances(location):
                has_named_folders = True
            elif self._aliases.requires_artificial_type_subfolder_handling(location):
                has_security = True

        if has_named_folders:
            return self._compare_named_folders(current_folder, past_folder, location, attributes_location)
        elif has_security:
            return self._compare_security_folders(current_folder, past_folder, location, attributes_location)
        else:
            return self._compare_folder_contents(current_folder, past_folder, location, attributes_location)

    def _compare_security_folders(self, current_folder, past_folder, location, attributes_location):
        """
        Compare current and past security configuration provider section. If a provider section has an entry
        that is different from the original, the entire provider section will be returned as differences between
        the two folders.
        :param current_folder: a folder in the current model
        :param past_folder: corresponding folder in the past model
        :param location: the location for the specified folders
        :param attributes_location: the attribute location for the specified folders
        :return: a dictionary of differences between these folders
        """
        providers = self._aliases.get_model_subfolder_names(location)
        matches = True
        custom = True
        if len(current_folder) == len(past_folder):
            curr_keys = current_folder.keys()
            past_keys = past_folder.keys()
            idx = 0
            while idx < len(curr_keys):
                if curr_keys[idx] == past_keys[idx]:
                    custom = curr_keys[idx] not in providers
                    next_curr_folder = current_folder[curr_keys[idx]]
                    next_curr_keys = next_curr_folder.keys()
                    next_past_folder = past_folder[past_keys[idx]]
                    next_past_keys = next_past_folder.keys()
                    next_idx = 0
                    while next_idx < len(next_curr_keys):
                        if next_curr_keys[next_idx] == next_past_keys[next_idx]:
                            if custom:
                                changes = self._compare_folder_sc_contents(next_curr_folder, next_past_folder,
                                                                           location, attributes_location)
                            else:
                                changes = self._compare_folder_contents(next_curr_folder, next_past_folder,
                                                                        location, attributes_location)
                            if changes:
                                matches = False
                                break
                        else:
                            matches = False
                            break
                        next_idx +=1
                else:
                    matches = False
                    break
                idx +=1
        else:
            matches = False
        if matches is False:
            self._messages.add(('WLSDPLY-05716', location.get_folder_path()))
            comment = "Replace entire Security Provider section "
            new_folder = PyOrderedDict()
            new_folder.update(current_folder)
            if new_folder:
                new_folder.addComment(new_folder.keys()[0], comment)
            return new_folder
        return PyOrderedDict()

    def _compare_named_folders(self, current_folder, past_folder, location, attributes_location):
        """
        Compare current and past named folders using the specified locations.
        A named folder is a subfolder of a multiple-MBean folder, such as topology/Server/my-server
        :param current_folder: a folder in the current model
        :param past_folder: corresponding folder in the past model
        :param location: the location for the specified folders
        :param attributes_location: the attribute location for the specified folders
        :return: a dictionary of differences between these folders
        """
        change_folder = PyOrderedDict()

        for name in current_folder:
            # check if name is present in both folders.
            # if found, compare the two folders recursively.
            if name in past_folder:
                next_current = current_folder[name]
                next_past = past_folder[name]
                location.add_name_token(self._aliases.get_name_token(location), name)
                attributes_location.add_name_token(self._aliases.get_name_token(attributes_location), name)
                changes = self._compare_folder_contents(next_current, next_past, location, attributes_location)
                if changes:
                    change_folder[name] = changes

            # check for added names.
            # if found, add the entire folder contents.
            else:
                change_folder[name] = current_folder[name]

        # check for deleted names.
        # if name is not in the current folder, add its delete name.
        for name in past_folder:
            if name not in current_folder:
                delete_name = model_helper.get_delete_name(name)
                change_folder[delete_name] = PyOrderedDict()

        return change_folder

    def _compare_folder_sc_contents(self, current_folder, past_folder, location, attributes_location):
        """
        Compare the contents of current and past folders, looking at attribute changes for a security provider.
        Return any changes so that calling routine will know changes occurred and the entire section will
        of the current folder will be marked as changed.
        :param current_folder: a folder in the current model
        :param past_folder: corresponding folder in the past model
        :param location: the location for the specified folders
        :param attributes_location: the attribute location for the specified folders
        :return: a dictionary of differences between these folders
        """
        change_folder = PyOrderedDict()

        # check if keys in the current folder are present in the past folder
        for key in current_folder:
            if not self._check_key(key, location):
                continue

            if key in past_folder:
                current_value = current_folder[key]
                past_value = past_folder[key]

                self._compare_attribute_sc(current_value, past_value, attributes_location, key, change_folder)

            else:
                # key is present the current folder, not in the past folder.
                # just add to the change folder, no further recursion needed.
                change_folder[key] = current_folder[key]

        # check if keys in the past folder are not in the current folder
        for key in past_folder:
            if not self._check_key(key, location):
                continue

            if key not in current_folder:
                change_folder[key] = past_folder[key]

        self._finalize_folder(current_folder, past_folder, change_folder, location)
        return change_folder

    def _compare_folder_contents(self, current_folder, past_folder, location, attributes_location):
        """
        Compare the contents of current and past folders using the specified locations.
        :param current_folder: a folder in the current model
        :param past_folder: corresponding folder in the past model
        :param location: the location for the specified folders
        :param attributes_location: the attribute location for the specified folders
        :return: a dictionary of differences between these folders
        """
        change_folder = PyOrderedDict()

        attribute_names = []
        if attributes_location is not None:
            attribute_names = self._aliases.get_model_attribute_names(attributes_location)

        # check if keys in the current folder are present in the past folder
        for key in current_folder:
            if not self._check_key(key, location):
                continue

            if key in past_folder:
                current_value = current_folder[key]
                past_value = past_folder[key]

                if key in attribute_names:
                    self._compare_attribute(current_value, past_value, attributes_location, key, change_folder)

                else:  # could be a folder
                    next_location, next_attributes_location = self._get_next_location(location, key)
                    if self._aliases.is_model_location_valid(next_location):
                        next_change = self._compare_folders(current_value, past_value, next_location,
                                                            next_attributes_location)

                        if next_change:
                            change_folder[key] = next_change

            else:
                # key is present the current folder, not in the past folder.
                # just add to the change folder, no further recursion needed.
                change_folder[key] = current_folder[key]

        # check if keys in the past folder are not in the current folder
        for key in past_folder:
            if not self._check_key(key, location):
                continue

            if key not in current_folder:
                if key in attribute_names:
                    # if an attribute was deleted, just add a message
                    change_path = self._aliases.get_model_folder_path(location) + "/" + key
                    self._messages.add(('WLSDPLY-05701', change_path))

                else:  # could be a folder
                    next_location, next_attributes_location = self._get_next_location(location, key)
                    if self._aliases.is_model_location_valid(next_location):
                        # if a folder was deleted, keep recursing through the past model.
                        # there may be named elements underneath that need to be deleted.
                        current_value = PyOrderedDict()
                        past_value = past_folder[key]
                        next_change = self._compare_folders(current_value, past_value, next_location,
                                                            next_attributes_location)

                        if next_change:
                            change_folder[key] = next_change

        self._finalize_folder(current_folder, past_folder, change_folder, location)
        return change_folder

    def _get_next_location(self, location, key):
        """
        Get the next locations for the specified key and location.
        :param location: the current location (None indicates model root)
        :param key: the key of the next location
        :return: a tuple with the next location and the next attributes location
        """
        if location is None:
            next_location = LocationContext()
            next_attributes_location = self._aliases.get_model_section_attribute_location(key)
        else:
            next_location = LocationContext(location)
            next_location.append_location(key)
            next_location.add_name_token(self._aliases.get_name_token(next_location), 'FOLDER')
            next_attributes_location = next_location

        return next_location, next_attributes_location

    def _compare_attribute_sc(self, current_value, past_value, location, key, change_folder):
        """
        Compare values of an attribute from the current and past folders.
        The changed value will signal the calling method that the entire new
        :param current_value: the value from the current model
        :param past_value: the value from the past model
        :param key: the key of the attribute
        :param change_folder: the folder in the change model to be updated
        :param location: the location for attributes in the specified folders
        """
        if current_value != past_value:
            if type(current_value) == list:
                current_list = list(current_value)
                past_list = list(past_value)
                self._compare_lists(current_list, past_list, key, change_folder)

            elif isinstance(current_value, Properties):
                self._compare_properties(current_value, past_value, key, change_folder)

            else:
                change_folder[key] = current_value

    def _compare_attribute(self, current_value, past_value, location, key, change_folder):
        """
        Compare values of an attribute from the current and past folders.
        The change value and any comments will be added to the change folder.
        :param current_value: the value from the current model
        :param past_value: the value from the past model
        :param key: the key of the attribute
        :param change_folder: the folder in the change model to be updated
        :param location: the location for attributes in the specified folders
        """
        if current_value != past_value:
            attribute_type = self._aliases.get_model_attribute_type(location, key)
            if self._is_jvm_args_key(key, location):
                current_text = self._get_jvm_args_text(current_value)
                previous_text = self._get_jvm_args_text(past_value)
                if current_text != previous_text:
                    comment = key + ": '" + str_helper.to_string(previous_text) + "'"
                    change_folder.addComment(key, comment)
                    change_folder[key] = current_text

            elif attribute_type in ALIAS_LIST_TYPES:
                current_list = alias_utils.create_list(current_value, 'WLSDPLY-08001')
                previous_list = alias_utils.create_list(past_value, 'WLSDPLY-08000')
                self._compare_lists(current_list, previous_list, key, change_folder)

            elif attribute_type == PROPERTIES:
                self._compare_properties(current_value, past_value, key, change_folder)

            else:
                if not isinstance(past_value, dict):
                    comment = key + ": '" + str_helper.to_string(past_value) + "'"
                    change_folder.addComment(key, comment)
                change_folder[key] = current_value

    def _compare_properties(self, current_value, past_value, key, change_folder):
        """
        Compare values of a properties attribute from the current and past folders.
        The change value and any comments will be added to the change folder.
        :param current_value: the value from the current model
        :param past_value: the value from the past model
        :param key: the key of the attribute
        :param change_folder: the folder in the change model to be updated
        """
        property_dict = PyOrderedDict()
        for property_key in current_value:
            current_property_value = current_value[property_key]
            if property_key in past_value:
                past_property_value = past_value[property_key]
                if past_property_value != current_property_value:
                    comment = property_key + ": '" + str_helper.to_string(past_property_value) + "'"
                    property_dict.addComment(property_key, comment)
                    property_dict[property_key] = current_property_value
            else:
                property_dict[property_key] = current_property_value

        # property values don't support delete notation,
        # so any deleted keys in the current value will be ignored.

        if property_dict:
            change_folder[key] = property_dict

    def _compare_lists(self, current_list, past_list, key, change_folder):
        """
        Compare values of a list attribute from the current and past folders.
        The change value and any comments will be added to the change folder.
        :param current_list: the value from the current model
        :param past_list: the value from the past model
        :param key: the key of the attribute
        :param change_folder: the folder in the change model to be updated
        """
        change_list = list(past_list)
        for item in current_list:
            if item in past_list:
                change_list.remove(item)
            else:
                change_list.append(item)
        for item in past_list:
            if item not in current_list:
                change_list.remove(item)
                change_list.append(model_helper.get_delete_name(item))

        current_text = ','.join(current_list)
        previous_text = ','.join(past_list)
        comment = key + ": '" + previous_text + "' -> '" + current_text + "'"
        change_folder.addComment(key, comment)
        change_folder[key] = ','.join(change_list)

    def _check_key(self, key, location):
        """
        Determine if the specified key and location will be compared.
        :param key: the key to be checked
        :param location: the location to be checked
        :return: True if the key and location will be compared, False otherwise
        """
        _method_name = '_check_key'

        if (location is None) and (key in CRD_MODEL_SECTIONS):
            self._logger.info('WLSDPLY-05713', key, class_name=self._class_name, method_name=_method_name)
            return False
        return True

    def _is_jvm_args_key(self, key, location):
        """
        Determine if the specified attribute requires special JVM argument processing.
        :param key: the key to be checked
        :param location: the location to be checked
        :return: True if the attribute requires special processing, False otherwise
        """
        set_method_info = self._aliases.get_model_mbean_set_method_attribute_names_and_types(location)
        return key in set_method_info and set_method_info[key]['set_method'] == 'set_jvm_args'

    def _get_jvm_args_text(self, value):
        """
        Return the normalized text for the specified JVM arguments value.
        These attributes have special handling for create and deploy,
        so list delimiter comparison will not cover all the cases.
        :param value: the value to be converted, may be a list, string, or None
        :return: the normalized text value
        """
        if isinstance(value, basestring):
            value = value.split()
        if isinstance(value, list):
            return ' '.join(value)
        return value

    def _finalize_folder(self, current_folder, past_folder, change_folder, location):
        """
        Perform any adjustments after a folder has been evaluated.
        :param current_folder: folder in the current model
        :param past_folder: corresponding folder in the past model
        :param change_folder: the folder with the changed attributes and sub-folders
        :param location: the location for the specified folders
        """
        folder_path = []
        if location is not None:
            folder_path = location.get_model_folders()

        # Application and Library should include all attributes from past and change folders.
        # Changes to source path or underlying jar may require redeployment.
        if (len(folder_path) == 1) and (folder_path[0] in self.SOURCE_PATH_FOLDERS):
            if change_folder:
                past_keys = dictionary_utils.get_dictionary_attributes(past_folder)
                for past_key in past_keys:
                    attribute_type = self._aliases.get_model_attribute_type(location, past_key)

                    if past_key not in change_folder.keys():
                        key_value = dictionary_utils.get_element(past_folder, past_key)
                        if key_value is not None:
                            change_folder[past_key] = key_value

                    elif attribute_type in ALIAS_LIST_TYPES:  # update list with past + change items (ex: Target)
                        past_list = alias_utils.create_list(past_folder[past_key], 'WLSDPLY-08001')
                        change_list = alias_utils.create_list(change_folder[past_key], 'WLSDPLY-08000')
                        new_list = list()
                        for past_item in past_list:
                            past_delete_item = model_helper.get_delete_name(past_item)
                            if past_item not in change_list and past_delete_item not in change_list:
                                new_list.append(past_item)
                        new_list.extend(change_list)
                        change_folder[past_key] = ','.join(new_list)
