"""
Copyright (c) 2022, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging import platform_logger
from wlsdeploy.tool.util.targets import model_crd_folder
from wlsdeploy.tool.util.targets import schema_helper
from wlsdeploy.tool.util.targets.model_crd_folder import ModelCrdFolder
from wlsdeploy.util import dictionary_utils

_logger = platform_logger.PlatformLogger('wlsdeploy.deploy')
_class_name = 'model_crd_helper'

WKO_PRODUCT_KEY = "wko"

WKO_VERSION_3 = 'v3'
WKO_VERSION_4 = 'v4'

WKO_VALID_VERSIONS = [
    WKO_VERSION_3,
    WKO_VERSION_4
]

WKO_CLUSTER_SCHEMA_NAME = 'cluster-crd-schema'
WKO_DOMAIN_SCHEMA_NAME = 'domain-crd-schema'


class ModelCrdHelper:
    """
    Manages the mappings between model folders and CRD schemas,
    such as kubernetes/domain and kubernetes/clusters.
    This should be instantiated using static methods below,
    in order to get the correct configuration for product / version.
    """
    _class_name = "ModelCrdHelper"

    def __init__(self, product_name, product_version, exception_type):
        self._product = product_name
        self._version = product_version
        self._exception_type = exception_type
        self._crd_folders = []
        self._crd_folder_map = {}

    # get CRD information for model folders directly under kubernetes,
    def get_crd_folders(self):
        return self._crd_folders

    # return the document folder for the specified and model key.
    def get_crd_folder(self, model_key):
        return dictionary_utils.get_element(self._crd_folder_map, model_key)

    # return the keyless document folder for the specified wko_version, if available.
    def get_keyless_crd_folder(self):
        return self.get_crd_folder(model_crd_folder.NO_FOLDER_KEY)

    def get_crd_folder_keys(self):
        return self._crd_folder_map.keys()

    def add_crd_folder(self, crd_folder):
        self._crd_folders.append(crd_folder)
        self._crd_folder_map[crd_folder.get_model_key()] = crd_folder


# get a helper for on the version in the model context
def get_helper(model_context, exception_type=ExceptionType.DEPLOY):
    # product key could be in target config if more products come along, such as VZ
    product_version = model_context.get_target_configuration().get_product_version()
    return get_product_helper(WKO_PRODUCT_KEY, product_version, exception_type)


# get a helper for the specified product and version
def get_product_helper(product_key, product_version, exception_type=ExceptionType.DEPLOY):
    helper = ModelCrdHelper(product_key, product_version, exception_type)

    if product_version == WKO_VERSION_4:
        cluster_schema = schema_helper.get_schema(WKO_CLUSTER_SCHEMA_NAME + "-v1", exception_type)
        cluster_folder = ModelCrdFolder("clusters", cluster_schema, True)
        helper.add_crd_folder(cluster_folder)

        domain_schema = schema_helper.get_schema(WKO_DOMAIN_SCHEMA_NAME + "-v9", exception_type)
        domain_folder = ModelCrdFolder("domain", domain_schema, False)
        domain_folder.add_object_list_key('spec/adminServer/adminService/channels', 'channelName')
        domain_folder.add_object_list_key('spec/managedServers', 'serverName')
        helper.add_crd_folder(domain_folder)

    elif product_version == WKO_VERSION_3:
        domain_schema = schema_helper.get_schema(WKO_DOMAIN_SCHEMA_NAME + "-v8", exception_type)
        domain_folder = ModelCrdFolder(model_crd_folder.NO_FOLDER_KEY, domain_schema, False)
        domain_folder.add_object_list_key('spec/adminServer/adminService/channels', 'channelName')
        domain_folder.add_object_list_key('spec/managedServers', 'serverName')
        domain_folder.add_object_list_key('spec/clusters', 'clusterName')
        helper.add_crd_folder(domain_folder)

    return helper


# get versions that are valid for the specified product
def get_valid_versions(product_key):
    if product_key == WKO_PRODUCT_KEY:
        return WKO_VALID_VERSIONS
    return []
