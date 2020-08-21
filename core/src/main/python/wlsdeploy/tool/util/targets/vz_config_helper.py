"""
Copyright (c) 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods for creating Kubernetes resource configuration files for Verrazzano.
"""
from java.io import File

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import URL
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import target_configuration_helper

__class_name = 'vz_config_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

TEMPLATE_PATH = 'oracle/weblogic/deploy/targets/vz'

# substitution keys used in the templates
CLUSTER_NAME = 'clusterName'
CLUSTERS = 'clusters'
DATABASE_CREDENTIALS = 'databaseCredentials'
DATABASE_PREFIX = 'databasePrefix'
DATABASES = 'databases'
DATASOURCE_NAME = 'datasourceName'
DOMAIN_NAME = 'domainName'
DOMAIN_PREFIX = 'domainPrefix'
DOMAIN_TYPE = 'domainType'
DOMAIN_UID = 'domainUid'
DS_URL = 'url'
HAS_CLUSTERS = 'hasClusters'
HAS_DATABASES = 'hasDatabases'
REPLICAS = 'replicas'
WEBLOGIC_CREDENTIALS_SECRET = 'webLogicCredentialsSecret'


def create_vz_configuration(model, model_context, aliases, exception_type):
    """
    Create and write the Kubernetes resource configuration files for Verrazzano.
    :param model: Model object, used to derive some values in the configurations
    :param model_context: used to determine location and content for the configurations
    :param aliases: used to derive secret names
    :param exception_type: the type of exception to throw if needed
    """

    # -output_dir argument was previously verified
    output_dir = model_context.get_kubernetes_output_dir()

    template_hash = _build_template_hash(model, model_context, aliases)

    _create_file('model.yaml', template_hash, output_dir, exception_type)

    _create_file('binding.yaml', template_hash, output_dir, exception_type)


def _create_file(template_name, template_hash, output_dir, exception_type):
    """
    Read the template from the resource stream, perform any substitutions,
    and write it to a file with the same name in the output directory.
    :param template_name: the name of the template file, and the output file
    :param template_hash: a dictionary of substitution values
    :param output_dir: the directory to write the output file
    :param exception_type: the type of exception to throw if needed
    """
    _method_name = '_create_file'

    template_path = TEMPLATE_PATH + '/' + template_name
    output_file = File(output_dir, template_name)

    __logger.info('WLSDPLY-01662', output_file, class_name=__class_name, method_name=_method_name)

    file_template_helper.create_file(template_path, template_hash, output_file, exception_type)


def _build_template_hash(model, model_context, aliases):
    """
    Create a dictionary of substitution values to apply to the templates.
    :param model: Model object used to derive values
    :param model_context: used to determine domain type
    :param aliases: used to derive folder names
    :return: the hash dictionary
    """
    template_hash = dict()

    # domain name and prefix

    domain_name = dictionary_utils.get_element(model.get_model_topology(), NAME)
    if domain_name is None:
        domain_name = DEFAULT_WLS_DOMAIN_NAME

    template_hash[DOMAIN_NAME] = domain_name

    # should change spaces to hyphens?
    template_hash[DOMAIN_PREFIX] = domain_name.lower()

    # domain UID

    domain_uid = k8s_helper.get_domain_uid(domain_name)
    template_hash[DOMAIN_UID] = domain_uid

    # admin credential

    admin_secret = domain_uid + target_configuration_helper.WEBLOGIC_CREDENTIALS_SECRET_SUFFIX
    template_hash[WEBLOGIC_CREDENTIALS_SECRET] = admin_secret

    # configuration / model
    template_hash[DOMAIN_TYPE] = model_context.get_domain_type()

    # clusters

    clusters = []
    cluster_list = dictionary_utils.get_dictionary_element(model.get_model_topology(), CLUSTER)
    for cluster_name in cluster_list:
        cluster_hash = dict()
        cluster_hash[CLUSTER_NAME] = cluster_name

        cluster_values = dictionary_utils.get_dictionary_element(cluster_list, cluster_name)
        server_count = k8s_helper.get_server_count(cluster_name, cluster_values, model.get_model())
        cluster_hash[REPLICAS] = str(server_count)
        clusters.append(cluster_hash)

    template_hash[CLUSTERS] = clusters
    template_hash[HAS_CLUSTERS] = len(clusters) != 0

    # databases

    databases = []

    location = LocationContext().append_location(JDBC_SYSTEM_RESOURCE)
    name_token = aliases.get_name_token(location)
    location.append_location(JDBC_RESOURCE, JDBC_DRIVER_PARAMS)

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

        # should change spaces to hyphens?
        database_hash[DATABASE_PREFIX] = jdbc_name.lower()

        # get the name that matches secret
        location.add_name_token(name_token, jdbc_name)
        secret_name = target_configuration_helper.get_secret_name_for_location(location, domain_uid, aliases)
        database_hash[DATABASE_CREDENTIALS] = secret_name

        databases.append(database_hash)

    template_hash[DATABASES] = databases
    template_hash[HAS_DATABASES] = len(databases) != 0

    return template_hash
