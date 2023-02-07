"""
Copyright (c) 2022, 2023, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods to update an output file with information from the kubernetes section of the model.
"""
import re

from oracle.weblogic.deploy.util import PyOrderedDict
from oracle.weblogic.deploy.util import PyRealBoolean
from oracle.weblogic.deploy.yaml import YamlException

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import schema_helper
from wlsdeploy.tool.validate.crd_sections_validator import CrdSectionsValidator
from wlsdeploy.util import dictionary_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.yaml.yaml_translator import PythonToYaml
from wlsdeploy.yaml.yaml_translator import YamlToPython

__class_name = 'crd_file_updater'
__logger = PlatformLogger('wlsdeploy.tool.util')

KIND = 'kind'
SPEC = 'spec'

WKO_CLUSTER_KIND = 'Cluster'
WKO_DOMAIN_KIND = 'Domain'
CLUSTER_NAME = 'clusterName'
CLUSTERS = 'clusters'
DOMAIN_HOME = 'domainHome'
IMAGE_PULL_SECRETS = 'imagePullSecrets'
REPLICAS = 'replicas'

# specific to Verrazzano
CONFIG_MAP_WORKLOAD_KIND = 'ConfigMap'
OAM_COMPONENT_KIND = 'Component'
TEMPLATE = 'template'
VERRAZZANO_WEBLOGIC_WORKLOAD_KIND = 'VerrazzanoWebLogicWorkload'
VERRAZZANO_APPLICATION_KIND = 'ApplicationConfiguration'
WORKLOAD = 'workload'

# specific to Verrazzano application document
COMPONENTS = "components"
DESTINATION = "destination"
INGRESS_TRAIT = "IngressTrait"
PATH = "path"
PATH_TYPE = "pathType"
PATHS = "paths"
RULES = "rules"
TRAIT = "trait"
TRAITS = "traits"

PATH_SAMPLE_PATTERN = '^\\(path for.*\\)$'


def update_from_model(crd_file, model, crd_helper):
    """
    Update the CRD file content with information from the kubernetes section of the model.
    :param crd_file: the CRD java.io.File to be updated
    :param model: the model to use for update
    :param crd_helper: used to get CRD folder information
    """
    _method_name = 'update_from_model'

    model_section = crd_helper.get_model_section()
    model_crd_content = dictionary_utils.get_dictionary_element(model.get_model(), model_section)

    # failures will be logged as severe, but not cause tool failure.
    # this will allow the unaltered output file to be examined for problems.

    __logger.info('WLSDPLY-01675', crd_file, model_section, class_name=__class_name, method_name=_method_name)

    try:
        reader = YamlToPython(crd_file.getPath(), True)
        documents = reader.parse_documents()
    except YamlException, ex:
        __logger.severe('WLSDPLY-01673', crd_file, str_helper.to_string(ex), error=ex, class_name=__class_name,
                        method_name=_method_name)
        return

    _update_documents(documents, model_crd_content, crd_helper, crd_file.getPath())

    try:
        writer = PythonToYaml(documents)
        writer.write_to_yaml_file(crd_file.getPath())
    except YamlException, ex:
        __logger.severe('WLSDPLY-01674', crd_file, str_helper.to_string(ex), error=ex, class_name=__class_name,
                        method_name=_method_name)
    return


def _update_documents(crd_documents, model_content, crd_helper, output_file_path):
    """
    Update each CRD document from the model, if required.
    :param crd_documents: the CRD documents to be updated
    :param model_content: the model content to use for update
    :param crd_helper: used to get CRD folder information
    :param output_file_path: used for logging
    """
    _method_name = '_update_documents'
    found = False

    # update section(s) based on their kind, etc.
    for crd_document in crd_documents:
        if isinstance(crd_document, dict):
            kind = dictionary_utils.get_element(crd_document, KIND)

            # is this a WKO domain document?
            if kind == WKO_DOMAIN_KIND:
                _update_crd_domain(crd_document, model_content, crd_helper, output_file_path)
                _add_domain_comments(crd_document)
                found = True

            # is this a WKO v4 cluster document?
            elif kind == WKO_CLUSTER_KIND:
                _update_crd_cluster(crd_document, model_content, crd_helper, output_file_path)
                _add_cluster_comments(crd_document)
                found = True

            elif kind == OAM_COMPONENT_KIND:
                _update_crd_component(crd_document, model_content, crd_helper, output_file_path)
                found = True

            elif kind == VERRAZZANO_APPLICATION_KIND:
                _update_crd_application(crd_document, model_content, crd_helper, output_file_path)
                found = True

    if not found:
        __logger.warning('WLSDPLY-01676', output_file_path, class_name=__class_name, method_name=_method_name)


