"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.json.json_translator import JsonStreamToPython
from wlsdeploy.logging import platform_logger
from wlsdeploy.util import dictionary_utils

DOMAIN_RESOURCE_SCHEMA_ROOT = "openAPIV3Schema"
DOMAIN_RESOURCE_SCHEMA_FILE = 'domain-crd-schema-v8.json'
DOMAIN_RESOURCE_SCHEMA_PATH = 'oracle/weblogic/deploy/wko/' + DOMAIN_RESOURCE_SCHEMA_FILE

SIMPLE_TYPES = [
    'number',
    'string',
    'boolean'
]

UNSUPPORTED_FOLDERS = [
    'status',
    'metadata/initializers',
    'metadata/ownerReferences'
]

_logger = platform_logger.PlatformLogger('wlsdeploy.deploy')
_class_name = 'wko_schema_helper'


def get_domain_resource_schema(exception_type=ExceptionType.DEPLOY):
    """
    Read the WKO domain resource schema from its resource path.
    """
    _method_name = 'get_domain_resource_schema'

    template_stream = None
    try:
        template_stream = FileUtils.getResourceAsStream(DOMAIN_RESOURCE_SCHEMA_PATH)
        if template_stream is None:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-10010', DOMAIN_RESOURCE_SCHEMA_PATH)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        full_schema = JsonStreamToPython(DOMAIN_RESOURCE_SCHEMA_FILE, template_stream, True).parse()

        # remove the root element, since it has a version-specific name
        schema = full_schema[DOMAIN_RESOURCE_SCHEMA_ROOT]

    finally:
        if template_stream:
            template_stream.close()

    return schema


def is_single_folder(schema_map):
    """
    Return True if the schema map describes a single folder.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies a single folder
    """
    property_type = dictionary_utils.get_element(schema_map, "type")
    if property_type == "object":
        additional = dictionary_utils.get_dictionary_element(schema_map, "additionalProperties")
        additional_type = dictionary_utils.get_element(additional, "type")
        return not additional_type
    return False


def is_multiple_folder(schema_map):
    """
    Return True if the schema map identifies a multiple folder.
    :param schema_map: the schema map to be examined
    :return: True if the map identifies a multiple folder
    """
    property_type = dictionary_utils.get_element(schema_map, "type")
    if property_type == "array":
        array_items = dictionary_utils.get_dictionary_element(schema_map, "items")
        array_type = dictionary_utils.get_dictionary_element(array_items, "type")
        return array_type == "object"
    return False


def is_unsupported_folder(path):
    return path in UNSUPPORTED_FOLDERS


def append_path(path, element):
    if path:
        return path + "/" + element
    return element
