# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Shared methods for using target environments (-target abc).
# Used by discoverDomain and prepareModel.
import os
import re

from java.io import File
from oracle.weblogic.deploy.encrypt import EncryptionUtils
from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases.alias_constants import SECRET_PASSWORD_KEY
from wlsdeploy.aliases.alias_constants import SECRET_USERNAME_KEY
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import CLUSTER
from wlsdeploy.aliases.model_constants import DEFAULT_ADMIN_SERVER_NAME
from wlsdeploy.aliases.model_constants import SERVER
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.exception import exception_helper
from wlsdeploy.json.json_translator import PythonToJson
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util import variable_injector_functions
from wlsdeploy.tool.util.targets import additional_output_helper
from wlsdeploy.tool.util.targets import file_template_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode

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

MAX_SECRET_LENGTH=63

# placeholders for config override secrets
ADMIN_USERNAME_KEY = ADMIN_USERNAME.lower()
ADMIN_PASSWORD_KEY = ADMIN_PASSWORD.lower()

# placeholders for config override secrets
ADMINUSER_PLACEHOLDER = "weblogic"
PASSWORD_PLACEHOLDER = "password1"
USERNAME_PLACEHOLDER = "username"

# list of normal secret keys that are password fields
PASSWORD_SECRET_KEY_NAMES = [ 'password' ]

# recognize these to apply special override secret
ADMIN_USER_SECRET_NAMES = [
    ADMIN_USERNAME_KEY + ":" + SECRET_USERNAME_KEY,
    WEBLOGIC_CREDENTIALS_SECRET_NAME + ":" + SECRET_USERNAME_KEY
]

# for matching and refining credential secret names
JDBC_USER_PATTERN = re.compile('.user.Value$')
JDBC_USER_REPLACEMENT = '.user-value'

K8S_SCRIPT_NAME = 'create_k8s_secrets.sh'
K8S_SCRIPT_RESOURCE_PATH = 'oracle/weblogic/deploy/k8s/' + K8S_SCRIPT_NAME + file_template_helper.MUSTACHE_SUFFIX
RESULTS_FILE_NAME = 'results.json'

PASSWORD_HASH_MARKER = "{ssha256}"


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
    script_hash = {'domainUid': domain_uid, 'topComment': comment, 'namespace': domain_uid,
                   'maxSecretLength': str(MAX_SECRET_LENGTH)}

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
            secret_keys[secret_key] = _get_output_value(secret_key, value, model_context, False)

    # update the secrets hash

    # include WebLogic credentials always, they're not in secret_map
    secrets = [_build_secret_hash(WEBLOGIC_CREDENTIALS_SECRET_NAME, {
        SECRET_USERNAME_KEY: None,
        SECRET_PASSWORD_KEY: None
    })]

    # add secrets found in the model
    secret_names = secret_map.keys()
    secret_names.sort()
    for secret_name in secret_names:
        secret_keys = secret_map[secret_name]
        secrets.append(_build_secret_hash(secret_name, secret_keys))

    # add a secret with a specific comment for runtime encryption
    target_config = model_context.get_target_configuration()
    additional_secrets = target_config.get_additional_secrets()
    if RUNTIME_ENCRYPTION_SECRET_NAME in additional_secrets:
        runtime_hash = _build_secret_hash(RUNTIME_ENCRYPTION_SECRET_NAME, {
            SECRET_PASSWORD_KEY: None
        })
        message1 = exception_helper.get_message("WLSDPLY-01671", SECRET_PASSWORD_KEY)
        message2 = exception_helper.get_message("WLSDPLY-01672")
        runtime_hash['comments'] = [{'comment': message1}, {'comment': message2}]
        secrets.append(runtime_hash)

    script_hash['secrets'] = secrets
    script_hash['longMessage'] = exception_helper.get_message('WLSDPLY-01667', '${LONG_SECRETS_COUNT}')

    long_messages = [
        {'text': exception_helper.get_message('WLSDPLY-01668', MAX_SECRET_LENGTH)},
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
        'secrets': _build_json_secrets_result(model_context, token_dictionary),
        'clusters': _build_json_cluster_result(model_dictionary),
        'servers': _build_json_server_result(model_dictionary)
    }
    json_object = PythonToJson(result)

    try:
        json_object.write_to_json_file(results_file)
    except JsonException, ex:
        raise exception_helper.create_exception(exception_type, 'WLSDPLY-01681', results_file,
                                                ex.getLocalizedMessage(), error=ex)


