"""
Copyright (c) 2020, 2021, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods for creating Kubernetes resource configuration files for Verrazzano.
"""
from java.io import File

from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
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
from wlsdeploy.util import path_utils
from wlsdeploy.util import target_configuration_helper

__class_name = 'vz_config_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

# substitution keys used in the templates
ADDITIONAL_SECRET_NAME = 'additionalSecretName'
ADDITIONAL_SECRETS = 'additionalSecrets'
APPLICATIONS = 'applications'
APPLICATION_NAME = 'applicationName'
APPLICATION_PREFIX = 'applicationPrefix'
CLUSTER_NAME = 'clusterName'
CLUSTERS = 'clusters'
DATASOURCE_CREDENTIALS = 'datasourceCredentials'
DATASOURCE_PREFIX = 'datasourcePrefix'
DATASOURCES = 'datasources'
DATASOURCE_NAME = 'datasourceName'
DATASOURCE_URL = 'url'
DOMAIN_NAME = 'domainName'
DOMAIN_PREFIX = 'domainPrefix'
DOMAIN_TYPE = 'domainType'
DOMAIN_UID = 'domainUid'
HAS_ADDITIONAL_SECRETS = 'hasAdditionalSecrets'
HAS_APPLICATIONS = 'hasApplications'
HAS_CLUSTERS = 'hasClusters'
HAS_DATASOURCES = 'hasDatasources'
NAMESPACE = 'namespace'
REPLICAS = 'replicas'
RUNTIME_ENCRYPTION_SECRET = "runtimeEncryptionSecret"
WEBLOGIC_CREDENTIALS_SECRET = 'webLogicCredentialsSecret'


def create_additional_output(model, model_context, aliases, credential_injector, exception_type):
    """
    Create and write additional output for the configured target type.
    :param model: Model object, used to derive some values in the output
    :param model_context: used to determine location and content for the output
    :param aliases: used to derive secret names
    :param credential_injector: used to identify secrets
    :param exception_type: the type of exception to throw if needed
    """

    # -output_dir argument was previously verified
    output_dir = model_context.get_output_dir()

    # all current output types use this hash, and process a set of template files
    template_hash = _build_template_hash(model, model_context, aliases, credential_injector)
    template_names = model_context.get_target_configuration().get_additional_output_types()
    for template_name in template_names:
        _create_file(template_name, template_hash, model_context, output_dir, exception_type)


def _create_file(template_name, template_hash, model_context, output_dir, exception_type):
    """
    Read the template from the resource stream, perform any substitutions,
    and write it to a file with the same name in the output directory.
    :param template_name: the name of the template file, and the output file
    :param template_hash: a dictionary of substitution values
    :param model_context: used to determine location and content for the output
    :param output_dir: the directory to write the output file
    :param exception_type: the type of exception to throw if needed
    """
    _method_name = '_create_file'

    target_key = model_context.get_target()
    template_subdir = "targets/" + target_key + "/" + template_name
    template_path = path_utils.find_config_path(template_subdir)
    output_file = File(output_dir, template_name)

    __logger.info('WLSDPLY-01662', output_file, class_name=__class_name, method_name=_method_name)

    file_template_helper.create_file_from_file(template_path, template_hash, output_file, exception_type)


def _build_template_hash(model, model_context, aliases, credential_injector):
    """
    Create a dictionary of substitution values to apply to the templates.
    :param model: Model object used to derive values
    :param model_context: used to determine domain type
    :param aliases: used to derive folder names
    :param credential_injector: used to identify secrets
    :return: the hash dictionary
    """
    template_hash = dict()

    # actual domain name

    domain_name = dictionary_utils.get_element(model.get_model_topology(), NAME)
    if domain_name is None:
        domain_name = DEFAULT_WLS_DOMAIN_NAME
    template_hash[DOMAIN_NAME] = domain_name

    # domain UID, prefix, and namespace must follow DNS-1123

    domain_uid = k8s_helper.get_domain_uid(domain_name)
    template_hash[DOMAIN_UID] = domain_uid
    template_hash[DOMAIN_PREFIX] = domain_uid
    template_hash[NAMESPACE] = domain_uid

    # secrets that should not be included in secrets section
    declared_secrets = []

    # admin credential

    admin_secret = domain_uid + target_configuration_helper.WEBLOGIC_CREDENTIALS_SECRET_SUFFIX
    declared_secrets.append(admin_secret)
    template_hash[WEBLOGIC_CREDENTIALS_SECRET] = admin_secret

    # runtime encryption secret

    runtime_secret = domain_uid + target_configuration_helper.RUNTIME_ENCRYPTION_SECRET_SUFFIX
    declared_secrets.append(runtime_secret)
    template_hash[RUNTIME_ENCRYPTION_SECRET] = runtime_secret

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
        database_hash[DATASOURCE_URL] = url

        # should change spaces to hyphens?
        database_hash[DATASOURCE_PREFIX] = k8s_helper.get_dns_name(jdbc_name)

        # get the name that matches secret
        location.add_name_token(name_token, jdbc_name)
        secret_name = target_configuration_helper.get_secret_name_for_location(location, domain_uid, aliases)
        database_hash[DATASOURCE_CREDENTIALS] = secret_name

        databases.append(database_hash)

    template_hash[DATASOURCES] = databases
    template_hash[HAS_DATASOURCES] = len(databases) != 0

    # applications

    apps = []

    applications = dictionary_utils.get_dictionary_element(model.get_model_app_deployments(), APPLICATION)
    for app_name in applications:
        app_hash = dict()
        prefix = '/' + app_name

        # get the prefix from the app descriptor?

        app_hash[APPLICATION_NAME] = app_name
        app_hash[APPLICATION_PREFIX] = prefix

        apps.append(app_hash)

    template_hash[APPLICATIONS] = apps
    template_hash[HAS_APPLICATIONS] = len(apps) != 0

    # additional secrets - exclude admin

    additional_secrets = []

    # combine user/password properties to get a single list
    secrets = []
    for property_name in credential_injector.get_variable_cache():
        halves = property_name.split(':', 1)
        name = halves[0]
        if name not in secrets:
            secrets.append(name)

    for secret in secrets:
        secrets_hash = dict()
        qualified_name = domain_uid + "-" + secret
        if qualified_name not in declared_secrets:
            secrets_hash[ADDITIONAL_SECRET_NAME] = qualified_name
            additional_secrets.append(secrets_hash)

    template_hash[ADDITIONAL_SECRETS] = additional_secrets
    template_hash[HAS_ADDITIONAL_SECRETS] = len(additional_secrets) != 0

    return template_hash
