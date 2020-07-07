# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Shared methods for using target environments (-target abc).
# Used by discoverDomain and prepareModel.
import re

import os

from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import PROPERTIES
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util import variable_injector_functions
from wlsdeploy.tool.util.targets import vz_config_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil

__class_name = 'target_configuration_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

# Kubernetes secret for admin name and password is <domainUid>-weblogic-credentials
WEBLOGIC_CREDENTIALS_SECRET_NAME = 'weblogic-credentials'
WEBLOGIC_CREDENTIALS_SECRET_SUFFIX = '-' + WEBLOGIC_CREDENTIALS_SECRET_NAME

VZ_EXTRA_CONFIG = 'vz'

ADMIN_USER_TAG = "<admin-user>"
ADMIN_PASSWORD_TAG = "<admin-password>"
USER_TAG = "<user>"
PASSWORD_TAG = "<password>"

# placeholders for config override secrets
ADMINUSER_PLACEHOLDER = "weblogic"
PASSWORD_PLACEHOLDER = "password1"

_jdbc_pattern = re.compile("^JDBC\\.([ \\w.-]+)\\.PasswordEncrypted$")


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
    target_config = model_context.get_target_configuration()
    if not target_config.requires_secrets_script():
        return

    # determine the domain name and UID
    topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
    domain_name = dictionary_utils.get_element(topology, NAME)
    if domain_name is None:
        domain_name = DEFAULT_WLS_DOMAIN_NAME

    domain_uid = k8s_helper.get_domain_uid(domain_name)

    nl = '\n'
    file_location = model_context.get_kubernetes_output_dir()
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

    for property_name in token_dictionary:
        # AdminPassword, AdminUser are created separately,
        # and SecurityConfig.NodeManagerPasswordEncrypted is the short name which filters out
        if property_name in ['AdminPassword', 'AdminUserName', 'SecurityConfig.NodeManagerPasswordEncrypted']:
            continue

        user_name = find_user_name(property_name, model_dictionary)
        secret_names = property_name.lower().split('.')
        secret_name = '-'.join(secret_names[:-1])

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


def format_as_secret_token(variable_name):
    """
    Format the variable as a secret name token for use in a model.
    :param variable_name: variable name in dot separated format
    :return: formatted name
    """
    name_lower_tokens = variable_name.lower().split('.')
    if len(name_lower_tokens) == 1:
        admin_lower_token = name_lower_tokens[0]
        if admin_lower_token in ['adminusername', 'adminpassword']:
            # these should just be 'username' and 'password', to match secrets script
            admin_token = admin_lower_token[5:]
            return get_secret_model_token(WEBLOGIC_CREDENTIALS_SECRET_NAME, admin_token)

    # for paired and single secrets, password key is always named "password"
    secret_name = "password"

    return get_secret_model_token('-'.join(name_lower_tokens[:-1]), secret_name)


def get_secret_model_token(name, key):
    """
    Returns the substitution string to be put in the model for a secret value.
    :param name: the name of the secret
    :param key: the key of the secret
    :return: the substitution string
    """
    return '@@SECRET:@@ENV:DOMAIN_UID@@-%s:%s@@' % (name, key)


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
    name_lower_tokens = variable_name.lower().split('.')
    return domain_uid + '-' + '-'.join(name_lower_tokens[:-1])


def create_additional_output(model, model_context, aliases, exception_type):
    """
    Create any additional output specified in the target configuration.
    :param model: used to create additional content
    :param model_context: provides access to the target configuration
    :param aliases: used for template fields
    :param exception_type: type of exception to throw
    """
    _method_name = 'create_additional_output'

    output_types = model_context.get_target_configuration().get_additional_output_types()
    for output_type in output_types:
        if output_type == VZ_EXTRA_CONFIG:
            vz_config_helper.create_vz_configuration(model, model_context, aliases, exception_type)
        else:
            __logger.warning('WLSDPLY-01660', output_type, model_context.get_target(), class_name=__class_name,
                             method_name=_method_name)


def find_user_name(property_name, model_dictionary):
    """
    Determine the user name associated with the specified property name.
    Return None if the property name is not part of a paired secret with .username and .password .
    Return <user> if the property name is paired, but user is not found.
    Currently only supports user for JDBC.[name].PasswordEncrypted
    Needs a much better implementation for future expansion.
    :param property_name: the property name, such as JDBC.Generic2.PasswordEncrypted
    :param model_dictionary: for looking up the user name
    :return: the matching user name, a substitution string, or None
    """
    matches = _jdbc_pattern.findall(property_name)
    if matches:
        name = matches[0]
        resources = dictionary_utils.get_dictionary_element(model_dictionary, RESOURCES)
        system_resources = dictionary_utils.get_dictionary_element(resources, JDBC_SYSTEM_RESOURCE)
        datasource = dictionary_utils.get_dictionary_element(system_resources, name)
        jdbc_resources = dictionary_utils.get_dictionary_element(datasource, JDBC_RESOURCE)
        driver_params = dictionary_utils.get_dictionary_element(jdbc_resources, JDBC_DRIVER_PARAMS)
        properties = dictionary_utils.get_dictionary_element(driver_params, PROPERTIES)
        user = dictionary_utils.get_dictionary_element(properties, "user")
        value = dictionary_utils.get_element(user, "Value")
        if value is None:
            return "<user>"
        else:
            return value

    return None


def _is_paired_secret(property_name):
    """
    Determine if the property name is part of a paired secret with .username and .password .
    Currently only supports user for JDBC.[name].PasswordEncrypted
    Needs a much better implementation for future expansion.
    :param property_name: the property name, such as JDBC.Generic2.PasswordEncrypted
    :return: True if the property is part of a paired secret
    """
    if _jdbc_pattern.findall(property_name):
        return True
    return False
