# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Shared methods for using target environments (-target abc).
# Used by discoverDomain and prepareModel.
import re
import os
from java.io import File

from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util import variable_injector_functions
from wlsdeploy.tool.util.targets import additional_output_helper
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.json.json_translator import PythonToJson


__class_name = 'target_configuration_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

# Kubernetes secret for admin name and password is <domainUid>-weblogic-credentials
WEBLOGIC_CREDENTIALS_SECRET_NAME = 'weblogic-credentials'
WEBLOGIC_CREDENTIALS_SECRET_SUFFIX = '-' + WEBLOGIC_CREDENTIALS_SECRET_NAME

JDBC_CREDENTIALS_SECRET_USER_NAME = 'standalone-jdbc.xml.user'
JDBC_CREDENTIALS_SECRET_USER_SUFFIX = '-' + JDBC_CREDENTIALS_SECRET_USER_NAME

JDBC_CREDENTIALS_SECRET_PASS_NAME = 'standalone-jdbc.xml.pass.encrypt'
JDBC_CREDENTIALS_SECRET_PASS_SUFFIX = '-' + JDBC_CREDENTIALS_SECRET_PASS_NAME

JDBC_CREDENTIALS_SECRET_ONS_PASS_NAME = 'standalone-jdbc.xml.ons.pass.encrypt'
JDBC_CREDENTIALS_SECRET_ONS_PASS_SUFFIX = '-' + JDBC_CREDENTIALS_SECRET_ONS_PASS_NAME

RUNTIME_ENCRYPTION_SECRET_NAME = 'runtime-encryption-secret'
RUNTIME_ENCRYPTION_SECRET_SUFFIX = '-' + RUNTIME_ENCRYPTION_SECRET_NAME

# keys for secrets, such as "password" in "jdbc-mydatasource:password"
SECRET_USERNAME_KEY = "username"
SECRET_PASSWORD_KEY = "password"

VZ_EXTRA_CONFIG = 'vz'

ADMIN_USER_TAG = "<admin-user>"
ADMIN_PASSWORD_TAG = "<admin-password>"
USER_TAG = "<user>"
PASSWORD_TAG = "<password>"

# placeholders for config override secrets
ADMIN_USERNAME_KEY = ADMIN_USERNAME.lower()
ADMIN_PASSWORD_KEY = ADMIN_PASSWORD.lower()

# placeholders for config override secrets
ADMINUSER_PLACEHOLDER = "weblogic"
PASSWORD_PLACEHOLDER = "password1"
USERNAME_PLACEHOLDER = "username"

# recognize these to apply special override secret
ADMIN_USER_SECRET_NAMES = [
    ADMIN_USERNAME_KEY + ":" + SECRET_USERNAME_KEY,
    WEBLOGIC_CREDENTIALS_SECRET_NAME + ":" + SECRET_USERNAME_KEY
]

# for matching and refining credential secret names
JDBC_USER_PATTERN = re.compile('.user.Value$')
JDBC_USER_REPLACEMENT = '.user-value'
SECURITY_NM_PATTERN = re.compile('^SecurityConfig.NodeManager')
SECURITY_NM_REPLACEMENT = 'SecurityConfig.NodeManager.'

K8S_SCRIPT_NAME = 'create_k8s_secrets.sh'
K8S_SCRIPT_RESOURCE_PATH = 'oracle/weblogic/deploy/k8s/' + K8S_SCRIPT_NAME
RESULTS_FILE_NAME = 'results.json'


def process_target_arguments(argument_map):
    """
    If the -target option is in the argument map, verify that -output_dir is specified.
    If variables_file was not specified, add it with the file <outputDir>/<targetName>_variable.properties .
    :param argument_map: the argument map to be checked and possibly modified
    """
    _method_name = 'process_target_arguments'

    if CommandLineArgUtil.TARGET_SWITCH in argument_map:
        target_name = argument_map[CommandLineArgUtil.TARGET_SWITCH]

        # if -target is specified -output_dir is required
        output_dir = dictionary_utils.get_element(argument_map, CommandLineArgUtil.OUTPUT_DIR_SWITCH)
        if (output_dir is None) or (not os.path.isdir(output_dir)):
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-01642', CommandLineArgUtil.OUTPUT_DIR_SWITCH,
                                                       CommandLineArgUtil.TARGET_SWITCH, target_name)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex


