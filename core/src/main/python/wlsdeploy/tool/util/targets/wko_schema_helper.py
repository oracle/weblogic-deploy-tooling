"""
Copyright (c) 2020, 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.json.json_translator import JsonStreamToPython
from wlsdeploy.logging import platform_logger
from wlsdeploy.tool.util.targets.document_folder import DocumentFolder
from wlsdeploy.util import dictionary_utils

CLUSTER_SCHEMA_NAME = 'cluster-crd-schema'
DOMAIN_SCHEMA_NAME = 'domain-crd-schema'
SCHEMA_RESOURCE_EXTENSION = '.json'
SCHEMA_RESOURCE_PATH = 'oracle/weblogic/deploy/wko'
SCHEMA_ROOT_KEY = "openAPIV3Schema"

SIMPLE_TYPES = [
    'integer',
    'number',
    'string',
    'boolean'
]

OBJECT_TYPES = [
    'object',
    None
]

UNSUPPORTED_FOLDERS = [
    'status',
    'metadata/initializers',
    'metadata/ownerReferences'
]

# some object list members don't use 'name' as a key
OBJECT_NAME_ATTRIBUTES = {
    'spec/adminServer/adminService/channels': 'channelName',
    'spec/clusters': 'clusterName',
    'spec/managedServers': 'serverName'
}

WKO_VERSION_3 = 'v3'
WKO_VERSION_4 = 'v4'

NO_DOC_FOLDER_KEY = "__NO_KEY__"

# the folder name "" indicates there is no extra folder level
# in the model between kubernetes and the schema data
VERSION_FOLDER_INFOS = {
    WKO_VERSION_3: {
        NO_DOC_FOLDER_KEY: {
            'schema_name': DOMAIN_SCHEMA_NAME + '-v8'
        }
    },
    WKO_VERSION_4: {
        "domain": {
            'schema_name': DOMAIN_SCHEMA_NAME + '-v9'
        },
        "clusters": {
            'schema_name': CLUSTER_SCHEMA_NAME + '-v1',
            'is_array': True
        }
    }
}


_logger = platform_logger.PlatformLogger('wlsdeploy.deploy')
_class_name = 'wko_schema_helper'


def get_valid_wko_versions():
    return VERSION_FOLDER_INFOS.keys()


# get document folder information for model folders directly under kubernetes,
# such as domain and clusters. these are not part of the schema definitions.
def get_document_folders(wko_version, exception_type=ExceptionType.DEPLOY):
    folder_infos = VERSION_FOLDER_INFOS[wko_version]
    folder_keys = folder_infos.keys()
    folder_keys.sort()
    folders = []
    for folder_key in folder_keys:
        # lazy-load the folder information when requested
        doc_folder = _get_document_folder(folder_infos, folder_key, exception_type)
        folders.append(doc_folder)
    return folders


# return the document folder for the specified wko_version and model key.
def get_document_folder(wko_version, model_key, exception_type=ExceptionType.DEPLOY):
    folder_infos = VERSION_FOLDER_INFOS[wko_version]
    return _get_document_folder(folder_infos, model_key, exception_type)


# return the keyless document folder for the specified wko_version, if available.
def get_keyless_document_folder(wko_version, exception_type=ExceptionType.DEPLOY):
    return get_document_folder(wko_version, NO_DOC_FOLDER_KEY, exception_type)


def get_document_folder_keys(wko_version):
    folder_infos = VERSION_FOLDER_INFOS[wko_version]
    return folder_infos.keys()


# deprecated, should be obsolete after WKO v4 changes
def get_default_domain_resource_schema(exception_type=ExceptionType.DEPLOY):
    doc_folder = get_document_folder(WKO_VERSION_3, NO_DOC_FOLDER_KEY, exception_type)
    return doc_folder.get_schema()


def is_single_object(schema_map):
    """
    Return True if the schema map describes a single object.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies a single object
    """
    property_type = get_type(schema_map)
    if property_type in OBJECT_TYPES:
        return get_map_element_type(schema_map) is None
    return False


def is_object_array(schema_map):
    """
    Return True if the schema map describes an object array.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies an object array
    """
    property_type = get_type(schema_map)
    if property_type == "array":
        return get_array_element_type(schema_map) in OBJECT_TYPES
    return False


def is_object_type(schema_map):
    """
    Return True if the schema map describes an object or object array.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies an object or object array
    """
    return is_single_object(schema_map) or is_object_array(schema_map)


def is_simple_map(schema_map):
    """
    Return True if the schema map describes a simple map.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies a simple map
    """
    property_type = get_type(schema_map)
    if property_type in OBJECT_TYPES:
        return get_map_element_type(schema_map) is not None
    return False


def is_simple_array(schema_map):
    """
    Return True if the schema map describes a simple array.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies a simple array
    """
    property_type = get_type(schema_map)
    if property_type == "array":
        return get_array_element_type(schema_map) not in OBJECT_TYPES
    return False


def is_simple_type(schema_map):
    """
    Return True if the schema map describes a simple type.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies a simple type
    """
    property_type = get_type(schema_map)
    return property_type in SIMPLE_TYPES


def get_array_element_type(schema_map):
    item_info = get_array_item_info(schema_map)
    return get_type(item_info)


def get_map_element_type(schema_map):
    additional = dictionary_utils.get_dictionary_element(schema_map, "additionalProperties")
    return get_type(additional)


def get_array_item_info(schema_map):
    return dictionary_utils.get_dictionary_element(schema_map, "items")


def get_properties(schema_map):
    properties = dictionary_utils.get_element(schema_map, "properties")
    return properties or {}


def get_type(schema_map):
    return dictionary_utils.get_element(schema_map, "type")


def get_enum_values(schema_map):
    return dictionary_utils.get_element(schema_map, 'enum')


def is_unsupported_folder(path):
    return path in UNSUPPORTED_FOLDERS


def get_object_list_key(schema_path):
    """
    Return the name of the attribute that acts as a key for objects in an object list.
    In most cases, this is 'name', but there are a few exceptions.
    :param schema_path: the path to be checked
    :return: the object key
    """
    mapped_key = dictionary_utils.get_element(OBJECT_NAME_ATTRIBUTES, schema_path)
    if mapped_key is not None:
        return mapped_key
    return 'name'


def append_path(path, element):
    if path:
        return path + "/" + element
    return element


def _get_schema(schema_name, exception_type):
    _method_name = '_get_schema'

    template_stream = None
    try:
        resource_name = schema_name + SCHEMA_RESOURCE_EXTENSION
        resource_path = SCHEMA_RESOURCE_PATH + '/' + resource_name
        template_stream = FileUtils.getResourceAsStream(resource_path)
        if template_stream is None:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-10010', resource_path)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        full_schema = JsonStreamToPython(resource_name, template_stream, True).parse()

        # remove the root element, since it has a version-specific name
        schema = full_schema[SCHEMA_ROOT_KEY]

    finally:
        if template_stream:
            template_stream.close()

    return schema


# return the document folder object for folder_info.
# lazy load the document folder and its schema.
def _get_document_folder(folder_infos, folder_key, exception_type):
    folder_info = dictionary_utils.get_element(folder_infos, folder_key)
    if not folder_info:
        return None

    doc_folder = dictionary_utils.get_element(folder_info, 'doc_folder')
    if not doc_folder:
        schema = _get_schema(folder_info['schema_name'], exception_type)
        is_array = dictionary_utils.get_element(folder_info, 'is_array')
        doc_folder = DocumentFolder(folder_key, schema, is_array)
        folder_info['doc_folder'] = doc_folder
    return doc_folder