def _build_json_secrets_result(model_context, token_dictionary):
    """
    Build a secrets result dictionary for use in the results.json file.
    Include the runtime encryption secret.
    Exclude the WebLogic credentials secret if included.
    :param model_context: use to used to get target configuration
    :param token_dictionary: the token dictionary from prepare or discover tools
    :return: the secrets dictionary
    """
    secrets_map = {}
    for property_name in token_dictionary:
        value = token_dictionary[property_name]

        # discard unresolved secret value - not sure if this still occurs
        if value.startswith('@@SECRET:'):
            value = ""

        halves = property_name.split(':', 1)
        if len(halves) == 2:
            secret_name = halves[0]
            secret_key = halves[1]

            # admin credentials are inserted later, at the top of the list
            if secret_name == WEBLOGIC_CREDENTIALS_SECRET_NAME:
                continue

            if secret_name not in secrets_map:
                secrets_map[secret_name] = {'keys': {}}

            secret_keys = secrets_map[secret_name]['keys']
            secret_keys[secret_key] = _get_output_value(secret_key, value, model_context, True)

    # runtime encryption key is not included in token_dictionary
    target_config = model_context.get_target_configuration()
    additional_secrets = target_config.get_additional_secrets()
    if RUNTIME_ENCRYPTION_SECRET_NAME in additional_secrets:
        secrets_map[RUNTIME_ENCRYPTION_SECRET_NAME] = {'keys': {'password': ''}}

    # sort by secret name
    secret_names = secrets_map.keys()
    secret_names.sort()
    sorted_map = PyOrderedDict()
    for secret_name in secret_names:
        sorted_map[secret_name] = secrets_map[secret_name]

    return sorted_map


def _build_json_cluster_result(model_dictionary):
    clusters_map = {}
    topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
    clusters = dictionary_utils.get_dictionary_element(topology, CLUSTER)
    for cluster_name, cluster_values in clusters.items():
        server_count = k8s_helper.get_server_count(cluster_name, cluster_values, model_dictionary)
        cluster_data = {'serverCount': server_count}
        clusters_map[cluster_name] = cluster_data
    return clusters_map


