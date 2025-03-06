"""
Copyright (c) 2017, 2025, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the discoverDomain tool.
"""
import os, re
import sys

from java.io import File
from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException
from java.lang import String
from java.lang import System
from java.util import HashSet
from oracle.weblogic.deploy.aliases import AliasException
from oracle.weblogic.deploy.discover import DiscoverException
from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import PyOrderedDict
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.validate import ValidateException

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

from wlsdeploy.aliases import alias_constants
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.validation_codes import ValidationCodes
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.json import json_translator
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.discover import discoverer
from wlsdeploy.tool.discover.deployments_discoverer import DeploymentsDiscoverer
from wlsdeploy.tool.discover.domain_info_discoverer import DomainInfoDiscoverer
from wlsdeploy.tool.discover.multi_tenant_discoverer import MultiTenantDiscoverer
from wlsdeploy.tool.discover.opss_wallet_discoverer import OpssWalletDiscoverer
from wlsdeploy.tool.discover.resources_discoverer import ResourcesDiscoverer
from wlsdeploy.tool.discover.security_provider_data_discoverer import SecurityProviderDataDiscoverer
from wlsdeploy.tool.discover.topology_discoverer import TopologyDiscoverer
from wlsdeploy.tool.encrypt import encryption_utils
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util.credential_injector import CredentialInjector
from wlsdeploy.tool.util.variable_injector import VariableInjector
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import cla_helper
from wlsdeploy.util import cla_utils
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import env_helper
from wlsdeploy.util import getcreds
from wlsdeploy.util import model_translator
from wlsdeploy.util import path_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.cla_utils import TOOL_TYPE_DISCOVER
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model import Model
from wlsdeploy.util import target_configuration_helper
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_PROPERTY_VALUE
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
from wlsdeploy.aliases.model_constants import ORACLE_DATABASE_CONNECTION_TYPE
from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
from wlsdeploy.aliases.model_constants import PROPERTIES
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_DB_CONN_STRING
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RESOURCES
from wlsdeploy.aliases.model_constants import URL



wlst_helper.wlst_functions = globals()

_program_name = 'discoverDomain'
_class_name = 'discover'
__logger = PlatformLogger(discoverer.get_discover_logger_name())
__wlst_mode = WlstModes.OFFLINE

_store_result_environment_variable = '__WLSDEPLOY_STORE_RESULT__'

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.JAVA_HOME_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_URL_SWITCH,
    CommandLineArgUtil.ADMIN_USER_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_ENV_SWITCH,
    CommandLineArgUtil.TARGET_MODE_SWITCH,
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH,
    CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH,
    CommandLineArgUtil.DISCOVER_RCU_DATASOURCES_SWITCH,
    CommandLineArgUtil.DISCOVER_OPSS_WALLET_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.TARGET_SWITCH,
    CommandLineArgUtil.REMOTE_SWITCH,
    CommandLineArgUtil.SSH_HOST_SWITCH,
    CommandLineArgUtil.SSH_PORT_SWITCH,
    CommandLineArgUtil.SSH_USER_SWITCH,
    CommandLineArgUtil.SSH_PASS_SWITCH,
    CommandLineArgUtil.SSH_PASS_ENV_SWITCH,
    CommandLineArgUtil.SSH_PASS_FILE_SWITCH,
    CommandLineArgUtil.SSH_PASS_PROMPT_SWITCH,
    CommandLineArgUtil.SSH_PRIVATE_KEY_SWITCH,
    CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_SWITCH,
    CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH
]


def __process_args(args, is_encryption_supported):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :param is_encryption_supported: whether WDT encryption is supported by the JVM
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    argument_map = cla_util.process_args(args, TOOL_TYPE_DISCOVER)

    __wlst_mode = cla_helper.process_online_args(argument_map)
    cla_helper.validate_if_domain_home_required(_program_name, argument_map, __wlst_mode)
    cla_helper.validate_ssh_is_supported(_program_name, argument_map)
    if __wlst_mode == WlstModes.ONLINE:
        cla_helper.process_encryption_args(argument_map, is_encryption_supported)

    __validate_skip_archive_and_remote_args(argument_map, __wlst_mode)

    target_configuration_helper.process_target_arguments(argument_map)
    __process_model_arg(argument_map)
    __process_archive_filename_arg(argument_map)
    __process_variable_filename_arg(argument_map)
    __process_java_home(argument_map)
    __process_domain_home(argument_map, __wlst_mode)

    model_context = model_context_helper.create_context(_program_name, argument_map)
    __validate_discover_passwords_and_security_data_args(model_context, argument_map, is_encryption_supported)
    __validate_discover_opss_wallet_args(model_context, argument_map, is_encryption_supported)
    model_context.get_validate_configuration().set_disregard_version_invalid_elements(True)
    return model_context


