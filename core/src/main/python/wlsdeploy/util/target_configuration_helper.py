# Copyright (c) 2020, Oracle Corporation and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
# Shared methods for using target environments (-target abc).
# Used by discoverDomain and prepareModel.

import os

from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import NAME
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import k8s_helper
from wlsdeploy.tool.util.targets import vz_config_helper
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.cla_utils import CommandLineArgUtil

__class_name = 'target_configuration_helper'
__logger = PlatformLogger('wlsdeploy.tool.util')

# Kubernetes secret for admin name and password is <domainUid>-weblogic-credentials
WEBLOGIC_CREDENTIALS_SECRET_NAME = 'weblogic-credentials'
WEBLOGIC_CREDENTIALS_SECRET_SUFFIX = '-' + WEBLOGIC_CREDENTIALS_SECRET_NAME

VZ_EXTRA_CONFIG = 'vz'


def process_target_arguments(argument_map):
    """
    If the -target option is in the argument map, verify that -output_dir is specified.
    If variables_file was not specified, add it with the file <outputDir>/<targetName>_variable.properties .
    :param argument_map: the argument map to be checked and possibly modified
    """
    _method_name = '__process_target_arg'

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
    :return:
    """

    # determine the domain name and UID
    topology = dictionary_utils.get_dictionary_element(model_dictionary, TOPOLOGY)
    domain_name = dictionary_utils.get_element(topology, NAME)
    if domain_name is None:
        domain_name = DEFAULT_WLS_DOMAIN_NAME

    domain_uid = k8s_helper.get_domain_uid(domain_name)

    NL = '\n'
    file_location = model_context.get_kubernetes_output_dir()
    k8s_file = os.path.join(file_location, "create_k8s_secrets.sh")
    k8s_create_script_handle = open(k8s_file, 'w')

    k8s_create_script_handle.write('#!/bin/bash')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('set -eu')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('NAMESPACE=default')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('DOMAIN_UID=' + domain_uid)
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('ADMIN_USER=wlsAdminUser')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('ADMIN_PWD=wlsAdminPwd')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('function create_k8s_secret {')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('kubectl -n $NAMESPACE delete secret ${DOMAIN_UID}-$1 --ignore-not-found')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('kubectl -n $NAMESPACE create secret generic ${DOMAIN_UID}-$1 ' +
                                   '--from-literal=$2=$3')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('kubectl -n $NAMESPACE label secret ${DOMAIN_UID}-$1 ' +
                                   'weblogic.domainUID=${DOMAIN_UID}')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('}')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write(NL)

    admin_secret_name = '${DOMAIN_UID}' + WEBLOGIC_CREDENTIALS_SECRET_SUFFIX
    k8s_create_script_handle.write("kubectl -n $NAMESPACE delete secret " + admin_secret_name + " --ignore-not-found")
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write("kubectl -n $NAMESPACE create secret generic " + admin_secret_name +
                                   " --from-literal=username=${ADMIN_USER} --from-literal=password=${ADMIN_PWD}")
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write('kubectl -n $NAMESPACE label secret ' + admin_secret_name +
                                   ' weblogic.domainUID=${DOMAIN_UID}')
    k8s_create_script_handle.write(NL)
    k8s_create_script_handle.write(NL)

    for property_name in token_dictionary:
        # AdminPassword, AdminUser are created separately,
        # and SecurityConfig.NodeManagerPasswordEncrypted is the short name which filters out
        if property_name in ['AdminPassword', 'AdminUserName', 'SecurityConfig.NodeManagerPasswordEncrypted']:
            continue

        secret_names = property_name.lower().split('.')
        command_string = "create_k8s_secret %s %s %s " %( '-'.join(secret_names[:-1]), secret_names[-1],
                                                          "<changeme>")
        k8s_create_script_handle.write(command_string)
        k8s_create_script_handle.write(NL)

    k8s_create_script_handle.close()


def format_as_secret(variable_name):
    """
    Format the variable as a secret name
    :param variable_name: variable name in dot separated format
    :return: formatted name
    """
    name_lower_tokens = variable_name.lower().split('.')
    if len(name_lower_tokens) == 1:
        if name_lower_tokens[0] == 'adminusername' or 'adminpassword' == name_lower_tokens[0]:
            return get_secret_model_token(WEBLOGIC_CREDENTIALS_SECRET_NAME, name_lower_tokens[0])

    return get_secret_model_token('-'.join(name_lower_tokens[:-1]), name_lower_tokens[-1])


def get_secret_model_token(name, key):
    """
    Returns the substitution string to be put in the model for a secret value,
    in a consistent manner.
    :param name: the name of the secret
    :param key: the key of the secret
    :return: the substitution string
    """
    return '@@SECRET:@@ENV:DOMAIN_UID@@-%s:%s@@' % (name, key)

def create_additional_output(model, model_context, aliases, exception_type):
    """
    Create any additional output specified in the target configuration.
    :param model: used to create additional content
    :param model_context: provides access to the target configuration
    """
    _method_name = 'create_additional_output'

    output_types = _get_additional_output_types(model_context)
    for output_type in output_types:
        if output_type == VZ_EXTRA_CONFIG:
            vz_config_helper.create_vz_configuration(model, model_context, aliases, exception_type)
        else:
            __logger.warning('WLSDPLY-01660', output_type, model_context.get_target(), class_name=__class_name,
                             method_name=_method_name)


def _get_additional_output_types(model_context):
    """
    Returns a list of additional output types configured for the target environment.
    :param model_context: provides access to the target configuration
    :return: a list of additional output types
    """
    config = model_context.get_target_configuration()
    if config is not None:
        additional_output = dictionary_utils.get_element(config, "additional_output")
        if additional_output is not None:
            return additional_output.split(',')
    return {}
