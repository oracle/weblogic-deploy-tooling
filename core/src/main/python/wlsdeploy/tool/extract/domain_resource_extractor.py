"""
Copyright (c) 2019, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import BOOLEAN
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_translator import PythonToFile
from wlsdeploy.yaml.dictionary_list import DictionaryList

CHANNELS = 'channels'
CLUSTERS = 'clusters'
EXPOSE_ADMIN_T3_CHANNEL = 'exposeAdminT3Channel'
NAMESPACE = 'namespace'


class DomainResourceExtractor:
    """
    Create a domain resource file for use with Kubernetes deployment.
    """
    _class_name = "DomainResourceExtractor"

    # the name field keys corresponding to named model elements
    NAME_KEY_MAP = {
        CHANNELS: 'channelName',
        CLUSTERS: 'clusterName'
    }

    def __init__(self, model, model_context, aliases, logger):
        self._model = model
        self._model_context = model_context
        self._aliases = AliasHelper(aliases, logger, ExceptionType.DEPLOY)
        self._logger = logger
        return

    def extract(self):
        """
        Deploy resource model elements at the domain level, including multi-tenant elements.
        """
        _method_name = 'extract'

        resource_file = self._model_context.get_domain_resource_file()
        self._logger.info("WLSDPLY-10000", resource_file, method_name=_method_name, class_name=self._class_name)

        kubernetes_map = self._model.get_model_kubernetes()

        resource_dict = PyOrderedDict()

        attribute_location = self._aliases.get_model_section_attribute_location(KUBERNETES)
        top_attributes_map = self._aliases.get_model_attribute_names_and_types(attribute_location)
        top_folders = self._aliases.get_model_section_top_level_folder_names(KUBERNETES)

        self._process_fields(kubernetes_map, top_folders, top_attributes_map, LocationContext(), resource_dict)

        resource_dir = File(resource_file).getParentFile()
        if (not resource_dir.isDirectory()) and (not resource_dir.mkdirs()):
            mkdir_ex = exception_helper.create_deploy_exception('WLSDPLY-10001', resource_dir)
            raise mkdir_ex

        writer = PythonToFile(resource_dict)

        writer.write_to_file(resource_file)
        return

    def _process_fields(self, model_dict, folder_names, attributes_map, location, target_dict):
        """
        Transfer folders and attributes from the model dictionary to the target domain resource dictionary.
        For the top level, the folders and attributes are not derived directly from the location.
        :param model_dict: the source model dictionary
        :param folder_names: the names of the folders at this location
        :param attributes_map: the map of attribute names to types for this location
        :param location: the location used for alias processing
        :param target_dict: the target dictionary for the domain resource file.
       """
        for key, model_value in model_dict.items():
            if key in attributes_map.keys():
                type_name = attributes_map[key]
                target_dict[key] = _get_target_value(model_value, type_name)

            elif key in folder_names:
                child_location = LocationContext(location).append_location(key)

                if self._aliases.supports_multiple_mbean_instances(child_location):
                    target_dict[key] = self._build_dictionary_list(key, model_value, child_location)
                else:
                    if key not in target_dict:
                        target_dict[key] = PyOrderedDict()
                    target_child_dict = target_dict[key]
                    self._process_location_fields(model_value, child_location, target_child_dict)
        return

    def _process_location_fields(self, model_dict, location, target_dict):
        """
        Transfer folders and attributes from the model dictionary to the target domain resource dictionary.
        Below the top level, the folders and attributes can be derived from the location.
        :param model_dict: the source model dictionary
        :param location: the location used for alias processing
        :param target_dict: the target dictionary for the domain resource file.
       """
        attributes_map = self._aliases.get_model_attribute_names_and_types(location)
        folder_names = self._aliases.get_model_subfolder_names(location)
        self._process_fields(model_dict, folder_names, attributes_map, location, target_dict)
        return

    def _build_dictionary_list(self, model_key, name_dictionary, location):
        """
        Build a dictionary list object based on the name dictionary and location.
        :param name_dictionary: a dictionary containing named levels
        :param location: the location used for alias resolution
        :return:
        """
        child_list = DictionaryList()
        for name in name_dictionary:
            model_named_dict = name_dictionary[name]
            name_key = self._get_name_key(model_key)
            target_list_dict = PyOrderedDict()
            target_list_dict[name_key] = name
            self._process_location_fields(model_named_dict, location, target_list_dict)
            child_list.append(target_list_dict)
        return child_list

    def _get_name_key(self, key):
        """
        Return the key to be used for the name in a dictionary list element.
        :param key: the folder key in the model
        :return: the name key
        """
        key = dictionary_utils.get_element(self.NAME_KEY_MAP, key)
        if key is not None:
            return key
        return 'name'


def _get_target_value(model_value, type_name):
    """
    Return the value for the specified attribute value, to be used in the domain resource file.
    :param model_value: the value to be checked
    :param type_name: the alias type name of the value
    :return: the formatted value
    """
    if type_name == BOOLEAN:
        # the model values can be true, false, 1, 0, etc.
        # target boolean values must be 'true' or 'false'
        return alias_utils.convert_to_type('boolean', model_value)

    return model_value