def __validate_skip_archive_and_remote_args(argument_map, wlst_mode):
    _method_name = '__validate_skip_archive_and_remote_args'

    if wlst_mode == WlstModes.OFFLINE and CommandLineArgUtil.REMOTE_SWITCH in argument_map:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06064',
                                                   _program_name, CommandLineArgUtil.REMOTE_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    if CommandLineArgUtil.REMOTE_SWITCH in argument_map and CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH in argument_map:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06065',
                                                   _program_name, CommandLineArgUtil.REMOTE_SWITCH,
                                                   CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def __process_model_arg(argument_map):
    """
    Verify that specified model file's parent directory exists.
    :param argument_map: containing the CLA arguments
    """
    _method_name = '__process_model_arg'

    model_file_name = argument_map[CommandLineArgUtil.MODEL_FILE_SWITCH]
    path_helper_obj = path_helper.get_path_helper()
    model_dir_name = path_helper_obj.get_local_parent_directory(model_file_name)
    if os.path.exists(model_dir_name) is False:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                   'WLSDPLY-06037', model_file_name)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def __process_archive_filename_arg(argument_map):
    """
    Validate the archive file name and load the archive file object.
    :param argument_map: the optional arguments map
    :raises CLAException: if a validation error occurs while loading the archive file object
    """
    _method_name = '__process_archive_filename_arg'

    if CommandLineArgUtil.ARCHIVE_FILE_SWITCH not in argument_map:
        archive_file = None
        if CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH not in argument_map and \
                CommandLineArgUtil.REMOTE_SWITCH not in argument_map:
            ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-06028')
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH in argument_map or\
            CommandLineArgUtil.REMOTE_SWITCH in argument_map:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                   'WLSDPLY-06033')
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    else:
        archive_file_name = argument_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
        path_helper_obj = path_helper.get_path_helper()
        archive_dir_name = path_helper_obj.get_local_parent_directory(archive_file_name)
        if not os.path.exists(archive_dir_name):
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-06026', archive_file_name)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        # Delete any existing archive file for discoverDomain so that we always start with a fresh zip file.
        archive_file_obj = FileUtils.getCanonicalFile(archive_file_name)
        if archive_file_obj.exists() and not archive_file_obj.delete():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,'WLSDPLY-06047',
                                                       _program_name, archive_file_name)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        try:
            archive_file = WLSDeployArchive(archive_file_name)
        except (IllegalArgumentException, IllegalStateException), ie:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-06013', _program_name, archive_file_name,
                                                       ie.getLocalizedMessage(), error=ie)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        argument_map[CommandLineArgUtil.ARCHIVE_FILE] = archive_file


def __process_variable_filename_arg(optional_arg_map):
    """
    Validate the variable filename argument if present.
    :param optional_arg_map: containing the variable file name
    :raises: CLAException: if this argument is present but fails validation
    """
    _method_name = '__process_variable_filename_arg'

    if CommandLineArgUtil.VARIABLE_FILE_SWITCH in optional_arg_map:
        variable_file_name = optional_arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]
        path_helper_obj = path_helper.get_path_helper()
        variable_dir_name = path_helper_obj.get_local_parent_directory(variable_file_name)

        if not os.path.exists(variable_dir_name):
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-06048', variable_file_name)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        # Delete any existing variable file for discoverDomain so that we always start with a fresh file.
        variable_file_obj = FileUtils.getCanonicalFile(variable_file_name)
        if variable_file_obj.exists() and not variable_file_obj.delete():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,'WLSDPLY-06049',
                                                       _program_name, variable_file_name)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex


def __process_java_home(optional_arg_map):
    _method_name = '__process_java_home'
    if CommandLineArgUtil.JAVA_HOME_SWITCH in optional_arg_map:
        java_home_name = optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH]
    else:
        java_home_name = env_helper.getenv('JAVA_HOME')
        optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH] = java_home_name

    try:
        FileUtils.validateExistingDirectory(java_home_name)
    except IllegalArgumentException, iae:
        # this value is used for java home global token in attributes.
        # If this was passed as command line, it might no longer exist.
        # The JAVA_HOME environment variable was validated by script.
        __logger.info('WLSDPLY-06027', java_home_name, iae.getLocalizedMessage(),
                      class_name=_class_name, method_name=_method_name)


def __process_domain_home(arg_map, wlst_mode):
    if CommandLineArgUtil.DOMAIN_HOME_SWITCH not in arg_map:
        return
    domain_home = arg_map[CommandLineArgUtil.DOMAIN_HOME_SWITCH]
    perform_domain_home_validation = True
    if CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH in arg_map:
        # No need to validate the domain home in offline mode when the user specifies -skip_archive
        perform_domain_home_validation = False
    if wlst_mode == WlstModes.OFFLINE and perform_domain_home_validation:
        full_path = cla_utils.validate_domain_home_arg(domain_home)
        arg_map[CommandLineArgUtil.DOMAIN_HOME_SWITCH] = full_path


