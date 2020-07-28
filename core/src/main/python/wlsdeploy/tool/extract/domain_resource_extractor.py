"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.io import File
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import BOOLEAN
from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.exception import exception_helper
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_translator import PythonToFile
from wlsdeploy.yaml.dictionary_list import DictionaryList

API_VERSION = 'apiVersion'
CHANNELS = 'channels'
CLUSTERS = 'clusters'
CLUSTER_NAME = 'clusterName'
DOMAIN_HOME = 'domainHome'
IMAGE = 'image'
IMAGE_PULL_POLICY = 'imagePullPolicy'
IMAGE_PULL_SECRETS = 'imagePullSecrets'
K_NAME = 'name'
KIND = 'kind'
METADATA = 'metadata'
NAMESPACE = 'namespace'
NEVER = 'Never'
REPLICAS = 'replicas'
SPEC = 'spec'
WEBLOGIC_CREDENTIALS_SECRET = 'webLogicCredentialsSecret'

DEFAULT_API_VERSION = 'weblogic.oracle/v6'
DEFAULT_KIND = 'Domain'
DEFAULT_WEBLOGIC_CREDENTIALS_SECRET = PASSWORD_TOKEN
DEFAULT_IMAGE = PASSWORD_TOKEN
DEFAULT_IMAGE_PULL_SECRETS = PASSWORD_TOKEN


class DomainResourceExtractor:
    """
    Create a domain resource file for use with Kubernetes deployment.
    """
    _class_name = "DomainResourceExtractor"

    # the name field keys corresponding to named model elements
    NAME_KEY_MAP = {
        CHANNELS: 'channelName',
        CLUSTERS: CLUSTER_NAME
    }

    def __init__(self, model, model_context, aliases, logger):
        self._model = model
        self._model_context = model_context
        self._aliases = aliases
        self._logger = logger
        return

    def extract(self):
        """
        Deploy resource model elements at the domain level, including multi-tenant elements.
        """
        _method_name = 'extract'

        resource_file = self._model_context.get_domain_resource_file()
        self._logger.info("WLSDPLY-10000", resource_file, method_name=_method_name, class_name=self._class_name)

        # create the target file directory, if needed
        resource_dir = File(resource_file).getParentFile()
        if (not resource_dir.isDirectory()) and (not resource_dir.mkdirs()):
            mkdir_ex = exception_helper.create_deploy_exception('WLSDPLY-10001', resource_dir)
            raise mkdir_ex

        # build the resource file structure from the kubernetes section of the model
        resource_dict = self._create_domain_resource_dictionary()

        # revise the resource file structure with values from command line, and elsewhere in model
        self._update_resource_dictionary(resource_dict)

        # write the resource file structure to the output file
        writer = PythonToFile(resource_dict)

        writer.write_to_file(resource_file)
        return

    def _create_domain_resource_dictionary(self):
        """
        Build the resource file structure from the kubernetes section of the model.
        :return: the resource file structure
        """
        kubernetes_map = self._model.get_model_kubernetes()

        resource_dict = PyOrderedDict()

        attribute_location = self._aliases.get_model_section_attribute_location(KUBERNETES)
        top_attributes_map = self._aliases.get_model_attribute_names_and_types(attribute_location)
        top_folders = self._aliases.get_model_section_top_level_folder_names(KUBERNETES)

        self._process_fields(kubernetes_map, top_folders, top_attributes_map, LocationContext(), resource_dict)
        return resource_dict

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

    def _update_resource_dictionary(self, resource_dict):
        """
        Revise the resource file structure with values from defaults, command line, and elsewhere in model
        :param resource_dict: the resource file dictionary
        """
        _method_name = '_update_resource_dictionary'

        # add API version if not present
        if API_VERSION not in resource_dict:
            resource_dict[API_VERSION] = DEFAULT_API_VERSION

        # add kind if not present
        if KIND not in resource_dict:
            resource_dict[KIND] = DEFAULT_KIND

        # add a metadata section if not present, since we'll at least add name
        if METADATA not in resource_dict:
            resource_dict[METADATA] = PyOrderedDict()
        metadata_section = resource_dict[METADATA]

        # if metadata name not present, use the domain name from the model, or default
        if K_NAME not in metadata_section:
            domain_name = dictionary_utils.get_element(self._model.get_model_topology(), NAME)
            if domain_name is None:
                domain_name = DEFAULT_WLS_DOMAIN_NAME
            metadata_section[K_NAME] = domain_name

        # add a spec section if not present, since we'll at least add domain home
        if SPEC not in resource_dict:
            resource_dict[SPEC] = PyOrderedDict()
        spec_section = resource_dict[SPEC]

        # only set domain home if it is not present in spec section
        if DOMAIN_HOME not in spec_section:
            spec_section[DOMAIN_HOME] = self._model_context.get_domain_home()

        # only set image if it is not present in spec section
        if IMAGE not in spec_section:
            spec_section[IMAGE] = DEFAULT_IMAGE

        # imagePullSecrets is required unless imagePullPolicy is Never
        pull_secrets_required = True
        if IMAGE_PULL_POLICY in spec_section:
            policy = str(spec_section[IMAGE_PULL_POLICY])
            pull_secrets_required = (policy != NEVER)

        # if imagePullSecrets required and not present, add a list with one FIX ME value
        if pull_secrets_required and (IMAGE_PULL_SECRETS not in spec_section):
            secrets_list = DictionaryList()
            secrets_list.append({'name': DEFAULT_IMAGE_PULL_SECRETS})
            spec_section[IMAGE_PULL_SECRETS] = secrets_list

        # if webLogicCredentialsSecret not present, add it using the FIX ME value
        if WEBLOGIC_CREDENTIALS_SECRET not in spec_section:
            spec_section[WEBLOGIC_CREDENTIALS_SECRET] = DEFAULT_WEBLOGIC_CREDENTIALS_SECRET

        # only update clusters if section is not present in spec section
        if CLUSTERS not in spec_section:
            topology = self._model.get_model_topology()
            model_clusters = dictionary_utils.get_dictionary_element(topology, CLUSTER)
            if len(model_clusters) > 0:
                cluster_list = DictionaryList()
                spec_section[CLUSTERS] = cluster_list
                for cluster_name, cluster_values in model_clusters.items():
                    server_count = k8s_helper.get_server_count(cluster_name, cluster_values, self._model.get_model())
                    cluster_dict = PyOrderedDict()
                    cluster_dict[CLUSTER_NAME] = cluster_name
                    cluster_dict[REPLICAS] = server_count

                    self._logger.info("WLSDPLY-10002", cluster_name, server_count, method_name=_method_name,
                                      class_name=self._class_name)
                    cluster_list.append(cluster_dict)
        return


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
