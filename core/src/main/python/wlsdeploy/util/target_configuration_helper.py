# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Shared methods for using target environments (-target abc).
# Used by discoverDomain and prepareModel.
import re
import os

from oracle.weblogic.deploy.util import FileUtils

from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util import variable_injector_functions
from wlsdeploy.tool.util.targets import additional_output_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil

__class_name = 'target_configuration_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

# Kubernetes secret for admin name and password is <domainUid>-weblogic-credentials
WEBLOGIC_CREDENTIALS_SECRET_NAME = 'weblogic-credentials'
WEBLOGIC_CREDENTIALS_SECRET_SUFFIX = '-' + WEBLOGIC_CREDENTIALS_SECRET_NAME

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
            ex = exception_helper.create_cla_exception('WLSDPLY-01642', CommandLineArgUtil.OUTPUT_DIR_SWITCH,
                                                       CommandLineArgUtil.TARGET_SWITCH, target_name)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex

        # Set the -variable_file parameter if not present with default
        if CommandLineArgUtil.VARIABLE_FILE_SWITCH not in argument_map:
            path = os.path.join(output_dir, target_name + "_variable.properties")
            argument_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH] = path


def generate_k8s_script(model_context, token_dictionary, model_dictionary):
    """
    Generate a shell script for creating k8s secrets.
    :param model_context: used to determine output directory
    :param token_dictionary: contains every token
    :param model_dictionary: used to determine domain UID
    """

    # determine the domain name and UID
    topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
    domain_name = dictionary_utils.get_element(topology, NAME)
    if domain_name is None:
        domain_name = DEFAULT_WLS_DOMAIN_NAME

    domain_uid = k8s_helper.get_domain_uid(domain_name)

    nl = '\n'
    file_location = model_context.get_output_dir()
    k8s_file = os.path.join(file_location, "create_k8s_secrets.sh")
    k8s_script = open(k8s_file, 'w')

    k8s_script.write('#!/bin/bash' + nl)

    k8s_script.write(nl)
    k8s_script.write('set -eu' + nl)

    k8s_script.write(nl)
    message = exception_helper.get_message("WLSDPLY-01665", ADMIN_USER_TAG, ADMIN_PASSWORD_TAG)
    k8s_script.write("# " + message + nl)
    k8s_script.write('NAMESPACE=default' + nl)
    k8s_script.write('DOMAIN_UID=' + domain_uid + nl)

    k8s_script.write(nl)
    k8s_script.write('function create_k8s_secret {' + nl)
    k8s_script.write('  kubectl -n $NAMESPACE delete secret ${DOMAIN_UID}-$1 --ignore-not-found' + nl)
    k8s_script.write('  kubectl -n $NAMESPACE create secret generic ${DOMAIN_UID}-$1 --from-literal=password=$2' + nl)
    k8s_script.write('  kubectl -n $NAMESPACE label secret ${DOMAIN_UID}-$1 weblogic.domainUID=${DOMAIN_UID}' + nl)
    k8s_script.write('}' + nl)

    k8s_script.write(nl)
    k8s_script.write('function create_paired_k8s_secret {' + nl)
    k8s_script.write('  kubectl -n $NAMESPACE delete secret ${DOMAIN_UID}-$1 --ignore-not-found' + nl)
    k8s_script.write('  kubectl -n $NAMESPACE create secret generic ${DOMAIN_UID}-$1' +
                     ' --from-literal=username=$2 --from-literal=password=$3' + nl)
    k8s_script.write('  kubectl -n $NAMESPACE label secret ${DOMAIN_UID}-$1 weblogic.domainUID=${DOMAIN_UID}' + nl)
    k8s_script.write('}' + nl)

    command_string = "create_paired_k8s_secret %s %s %s" \
                     % (WEBLOGIC_CREDENTIALS_SECRET_NAME, ADMIN_USER_TAG, ADMIN_PASSWORD_TAG)

    k8s_script.write(nl)
    message = exception_helper.get_message("WLSDPLY-01664", ADMIN_USER_TAG, ADMIN_PASSWORD_TAG,
                                           WEBLOGIC_CREDENTIALS_SECRET_NAME)
    k8s_script.write("# " + message + nl)
    k8s_script.write(command_string + nl)

    # build a map of secret names (jdbc-generic1) to keys (username, password)
    secret_map = {}
    for property_name in token_dictionary:
        halves = property_name.split(':', 1)
        value = token_dictionary[property_name]
        if len(halves) == 2:
            secret_name = halves[0]

            # admin credentials are hard-coded in the script, to be first in the list
            if secret_name == WEBLOGIC_CREDENTIALS_SECRET_NAME:
                continue

            secret_key = halves[1]
            if secret_name not in secret_map:
                secret_map[secret_name] = {}
            secret_keys = secret_map[secret_name]
            secret_keys[secret_key] = value

    secret_names = secret_map.keys()
    secret_names.sort()

    for secret_name in secret_names:
        secret_keys = secret_map[secret_name]
        user_name = dictionary_utils.get_element(secret_keys, SECRET_USERNAME_KEY)

        if user_name is None:
            message = exception_helper.get_message("WLSDPLY-01663", PASSWORD_TAG, secret_name)
            command_string = "create_k8s_secret %s %s " \
                             % (secret_name, PASSWORD_TAG)
        else:
            message = exception_helper.get_message("WLSDPLY-01664", USER_TAG, PASSWORD_TAG, secret_name)
            command_string = "create_paired_k8s_secret %s %s %s " \
                             % (secret_name, user_name, PASSWORD_TAG)

        k8s_script.write(nl)
        k8s_script.write("# " + message + nl)
        k8s_script.write(command_string + nl)

    k8s_script.close()
    FileUtils.chmod(k8s_file, 0750)


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


def create_additional_output(model, model_context, aliases, credential_injector, exception_type):
    """
    Create any additional output specified in the target configuration.
    :param model: used to create additional content
    :param model_context: provides access to the target configuration
    :param aliases: used for template fields
    :param credential_injector: used to identify secrets
    :param exception_type: type of exception to throw
    """
    _method_name = 'create_additional_output'

    additional_output_helper.create_additional_output(model, model_context, aliases, credential_injector,
                                                      exception_type)


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