def __validate_discover_passwords_and_security_data_args(model_context, argument_map, is_encryption_supported):
    _method_name = '__validate_discover_passwords_and_security_data_args'
    if model_context.is_discover_passwords():
        # -remote cannot be supported because we need access to SSI.dat
        if model_context.is_remote():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06050',
                                                       _program_name, CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH,
                                                       CommandLineArgUtil.REMOTE_SWITCH)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif model_context.is_discover_security_provider_data():
        if model_context.get_target_wlst_mode() == WlstModes.OFFLINE:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06059',_program_name,
                                                       CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        # -remote cannot be supported because we need access to the exported data files and possibly SSI.dat.
        if model_context.is_remote():
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06058',_program_name,
                                                       CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH,
                                                       CommandLineArgUtil.REMOTE_SWITCH)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif model_context.is_discover_opss_wallet():
        # Allow the encryption passphrase
        pass
    elif model_context.is_discover_rcu_datasources():
        pass
    elif model_context.get_encryption_passphrase() is not None:
        # Don't allow the passphrase arg unless we are discovering passwords or security provider data.
        if CommandLineArgUtil.PASSPHRASE_ENV_SWITCH in argument_map:
            bad_arg = CommandLineArgUtil.PASSPHRASE_ENV_SWITCH
        elif CommandLineArgUtil.PASSPHRASE_FILE_SWITCH in argument_map:
            bad_arg = CommandLineArgUtil.PASSPHRASE_FILE_SWITCH
        elif CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH in argument_map:
            bad_arg = CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH
        else:
            bad_arg = CommandLineArgUtil.PASSPHRASE_SWITCH

        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06056',
                                                   _program_name, bad_arg,
                                                   CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH,
                                                   CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    # check if any argument requires password discovery
    passwords_argument = None
    if model_context.is_discover_passwords():
        passwords_argument = CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH
    elif model_context.is_discover_opss_wallet():
        passwords_argument = CommandLineArgUtil.DISCOVER_OPSS_WALLET_SWITCH
    elif model_context.is_discover_security_provider_passwords():
        passwords_argument = CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH + " " \
                             + model_context.get_discover_security_provider_data_types_label()

    if passwords_argument and model_context.is_encrypt_discovered_passwords():
        # To discover encrypted passwords, we always need the WDT encryption passphrase and JDK8 or above.
        if not is_encryption_supported:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06057',
                                                       _program_name, passwords_argument,
                                                       System.getProperty('java.version'))
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

        if model_context.get_encryption_passphrase() is None:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06051',
                                                       _program_name, passwords_argument,
                                                       CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
                                                       CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
                                                       CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    if passwords_argument:
        if not model_context.is_encrypt_discovered_passwords() and model_context.get_encryption_passphrase() is not None:
            # don't allow turning off encryption and supplying an encryption passphrase
            if CommandLineArgUtil.PASSPHRASE_ENV_SWITCH in argument_map:
                bad_arg = CommandLineArgUtil.PASSPHRASE_ENV_SWITCH
            elif CommandLineArgUtil.PASSPHRASE_FILE_SWITCH in argument_map:
                bad_arg = CommandLineArgUtil.PASSPHRASE_FILE_SWITCH
            elif CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH in argument_map:
                bad_arg = CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH
            else:
                bad_arg = CommandLineArgUtil.PASSPHRASE_SWITCH

            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-06052',
                                                       _program_name, passwords_argument, bad_arg)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex


def __validate_discover_opss_wallet_args(model_context, argument_map, is_encryption_supported):
    _method_name = '__validate_discover_opss_wallet_args'

    if CommandLineArgUtil.DISCOVER_OPSS_WALLET_SWITCH in argument_map:

        # Cannot verify that JRF is installed because the model_content is not fully
        # initialized at this point so the domain typedef is not available.
        if model_context.get_opss_wallet_passphrase() is None:
            try:
                passphrase_char_array = getcreds.getpass('WLSDPLY-06061')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,'WLSDPLY-06062',
                                                           ioe.getLocalizedMessage(), error=ioe)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

            if passphrase_char_array is not None:
                opss_wallet_passphrase = str_helper.to_string(String(passphrase_char_array))
                model_context.set_opss_wallet_passphrase(opss_wallet_passphrase)
            else:
                ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,'WLSDPLY-06063')
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

