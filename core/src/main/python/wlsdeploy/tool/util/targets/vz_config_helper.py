"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods for creating Kubernetes resource configuration files for Verrazzano.
"""
from java.io import File

from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME, JDBC_RESOURCE, JDBC_DRIVER_PARAMS, URL, CLUSTER
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils

__class_name = 'vz_config_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

TEMPLATE_PATH = 'oracle/weblogic/deploy/targets/vz'

# substitution keys used in the templates
CLUSTER_NAME = 'clusterName'
CLUSTERS = 'clusters'
DATABASES = 'databases'
DATASOURCE_NAME = 'datasourceName'
DOMAIN_UID = 'domainUid'
DS_URL = 'url'


def create_vz_configuration(model, model_context, exception_type):
    """
    Create and write the Kubernetes resource configuration files for Verrazzano.
    :param model: Model object, used to derive some values in the configurations
    :param model_context: used to determine location and content for the configurations
    """

    # -output_dir argument was previously verified
    output_dir = model_context.get_kubernetes_output_dir()

    template_hash = _build_template_hash(model)

    _create_file('model.yaml', template_hash, output_dir, exception_type)

    _create_file('binding.yaml', template_hash, output_dir, exception_type)


def _create_file(template_name, template_hash, output_dir, exception_type):
    """
    Read the template from the resource stream, perform any substitutions,
    and write it to a file with the same name in the output directory.
    :param template_name: the name of the template file, and the output file
    :param template_hash: a dictionary of substitution values
    :param output_dir: the directory to write the output file
    """
    _method_name = '_create_file'

    template_path = TEMPLATE_PATH + '/' + template_name
    output_file = File(output_dir, template_name)

    __logger.info('WLSDPLY-01662', output_file, class_name=__class_name, method_name=_method_name)

    file_template_helper.create_file(template_path, template_hash, output_file, exception_type)


def _build_template_hash(model):
    """
    Create a dictionary of substitution values to apply to the templates.
    :param model: used to derive values
    :return: the hash dictionary
    """
    template_hash = dict()

    # domain UID

    domain_uid = dictionary_utils.get_element(model.get_model_topology(), NAME)
    if domain_uid is None:
        domain_uid = DEFAULT_WLS_DOMAIN_NAME

    template_hash[DOMAIN_UID] = domain_uid

    # clusters

    clusters = []
    cluster_list = dictionary_utils.get_dictionary_element(model.get_model_topology(), CLUSTER)
    for cluster_name in cluster_list:
        cluster_hash = dict()
        cluster_hash[CLUSTER_NAME] = cluster_name

        clusters.append(cluster_hash)

    template_hash[CLUSTERS] = clusters

    # databases

    databases = []
    system_resources = dictionary_utils.get_dictionary_element(model.get_model_resources(), JDBC_SYSTEM_RESOURCE)
    for jdbc_name in system_resources:
        database_hash = dict()
        database_hash[DATASOURCE_NAME] = jdbc_name

        named = dictionary_utils.get_dictionary_element(system_resources, jdbc_name)
        resources = dictionary_utils.get_dictionary_element(named, JDBC_RESOURCE)
        driver_params = dictionary_utils.get_dictionary_element(resources, JDBC_DRIVER_PARAMS)
        url = dictionary_utils.get_element(driver_params, URL)
        if url is None:
            url = ''
        database_hash[DS_URL] = url

        databases.append(database_hash)

    template_hash[DATABASES] = databases

    return template_hash
