"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The main module for the WLSDeploy tool to create empty domains.
"""
import os
import sys

from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import String
from java.lang import System
from oracle.weblogic.deploy.create import CreateException
from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.model_constants import DEFAULT_WLS_DOMAIN_NAME
from wlsdeploy.aliases.model_constants import DOMAIN_NAME
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.rcudbinfo_helper import RcuDbInfo
from wlsdeploy.tool.create.domain_creator import DomainCreator
from wlsdeploy.tool.create.domain_typedef import CREATE_DOMAIN
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util.archive_helper import ArchiveHelper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import getcreds
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.cla_utils import TOOL_TYPE_CREATE
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.tool.create import atp_helper
from wlsdeploy.tool.create import ssl_helper

wlst_helper.wlst_functions = globals()

_program_name = CREATE_DOMAIN

_class_name = 'create'
__logger = PlatformLogger('wlsdeploy.create')
__wlst_mode = WlstModes.OFFLINE
__version = WebLogicHelper(__logger).get_actual_weblogic_version()

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.JAVA_HOME_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.RUN_RCU_SWITCH,
    CommandLineArgUtil.RCU_SYS_PASS_SWITCH,
    CommandLineArgUtil.RCU_DB_SWITCH,
    CommandLineArgUtil.RCU_DB_USER_SWITCH,
    CommandLineArgUtil.RCU_PREFIX_SWITCH,
    CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_SWITCH,
    CommandLineArgUtil.OPSS_WALLET_PASSPHRASE,
    CommandLineArgUtil.OPSS_WALLET_FILE_PASSPHRASE,
    CommandLineArgUtil.OPSS_WALLET_ENV_PASSPHRASE,
    CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args, TOOL_TYPE_CREATE)
    __process_java_home_arg(argument_map)
    __process_domain_location_args(argument_map)

    # don't verify that the archive is valid until it is needed.
    # this requirement is specific to create, other tools will verify it.
    cla_helper.validate_model_present(_program_name, argument_map)
    cla_helper.validate_variable_file_exists(_program_name, argument_map)

    #
    # Verify that the domain type is a known type and load its typedef.
    #
    domain_typedef = model_context_helper.create_typedef(_program_name, argument_map)

    __process_rcu_args(argument_map, domain_typedef.get_domain_type(), domain_typedef)
    cla_helper.process_encryption_args(argument_map)
    __process_opss_args(argument_map)

    return model_context_helper.create_context(_program_name, argument_map, domain_typedef)


def __process_java_home_arg(optional_arg_map):
    """
    Verify that java_home is set.  If not, set it.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the java home argument is not valid
    """
    _method_name = '__process_java_home_arg'

    if CommandLineArgUtil.JAVA_HOME_SWITCH not in optional_arg_map:
        java_home_name = os.environ.get('JAVA_HOME')
        try:
            java_home = FileUtils.validateExistingDirectory(java_home_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-12400', _program_name, java_home_name,
                                                       iae.getLocalizedMessage(), error=iae)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH] = java_home.getAbsolutePath()


def __process_domain_location_args(optional_arg_map):
    """
    Verify that either the domain_home or domain_parent was specified, and not both.
    Their values were already checked in the process_args call.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are invalid or an error occurs extracting the model from the archive
    """
    _method_name = '__process_domain_location_args'

    has_home = CommandLineArgUtil.DOMAIN_HOME_SWITCH in optional_arg_map
    has_parent = CommandLineArgUtil.DOMAIN_PARENT_SWITCH in optional_arg_map

    if (has_home and has_parent) or (not has_home and not has_parent):
        ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
                                                   'WLSDPLY-20025', _program_name,
                                                   CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
                                                   CommandLineArgUtil.DOMAIN_HOME_SWITCH)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def __process_rcu_args(optional_arg_map, domain_type, domain_typedef):
    """
    Determine if the RCU is needed and validate/prompt for any missing information
    :param optional_arg_map: the optional arguments map
    :param domain_type:      the domain type
    :param domain_typedef:   the domain_typedef data structure
    :raises CLAException:    if an error occurs getting the passwords from the user or arguments are missing
    """
    _method_name = '__process_rcu_args'

    rcu_schema_count = len(domain_typedef.get_rcu_schemas())
    run_rcu = False
    if CommandLineArgUtil.RUN_RCU_SWITCH in optional_arg_map:
        run_rcu = optional_arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]
        if rcu_schema_count == 0:
            __logger.info('WLSDPLY-12402', _program_name, CommandLineArgUtil.RUN_RCU_SWITCH, domain_type)
            del optional_arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]
            return

    if rcu_schema_count > 0:
        if CommandLineArgUtil.RCU_DB_SWITCH in optional_arg_map:
            if CommandLineArgUtil.RCU_PREFIX_SWITCH in optional_arg_map:
                if run_rcu and CommandLineArgUtil.RCU_SYS_PASS_SWITCH not in optional_arg_map:
                    try:
                        password = getcreds.getpass('WLSDPLY-12403')
                    except IOException, ioe:
                        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                                   'WLSDPLY-12404', ioe.getLocalizedMessage(),
                                                                   error=ioe)
                        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex
                    optional_arg_map[CommandLineArgUtil.RCU_SYS_PASS_SWITCH] = String(password)
                if CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH not in optional_arg_map:
                    try:
                        password = getcreds.getpass('WLSDPLY-12405')
                    except IOException, ioe:
                        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                                   'WLSDPLY-12406', ioe.getLocalizedMessage(),
                                                                   error=ioe)
                        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex
                    optional_arg_map[CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH] = String(password)
            else:
                ex = exception_helper.create_cla_exception(ExitCode.USAGE_ERROR,
                                                           'WLSDPLY-12407', _program_name,
                                                           CommandLineArgUtil.RCU_DB_SWITCH,
                                                           CommandLineArgUtil.RCU_PREFIX_SWITCH)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

        # Delay the checking later for rcu related parameters


def __process_opss_args(optional_arg_map):
    """
    Determine if the user is using opss wallet and if so, get the passphrase.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if getting the passphrase from the user fails
    """
    _method_name = '__process_opss_args'

    if CommandLineArgUtil.OPSS_WALLET_SWITCH in optional_arg_map and \
            CommandLineArgUtil.OPSS_WALLET_PASSPHRASE not in optional_arg_map:
        try:
            passphrase = getcreds.getpass('WLSDPLY-20027')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                                       'WLSDPLY-20028', ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.OPSS_WALLET_PASSPHRASE] = String(passphrase)


def validate_rcu_args_and_model(model_context, model, archive_helper, aliases):
    _method_name = 'validate_rcu_args_and_model'

    has_atpdbinfo = 0
    has_ssldbinfo = 0

    if model_constants.DOMAIN_INFO in model and model_constants.RCU_DB_INFO in model[model_constants.DOMAIN_INFO]:
        rcu_db_info = RcuDbInfo(model_context, aliases, model[model_constants.DOMAIN_INFO][model_constants.RCU_DB_INFO])
        has_tns_admin = rcu_db_info.has_tns_admin()
        is_regular_db = rcu_db_info.is_regular_db()
        has_atpdbinfo = rcu_db_info.has_atpdbinfo()
        has_ssldbinfo = rcu_db_info.has_ssldbinfo()

        _validate_atp_wallet_in_archive(archive_helper, is_regular_db, has_tns_admin, model,
                                        model_context)
    else:
        if model_context.get_domain_typedef().required_rcu():
            if not model_context.get_rcu_database() or not model_context.get_rcu_prefix():
                __logger.severe('WLSDPLY-12408', model_context.get_domain_type(), CommandLineArgUtil.RCU_DB_SWITCH,
                                CommandLineArgUtil.RCU_PREFIX_SWITCH, class_name=_class_name, method_name=_method_name)
                ex = exception_helper.create_create_exception('WLSDPLY-12408', model_context.get_domain_type(),
                                                              CommandLineArgUtil.RCU_DB_SWITCH,
                                                              CommandLineArgUtil.RCU_PREFIX_SWITCH)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

    return has_atpdbinfo, has_ssldbinfo


def _validate_atp_wallet_in_archive(archive_helper, is_regular_db, has_tns_admin, model, model_context):
    _method_name = '_validate_atp_wallet_in_archive'
    if archive_helper and not is_regular_db:
        # 1. If it does not have the oracle.net.tns_admin specified, then extract to domain/atpwallet
        # 2. If it is plain old regular oracle db, do nothing
        # 3. If it deos not have tns_admin in the model, then the wallet must be in the archive
        if not has_tns_admin:
            wallet_path = archive_helper.extract_atp_wallet()
            if wallet_path:
                # update the model to add the tns_admin
                model[model_constants.DOMAIN_INFO][model_constants.RCU_DB_INFO][
                    model_constants.DRIVER_PARAMS_NET_TNS_ADMIN] = wallet_path
            else:
                __logger.severe('WLSDPLY-12411', class_name=_class_name, method_name=_method_name)
                ex = exception_helper.create_create_exception('WLSDPLY-12411')
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

    if not is_regular_db:
        System.setProperty('oracle.jdbc.fanEnabled', 'false')


def _get_domain_path(model_context, model):
    """
    Returns the domain home path.
    :param model_context: the model context
    :param model: the model
    :return: the domain path
    """
    domain_parent = model_context.get_domain_parent_dir()
    if domain_parent is None:
        return model_context.get_domain_home()
    elif TOPOLOGY in model and DOMAIN_NAME in model[TOPOLOGY]:
        return domain_parent + os.sep + model[TOPOLOGY][DOMAIN_NAME]
    else:
        return domain_parent + os.sep + DEFAULT_WLS_DOMAIN_NAME


def main(model_context):
    """
    The entry point for the createDomain tool.

    :param model_context: The model_context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    WlstHelper(ExceptionType.CREATE).silence()
    _exit_code = ExitCode.OK

    try:
        aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.CREATE)
        model_dictionary = cla_helper.load_model(_program_name, model_context, aliases, "create", __wlst_mode,
                                                 validate_crd_sections=False)

        archive_helper = None
        archive_file_name = model_context.get_archive_file_name()
        if archive_file_name:
            domain_path = _get_domain_path(model_context, model_dictionary)
            archive_helper = ArchiveHelper(archive_file_name, domain_path, __logger, ExceptionType.CREATE)

        has_atp, has_ssl = validate_rcu_args_and_model(model_context, model_dictionary, archive_helper, aliases)
        # check if there is an atpwallet and extract in the domain dir
        # it is to support non JRF domain but user wants to use ATP database
        if has_atp and archive_helper:
            archive_helper.extract_atp_wallet()

        creator = DomainCreator(model_dictionary, model_context, aliases)
        creator.create()

        if has_atp:
            rcu_properties_map = model_dictionary[model_constants.DOMAIN_INFO][model_constants.RCU_DB_INFO]
            rcu_db_info = RcuDbInfo(model_context, aliases, rcu_properties_map)
            atp_helper.fix_jps_config(rcu_db_info, model_context)
        elif has_ssl:
            rcu_properties_map = model_dictionary[model_constants.DOMAIN_INFO][model_constants.RCU_DB_INFO]
            rcu_db_info = RcuDbInfo(model_context, aliases, rcu_properties_map)
            ssl_helper.fix_jps_config(rcu_db_info, model_context)
    except WLSDeployArchiveIOException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except CreateException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except IOException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
    except DeployException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-12410', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