def generate_all_output_files(model, aliases, credential_injector, model_context, exception_type):
    """
    Create all output files indicated by the target configuration.
    This should be called after model is filtered, but before it is tokenized.
    :param model: Model object, used to derive some values in the output
    :param aliases: used to derive secret names
    :param credential_injector: used to identify secrets
    :param model_context: used to determine location and content for the output
    :param exception_type: the type of exception to throw if needed
    """
    if model_context.is_targetted_config():
        target_config = model_context.get_target_configuration()
        credential_cache = credential_injector.get_variable_cache()

        if target_config.generate_results_file():
            generate_results_json(model_context, credential_cache, model.get_model(), exception_type)

        if target_config.generate_output_files():
            # Generate k8s create secret script
            generate_k8s_script(model_context, credential_cache, model.get_model(), exception_type)

            # create additional output files
            additional_output_helper.create_additional_output(model, model_context, aliases, credential_injector,
                                                              exception_type)


def _prepare_k8s_secrets(model_context, token_dictionary, model_dictionary):

    # determine the domain name and UID
    domain_name = k8s_helper.get_domain_name(model_dictionary)
    domain_uid = k8s_helper.get_domain_uid(domain_name)
    comment = exception_helper.get_message("WLSDPLY-01665")
    script_hash = {'domainUid': domain_uid, 'topComment': comment, 'namespace': domain_uid}

    # build a map of secret names (jdbc-generic1) to keys (username, password)
    secret_map = {}
    for property_name in token_dictionary:
        halves = property_name.split(':', 1)
        value = token_dictionary[property_name]
        if len(halves) == 2:
            secret_name = halves[0]

            # admin credentials are inserted later, at the top of the list
            if secret_name == WEBLOGIC_CREDENTIALS_SECRET_NAME:
                continue

            secret_key = halves[1]
            if secret_name not in secret_map:
                secret_map[secret_name] = {}
            secret_keys = secret_map[secret_name]
            secret_keys[secret_key] = value

    # update the hash with secrets and paired secrets
    secrets = []
    paired_secrets = [_build_secret_hash(WEBLOGIC_CREDENTIALS_SECRET_NAME, USER_TAG, PASSWORD_TAG)]

    secret_names = secret_map.keys()
    secret_names.sort()
    for secret_name in secret_names:
        secret_keys = secret_map[secret_name]
        user_name = dictionary_utils.get_element(secret_keys, SECRET_USERNAME_KEY)

        if user_name is None:
            secrets.append(_build_secret_hash(secret_name, None, PASSWORD_TAG))
        else:
            paired_secrets.append(_build_secret_hash(secret_name, user_name, PASSWORD_TAG))

    # add a secret with a specific comment for runtime encryption
    target_config = model_context.get_target_configuration()
    additional_secrets = target_config.get_additional_secrets()
    if RUNTIME_ENCRYPTION_SECRET_NAME in additional_secrets:
        runtime_hash = _build_secret_hash(RUNTIME_ENCRYPTION_SECRET_NAME, None, PASSWORD_TAG)
        message1 = exception_helper.get_message("WLSDPLY-01671", PASSWORD_TAG)
        message2 = exception_helper.get_message("WLSDPLY-01672")
        runtime_hash['comments'] = [{'comment': message1}, {'comment': message2}]
        secrets.append(runtime_hash)

    script_hash['secrets'] = secrets
    script_hash['pairedSecrets'] = paired_secrets
    script_hash['longMessage'] = exception_helper.get_message('WLSDPLY-01667', '${LONG_SECRETS_COUNT}')

    long_messages = [
        {'text': exception_helper.get_message('WLSDPLY-01668')},
        {'text': exception_helper.get_message('WLSDPLY-01669')},
        {'text': exception_helper.get_message('WLSDPLY-01670')}
    ]
    script_hash['longMessageDetails'] = long_messages
    return script_hash