def _update_crd_domain(crd_dictionary, model_dictionary, crd_helper, output_file_path):
    """
    Update the CRD domain dictionary from the model.
    :param crd_dictionary: the CRD dictionary to be updated
    :param model_dictionary: the model content to use for update
    :param crd_helper: used to get CRD folder information
    :param output_file_path: used for logging
    """
    keyless_crd_folder = crd_helper.get_keyless_crd_folder()
    if keyless_crd_folder:
        # this WKO version does not use model CRD sub-folders, use the single schema
        schema = keyless_crd_folder.get_schema()
        _update_dictionary(crd_dictionary, model_dictionary, schema, None, keyless_crd_folder, output_file_path)
    else:
        # this WKO version uses CRD sub-folders, use the domain folder
        _update_crd(crd_dictionary, model_dictionary, 'domain', crd_helper, output_file_path)


def _update_crd_cluster(crd_dictionary, model_dictionary, crd_helper, output_file_path):
    """
    Update the CRD cluster dictionary from the model.
    :param crd_dictionary: the CRD dictionary to be updated
    :param model_dictionary: the model content to use for update
    :param crd_helper: used to get CRD folder information
    :param output_file_path: used for logging
    """
    _method_name = '_update_crd_cluster'

    folder_key = 'clusters'
    model_clusters = dictionary_utils.get_element(model_dictionary, folder_key)
    if model_clusters:
        crd_name = _get_cluster_name(crd_dictionary)
        model_cluster = _find_model_cluster(crd_name, model_clusters)
        if model_cluster:
            cluster_crd_folder = crd_helper.get_crd_folder(folder_key)
            schema = cluster_crd_folder.get_schema()
            _update_dictionary(crd_dictionary, model_cluster, schema, None, cluster_crd_folder, output_file_path)


def _update_crd_application(crd_dictionary, model_dictionary, crd_helper, output_file_path):
    """
    Update the CRD application dictionary from the model.
    :param crd_dictionary: the CRD dictionary to be updated
    :param model_dictionary: the model content to use for update
    :param crd_helper: used to get CRD folder information
    :param output_file_path: used for logging
    """
    _method_name = '_update_crd_application'

    _update_crd(crd_dictionary, model_dictionary, 'application', crd_helper, output_file_path)
    _add_application_comments(crd_dictionary)


def _update_crd_component(crd_dictionary, model_dictionary, crd_helper, output_file_path):
    """
    Update the CRD component dictionary from the model.
    :param crd_dictionary: the CRD dictionary to be updated
    :param model_dictionary: the model content to use for update
    :param crd_helper: used to get CRD folder information
    :param output_file_path: used for logging
    """
    _method_name = '_update_crd_component'

    spec_folder = dictionary_utils.get_dictionary_element(crd_dictionary, SPEC)
    workload_folder = dictionary_utils.get_dictionary_element(spec_folder, WORKLOAD)
    workload_kind = dictionary_utils.get_element(workload_folder, KIND)

    if workload_kind == VERRAZZANO_WEBLOGIC_WORKLOAD_KIND:
        _update_crd(crd_dictionary, model_dictionary, 'weblogic', crd_helper, output_file_path)
        _add_weblogic_workload_comments(crd_dictionary)

    elif workload_kind == CONFIG_MAP_WORKLOAD_KIND:
        _update_crd(crd_dictionary, model_dictionary, 'configmap', crd_helper, output_file_path)