def __discover(model_context, aliases, credential_injector, helper, extra_tokens):
    """
    Populate the model from the domain.
    :param model_context: the model context
    :param aliases: aliases instance for discover
    :param credential_injector: credential injector instance
    :param helper: wlst_helper instance
    :param extra_tokens: dictionary to store non-credential tokens during credential search
    :return: the fully-populated model
    :raises DiscoverException: if an error occurred while discover the domain
    """
    _method_name = '__discover'
    model = Model()
    base_location = LocationContext()
    __connect_to_domain(model_context, helper)
    try:
        _add_domain_name(base_location, aliases, helper)
        _establish_production_mode(aliases, helper)
        _establish_secure_mode(aliases, base_location, helper, model_context)

        DomainInfoDiscoverer(model_context, model.get_model_domain_info(), base_location, wlst_mode=__wlst_mode,
                             aliases=aliases, credential_injector=credential_injector).discover()
        topology_discoverer = \
            TopologyDiscoverer(model_context, model.get_model_topology(), base_location, wlst_mode=__wlst_mode,
                               aliases=aliases, credential_injector=credential_injector)
        __, security_provider_map = topology_discoverer.discover()
        ResourcesDiscoverer(model_context, model.get_model_resources(), base_location, wlst_mode=__wlst_mode,
                            aliases=aliases, credential_injector=credential_injector).discover()
        DeploymentsDiscoverer(model_context, model.get_model_app_deployments(), base_location, wlst_mode=__wlst_mode,
                              aliases=aliases, credential_injector=credential_injector,
                              extra_tokens=extra_tokens).discover()
        SecurityProviderDataDiscoverer(model_context, model, base_location, wlst_mode=__wlst_mode, aliases=aliases,
                                       credential_injector=credential_injector).discover(security_provider_map)
        OpssWalletDiscoverer(model_context, model.get_model_domain_info(), base_location, wlst_mode=__wlst_mode,
                             aliases=aliases, credential_injector=credential_injector).discover()
        __discover_multi_tenant(model, model_context, base_location, aliases, credential_injector)
    except AliasException, ae:
        wls_version = model_context.get_effective_wls_version()
        wlst_mode = WlstModes.from_value(__wlst_mode)
        ex = exception_helper.create_discover_exception('WLSDPLY-06000', model_context.get_domain_name(),
                                                        model_context.get_domain_home(), wls_version, wlst_mode,
                                                        ae.getLocalizedMessage(), error=ae)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    __disconnect_domain(helper)

    return model


def _add_domain_name(location, aliases, helper):
    _method_name = '_get_domain_name'
    try:
        helper.cd('/')
        domain_name = helper.get(model_constants.DOMAIN_NAME)
    except PyWLSTException, pe:
        de = exception_helper.create_discover_exception('WLSDPLY-06020', pe.getLocalizedMessage())
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de
    if domain_name is not None:
        location.add_name_token(aliases.get_name_token(location), domain_name)
        __logger.info('WLSDPLY-06022', domain_name, class_name=_class_name, method_name=_method_name)
    else:
        de = exception_helper.create_discover_exception('WLSDPLY-06023')
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de


def _establish_production_mode(aliases, helper):
    """
    Determine if production mode is enabled for the domain, and set it in the aliases.
    :param aliases: aliases instance for discover
    :param helper: wlst_helper instance
    :raises DiscoverException: if an error occurs during discovery
    """
    _method_name = '_establish_production_mode'
    try:
        helper.cd('/')
        production_mode_enabled = helper.get(model_constants.PRODUCTION_MODE_ENABLED)
        aliases.set_production_mode(production_mode_enabled)
    except PyWLSTException, pe:
        de = exception_helper.create_discover_exception('WLSDPLY-06036', pe.getLocalizedMessage())
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de


def _establish_secure_mode(aliases, base_location, helper, model_context):
    """
    Determine if secure mode is enabled for the domain, and set it in the aliases.
    :param aliases: aliases instance for discover
    :param base_location: location of root directory in WLST
    :param helper: wlst_helper instance
    :param model_context: used to check dependency
    :raises DiscoverException: if an error occurs during discovery
    """
    _method_name = '_establish_secure_mode'
    try:
        if model_context.get_weblogic_helper().is_secure_mode_implied_by_production_mode():
            # for 14.1.2, secure mode defaults to true if production mode is true.
            # this may be overridden by the value of SecurityConfiguration/SecureMode/SecureModeEnabled.
            helper.cd('/')
            secure_mode_enabled = helper.get(model_constants.PRODUCTION_MODE_ENABLED)
        else:
            secure_mode_enabled = False

        secure_mode_location = LocationContext(base_location)
        secure_mode_location.append_location(model_constants.SECURITY_CONFIGURATION)

        code, message = aliases.is_valid_model_folder_name(secure_mode_location, model_constants.SECURE_MODE)
        if code == ValidationCodes.VALID:
            security_config_path = aliases.get_wlst_list_path(secure_mode_location)
            security_config_token = helper.get_singleton_name(security_config_path)
            secure_mode_location.add_name_token(aliases.get_name_token(secure_mode_location), security_config_token)

            secure_mode_location.append_location(model_constants.SECURE_MODE)
            secure_mode_path = aliases.get_wlst_list_path(secure_mode_location)
            secure_mode_token = helper.get_singleton_name(secure_mode_path)
            if secure_mode_token is not None:
                secure_mode_location.add_name_token(aliases.get_name_token(secure_mode_location), secure_mode_token)
                helper.cd(aliases.get_wlst_attributes_path(secure_mode_location))
                secure_mode_enabled = helper.get(model_constants.SECURE_MODE_ENABLED)

        aliases.set_secure_mode(secure_mode_enabled)
        helper.cd(aliases.get_wlst_attributes_path(base_location))

    except PyWLSTException, pe:
        de = exception_helper.create_discover_exception('WLSDPLY-06038', pe.getLocalizedMessage())
        __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
        raise de


def __discover_multi_tenant(model, model_context, base_location, aliases, injector):
    """
    Discover the multi-tenant-related parts of the domain, if they exist.
    :param model: the model object to populate
    :param model_context: the model context object
    :raises DiscoverException: if an error occurs during discovery
    """
    MultiTenantDiscoverer(model, model_context, base_location,
                          wlst_mode=__wlst_mode, aliases=aliases, credential_injector=injector).discover()


