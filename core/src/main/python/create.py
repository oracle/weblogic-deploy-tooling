"""
Copyright (c) 2017, 2019, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The main module for the WLSDeploy tool to create empty domains.
"""
import javaos as os
import sys
from java.io import IOException
from java.lang import IllegalArgumentException
from java.lang import IllegalStateException
from java.lang import String
from java.lang import System
from oracle.weblogic.deploy.create import CreateException
from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.util import WLSDeployArchive
from oracle.weblogic.deploy.util import WLSDeployArchiveIOException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.validate import ValidateException

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here

from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases import model_constants
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.rcudbinfo_helper import RcuDbInfo
from wlsdeploy.tool.create.domain_creator import DomainCreator
from wlsdeploy.tool.create.domain_typedef import DomainTypedef
from wlsdeploy.tool.create.domain_typedef import CREATE_DOMAIN
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.util import getcreds
from wlsdeploy.util import tool_exit
from wlsdeploy.util import variables
from wlsdeploy.util import wlst_extended
from wlsdeploy.util import wlst_helper
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.tool.create import atp_helper

wlst_extended.wlst_functions = globals()

_program_name = CREATE_DOMAIN

_class_name = 'create'
__logger = PlatformLogger('wlsdeploy.create')
__wlst_mode = WlstModes.OFFLINE
__version = WebLogicHelper(__logger).get_actual_weblogic_version()
__tmp_model_dir = None

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
    CommandLineArgUtil.JAVA_HOME_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.RUN_RCU_SWITCH,
    CommandLineArgUtil.RCU_SYS_PASS_SWITCH,
    CommandLineArgUtil.RCU_DB_SWITCH,
    CommandLineArgUtil.RCU_PREFIX_SWITCH,
    CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    required_arg_map, optional_arg_map = cla_util.process_args(args, True)
    __verify_required_args_present(required_arg_map)
    __process_java_home_arg(optional_arg_map)
    __process_domain_location_args(optional_arg_map)
    __process_model_args(optional_arg_map)

    #
    # Verify that the domain type is a known type and load its typedef.
    #
    domain_type = required_arg_map[CommandLineArgUtil.DOMAIN_TYPE_SWITCH]
    domain_typedef = DomainTypedef(_program_name, domain_type)
    optional_arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF] = domain_typedef

    __process_rcu_args(optional_arg_map, domain_type, domain_typedef)
    __process_encryption_args(optional_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)
    model_context = ModelContext(_program_name, combined_arg_map)
    domain_typedef.set_model_context(model_context)
    return model_context


def __verify_required_args_present(required_arg_map):
    """
    Verify that the required args are present.
    :param required_arg_map: the required arguments map
    :raises CLAException: if one or more of the required arguments are missing
    """
    _method_name = '__verify_required_args_present'

    for req_arg in __required_arguments:
        if req_arg not in required_arg_map:
            ex = exception_helper.create_cla_exception('WLSDPLY-20005', _program_name, req_arg)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


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
            ex = exception_helper.create_cla_exception('WLSDPLY-12400', _program_name, java_home_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH] = java_home.getAbsolutePath()
    return