def _update_crd(crd_dictionary, model_dictionary, folder_key, crd_helper, output_file_path):
    """
    Update the CRD dictionary for folder_key from the model.
    :param crd_dictionary: the CRD dictionary to be updated
    :param model_dictionary: the model content to use for update
    :param folder_key: the model key for the CRD section subfolder
    :param crd_helper: used to get CRD folder information
    :param output_file_path: used for logging
    """
    _method_name = '_update_crd'

    domain_crd_folder = crd_helper.get_crd_folder(folder_key)
    model_content = dictionary_utils.get_element(model_dictionary, folder_key)
    if model_content:
        schema = domain_crd_folder.get_schema()
        _update_dictionary(crd_dictionary, model_content, schema, None, domain_crd_folder, output_file_path)


def _find_model_cluster(crd_name, model_clusters):
    for model_cluster in model_clusters:
        model_name = _get_cluster_name(model_cluster)
        if crd_name == model_name:
            return model_cluster
    return None


def _get_cluster_name(cluster):
    spec = dictionary_utils.get_dictionary_element(cluster, SPEC)
    return dictionary_utils.get_element(spec, CLUSTER_NAME)


def _update_dictionary(output_dictionary, model_dictionary, schema_folder, schema_path, model_crd_folder,
                       output_file_path):
    """
    Update output_dictionary with attributes from model_dictionary.
    :param output_dictionary: the dictionary to be updated
    :param model_dictionary: the dictionary to update from (type previously validated)
    :param schema_folder: the schema for this folder
    :param schema_path: used for schema_helper lookups and logging
    :param model_crd_folder: required for object list matching
    :param output_file_path: used for logging
    """
    _method_name = '_update_dictionary'
    if not isinstance(output_dictionary, dict):
        __logger.warning('WLSDPLY-01677', schema_path, output_file_path, class_name=__class_name,
                         method_name=_method_name)
        return

    # no type checking for elements of simple (single type) map
    if schema_helper.is_simple_map(schema_folder):
        for key, value in model_dictionary.items():
            output_dictionary[key] = value
        return

    # if this folder has multiple content options, choose the matching one
    folder_options = schema_helper.get_one_of_options(schema_folder)
    if folder_options:
        model_context = ModelContext(__class_name, {})
        validator = CrdSectionsValidator(model_context)
        folder_option = validator.find_folder_option(model_dictionary, folder_options, schema_path, schema_path)
        if not folder_option:
            __logger.warning("WLSDPLY-05043", schema_path, len(folder_options),
                             class_name=__class_name, method_name=_method_name)
            return
        properties = schema_helper.get_properties(folder_option)
    else:
        properties = schema_helper.get_properties(schema_folder)

    for key, value in model_dictionary.items():
        property_folder = properties[key]
        element_type = schema_helper.get_type(property_folder)

        value = _convert_value(value, element_type)

        if isinstance(value, dict):
            output_dictionary[key] = dictionary_utils.get_element(output_dictionary, key, PyOrderedDict())
            next_schema_path = schema_helper.append_path(schema_path, key)
            _update_dictionary(output_dictionary[key], value, property_folder, next_schema_path, model_crd_folder,
                               output_file_path)
        elif isinstance(value, list):
            if not value:
                # if the model has an empty list, override output value
                output_dictionary[key] = value
            else:
                output_dictionary[key] = dictionary_utils.get_element(output_dictionary, key, [])
                next_schema_path = schema_helper.append_path(schema_path, key)
                _update_list(output_dictionary[key], value, property_folder, next_schema_path, model_crd_folder,
                             output_file_path)
        else:
            output_dictionary[key] = value