def generate_k8s_script(model_context, token_dictionary, model_dictionary, exception_type):
    """
    Generate a shell script for creating k8s secrets.
    :param model_context: used to determine output directory
    :param token_dictionary: contains every token
    :param model_dictionary: used to determine domain UID
    :param exception_type: type of exception to throw
    """
    script_hash = _prepare_k8s_secrets(model_context, token_dictionary, model_dictionary)
    file_location = model_context.get_output_dir()
    k8s_file = File(file_location, K8S_SCRIPT_NAME)
    file_template_helper.create_file_from_resource(K8S_SCRIPT_RESOURCE_PATH, script_hash, k8s_file, exception_type)
    FileUtils.chmod(k8s_file.getPath(), 0750)


def generate_results_json(model_context, token_dictionary, model_dictionary, exception_type):
    """
    Generate a JSON results file.
    :param model_context: used to determine output directory
    :param token_dictionary: contains every token
    :param model_dictionary: used to determine data
    :param exception_type: type of exception to throw
    """
    file_location = model_context.get_output_dir()
    results_file = os.path.join(file_location, RESULTS_FILE_NAME)

    domain_name = k8s_helper.get_domain_name(model_dictionary)
    domain_uid = k8s_helper.get_domain_uid(domain_name)

    result = {
        'domainUID': domain_uid,
        'secrets': _build_json_secrets_result(model_context, token_dictionary, model_dictionary),
        'clusters': _build_json_cluster_result(model_dictionary)
    }
    json_object = PythonToJson(result)

    try:
        json_object.write_to_json_file(results_file)
    except JsonException, ex:
        raise exception_helper.create_exception(exception_type, 'WLSDPLY-01681', results_file,
                                                ex.getLocalizedMessage(), error=ex)


def _build_json_secrets_result(model_context, token_dictionary, model_dictionary):
    script_hash = _prepare_k8s_secrets(model_context, token_dictionary, model_dictionary)
    secrets_map = {}
    for secretType in ['secrets', 'pairedSecrets']:
        for node in script_hash[secretType]:
            secret_name = node['secretName']
            keys = {}
            user = dictionary_utils.get_element(node, 'user')
            if user:
                # For ui, empty it now.
                if user.startswith('@@SECRET:'):
                    user = ""
                if secret_name == WEBLOGIC_CREDENTIALS_SECRET_NAME:
                    user = ""
                keys['username'] = user

            keys['password'] = ""
            secret = {'keys': keys}
            secrets_map[secret_name] = secret
    return secrets_map


def _build_json_cluster_result(model_dictionary):
    clusters_map = {}
    topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
    clusters = dictionary_utils.get_dictionary_element(topology, CLUSTER)
    for cluster_name, cluster_values in clusters.items():
        server_count = k8s_helper.get_server_count(cluster_name, cluster_values, model_dictionary)
        cluster_data = {'serverCount': server_count}
        clusters_map[cluster_name] = cluster_data
    return clusters_map


def format_as_secret_token(secret_id, target_config):
    """
    Format the secret identifier as an @@SECRET token for use in a model.
    :param secret_id: secret name, such as "jdbc-mydatasource:password"
    :param target_config: target configuration
    :return: secret token, such as "@@SECRET:@@ENV:DOMAIN_UID@@-jdbc-mydatasource:password"
    """
    # check special case where target config has a WLS credential name, such as  "__weblogic-credentials__"
    wls_credentials_name = target_config.get_wls_credentials_name()
    parts = secret_id.split(':')
    if (wls_credentials_name is not None) and (len(parts) == 2):
        if parts[0] == WEBLOGIC_CREDENTIALS_SECRET_NAME:
            return '@@SECRET:%s:%s@@' % (wls_credentials_name, parts[1])

    return '@@SECRET:@@ENV:DOMAIN_UID@@-%s@@' % (secret_id)