def _build_json_server_result(model_dictionary):
    """
    Build a map containing servers that are not assigned to clusters.
    :param model_dictionary: the model to be searched
    :return: the map of servers
    """
    servers_map = {}
    topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
    servers = dictionary_utils.get_dictionary_element(topology, SERVER)
    for server_name, server_values in servers.items():
        assigned_cluster = dictionary_utils.get_element(server_values, CLUSTER)
        if not assigned_cluster:
            server_data = {}
            servers_map[server_name] = server_data

    # admin server may not be specified in the Server section of the model
    admin_server = dictionary_utils.get_element(topology, ADMIN_SERVER_NAME, DEFAULT_ADMIN_SERVER_NAME)
    if admin_server not in servers_map:
        server_data = {}
        servers_map[admin_server] = server_data

    return servers_map


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
    Returns the secret name for the specified model location, such as mydomain-opsssecrets:password.
    Example: mydomain-jdbc-mydatasource
    :param location: the location to be evaluated
    :param domain_uid: used to prefix the secret name
    :param aliases: used to examine the location
    :return: the secret name
    """
    secret_name = format_secret_name(location, location, None, aliases)
    return domain_uid + '-' + secret_name


def get_secret_path(model_location, attribute_location, attribute, aliases, suffix=None):
    """
    Get the full secret path <secretName>:<secretKey>
    Example: mail-mymailsession-properties-smtp:password
    :param model_location: the model location of the attribute
    :param attribute_location: the alias location of the attribute
    :param attribute: the attribute to be evaluated, or None
    :param aliases: for information about the location and attribute
    :param suffix: optional suffix for the name, such as "pop3.user"
    :return: the secret path
    """
    short_name = variable_injector_functions.get_short_name(model_location, attribute, aliases)
    secret_name = format_secret_name(model_location, attribute_location, attribute, aliases, suffix)

    if JDBC_USER_PATTERN.search(short_name):
        # JDBC user property is still a special case
        secret_key = SECRET_USERNAME_KEY
    elif suffix:
        # derive the secret key from the suffix, specific to MailSession
        secret_key = SECRET_USERNAME_KEY
        if suffix.endswith(".password"):
            secret_key = SECRET_PASSWORD_KEY
    else:
        # derive the secret key from the alias
        secret_key = aliases.get_secret_key(attribute_location, attribute)
        secret_key = secret_key or 'unknown'

    return '%s:%s' % (secret_name, secret_key)


def format_secret_name(model_location, attribute_location, attribute, aliases, suffix=None):
    """
    Return a secret name for the specified attribute and location.
    Some corrections are made for known attributes to associate usernames with passwords.
    Remove the last element of the variable name, which corresponds to the attribute name.
    Example: mail-mymailsession-properties-smtp
    :param model_location: the model location of the attribute
    :param attribute_location: the alias location of the attribute
    :param attribute: the attribute to be evaluated, or None
    :param aliases: for information about the location and attribute
    :param suffix: optional suffix for the name, such as "pop3.user"
    :return: the secret name
    """
    _method_name = 'format_secret_name'

    # if no attribute passed in, use placeholder
    short_attribute = attribute or '(none)'
    short_attribute = re.sub('[.]', '-', short_attribute)  # RCU attributes have "."
    short_name = variable_injector_functions.get_short_name(model_location, short_attribute, aliases)

    # JDBC user ends with ".user.Value", needs to be .user-value to match with password secret
    short_name = JDBC_USER_PATTERN.sub(JDBC_USER_REPLACEMENT, short_name)

    # append the suffix if present, such as mail-mymailsession-properties-pop3.user
    if suffix:
        short_name = '%s-%s' % (short_name, suffix)

    # split the short name into keys
    name_keys = short_name.lower().split('.')
    is_single_key = len(name_keys) == 1

    # admin user and password have a special secret name
    if name_keys[-1] in [ADMIN_USERNAME_KEY, ADMIN_PASSWORD_KEY]:
        return WEBLOGIC_CREDENTIALS_SECRET_NAME

    # discard the last key (the attribute), unless it is the only key
    if len(name_keys) > 1:
        name_keys = name_keys[:-1]

    # join the secret keys with hyphens, remove leading and trailing hyphens
    secret = '-'.join(name_keys)
    secret = re.sub('[^a-z0-9-]', '-', secret)
    secret = secret.strip('-')

    # apply the alias suffix if present.
    # aliases may define a suffix to distinguish multiple credentials.
    alias_suffix = aliases.get_secret_suffix(attribute_location, attribute)
    if alias_suffix:
        if is_single_key:
            # replace a single name (top-level attribute) with the alias suffix
            secret = alias_suffix
        else:
            # append to secret
            secret = '%s-%s' % (secret, alias_suffix)

    # if the secret was empty, just return "secret"
    return secret or 'secret'


def _build_secret_hash(secret_name, secret_key_map):
    """
    Build a hash for a single secret, for use with the create secrets script template.
    :param secret_name: the name of the secret
    :param secret_key_map: a map of secret names to values
    :return: a secret hash
    """
    secret_pairs = []
    update_keys = []
    for secret_key in secret_key_map:
        value = secret_key_map[secret_key]
        if not value:
            value = '<' + secret_key + '>'
            update_keys.append(secret_key)
        secret_pairs.append('"' + secret_key + '=' + value + '"')

    secret_pairs_text = ' '.join(secret_pairs)
    message = exception_helper.get_message("WLSDPLY-01684", secret_name)
    if update_keys:
        message = exception_helper.get_message("WLSDPLY-01683", secret_name, ', '.join(update_keys))

    return {'secretName': secret_name, 'secretPairs': secret_pairs_text, 'comments': [{'comment': message}]}


def _get_output_value(secret_key, value, model_context, include_encrypted_passwords):
    """
    Determine the secret value to be provided to the secrets script or results output JSON.
    Exclude password values unless they are one-way hashed values, such as those in LDIF files.
    :param secret_key: the key into the credentials map
    :param value: the value to be examined
    :param model_context: used to decrypt value
    :param include_encrypted_passwords: whether to return encrypted passwords
    :return: the value to be provided
    """
    if secret_key in PASSWORD_SECRET_KEY_NAMES and value:
        if EncryptionUtils.isEncryptedString(value):
            if include_encrypted_passwords:
                return value
            value = encryption_utils.decrypt_one_password(model_context.get_encryption_passphrase(), value)

        if value.startswith(PASSWORD_HASH_MARKER):
            return value
        else:
            return None
    else:
        return value