def _update_list(output_list, model_list, schema_folder, schema_path, model_crd_folder, output_file_path):
    """
    Update output_list from model_list, overriding or merging existing values
    :param output_list: the list to be updated
    :param model_list: the list to update from (type previously validated)
    :param schema_folder: the schema for members of this list
    :param schema_path: used for schema_helper lookups and logging
    :param model_crd_folder: required for object list matching
    :param output_file_path: used for logging
    """
    _method_name = '_update_list'
    if not isinstance(output_list, list):
        __logger.warning('WLSDPLY-01678', schema_path, output_file_path, class_name=__class_name,
                         method_name=_method_name)
        return

    for item in model_list:
        if isinstance(item, dict):
            match = _find_object_match(item, output_list, schema_path, model_crd_folder)
            if match:
                next_schema_folder = schema_helper.get_array_item_info(schema_folder)
                _update_dictionary(match, item, next_schema_folder, schema_path, model_crd_folder, output_file_path)
            else:
                output_list.append(item)
        elif item not in output_list:
            element_type = schema_helper.get_array_element_type(schema_folder)
            item = _convert_value(item, element_type)
            output_list.append(item)


def _find_object_match(item, match_list, schema_path, model_crd_folder):
    """
    Find an object in match_list that has a name matching the item.
    :param item: the item to be matched
    :param match_list: a list of items
    :param schema_path: used for schema_helper key lookup
    :param model_crd_folder: required for object list matching
    :return: a matching dictionary object
    """
    key = model_crd_folder.get_object_list_key(schema_path)
    item_key = _get_key_value(item, key)
    if item_key:
        for match_item in match_list:
            if isinstance(match_item, dict):
                if item_key == _get_key_value(match_item, key):
                    return match_item
    return None


def _get_key_value(item, key):
    """
    Return the value for the specified key in the specified item object.
    The key may be nested, such as spec/clusterName.
    :param item: the item to be examined
    :param key: the key to be evaluated
    :return: the value if found, otherwise None
    """
    key_parts = key.split('/')
    key_folders = key_parts[:-1]
    match_key = key_parts[-1]
    match_folder = item
    for key_folder in key_folders:
        match_folder = dictionary_utils.get_dictionary_element(match_folder, key_folder)
    return dictionary_utils.get_element(match_folder, match_key)


def _convert_value(model_value, type_name):
    """
    Convert the specified model value to match the schema type for the domain resource file.
    WDT allows some model conventions that are not allowed in the domain resource file.
    :param model_value: the value to be checked
    :param type_name: the schema type name of the value
    :return: the converted value
    """
    if type_name == 'boolean':
        # the model values can be true, false, 1, 0, etc.
        # target boolean values must be 'true' or 'false'
        return PyRealBoolean(alias_utils.convert_boolean(model_value))

    if type_name == 'array':
        # the model values can be 'abc,123'.
        # target values must be a list object.
        return alias_utils.convert_to_type('list', model_value, delimiter=MODEL_LIST_DELIMITER)

    return model_value


def _add_domain_comments(wko_dictionary):
    """
    Add relevant comments to the domain CRD dictionary to provide additional information.
    :param wko_dictionary: the WKO dictionary containing metadata, spec, etc.
    """
    spec = dictionary_utils.get_dictionary_element(wko_dictionary, SPEC)
    image_pull_secrets = dictionary_utils.get_element(spec, IMAGE_PULL_SECRETS)
    if image_pull_secrets is not None and not len(image_pull_secrets):
        message = exception_helper.get_message('WLSDPLY-01679')
        spec.addComment(IMAGE_PULL_SECRETS, message)

    clusters = dictionary_utils.get_dictionary_element(spec, CLUSTERS)
    for cluster in clusters:
        cluster_keys = cluster.keys()
        # check for clusterName to avoid commenting WKO V4
        if CLUSTER_NAME in cluster_keys and REPLICAS not in cluster_keys:
            last_key = cluster.keys()[-1]
            message = exception_helper.get_message('WLSDPLY-01680')
            cluster.addComment(last_key, REPLICAS + ': 99  # ' + message)


def _add_cluster_comments(wko_dictionary):
    """
    Add relevant comments to the cluster CRD dictionary to provide additional information.
    :param wko_dictionary: the WKO dictionary containing metadata, spec, etc.
    """
    spec = dictionary_utils.get_dictionary_element(wko_dictionary, SPEC)
    _add_cluster_spec_comments(spec)


