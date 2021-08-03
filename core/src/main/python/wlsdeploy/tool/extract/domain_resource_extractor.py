"""
Copyright (c) 2020, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import re

from java.io import File
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.alias_constants import PASSWORD_TOKEN
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.tool.extract import wko_schema_helper
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_translator import PythonToFile

API_VERSION = 'apiVersion'
CHANNELS = 'channels'
CLUSTERS = 'clusters'
CLUSTER_NAME = 'clusterName'
CONFIGURATION = 'configuration'
DOMAIN_HOME = 'domainHome'
DOMAIN_HOME_SOURCE_TYPE = 'domainHomeSourceType'
DOMAIN_TYPE = 'domainType'
IMAGE = 'image'
IMAGE_PULL_POLICY = 'imagePullPolicy'
IMAGE_PULL_SECRETS = 'imagePullSecrets'
K_NAME = 'name'
KIND = 'kind'
METADATA = 'metadata'
MODEL = 'model'
NAMESPACE = 'namespace'
NEVER = 'Never'
REPLICAS = 'replicas'
SECRETS = 'secrets'
SPEC = 'spec'
WEBLOGIC_CREDENTIALS_SECRET = 'webLogicCredentialsSecret'

DEFAULT_API_VERSION = 'weblogic.oracle/v8'
DEFAULT_KIND = 'Domain'
DEFAULT_WEBLOGIC_CREDENTIALS_SECRET = PASSWORD_TOKEN
DEFAULT_IMAGE = PASSWORD_TOKEN
DEFAULT_IMAGE_PULL_SECRETS = PASSWORD_TOKEN
DEFAULT_SOURCE_TYPE = 'Image'

MULTI_KEYS = {
    'spec/adminServer/adminService/channels': 'channelName',
    'spec/clusters': 'clusterName'
}

_secret_pattern = re.compile("@@SECRET:([\\w.-]+):[\\w.-]+@@")


class DomainResourceExtractor:
    """
    Create a domain resource file for use with Kubernetes deployment.
    """
    _class_name = "DomainResourceExtractor"

    def __init__(self, model, model_context, logger):
        self._model = model
        self._model_context = model_context
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
        writer.set_yaml_hyphenate_yaml_lists(True)
        writer.write_to_file(resource_file)
        return

    def _create_domain_resource_dictionary(self):
        """
        Build the resource file structure from the kubernetes section of the model.
        :return: the resource file structure
        """
        kubernetes_map = self._model.get_model_kubernetes()

        resource_dict = PyOrderedDict()

        schema = wko_schema_helper.get_domain_resource_schema(ExceptionType.DEPLOY)

        model_path = KUBERNETES + ":"
        self._process_folder(kubernetes_map, schema, resource_dict, None, model_path)
        return resource_dict

    def _process_folder(self, model_dict, schema_folder, target_dict, schema_path, model_path):
        """
        Transfer folders and attributes from the model dictionary to the target domain resource dictionary.
        :param model_dict: the source model dictionary
        :param schema_folder: the schema for this folder
        :param target_dict: the target dictionary for the domain resource file.
        :param schema_path: the path of schema elements (no multi-element names), used for supported check
        :param model_path: the path of model elements (including multi-element names), used for logging
        """
        folder_properties = schema_folder["properties"]

        for key, model_value in model_dict.items():
            properties = folder_properties[key]

            if wko_schema_helper.is_single_folder(properties):
                # single object instance
                next_schema_path = wko_schema_helper.append_path(schema_path, key)
                next_model_path = model_path + "/" + key
                if not wko_schema_helper.is_unsupported_folder(next_schema_path):
                    next_target_dict = PyOrderedDict()
                    target_dict[key] = next_target_dict
                    self._process_folder(model_value, properties, next_target_dict, next_schema_path,
                                         next_model_path)

            elif wko_schema_helper.is_multiple_folder(properties):
                # multiple object instances
                next_schema_path = wko_schema_helper.append_path(schema_path, key)
                next_model_path = model_path + "/" + key
                if not wko_schema_helper.is_unsupported_folder(next_schema_path):
                    item_info = wko_schema_helper.get_array_item_info(properties)
                    target_dict[key] = \
                        self._process_multiple_folder(model_value, item_info, next_schema_path, next_model_path)

            elif wko_schema_helper.is_simple_map(properties):
                # map of key / value pairs
                target_dict[key] = model_value

            else:
                # simple type or array of simple type, such as number, string
                property_type = wko_schema_helper.get_type(properties)
                target_dict[key] = _get_target_value(model_value, property_type)

    def _process_multiple_folder(self, model_value, item_info, schema_path, model_path):
        """
        Process a multiple-element model section.
        There should be a dictionary of names, each containing a sub-folder.
        :param model_value: the model contents for a folder
        :param item_info: describes the contents of the sub-folder for each element
        :param schema_path: the path of schema elements (no multi-element names), used for supported check
        :param model_path: the path of model elements (including multi-element names), used for logging
        """
        child_list = list()
        for name in model_value:
            name_map = model_value[name]
            next_target_dict = PyOrderedDict()
            next_model_path = model_path + "/" + name
            self._process_folder(name_map, item_info, next_target_dict, schema_path, next_model_path)

            # see if the model name should become an attribute in the target dict
            mapped_name = get_mapped_key(schema_path)
            properties = wko_schema_helper.get_properties(item_info)
            if (mapped_name in properties.keys()) and (mapped_name not in next_target_dict.keys()):
                _add_to_top(next_target_dict, mapped_name, name)

            child_list.append(next_target_dict)

        return child_list

    def _update_resource_dictionary(self, resource_dict):
        """
        Revise the resource file structure with values from defaults, command line, and elsewhere in model
        :param resource_dict: the resource file dictionary
        """
        _method_name = '_update_resource_dictionary'

        # add a metadata section if not present, since we'll at least add name
        if METADATA not in resource_dict:
            _add_to_top(resource_dict, METADATA, PyOrderedDict())
        metadata_section = resource_dict[METADATA]

        # add kind if not present
        if KIND not in resource_dict:
            _add_to_top(resource_dict, KIND, DEFAULT_KIND)

        # add API version if not present
        if API_VERSION not in resource_dict:
            _add_to_top(resource_dict, API_VERSION, DEFAULT_API_VERSION)

        # if metadata name not present, use the domain name from the model, or default
        if K_NAME not in metadata_section:
            domain_name = dictionary_utils.get_element(self._model.get_model_topology(), NAME)
            if domain_name is None:
                domain_name = DEFAULT_WLS_DOMAIN_NAME
            domain_name = k8s_helper.get_domain_uid(domain_name)
            metadata_section[K_NAME] = domain_name
        domain_uid = metadata_section[K_NAME]

        # add a spec section if not present, since we'll at least add domain home
        if SPEC not in resource_dict:
            resource_dict[SPEC] = PyOrderedDict()
        spec_section = resource_dict[SPEC]

        # only set domain home if it is not present in spec section
        if DOMAIN_HOME not in spec_section:
            spec_section[DOMAIN_HOME] = self._model_context.get_domain_home()

        # only set domain home source type if it is not present in spec section
        if DOMAIN_HOME_SOURCE_TYPE not in spec_section:
            spec_section[DOMAIN_HOME_SOURCE_TYPE] = DEFAULT_SOURCE_TYPE

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
            secrets_list = list()
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
                cluster_list = list()
                spec_section[CLUSTERS] = cluster_list
                for cluster_name, cluster_values in model_clusters.items():
                    if REPLICAS in spec_section:
                        server_count = spec_section[REPLICAS]
                    else:
                        server_count = k8s_helper.get_server_count(cluster_name, cluster_values,
                                                                   self._model.get_model())
                    cluster_dict = PyOrderedDict()
                    cluster_dict[CLUSTER_NAME] = cluster_name
                    cluster_dict[REPLICAS] = server_count

                    self._logger.info("WLSDPLY-10002", cluster_name, server_count, method_name=_method_name,
                                      class_name=self._class_name)
                    cluster_list.append(cluster_dict)

        # create a configuration section in spec if needed
        if CONFIGURATION not in spec_section:
            spec_section[CONFIGURATION] = PyOrderedDict()
        configuration_section = spec_section[CONFIGURATION]

        # create a model section in configuration if needed
        if MODEL not in configuration_section:
            configuration_section[MODEL] = PyOrderedDict()
        model_section = configuration_section[MODEL]

        # set domainType if not specified
        if DOMAIN_TYPE not in model_section:
            model_section[DOMAIN_TYPE] = self._model_context.get_domain_type()

        if SECRETS in configuration_section:
            # if secrets specified, convert them to a hyphen list
            secrets = alias_utils.convert_to_model_type("list", configuration_section[SECRETS], MODEL_LIST_DELIMITER)
            secrets_list = list()
            secrets_list.extend(secrets)

        else:
            # pull the secrets from the model
            secrets_list = list()
            _add_secrets(self._model.get_model(), secrets_list, domain_uid)

        if secrets_list:
            configuration_section[SECRETS] = secrets_list

        return


def _get_target_value(model_value, type_name):
    """
    Return the value for the specified attribute value, to be used in the domain resource file.
    :param model_value: the value to be checked
    :param type_name: the schema type name of the value
    :return: the formatted value
    """
    if type_name == 'boolean':
        # the model values can be true, false, 1, 0, etc.
        # target boolean values must be 'true' or 'false'
        return alias_utils.convert_to_type('boolean', model_value)

    if type_name == 'array':
        # the model values can be 'abc,123'.
        # target values must be a list object.
        return alias_utils.convert_to_type('list', model_value, delimiter=MODEL_LIST_DELIMITER)

    return model_value


def _add_secrets(folder, secrets, domain_uid):
    """
    Recursively add any secrets found in the specified folder.
    :param folder: the folder to be checked
    :param secrets: the list to be appended
    """
    for name in folder:
        value = folder[name]
        if isinstance(value, dict):
            _add_secrets(value, secrets, domain_uid)
        else:
            text = str(value)

            # secrets created by discover or prepareModel use this environment variable.
            # if it wasn't resolved from the environment, replace with model's domain UID.
            text = text.replace("@@ENV:DOMAIN_UID@@", domain_uid)

            matches = _secret_pattern.findall(text)
            for secret_name in matches:
                if secret_name not in secrets:
                    secrets.append(secret_name)


def get_mapped_key(schema_path):
    """
    Because the WDT model does not support hyphenated lists, the name of each item in a
    multiple folder sometimes corresponds to one of its attributes, usually "name".
    If a different attribute name is used for the path, return that name.
    If the default 'name' is returned, caller should verify that it is an available attribute.
    :param schema_path: the slash-delimited path of the elements (no multi-element names)
    :return: the attribute key to be used
    """
    mapped_key = dictionary_utils.get_element(MULTI_KEYS, schema_path)
    if mapped_key is not None:
        return mapped_key
    return 'name'


def _add_to_top(dictionary, key, item):
    """
    Add an item to the beginning of an ordered dictionary.
    :param dictionary: the dictionary
    :param key: the key of the item to be added
    :param item: the item to be added
    """
    temp_dict = PyOrderedDict()
    for each_key in dictionary:
        temp_dict[each_key] = dictionary[each_key]
    dictionary.clear()
    dictionary[key] = item
    for each_key in temp_dict:
        dictionary[each_key] = temp_dict[each_key]