def __process_domain_location_args(optional_arg_map):
    """
    Verify that either the domain_home or domain_parent was specified, and not both.
    Their values were already checked in the process_args call.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are invalid or an error occurs extracting the model from the archive
    """
    _method_name = '__process_domain_location_args'
    global __tmp_model_dir

    has_home = CommandLineArgUtil.DOMAIN_HOME_SWITCH in optional_arg_map
    has_parent = CommandLineArgUtil.DOMAIN_PARENT_SWITCH in optional_arg_map

    if (has_home and has_parent) or (not has_home and not has_parent):
        ex = exception_helper.create_cla_exception('WLSDPLY-20025', _program_name,
                                                   CommandLineArgUtil.DOMAIN_PARENT_SWITCH,
                                                   CommandLineArgUtil.DOMAIN_HOME_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return


def __process_model_args(optional_arg_map):
    """
    Verify that either the model_file or archive_file was provided and exists.
    Extract the model file if only the archive_file was provided.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if the arguments are invalid or an error occurs extracting the model from the archive
    """
    _method_name = '__process_model_args'
    global __tmp_model_dir

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_name = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]

        try:
            FileUtils.validateExistingFile(model_file_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-20006', _program_name, model_file_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.ARCHIVE_FILE_SWITCH in optional_arg_map:
        archive_file_name = optional_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]

        try:
            archive_file = WLSDeployArchive(archive_file_name)
            __tmp_model_dir = FileUtils.createTempDirectory(_program_name)
            tmp_model_raw_file = archive_file.extractModel(__tmp_model_dir)
            if not tmp_model_raw_file:
                ex = exception_helper.create_cla_exception('WLSDPLY-20026', _program_name, archive_file_name,
                                                           CommandLineArgUtil.MODEL_FILE_SWITCH)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

            tmp_model_file = FileUtils.fixupFileSeparatorsForJython(tmp_model_raw_file.getAbsolutePath())
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-20010', _program_name, archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = FileUtils.fixupFileSeparatorsForJython(tmp_model_file)
    else:
        ex = exception_helper.create_cla_exception('WLSDPLY-20015', _program_name, CommandLineArgUtil.MODEL_FILE_SWITCH,
                                                   CommandLineArgUtil.ARCHIVE_FILE_SWITCH)
        ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return


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
                        ex = exception_helper.create_cla_exception('WLSDPLY-12404', ioe.getLocalizedMessage(),
                                                                   error=ioe)
                        ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex
                    optional_arg_map[CommandLineArgUtil.RCU_SYS_PASS_SWITCH] = String(password)
                if CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH not in optional_arg_map:
                    try:
                        password = getcreds.getpass('WLSDPLY-12405')
                    except IOException, ioe:
                        ex = exception_helper.create_cla_exception('WLSDPLY-12406', ioe.getLocalizedMessage(),
                                                                   error=ioe)
                        ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                        raise ex
                    optional_arg_map[CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH] = String(password)
            else:
                ex = exception_helper.create_cla_exception('WLSDPLY-12407', _program_name,
                                                           CommandLineArgUtil.RCU_DB_SWITCH,
                                                           CommandLineArgUtil.RCU_PREFIX_SWITCH)
                ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex

        # Delay the checking later for rcu related parameters

    return


def __process_encryption_args(optional_arg_map):
    """
    Determine if the user is using our encryption and if so, get the passphrase.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if getting the passphrase from the user fails
    """
    _method_name = '__process_encryption_args'

    if CommandLineArgUtil.USE_ENCRYPTION_SWITCH in optional_arg_map and \
            CommandLineArgUtil.PASSPHRASE_SWITCH not in optional_arg_map:
        try:
            passphrase = getcreds.getpass('WLSDPLY-20002')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception('WLSDPLY-20003', ioe.getLocalizedMessage(),
                                                       error=ioe)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = String(passphrase)
    return


def __clean_up_temp_files():
    """
    If a temporary directory was created to extract the model from the archive, delete the directory and its contents.
    """
    global __tmp_model_dir

    if __tmp_model_dir is not None:
        FileUtils.deleteDirectory(__tmp_model_dir)
        __tmp_model_dir = None


