"""
Copyright (c) 2020, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Methods for creating Kubernetes resource configuration files for Verrazzano.
"""
import os.path

from java.io import File

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import APPLICATION
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DYNAMIC_SERVERS
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import LISTEN_PORT
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import SERVER_TEMPLATE
from wlsdeploy.aliases.model_constants import TARGET
from wlsdeploy.aliases.model_constants import URL
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util.targets import crd_file_updater
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.tool.util.targets import model_crd_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import path_helper
from wlsdeploy.util import target_configuration_helper
import wlsdeploy.util.unicode_helper as str_helper

__class_name = 'vz_config_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

# substitution keys used in the templates
ADDITIONAL_SECRET_NAME = 'additionalSecretName'
ADDITIONAL_SECRETS = 'additionalSecrets'
APPLICATIONS = 'applications'
APPLICATION_NAME = 'applicationName'
APPLICATION_PREFIX = 'applicationPrefix'
CLUSTER_NAME = 'clusterName'
CLUSTER_UID = 'clusterUid'
CLUSTERS = 'clusters'
DATASOURCE_CREDENTIALS = 'datasourceCredentials'
DATASOURCE_PREFIX = 'datasourcePrefix'
DATASOURCES = 'datasources'
DATASOURCE_NAME = 'datasourceName'
DATASOURCE_URL = 'url'
DOMAIN_HOME = 'domainHome'
DOMAIN_HOME_SOURCE_TYPE = 'domainHomeSourceType'
DOMAIN_NAME = 'domainName'
DOMAIN_PREFIX = 'domainPrefix'
DOMAIN_TYPE = 'domainType'
DOMAIN_UID = 'domainUid'
HAS_ADDITIONAL_SECRETS = 'hasAdditionalSecrets'
HAS_APPLICATIONS = 'hasApplications'
HAS_CLUSTERS = 'hasClusters'
HAS_DATASOURCES = 'hasDatasources'
HAS_HOST_APPLICATIONS = 'hasHostApplications'
HAS_MODEL = 'hasModel'
HOST_APPLICATION_APPLICATIONS = 'applications'
HOST_APPLICATION_HOST = 'host'
HOST_APPLICATION_PORT = 'port'
HOST_APPLICATIONS = 'hostApplications'
NAMESPACE = 'namespace'
REPLICAS = 'replicas'
RUNTIME_ENCRYPTION_SECRET = "runtimeEncryptionSecret"
SET_CLUSTER_REPLICAS = "setClusterReplicas"
USE_PERSISTENT_VOLUME = "usePersistentVolume"
WEBLOGIC_CREDENTIALS_SECRET = 'webLogicCredentialsSecret'

DEFAULT_LISTEN_PORT = 7001


def create_additional_output(model, model_context, aliases, credential_injector, exception_type,
                             domain_home_override=None):
    """
    Create and write additional output for the configured target type.
    Build a hash map of values to be applied to each template.
    For each additional output type:
      1) read the source template
      2) apply the template hash to the template
      3) write the result to the template output file
      4) update the output file with content from the model (crd_file_updater)
    :param model: Model object, used to derive some values in the output
    :param model_context: used to determine location and content for the output
    :param aliases: used to derive secret names
    :param credential_injector: used to identify secrets
    :param exception_type: the type of exception to throw if needed
    :param domain_home_override: (optionsl) domain home value to use in CRD, or None
    """
    _method_name = 'create_additional_output'
    __logger.entering(exception_type, domain_home_override, class_name=__class_name, method_name=_method_name)

    target_configuration = model_context.get_target_configuration()
    template_names = target_configuration.get_additional_output_types()
    if not len(template_names):
        return

    # -output_dir argument was previously verified
    output_dir = model_context.get_output_dir()

    # all current output types use this hash, and process a set of template files
    template_hash = _build_template_hash(model, model_context, aliases, credential_injector, domain_home_override)
    for index, template_name in enumerate(template_names):
        source_file_name = (_get_template_source_name(template_name, target_configuration) +
                            file_template_helper.MUSTACHE_SUFFIX)
        output_file = File(os.path.join(output_dir, template_name))

        _create_file(source_file_name, template_hash, output_file, exception_type)

        crd_helper = model_crd_helper.get_helper(model_context)
        crd_file_updater.update_from_model(output_file, model, crd_helper)

    __logger.exiting(class_name=__class_name, method_name=_method_name)

def _create_file(template_name, template_hash, output_file, exception_type):
    """
    Read the template from the resource stream, perform any substitutions,
    and write it to a file with the same name in the output directory.
    :param template_name: the name of the template file
    :param template_hash: a dictionary of substitution values
    :param output_file: the CRD java.io.File to be created
    :param exception_type: the type of exception to throw if needed
    """
    _method_name = '_create_file'

    template_subdir = "targets/templates/" + template_name
    _path_helper = path_helper.get_path_helper()
    template_path = _path_helper.find_local_config_path(template_subdir)

    __logger.info('WLSDPLY-01662', output_file, class_name=__class_name, method_name=_method_name)

    file_template_helper.create_file_from_file(template_path, template_hash, output_file, exception_type)


def _get_template_source_name(template_name, target_configuration):
    product_version = target_configuration.get_product_version()

    # for backward compatibility with WKO v3
    if product_version == model_crd_helper.WKO_VERSION_3:
        return template_name

    prefix, suffix = os.path.splitext(template_name)
    return prefix + "-" + product_version + suffix


