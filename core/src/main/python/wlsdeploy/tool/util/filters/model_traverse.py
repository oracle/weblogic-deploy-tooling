# Copyright (c) 2021, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.logging.platform_logger import PlatformLogger

_class_name = 'ModelTraverse'


class ModelTraverse:
    """
    This class traverses all model folders and attributes.
    Sub-classes can override specific methods to avoid re-implementing the recursive traversal.
    """
    def __init__(self, model_context, wlst_mode, exception_type):
        self._aliases = Aliases(model_context=model_context, wlst_mode=wlst_mode, exception_type=exception_type)
        self._logger = PlatformLogger('wlsdeploy.model_traverse')

    def traverse_model(self, root_dict):
        section_names = [DOMAIN_INFO, TOPOLOGY, RESOURCES]
        for section_name in section_names:
            self.traverse_section(section_name, root_dict,
                                  self._aliases.get_model_section_top_level_folder_names(section_name))

    def traverse_section(self, model_section_key, model_dict, valid_section_folders):
        if model_section_key not in model_dict.keys():
            return

        # only specific top-level sections have attributes
        attribute_location = self._aliases.get_model_section_attribute_location(model_section_key)
        valid_attr_infos = []

        if attribute_location is not None:
            valid_attr_infos = self._aliases.get_model_attribute_names_and_types(attribute_location)

        model_section_dict = model_dict[model_section_key]
        # use items(), not iteritems(), to avoid ConcurrentModificationException if dict is modified
        for section_dict_key, section_dict_value in model_section_dict.items():
            # section_dict_key is the name of a folder or attribute in the section.

            if section_dict_key in valid_attr_infos:
                # section_dict_key is the name of an attribute in the section
                self.traverse_attribute(model_section_dict, section_dict_key, attribute_location)

            elif section_dict_key in valid_section_folders:
                # section_dict_key is a folder under the model section

                # Append section_dict_key to location context
                model_location = LocationContext()
                model_location.append_location(section_dict_key)

                # Call self.traverse_folder() passing in section_dict_value as the model_node to process
                self.traverse_folder(section_dict_value, model_location)

    def traverse_folder(self, model_node, model_location):
        """
        Traverse a folder that may have named sub-folders (such as Server), artificial named sub-folders (such
        as a security provider type), or its own sub-folders and attributes (such as .
        """

        # avoid checking folder type if is_artificial_type_folder
        is_multiple = not self._aliases.is_artificial_type_folder(model_location) and \
            (self._aliases.supports_multiple_mbean_instances(model_location) or
                self._aliases.requires_artificial_type_subfolder_handling(model_location))

        if is_multiple:
            for name in model_node:
                expanded_name = name
                new_location = LocationContext(model_location)
                name_token = self._aliases.get_name_token(new_location)
                if name_token is not None:
                    new_location.add_name_token(name_token, expanded_name)
                value_dict = model_node[name]
                self.traverse_node(value_dict, new_location)
        else:
            name_token = self._aliases.get_name_token(model_location)
            if name_token is not None:
                name = model_location.get_name_for_token(name_token)
                if name is None:
                    name = '%s-0' % name_token
                model_location.add_name_token(name_token, name)
            self.traverse_node(model_node, model_location)

    def traverse_node(self, model_node, model_location):
        """
        Traverse a node that contains only attributes, non-named sub-folders, and artificial type folders.
        """
        valid_folder_keys = self._aliases.get_model_subfolder_names(model_location)
        valid_attr_infos = self._aliases.get_model_attribute_names_and_types(model_location)

        # use items(), not iteritems(), to avoid ConcurrentModificationException if node is modified
        for key, value in model_node.items():
            if key in valid_folder_keys:
                new_location = LocationContext(model_location).append_location(key)
                self.traverse_folder(value, new_location)

            elif key in valid_attr_infos:
                self.traverse_attribute(model_node, key, model_location)

            else:
                self.unrecognized_field(model_node, key, model_location)

    def traverse_attribute(self, model_dict, attribute_name, model_location):
        """
        Called for each attribute that is encountered in the model.
        """
        pass

    def unrecognized_field(self, model_dict, key, model_location):
        """
        Called if a key in a model dictionary is not recognized as an attribute or a sub-folder.
        This can happen if:
        - the key is the name of a custom security provider, usually a full Java class name
        - the key is an attribute that is not applicable for the current WLS version or offline/online status
        - the field is not a valid attribute or folder name
        """
        pass
