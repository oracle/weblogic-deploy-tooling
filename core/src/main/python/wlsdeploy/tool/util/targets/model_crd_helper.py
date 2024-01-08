"""
Copyright (c) 2022, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases.model_constants import KUBERNETES
from wlsdeploy.aliases.model_constants import VERRAZZANO
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging import platform_logger
from wlsdeploy.tool.util.targets import model_crd_folder
from wlsdeploy.tool.util.targets import schema_helper
from wlsdeploy.tool.util.targets.model_crd_folder import ModelCrdFolder
from wlsdeploy.util import dictionary_utils

_logger = platform_logger.PlatformLogger('wlsdeploy.deploy')
_class_name = 'model_crd_helper'

VERRAZZANO_PRODUCT_KEY = "vz"
VERRAZZANO_VERSION_1 = "v1"

VERRAZZANO_VALID_VERSIONS = [
    VERRAZZANO_VERSION_1
]

VZ_APPLICATION_SCHEMA_NAME = 'vz-application'
VZ_CONFIGMAP_SCHEMA_NAME = 'vz-configmap'
VZ_WEBLOGIC_SCHEMA_NAME = 'vz-weblogic'
VZ_1_SCHEMA_SUFFIX = '-v1alpha1'
VZ_1_APPLICATION_SCHEMA_NAME = VZ_APPLICATION_SCHEMA_NAME + VZ_1_SCHEMA_SUFFIX
VZ_1_CONFIGMAP_SCHEMA_NAME = VZ_CONFIGMAP_SCHEMA_NAME + VZ_1_SCHEMA_SUFFIX
VZ_1_WEBLOGIC_SCHEMA_NAME = VZ_WEBLOGIC_SCHEMA_NAME + VZ_1_SCHEMA_SUFFIX

WKO_PRODUCT_KEY = "wko"
WKO_VERSION_3 = 'v3'
WKO_VERSION_4 = 'v4'

WKO_VALID_VERSIONS = [
    WKO_VERSION_3,
    WKO_VERSION_4
]

WKO_CLUSTER_SCHEMA_NAME = 'cluster-crd-schema'
WKO_DOMAIN_SCHEMA_NAME = 'domain-crd-schema'
WKO_3_DOMAIN_SCHEMA_NAME = WKO_DOMAIN_SCHEMA_NAME + "-v8"
WKO_4_CLUSTER_SCHEMA_NAME = WKO_CLUSTER_SCHEMA_NAME + "-v1"
WKO_4_DOMAIN_SCHEMA_NAME = WKO_DOMAIN_SCHEMA_NAME + "-v9"


class ModelCrdHelper:
    """
    Manages the mappings between model folders and CRD schemas,
    such as kubernetes/domain and kubernetes/clusters.
    This should be instantiated using static methods below,
    in order to get the correct configuration for product / version.
    """
    _class_name = "ModelCrdHelper"

    def __init__(self, exception_type):
        self._exception_type = exception_type
        self._crd_folders = []
        self._crd_folder_map = {}
        self._model_section = None

    # get CRD information for model folders directly under the section name
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

    def get_model_section(self):
        return self._model_section

    def set_model_section(self, model_section):
        self._model_section = model_section


# get a helper for on the version in the model context
def get_helper(model_context, exception_type=ExceptionType.DEPLOY):
    product_key = model_context.get_target_configuration().get_product_key()
    product_version = model_context.get_target_configuration().get_product_version()
    return get_product_helper(product_key, product_version, exception_type)


# get a helper for the specified product and version
def get_product_helper(product_key, product_version, exception_type=ExceptionType.DEPLOY):
    helper = ModelCrdHelper(exception_type)

    if product_key == VERRAZZANO_PRODUCT_KEY:
        helper.set_model_section(VERRAZZANO)

        application_schema = schema_helper.get_schema(VZ_1_APPLICATION_SCHEMA_NAME, exception_type)
        application_folder = ModelCrdFolder("application", application_schema, False)
        application_folder.add_object_list_key('spec/components', 'componentName')
        application_folder.add_object_list_key('spec/components/traits', 'trait/kind')
        application_folder.add_object_list_key('spec/components/traits/trait/spec/rules', 'destination/host')
        helper.add_crd_folder(application_folder)

        weblogic_schema_name = VZ_1_WEBLOGIC_SCHEMA_NAME
        weblogic_schema = schema_helper.get_schema(weblogic_schema_name, exception_type)
        _update_weblogic_schema(weblogic_schema, weblogic_schema_name, exception_type)
        weblogic_folder = ModelCrdFolder("weblogic", weblogic_schema, False)
        weblogic_folder.add_object_list_key('spec/workload/spec/clusters', 'spec/clusterName')
        weblogic_folder.add_object_list_key('spec/workload/spec/template/spec/adminServer/adminService/channels',
                                            'channelName')
        weblogic_folder.add_object_list_key('spec/workload/spec/template/spec/managedServers', 'serverName')
        helper.add_crd_folder(weblogic_folder)

        configmap_schema = schema_helper.get_schema(VZ_1_CONFIGMAP_SCHEMA_NAME, exception_type)
        configmap_folder = ModelCrdFolder("configmap", configmap_schema, False)
        helper.add_crd_folder(configmap_folder)

    elif product_version == WKO_VERSION_4:
        helper.set_model_section(KUBERNETES)

        cluster_schema = schema_helper.get_schema(WKO_4_CLUSTER_SCHEMA_NAME, exception_type)
        cluster_folder = ModelCrdFolder("clusters", cluster_schema, True)
        helper.add_crd_folder(cluster_folder)

        domain_schema = schema_helper.get_schema(WKO_4_DOMAIN_SCHEMA_NAME, exception_type)
        domain_folder = ModelCrdFolder("domain", domain_schema, False)
        domain_folder.add_object_list_key('spec/adminServer/adminService/channels', 'channelName')
        domain_folder.add_object_list_key('spec/managedServers', 'serverName')
        helper.add_crd_folder(domain_folder)

    elif product_version == WKO_VERSION_3:
        helper.set_model_section(KUBERNETES)

        domain_schema = schema_helper.get_schema(WKO_3_DOMAIN_SCHEMA_NAME, exception_type)
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
    if product_key == VERRAZZANO_PRODUCT_KEY:
        return VERRAZZANO_VALID_VERSIONS
    return []


def get_default_version(product_key):
    if product_key == WKO_PRODUCT_KEY:
        return WKO_VERSION_3
    if product_key == VERRAZZANO_PRODUCT_KEY:
        return VERRAZZANO_VERSION_1
    return None


def _update_weblogic_schema(schema, schema_name, exception_type):
    """
    Update the Verrazzano WebLogic workload schema with the WKO domain and cluster schemas.
    These are combined at runtime to reduce the size of the workload schema file.
    :param schema: the WebLogic workload schema
    :param schema_name: the WebLogic workload schema name, used for logging
    :param exception_type: the exception type to be thrown
    """
    workload_spec_folder = _get_nested_folder(schema, schema_name, exception_type, 'properties',
                                              'spec', 'properties', 'workload', 'properties', 'spec', 'properties')

    domain_schema = schema_helper.get_schema(WKO_4_DOMAIN_SCHEMA_NAME, exception_type)
    domain_folder = _get_nested_folder(workload_spec_folder, schema_name, exception_type, 'template')
    for key in domain_schema.keys():
        domain_folder[key] = domain_schema[key]

    cluster_schema = schema_helper.get_schema(WKO_4_CLUSTER_SCHEMA_NAME, exception_type)
    cluster_folder = _get_nested_folder(workload_spec_folder, schema_name, exception_type, 'clusters', 'items')
    for key in cluster_schema.keys():
        cluster_folder[key] = cluster_schema[key]


def _get_nested_folder(parent_folder, schema_name, exception_type, *names):
    """
    Get the folder inside parent_folder at the path specified by the list of names.
    :param parent_folder: the folder to be examined
    :param exception_type: the exception type to throw if the lookup fails
    :param names: a list of names specifying the path inside parent_folder
    :return: the nested folder
    """
    _method_name = '_get_nested_folder'

    folder = parent_folder
    for name in names:
        if name not in folder:
            ex = exception_helper.create_exception(exception_type, 'WLSDPLY-10050', name, '/'.join(names),
                                                   schema_name)
            _logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        folder = folder[name]
    return folder