def _build_template_hash(model, model_context, aliases, credential_injector, domain_home_override):
    """
    Create a dictionary of substitution values to apply to the templates.
    :param model: Model object used to derive values
    :param model_context: used to determine domain type
    :param aliases: used to derive folder names
    :param credential_injector: used to identify secrets
    :param domain_home_override: used as domain home if not None
    :return: the hash dictionary
    """
    template_hash = dict()
    target_configuration = model_context.get_target_configuration()

    # actual domain name

    domain_name = k8s_helper.get_domain_name(model.get_model())
    template_hash[DOMAIN_NAME] = domain_name

    if domain_home_override:
        template_hash[DOMAIN_HOME] = domain_home_override

    # domain UID, prefix, and namespace must follow DNS-1123

    domain_uid = k8s_helper.get_domain_uid(domain_name)
    template_hash[DOMAIN_UID] = domain_uid
    template_hash[DOMAIN_PREFIX] = domain_uid
    template_hash[NAMESPACE] = domain_uid

    # domain home source type
    template_hash[DOMAIN_HOME_SOURCE_TYPE] = target_configuration.get_domain_home_source_name()
    template_hash[HAS_MODEL] = target_configuration.uses_wdt_model()

    # secrets that should not be included in secrets section
    declared_secrets = []

    # admin credential

    admin_secret = domain_uid + target_configuration_helper.WEBLOGIC_CREDENTIALS_SECRET_SUFFIX
    declared_secrets.append(admin_secret)
    template_hash[WEBLOGIC_CREDENTIALS_SECRET] = admin_secret

    # runtime encryption secret

    additional_secrets = target_configuration.get_additional_secrets()
    if target_configuration_helper.RUNTIME_ENCRYPTION_SECRET_NAME in additional_secrets:
        runtime_secret = domain_uid + target_configuration_helper.RUNTIME_ENCRYPTION_SECRET_SUFFIX
        declared_secrets.append(runtime_secret)
        template_hash[RUNTIME_ENCRYPTION_SECRET] = runtime_secret

    # use persistent_volume

    template_hash[USE_PERSISTENT_VOLUME] = target_configuration.use_persistent_volume()

    # configuration / model
    template_hash[DOMAIN_TYPE] = model_context.get_domain_type()

    # clusters

    clusters = []
    cluster_list = dictionary_utils.get_dictionary_element(model.get_model_topology(), CLUSTER)
    for cluster_name in cluster_list:
        cluster_hash = dict()
        cluster_hash[CLUSTER_NAME] = cluster_name
        cluster_hash[CLUSTER_UID] = k8s_helper.get_dns_name(cluster_name)

        cluster_values = dictionary_utils.get_dictionary_element(cluster_list, cluster_name)
        server_count = k8s_helper.get_server_count(cluster_name, cluster_values, model.get_model())
        cluster_hash[REPLICAS] = str_helper.to_string(server_count)
        cluster_hash[SET_CLUSTER_REPLICAS] = target_configuration.sets_cluster_replicas()
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

    # host applications - applications organized by host, for Verrazzano IngressTrait

    app_map = {}
    applications = dictionary_utils.get_dictionary_element(model.get_model_app_deployments(), APPLICATION)
    for app_name in applications:
        app_hash = dict()
        app_hash[APPLICATION_NAME] = app_name
        # this text is matched in crd_file_updater, be careful if changing
        app_hash[APPLICATION_PREFIX] = '(path for ' + app_name + ')'

        app_folder = dictionary_utils.get_dictionary_element(applications, app_name)
        targets_value = dictionary_utils.get_dictionary_element(app_folder, TARGET)
        targets = alias_utils.create_list(targets_value, 'WLSDPLY-01682')
        for target in targets:
            if target not in app_map:
                app_map[target] = []
            app_map[target].append(app_hash)

    host_apps = []
    target_keys = app_map.keys()
    target_keys.sort()
    for target_key in target_keys:
        listen_port = DEFAULT_LISTEN_PORT
        target_cluster = _find_cluster(model, target_key)
        if target_cluster is not None:
            full_host_name = k8s_helper.get_dns_name(domain_uid + '-cluster-' + target_key)
            dynamic_servers = dictionary_utils.get_dictionary_element(target_cluster, DYNAMIC_SERVERS)
            template_name = dictionary_utils.get_element(dynamic_servers, SERVER_TEMPLATE)
            if template_name:
                server_template = _find_server_template(model, template_name)
                if server_template:
                    listen_port = server_template[LISTEN_PORT] or listen_port
        else:
            full_host_name = k8s_helper.get_dns_name(domain_uid + '-' + target_key)
            target_server = _find_server(model, target_key)
            if target_server is not None:
                listen_port = target_server[LISTEN_PORT] or listen_port

        host_app = {
            HOST_APPLICATION_HOST: full_host_name,
            HOST_APPLICATION_PORT: str_helper.to_string(listen_port),
            HOST_APPLICATION_APPLICATIONS: app_map[target_key]
        }
        host_apps.append(host_app)

    template_hash[HOST_APPLICATIONS] = host_apps
    template_hash[HAS_HOST_APPLICATIONS] = len(host_apps) != 0

    # additional secrets - exclude admin

    additional_secrets = []

    # combine user/password properties to get a single list
    secrets = []

    if target_configuration.uses_credential_secrets():
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


def _find_cluster(model, name):
    cluster_map = dictionary_utils.get_dictionary_element(model.get_model_topology(), CLUSTER)
    for cluster_name in cluster_map:
        if name == cluster_name:
            return cluster_map[cluster_name]
    return None


def _find_server(model, name):
    server_map = dictionary_utils.get_dictionary_element(model.get_model_topology(), SERVER)
    for server_name in server_map:
        if name == server_name:
            return server_map[server_name]
    return None


def _find_server_template(model, name):
    template_map = dictionary_utils.get_dictionary_element(model.get_model_topology(), SERVER_TEMPLATE)
    for template_name in template_map:
        if name == template_name:
            return template_map[template_name]
    return None