def __connect_to_domain(model_context, helper):
    """
    Connects WLST to the domain by either connecting to the Admin Server or reading the domain from disk.
    :param model_context: the model context
    :param helper: wlst helper instance
    :raises DiscoverException: if a WLST error occurs while connecting to or reading the domain
    """
    _method_name = '__connect_to_domain'

    __logger.entering(class_name=_class_name, method_name=_method_name)
    if __wlst_mode == WlstModes.ONLINE:
        try:
            helper.connect(model_context.get_admin_user(), model_context.get_admin_password(),
                           model_context.get_admin_url(), model_context.get_model_config().get_connect_timeout())

            # All online operations do not have domain home set, so get it from online wlst after connect
            model_context.set_domain_home_name_if_online(helper.get_domain_home_online(),
                                                         helper.get_domain_name_online())

        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06001', model_context.get_admin_url(),
                                                            model_context.get_admin_user(),
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            helper.read_domain(model_context.get_domain_home())
        except PyWLSTException, wlst_ex:
            wls_version = model_context.get_effective_wls_version()
            ex = exception_helper.create_discover_exception('WLSDPLY-06002', model_context.get_domain_home(),
                                                            wls_version, wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def __clear_archive_file(model_context):
    """
    Remove any binaries already in the archive file.
    :param model_context: the model context
    :raises DiscoverException: if an error occurs while removing the binaries
    """
    _method_name = '__clear_archive_file'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    archive_file = model_context.get_archive_file()

    if not model_context.is_skip_archive() and not model_context.is_remote():
        if archive_file is not None:
            try:
                archive_file.removeAllBinaries()
            except WLSDeployArchiveIOException, wioe:
                de = exception_helper.create_discover_exception('WLSDPLY-06005', wioe.getLocalizedMessage())
                __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
                raise de
        else:
            de = exception_helper.create_discover_exception('WLSDPLY-06004', model_context.get_archive_file_name())
            __logger.throwing(class_name=_class_name, method_name=_method_name, error=de)
            raise de

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def __close_archive(model_context):
    """
    Close the archive object
    :param model_context: the model context
    """
    _method_name = '__close_archive'

    __logger.entering(_class_name=_class_name, method_name=_method_name)
    archive_file = model_context.get_archive_file()
    if archive_file is not None:
        archive_file.close()
    __logger.exiting(class_name=_class_name, method_name=_method_name)


def __disconnect_domain(helper):
    """
    Disconnects WLST from the domain by either disconnecting from the Admin Server or closing the domain read from disk.
    :param helper: wlst_helper instance
    :raises DiscoverException: if a WLST error occurred while disconnecting or closing the domain
    """
    _method_name = '__disconnect_domain'

    __logger.entering(class_name=_class_name, method_name=_method_name)

    if __wlst_mode == WlstModes.ONLINE:
        try:
            # Force disconnect in case the domain is in dev mode and the user
            # has opened the Console, which automatically acquires an edit lock.
            helper.disconnect('true')
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06006',
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            helper.close_domain()
        except PyWLSTException, wlst_ex:
            ex = exception_helper.create_discover_exception('WLSDPLY-06007',
                                                            wlst_ex.getLocalizedMessage(), error=wlst_ex)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def __persist_model(model, model_context):
    """
    Save the model to the specified model file name.
    :param model: the model to save
    :param model_context: the model context
    :raises DiscoverException: if an error occurs while create a temporary file for the model
                               or while adding it to the archive
    :raises TranslateException: if an error occurs while serializing the model or writing it to disk
    """
    _method_name = '__persist_model'

    __logger.entering(class_name=_class_name, method_name=_method_name)

    global __wlst_mode

    # add model comments to dictionary extracted from the Model object
    model_dict = model.get_model()
    message_1 = exception_helper.get_message('WLSDPLY-06039', WebLogicDeployToolingVersion.getVersion(), _program_name)
    model_dict.addComment(DOMAIN_INFO, message_1)
    if __wlst_mode == WlstModes.ONLINE:
        remote_wls_version = model_context.get_remote_wls_version()
        if remote_wls_version is None:
            remote_wls_version = 'UNKNOWN'

        message_2 = exception_helper.get_message('WLSDPLY-06043', model_context.get_local_wls_version(),
                                                 WlstModes.from_value(__wlst_mode), remote_wls_version)
    else:
        message_2 = exception_helper.get_message('WLSDPLY-06040', WlstModes.from_value(__wlst_mode),
                                                 model_context.get_local_wls_version())
    model_dict.addComment(DOMAIN_INFO, message_2)
    model_dict.addComment(DOMAIN_INFO, '')

    model_file_name = model_context.get_model_file()
    model_file = FileUtils.getCanonicalFile(File(model_file_name))
    model_translator.PythonToFile(model_dict).write_to_file(model_file.getAbsolutePath())

    __logger.exiting(class_name=_class_name, method_name=_method_name)


def __check_and_customize_model(model, model_context, aliases, credential_injector, extra_tokens):
    """
    Customize the model dictionary before persisting. Validate the model after customization for informational
    purposes. Any validation errors will not stop the discovered model to be persisted.
    :param model: completely discovered model, before any tokenization
    :param model_context: configuration from command-line
    :param aliases: used for validation if model changes are made
    :param credential_injector: injector created to collect and tokenize credentials, possibly None
    :param extra_tokens: dictionary to handle non-credential tokenized arguments
    """
    _method_name = '__check_and_customize_model'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    if filter_helper.apply_filters(model.get_model(), "discover", model_context):
        __logger.info('WLSDPLY-06014', _class_name=_class_name, method_name=_method_name)

    filter_helper.apply_final_filters(model.get_model(), model.get_model(), model_context)
    rcu_credential_cache = __fix_discovered_template_datasource(model, model_context)

    credential_cache = None
    if credential_injector is not None:
        # filter variables or secrets that are no longer in the model
        credential_injector.filter_unused_credentials(model.get_model())

        credential_cache = credential_injector.get_variable_cache()
        if credential_cache is not None:
            for item in rcu_credential_cache:
                credential_cache[item] = rcu_credential_cache[item]

        target_configuration_helper.generate_all_output_files(model, aliases, credential_injector, model_context,
                                                              ExceptionType.DISCOVER)

        # if target handles credential configuration, clear property cache to keep out of variables file.
        if model_context.get_target_configuration().manages_credentials():
            credential_cache.clear()

    # Apply the injectors specified in model_variable_injector.json, or in the target configuration.
    # Include the variable mappings that were collected in credential_cache.

    variable_injector = VariableInjector(_program_name, model_context, aliases, variable_dictionary=credential_cache)

    variable_injector.add_to_cache(dictionary=extra_tokens)

    inserted, variable_model, variable_file_name = variable_injector.inject_variables_from_configuration(model.get_model())

    if inserted:
        model = Model(variable_model)
    try:
        validator = Validator(model_context, aliases, wlst_mode=__wlst_mode)

        # no variables are generated by the discover tool
        validator.validate_in_tool_mode(model.get_model(), variables_file_name=variable_file_name,
                                        archive_file_name=model_context.get_archive_file_name())
    except ValidateException, ex:
        __logger.warning('WLSDPLY-06015', ex.getLocalizedMessage(), class_name=_class_name, method_name=_method_name)
    __logger.exiting(_class_name, _method_name)
    return model

def __fix_discovered_template_datasource(model, model_context):
    # fix the case for discovering template datasources.
    # If all the template datasources use the dame passwords then generate the RUCDbInfo section
    # and remove the template datasources from the model
    # If not using the same passwords then do not generate RCUDbinfo,  need to go back to fix the password field value

    _method_name = '__fix_discovered_template_datasource'
    __logger.entering(class_name=_class_name, method_name=_method_name)
    credential_cache = None
    if model_context.get_variable_file() is not None:
        credential_cache = PyOrderedDict()

    domain_typedef = model_context.get_domain_typedef()
    if domain_typedef.requires_rcu() and model_context.is_discover_rcu_datasources():
        resources = model.get_model_resources()
        jdbc_system_resources = dictionary_utils.get_element(resources, JDBC_SYSTEM_RESOURCE)
        discover_filters = domain_typedef._discover_filters
        filtered_ds_patterns = dictionary_utils.get_element(discover_filters,'/JDBCSystemResource')
        passwords = HashSet()
        urls = HashSet()
        prefixes = HashSet()
        properties = __get_urls_and_passwords(model_context, jdbc_system_resources, filtered_ds_patterns,
                                                                       urls, passwords, prefixes)
        if _can_generate_rcudb_info(passwords, urls, prefixes):
            __set_rcuinfo_in_model(model, properties,  urls[0], passwords[0])
            __remove_discovered_template_datasource(jdbc_system_resources, filtered_ds_patterns, model)
            credential_cache = __fix_rcudbinfo_passwords(model, model_context,
                                                         credential_cache, model_context.is_discover_passwords())
        else:
            credential_cache =  __reset_password_to_regular_discovery(jdbc_system_resources,
                                                        filtered_ds_patterns, model_context,
                                                  credential_cache)

    __logger.exiting(_class_name, _method_name)
    return credential_cache

def _can_generate_rcudb_info(passwords, urls, prefixes):
    return passwords.size() == 1 and urls.size() == 1 and prefixes.size() == 1

def __get_urls_and_passwords(model_context, jdbc_system_resources, filtered_ds_patterns, urls, passwords, prefixes):
    properties = None
    for item in jdbc_system_resources:
        if not __match_filtered_ds_name(item, filtered_ds_patterns):
            continue
        jdbc_system_resource = jdbc_system_resources[item]
        jdbc_resource = dictionary_utils.get_element(jdbc_system_resource, JDBC_RESOURCE)
        driver_params = dictionary_utils.get_element(jdbc_resource, JDBC_DRIVER_PARAMS)
        properties = dictionary_utils.get_element(driver_params, PROPERTIES)
        password_encrypted = dictionary_utils.get_element(driver_params, PASSWORD_ENCRYPTED)
        passwords.add(password_encrypted)
        schema_user = __get_driver_param_property_value(properties, DRIVER_PARAMS_USER_PROPERTY)
        prefix = schema_user[0:schema_user.find('_')]
        prefixes.add(prefix)
        url = dictionary_utils.get_element(driver_params, URL)
        urls.add(url)

    return properties

def __set_rcuinfo_in_model(model, properties, url, password_encrypted):
    model_dict = model.get_model()
    domain_info = dictionary_utils.get_element(model_dict, DOMAIN_INFO)
    if domain_info is None:
        model_dict[DOMAIN_INFO] = {}
        domain_info = model_dict[DOMAIN_INFO]

    schema_user = __get_driver_param_property_value(properties, DRIVER_PARAMS_USER_PROPERTY)

    domain_info[RCU_DB_INFO] = {}
    rcudb_info = domain_info[RCU_DB_INFO]
    rcudb_info[RCU_DB_CONN_STRING] = url

    rcudb_info[RCU_SCHEMA_PASSWORD] = password_encrypted
    prefix = schema_user[0:schema_user.find('_')]
    rcudb_info[RCU_PREFIX] = prefix

    extra_properties = [DRIVER_PARAMS_TRUSTSTORE_PROPERTY,
                        DRIVER_PARAMS_KEYSTORE_PROPERTY,
                        DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY,
                        DRIVER_PARAMS_KEYSTORETYPE_PROPERTY,
                        DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY,
                        DRIVER_PARAMS_KEYSTOREPWD_PROPERTY,
                        DRIVER_PARAMS_NET_TNS_ADMIN
                        ]

    for property in extra_properties:
        __set_rcu_property_ifnecessary(rcudb_info, properties, property)


    # The ORACLE_DATABASE_CONNECTION_TYPE is only used by WDT for processing
    atp_tns_alias = __find_atp_tns_alias(url)
    if atp_tns_alias is not None:
        # This is just based on the observed pattern in tnsnames.ora file for ATP.
        # we don't set the actual tns.alias since the url format is subjected to change
        rcudb_info[ORACLE_DATABASE_CONNECTION_TYPE] = 'ATP'
    elif __test_if_ssl_properties_are_set(properties):
        rcudb_info[ORACLE_DATABASE_CONNECTION_TYPE] = 'SSL'

def __test_if_ssl_properties_are_set(properties):
    keystore_property = __get_driver_param_property_value(properties, DRIVER_PARAMS_KEYSTORE_PROPERTY)
    truststore_property = __get_driver_param_property_value(properties, DRIVER_PARAMS_TRUSTSTORE_PROPERTY)
    if keystore_property is not None and truststore_property is not None:
        return True
    return False

def __find_atp_tns_alias(url):
    pattern = r'\(service_name=([a-zA-Z0-9]+)_([a-zA-Z0-9_]+)\.adb\.oraclecloud\.com\)'
    match = re.search(pattern, url)
    if match:
        return match.group(2)
    else:
        return None

def __set_rcu_property_ifnecessary(rcu_db_info, properties, name):
    value = __get_driver_param_property_value(properties, name)
    if value is not None:
        rcu_db_info[name] = value

def __get_driver_param_property_value(properties, name):
    try:
        prop = dictionary_utils.get_element(properties, name)
        value = dictionary_utils.get_element(prop, DRIVER_PARAMS_PROPERTY_VALUE)
        return value
    except:
        return None

def __remove_discovered_template_datasource(jdbc_system_resources, filtered_ds_patterns, model):
    remove_items = []
    for item in jdbc_system_resources:
        if not __match_filtered_ds_name(item, filtered_ds_patterns):
            continue
        remove_items.append(item)

    for item in remove_items:
        del jdbc_system_resources[item]

    if len(jdbc_system_resources) == 0:
        model_dict = model.get_model()
        resources = model_dict[RESOURCES]
        del resources[JDBC_SYSTEM_RESOURCE]
        if len(resources) == 0:
            del model_dict[RESOURCES]

def __reset_password_to_regular_discovery(jdbc_system_resources, filtered_ds_patterns, model_context, credential_cache):
    for item in jdbc_system_resources:
        if not __match_filtered_ds_name(item, filtered_ds_patterns):
            continue
        jdbc_system_resource = jdbc_system_resources[item]
        jdbc_resource = dictionary_utils.get_element(jdbc_system_resource, JDBC_RESOURCE)
        driver_params = dictionary_utils.get_element(jdbc_resource, JDBC_DRIVER_PARAMS)
        jdbc_ds_password = driver_params[PASSWORD_ENCRYPTED]
        if model_context.is_discover_passwords():
            encrypted_model_value = encryption_utils.encrypt_one_password(
                model_context.get_encryption_passphrase(), jdbc_ds_password)
            if credential_cache is not None:
                name = 'JDBC.' + item + '.PasswordEncrypted'
                credential_cache[name] = encrypted_model_value
                encrypted_model_value = '@@PROP:' + name + '@@'
            driver_params[PASSWORD_ENCRYPTED] = encrypted_model_value
        else:
            if credential_cache is not None:
                name = 'JDBC.' + item + '.PasswordEncrypted'
                credential_cache[name] = ''
                model_value = '@@PROP:' + name + '@@'
                driver_params[PASSWORD_ENCRYPTED] = model_value
            else:
                driver_params[PASSWORD_ENCRYPTED] = alias_constants.PASSWORD_TOKEN

    return credential_cache

def __fix_rcudbinfo_passwords(model, model_context, credential_cache, encrypt=False):

    model_dict = model.get_model()
    rcudb_info = model_dict[DOMAIN_INFO][RCU_DB_INFO]

    possible_pwds = [
        RCU_SCHEMA_PASSWORD,
        DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY,
        DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
    ]

    for item in possible_pwds:
        if item in rcudb_info:
            if encrypt:
                passwd = rcudb_info[item]
                model_value = encryption_utils.encrypt_one_password(
                    model_context.get_encryption_passphrase(), passwd)
                if credential_cache is not None:
                    name = 'RCUDbInfo.' + item
                    credential_cache[name] = model_value
                    model_value = '@@PROP:' + name + '@@'
                rcudb_info[item] = model_value
            else:
                if credential_cache is not None:
                    name = 'RCUDbInfo.' + item
                    credential_cache[name] = ''
                    model_value = '@@PROP:' + name + '@@'
                    rcudb_info[item] = model_value
                else:
                    rcudb_info[item] = alias_constants.PASSWORD_TOKEN

    return credential_cache

def __match_filtered_ds_name(name, patterns):
    for pattern in patterns:
        regex = re.compile(pattern)
        if regex.match(name):
            return True
    return False

def __generate_remote_report_json(model_context):
    _method_name = '__remote_report'

    if not model_context.is_remote() or not env_helper.has_env(_store_result_environment_variable):
        return

    # write JSON output if the __WLSDEPLOY_STORE_RESULT__ environment variable is set.
    # write to the file before the stdout so any logging messages come first.
    remote_map = discoverer.remote_dict

    store_path = env_helper.getenv(_store_result_environment_variable)
    __logger.info('WLSDPLY-06034', store_path, class_name=_class_name, method_name=_method_name)
    missing_archive_entries = []
    for key in remote_map:
        archive_map = remote_map[key]
        missing_archive_entries.append({
            'sourceFile': key,
            'path': archive_map[discoverer.REMOTE_ARCHIVE_PATH],
            'type': archive_map[discoverer.REMOTE_TYPE]
        })
    result_root = PyOrderedDict()
    result_root['missingArchiveEntries'] = missing_archive_entries
    try:
        json_translator.PythonToJson(result_root).write_to_json_file(store_path)
    except JsonException, ex:
        __logger.warning('WLSDPLY-06035', _store_result_environment_variable, ex.getLocalizedMessage(),
                         class_name=_class_name, method_name=_method_name)


def main(model_context):
    """
    The main entry point for the discoverDomain tool.

    :param model_context: the model context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    helper = WlstHelper(ExceptionType.DISCOVER)
    helper.silence()

    _exit_code = ExitCode.OK

    try:
        __clear_archive_file(model_context)
    except DiscoverException, ex:
        __logger.severe('WLSDPLY-06010', _program_name, model_context.get_archive_file_name(),
                        ex.getLocalizedMessage(), error=ex, class_name=_class_name, method_name=_method_name)
        _exit_code = ExitCode.ERROR

    model = None
    if _exit_code == ExitCode.OK:
        aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.DISCOVER)
        credential_injector = None

        if model_context.get_variable_file() is not None or model_context.get_target() is not None:
            credential_injector = CredentialInjector(_program_name, model_context, aliases)
            if model_context.is_discover_passwords():
                password_key = 'WLSDPLY-06055'
            else:
                password_key = 'WLSDPLY-06025'
        else:
            if model_context.is_discover_passwords():
                password_key = 'WLSDPLY-06054'
            else:
                password_key = 'WLSDPLY-06024'
        __logger.info(password_key, class_name=_class_name, method_name=_method_name)

        extra_tokens = {}
        try:
            model = __discover(model_context, aliases, credential_injector, helper, extra_tokens)
            model = __check_and_customize_model(model, model_context, aliases, credential_injector, extra_tokens)

            __generate_remote_report_json(model_context)
        except DiscoverException, ex:
            __logger.severe('WLSDPLY-06011', _program_name, model_context.get_domain_name(),
                            model_context.get_domain_home(), ex.getLocalizedMessage(),
                            error=ex, class_name=_class_name, method_name=_method_name)
            _exit_code = ExitCode.ERROR

    if _exit_code == ExitCode.OK:
        try:
            __persist_model(model, model_context)

        except TranslateException, ex:
            __logger.severe('WLSDPLY-20024', _program_name, model_context.get_archive_file_name(), ex.getLocalizedMessage(),
                            error=ex, class_name=_class_name, method_name=_method_name)
            _exit_code = ExitCode.ERROR

    __close_archive(model_context)
    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