def format_as_overrides_secret(secret_id):
    """
    Format the secret identifier as a credential placeholder for use in a model.
    This is done when the target's credentials method is config_override_secrets .
    :param secret_id: secret name, such as "jdbc-mydatasource:password"
    :return: placeholder value, such as "password1"
    """
    if secret_id in ADMIN_USER_SECRET_NAMES:
        return ADMINUSER_PLACEHOLDER
    elif secret_id.endswith(':' + SECRET_USERNAME_KEY):
        return USERNAME_PLACEHOLDER
    return PASSWORD_PLACEHOLDER


def get_secret_name_for_location(location, domain_uid, aliases):
    """
    Returns the secret name for the specified model location.
    Example: mydomain-jdbc-mydatasource
    :param location: the location to be evaluated
    :param domain_uid: used to prefix the secret name
    :param aliases: used to examine the location
    :return: the secret name
    """
    variable_name = variable_injector_functions.format_variable_name(location, '(none)', aliases)
    secret_name = create_secret_name(variable_name)
    return domain_uid + '-' + secret_name


def create_secret_name(variable_name, suffix=None):
    """
    Return the secret name derived from the specified property variable name.
    Some corrections are made for known attributes to associate user names with passwords.
    Remove the last element of the variable name, which corresponds to the attribute name.
    Follow limitations for secret names: only alphanumeric and "-", must start and end with alphanumeric.
    For example, "JDBC.Generic1.PasswordEncrypted" becomes "jdbc-generic1".
    :param variable_name: the variable name to be converted
    :param suffix: optional suffix for the name, such as "pop3.user"
    :return: the derived secret name
    """

    # JDBC user ends with ".user.Value", needs to be .user-value to match with password
    variable_name = JDBC_USER_PATTERN.sub(JDBC_USER_REPLACEMENT, variable_name)

    # associate the two SecurityConfiguration.NodeManager* credentials, distinct from CredentialEncrypted
    variable_name = SECURITY_NM_PATTERN.sub(SECURITY_NM_REPLACEMENT, variable_name)

    # append the suffix ir present, such as mail-mymailsession-properties-pop3.user
    if suffix:
        variable_name = '%s-%s' % (variable_name, suffix)

    variable_keys = variable_name.lower().split('.')

    # admin user and password have a special secret name
    if variable_keys[-1] in [ADMIN_USERNAME_KEY, ADMIN_PASSWORD_KEY]:
        return WEBLOGIC_CREDENTIALS_SECRET_NAME

    # if the attribute was not in a folder, append an extra key to be skipped, such as opsssecrets.x
    if len(variable_keys) == 1:
        variable_keys.append('x')

    secret_keys = []
    for variable_key in variable_keys[:-1]:
        secret_key = re.sub('[^a-z0-9-]', '-', variable_key)
        secret_keys.append(secret_key)

    # rejoin with hyphens, remove leading and trailing hyphens from final name.
    # if empty, just return "x".
    secret = '-'.join(secret_keys).strip('-')
    return secret or 'x'


def _build_secret_hash(secret_name, user, password):
    """
    Build a hash for a single secret, for use with the create secrets script template.
    :param secret_name: the name of the secret
    :param user: the associated user name, or None
    :param password: the associated password
    :return: a secret hash
    """
    if user:
        message = exception_helper.get_message("WLSDPLY-01664", USER_TAG, PASSWORD_TAG, secret_name)
        return {'secretName': secret_name, 'user': user, 'password': password, 'comments': [{'comment': message}]}
    else:
        message = exception_helper.get_message("WLSDPLY-01663", PASSWORD_TAG, secret_name)
        return {'secretName': secret_name, 'password': password, 'comments': [{'comment': message}]}