def validate_model(model_dictionary, model_context, aliases):
    _method_name = 'validate_model'

    try:
        validator = Validator(model_context, aliases, wlst_mode=__wlst_mode)

        # no need to pass the variable file for processing, substitution has already been performed
        return_code = validator.validate_in_tool_mode(model_dictionary, variables_file_name=None,
                                                      archive_file_name=model_context.get_archive_file_name())
    except ValidateException, ex:
        __logger.severe('WLSDPLY-20000', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    if return_code == Validator.ReturnCode.STOP:
        __logger.severe('WLSDPLY-20001', _program_name, class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)


def validateRCUArgsAndModel(model_context, model, alias_helper):
    has_atpdbinfo = 0
    domain_info = model[model_constants.DOMAIN_INFO]
    if domain_info is not None:
        if model_constants.RCU_DB_INFO in domain_info:
            rcu_db_info = RcuDbInfo(alias_helper, domain_info[model_constants.RCU_DB_INFO])
            has_tns_admin = rcu_db_info.has_tns_admin()
            has_regular_db = rcu_db_info.is_regular_db()
            has_atpdbinfo = rcu_db_info.has_atpdbinfo()

            if model_context.get_archive_file_name() and not has_regular_db:
                System.setProperty('oracle.jdbc.fanEnabled', 'false')

                # 1. If it does not have the oracle.net.tns_admin specified, then extract to domain/atpwallet
                # 2. If it is plain old regular oracle db, do nothing
                # 3. If it deos not have tns_admin in the model, then the wallet must be in the archive
                if not has_tns_admin:
                    # extract the wallet first
                    archive_file = WLSDeployArchive(model_context.get_archive_file_name())
                    atp_wallet_zipentry = None
                    if archive_file:
                        atp_wallet_zipentry = archive_file.getATPWallet()
                    if atp_wallet_zipentry and model[model_constants.TOPOLOGY]['Name']:
                        extract_path = atp_helper.extract_walletzip(model, model_context, archive_file, atp_wallet_zipentry)
                        # update the model to add the tns_admin
                        model[model_constants.DOMAIN_INFO][model_constants.RCU_DB_INFO][
                            model_constants.DRIVER_PARAMS_NET_TNS_ADMIN] = extract_path
                    else:
                        __logger.severe('WLSDPLY-12411', error=None,
                                        class_name=_class_name, method_name="validateRCUArgsAndModel")
                        __clean_up_temp_files()
                        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

        else:
            if model_context.get_domain_typedef().required_rcu():
                if not model_context.get_rcu_database() or not model_context.get_rcu_prefix():
                    __logger.severe('WLSDPLY-12408', model_context.get_domain_type(), CommandLineArgUtil.RCU_DB_SWITCH,
                                    CommandLineArgUtil.RCU_PREFIX_SWITCH)
                    __clean_up_temp_files()
                    tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    return has_atpdbinfo


def main(args):
    """
    The entry point for the create domain tool.

    :param args:
    :return:
    """
    _method_name = 'main'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    wlst_helper.silence()

    exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE

    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(None, exit_code)

    model_file = model_context.get_model_file()
    try:
        model = FileToPython(model_file, True).parse()
    except TranslateException, te:
        __logger.severe('WLSDPLY-20009', _program_name, model_file, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    try:
        variable_map = {}
        if model_context.get_variable_file():
            variable_map = variables.load_variables(model_context.get_variable_file())
        variables.substitute(model, variable_map, model_context)
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    aliases = Aliases(model_context, wlst_mode=__wlst_mode)
    alias_helper = AliasHelper(aliases, __logger, ExceptionType.CREATE)
    validate_model(model, model_context, aliases)

    if filter_helper.apply_filters(model, "create"):
        # if any filters were applied, re-validate the model
        validate_model(model, model_context, aliases)
    try:

        has_atp = validateRCUArgsAndModel(model_context, model, alias_helper)
        # check if there is an atpwallet and extract in the domain dir
        # it is to support non JRF domain but user wants to use ATP database
        archive_file_name = model_context.get_archive_file_name()
        if not has_atp and archive_file_name and os.path.exists(archive_file_name):
            archive_file = WLSDeployArchive(archive_file_name)
            if archive_file:
                atp_wallet_zipentry = archive_file.getATPWallet()
                if atp_wallet_zipentry:
                    atp_helper.extract_walletzip(model, model_context, archive_file, atp_wallet_zipentry)

        creator = DomainCreator(model, model_context, aliases)
        creator.create()

        if has_atp:
            rcu_properties_map = model[model_constants.DOMAIN_INFO][model_constants.RCU_DB_INFO]
            rcu_db_info = RcuDbInfo(alias_helper, rcu_properties_map)
            atp_helper.fix_jps_config(rcu_db_info, model_context)

    except WLSDeployArchiveIOException, ex:
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    except CreateException, ex:
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    except IOException, ex:
        __logger.severe('WLSDPLY-12409', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)
    except DeployException, ex:
        __logger.severe('WLSDPLY-12410', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    __clean_up_temp_files()

    tool_exit.end(model_context, exit_code)
    return


if __name__ == "main":
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