def _add_cluster_spec_comments(spec_dictionary):
    """
    Add relevant comments to a cluster spec dictionary to provide additional information.
    :param spec_dictionary: the spec dictionary containing cluster attributes
    """
    cluster_keys = spec_dictionary.keys()
    if CLUSTER_NAME in cluster_keys and REPLICAS not in cluster_keys:
        last_key = spec_dictionary.keys()[-1]
        message = exception_helper.get_message('WLSDPLY-01680')
        spec_dictionary.addComment(last_key, REPLICAS + ': 99  # ' + message)


def _add_weblogic_workload_comments(vz_dictionary):
    """
    Add relevant comments to the Verrazzano WebLogic workload CRD dictionary for additional information.
    :param vz_dictionary: the Verrazzano dictionary
    """
    spec_folder = dictionary_utils.get_dictionary_element(vz_dictionary, SPEC)
    workload_folder = dictionary_utils.get_dictionary_element(spec_folder, WORKLOAD)
    workload_spec_folder = dictionary_utils.get_dictionary_element(workload_folder, SPEC)

    template_folder = dictionary_utils.get_dictionary_element(workload_spec_folder, TEMPLATE)
    _add_domain_comments(template_folder)

    clusters_folder = dictionary_utils.get_dictionary_element(workload_spec_folder, CLUSTERS)
    for cluster_spec in clusters_folder:
        _add_cluster_spec_comments(cluster_spec)


def _add_application_comments(vz_dictionary):
    """
    Add relevant comments to the Verrazzano application CRD dictionary for additional information.
    :param vz_dictionary: the Verrazzano dictionary
    """
    spec_folder = dictionary_utils.get_dictionary_element(vz_dictionary, SPEC)
    components = dictionary_utils.get_dictionary_element(spec_folder, COMPONENTS)
    for component in components:
        traits = _get_list_element(component, TRAITS)
        for trait in traits:
            trait_dictionary = dictionary_utils.get_dictionary_element(trait, TRAIT)
            trait_kind = dictionary_utils.get_element(trait_dictionary, KIND)
            if trait_kind == INGRESS_TRAIT:
                _add_ingress_trait_comments(trait_dictionary)


def _add_ingress_trait_comments(trait_dictionary):
    """
    Add relevant comments to the IngressTrait CRD dictionary for additional information.
    Convert sample rule paths to comments if none were added from WDT model.
    Remove sample rule paths if any paths were added from WDT model.
    :param trait_dictionary: the IngressTrait dictionary
    """
    trait_spec = dictionary_utils.get_dictionary_element(trait_dictionary, SPEC)
    rules = _get_list_element(trait_spec, RULES)
    for rule in rules:
        sample_paths = []
        has_defined_paths = False
        paths = _get_list_element(rule, PATHS)
        for path in paths:
            path_path = dictionary_utils.get_dictionary_element(path, PATH)
            is_sample_path = re.search(PATH_SAMPLE_PATTERN, str_helper.to_string(path_path))
            if is_sample_path:
                sample_paths.append(path)
            else:
                has_defined_paths = True

        if has_defined_paths:
            for sample_path in sample_paths:
                paths.remove(sample_path)
        else:
            rule.addComment(DESTINATION, PATHS + ':')
            for sample_path in sample_paths:
                rule.addComment(DESTINATION, '  - ' + PATH + ': ' + str_helper.to_string(sample_path[PATH]))
                rule.addComment(DESTINATION, '    ' + PATH_TYPE + ': ' + str_helper.to_string(sample_path[PATH_TYPE]))
            del rule[PATHS]


def _get_list_element(dictionary, element_name):
    """
    Retrieve the value for the provided element name from the dictionary.
    Return empty list if name is not in the dictionary.
    :param dictionary: to find the element name
    :param element_name: for which to retrieve the value
    :return: value from the dictionary or empty list
    """
    if element_name in dictionary:
        result = dictionary[element_name]
    else:
        result = []
    return result


def _get_or_create_dictionary(dictionary, key):
    if key not in dictionary:
        dictionary[key] = PyOrderedDict()

    return dictionary[key]
