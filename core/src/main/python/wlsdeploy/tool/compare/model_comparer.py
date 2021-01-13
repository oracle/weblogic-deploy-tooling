"""
Copyright (c) 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import ALIAS_LIST_TYPES
from wlsdeploy.aliases.alias_constants import PROPERTIES
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.json.json_translator import COMMENT_MATCH
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import model_helper


class ModelComparer(object):
    """
    Class for comparing two WDT models.
    """
    _class_name = "ModelComparer"
    _logger = PlatformLogger('wlsdeploy.compare_model')

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
        :param past_folder: a folder in the past model
        :param location: the location for the specified folders
        :param attributes_location: the attribute location for the specified folders
        :return: a dictionary of differences between these folders
        """
        _method_name = '_compare_folders'

        # determine if the specified location has named folders, such as topology/Server
        has_named_folders = False
        if (location is not None) and not self._aliases.is_artificial_type_folder(location):
            has_named_folders = self._aliases.supports_multiple_mbean_instances(location) or \
                                self._aliases.requires_artificial_type_subfolder_handling(location)

        if has_named_folders:
            return self._compare_named_folders(current_folder, past_folder, location, attributes_location)
        else:
            return self._compare_folder_contents(current_folder, past_folder, location, attributes_location)

    def _compare_named_folders(self, current_folder, past_folder, location, attributes_location):
        """
        Compare current and past named folders using the specified locations.
        A named folder is a subfolder of a multiple-MBean folder, such as topology/Server/my-server
        :param current_folder: a folder in the current model
        :param past_folder: a folder in the past model
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
                pass

        # check for deleted names.
        # if name is not in the current folder, add its delete name.
        for name in past_folder:
            if name not in current_folder:
                delete_name = model_helper.get_delete_name(name)
                change_folder[delete_name] = PyOrderedDict()

        return change_folder

    def _compare_folder_contents(self, current_folder, past_folder, location, attributes_location):
        """
        Compare the contents of current and past folders using the specified locations.
        :param current_folder: a folder in the current model
        :param past_folder: a folder in the past model
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

                else:
                    next_location, next_attributes_location = self._get_next_location(location, key)
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

                else:
                    # if a folder was deleted, keep recursing through the past model.
                    # there may be named elements underneath that need to be deleted.
                    current_value = PyOrderedDict()
                    past_value = past_folder[key]
                    next_location, next_attributes_location = self._get_next_location(location, key)
                    next_change = self._compare_folders(current_value, past_value, next_location,
                                                        next_attributes_location)

                    if next_change:
                        change_folder[key] = next_change

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
            if attribute_type in ALIAS_LIST_TYPES:
                current_list = alias_utils.create_list(current_value, 'WLSDPLY-08001')
                previous_list = alias_utils.create_list(past_value, 'WLSDPLY-08000')

                change_list = list(previous_list)
                for item in current_list:
                    if item in previous_list:
                        change_list.remove(item)
                    else:
                        change_list.append(item)
                for item in previous_list:
                    if item not in current_list:
                        change_list.remove(item)
                        change_list.append(model_helper.get_delete_name(item))

                current_text = ','.join(current_list)
                previous_text = ','.join(previous_list)
                comment = key + ": '" + previous_text + "' -> '" + current_text + "'"
                _add_comment(comment, change_folder)
                change_folder[key] = ','.join(change_list)

            elif attribute_type == PROPERTIES:
                self._compare_properties(current_value, past_value, key, change_folder)

            else:
                if not isinstance(past_value, dict):
                    comment = key + ": '" + str(past_value) + "'"
                    _add_comment(comment, change_folder)
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
                    comment = property_key + ": '" + str(past_property_value) + "'"
                    _add_comment(comment, property_dict)
                    property_dict[property_key] = current_property_value
            else:
                property_dict[property_key] = current_property_value

        # property values don't support delete notation,
        # so any deleted keys in the current value will be ignored.

        if property_dict:
            change_folder[key] = property_dict

    def _check_key(self, key, location):
        """
        Determine if the specified key and location will be compared.
        :param key: the key to be checked
        :param location: the location to be checked
        :return: True if the key and location will be compared, False otherwise
        """
        _method_name = '_check_key'

        if (location is None) and (key == KUBERNETES):
            self._logger.info('WLSDPLY-05713', KUBERNETES, class_name=self._class_name, method_name=_method_name)
            return False
        return True


def _add_comment(comment, dictionary):
    """
    Add a comment to the specified dictionary
    :param comment: the comment text
    :param dictionary: the dictionary to be appended
    """
    # make comment key unique, key will not appear in output
    comment_key = COMMENT_MATCH + comment
    dictionary[comment_key] = comment
