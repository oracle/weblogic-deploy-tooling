"""
Copyright (c) 2017, 2020, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the updateDomain tool.
"""
import os
import sys

from java.io import IOException, PrintStream
from java.lang import String, System

from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.exception import BundleAwareException
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import TranslateException
from oracle.weblogic.deploy.util import VariableException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.validate import ValidateException

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.tool.util.alias_helper import AliasHelper
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create.domain_typedef import UPDATE_DOMAIN
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy import model_deployer
from wlsdeploy.tool.deploy.topology_updater import TopologyUpdater
from wlsdeploy.tool.validate.validator import Validator
from wlsdeploy.tool.util import filter_helper
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.util.rcu_helper import RCUHelper
from wlsdeploy.tool.util.string_output_stream import StringOutputStream
from wlsdeploy.util import cla_helper
from wlsdeploy.util import getcreds
from wlsdeploy.util import tool_exit
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model import Model
from wlsdeploy.util.weblogic_helper import WebLogicHelper
from wlsdeploy.util import model as model_helper
# from wlsdeploy.aliases.model_constants import RCU_DB_INFO
# from wlsdeploy.aliases.model_constants import RCU_PREFIX
# from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
# from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_USER_PROPERTY
# from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS
# from wlsdeploy.aliases.model_constants import JDBC_DRIVER_PARAMS_PROPERTIES
# from wlsdeploy.aliases.model_constants import JDBC_RESOURCE
# from wlsdeploy.aliases.model_constants import JDBC_SYSTEM_RESOURCE
# from wlsdeploy.aliases.model_constants import PASSWORD_ENCRYPTED
#
#
# from wlsdeploy.tool.create.rcudbinfo_helper import RcuDbInfo
# from wlsdeploy.aliases.location_context import LocationContext


wlst_helper.wlst_functions = globals()

_program_name = UPDATE_DOMAIN
_class_name = 'update'
__logger = PlatformLogger('wlsdeploy.update')
__wls_helper = WebLogicHelper(__logger)
__wlst_helper = WlstHelper(ExceptionType.DEPLOY)
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_URL_SWITCH,
    CommandLineArgUtil.ADMIN_USER_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.ROLLBACK_IF_RESTART_REQ_SWITCH,
    CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    cla_util.set_allow_multiple_models(True)
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    __verify_required_args_present(required_arg_map)
    __process_model_args(optional_arg_map)
    __wlst_mode = __process_online_args(optional_arg_map)

    __process_encryption_args(optional_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)
    return model_context_helper.create_context(_program_name, combined_arg_map)


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


def __process_model_args(optional_arg_map):
    """
    Determine if the model file was passed separately or requires extraction from the archive.
    :param optional_arg_map:   the optional arguments map
    :raises CLAException: If an error occurs validating the arguments or extracting the model from the archive
    """
    cla_helper.validate_optional_archive(_program_name, optional_arg_map)
    cla_helper.validate_model_present(_program_name, optional_arg_map)
    cla_helper.validate_variable_file_exists(_program_name, optional_arg_map)
    return


def __process_online_args(optional_arg_map):
    """
    Determine if we are update in online mode and if so, validate/prompt for the necessary parameters.
    :param optional_arg_map: the optional arguments map
    :return: the WLST mode
    :raises CLAException: if an error occurs reading input from the user
    """
    _method_name = '__process_online_args'

    mode = WlstModes.OFFLINE
    if CommandLineArgUtil.ADMIN_URL_SWITCH in optional_arg_map:
        if CommandLineArgUtil.ADMIN_USER_SWITCH not in optional_arg_map:
            try:
                username = getcreds.getuser('WLSDPLY-09001')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception('WLSDPLY-09002', ioe.getLocalizedMessage(), error=ioe)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_USER_SWITCH] = username

        if CommandLineArgUtil.ADMIN_PASS_SWITCH not in optional_arg_map:
            try:
                password = getcreds.getpass('WLSDPLY-09003')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception('WLSDPLY-09004', ioe.getLocalizedMessage(), error=ioe)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_PASS_SWITCH] = String(password)

        mode = WlstModes.ONLINE
        optional_arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH] = 'online'
    return mode


def __process_encryption_args(optional_arg_map):
    """
    Determine if the user is using our encryption and if so, get the passphrase.
    :param optional_arg_map: the optional arguments map
    :raises CLAException: if an error occurs reading the passphrase inout from the user
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

# def __process_update_rcu_schema_password_args(model, model_context, aliases):
#     """
#     If the flag is set, it will update the password of each rcu schema and then update the bootstrap password
#     """
#
#     _method_name = '__process_update_rcu_schema_password_args'
#
#     # construct the partial dictionary of the JRF schema and just the password
#     # call the database deployer add_data_sources
#     # update the bootrap with the new password
#     # modifyBootStrapCredential(jpsConfigFile=model_context.get_domain_home() +
#     #   '/config/fmwconfig/jps-config-jse.xml',
#     #  username='schema_prefix_OPSS',password='new_password')
#
#     domain_info = model.get_model_domain_info()
#     if RCU_DB_INFO in domain_info:
#         alias_helper = AliasHelper(aliases, __logger, ExceptionType.CREATE)
#         rcu_db_info = RcuDbInfo(alias_helper, domain_info[RCU_DB_INFO])
#         rcu_schema_pass = rcu_db_info.get_rcu_schema_password()
#         rcu_prefix = rcu_db_info.get_rcu_prefix()
#
#         location = LocationContext()
#         location.append_location(JDBC_SYSTEM_RESOURCE)
#
#         folder_path = alias_helper.get_wlst_list_path(location)
#         __wlst_helper.cd(folder_path)
#         ds_names = __wlst_helper.lsc()
#         domain_typedef = model_context.get_domain_typedef()
#         rcu_schemas = domain_typedef.get_rcu_schemas()
#         if len(rcu_schemas) == 0:
#             return
#         schemas_len = len(rcu_schemas)
#
#         for i in range(0,schemas_len):
#             rcu_schemas[i] = rcu_prefix + '_' + rcu_schemas[i]
#
#         for ds_name in ds_names:
#             location = LocationContext()
#             location.append_location(JDBC_SYSTEM_RESOURCE)
#             token_name = alias_helper.get_name_token(location)
#             location.add_name_token(token_name, ds_name)
#
#             location.append_location(JDBC_RESOURCE)
#             location.append_location(JDBC_DRIVER_PARAMS)
#             password_location = LocationContext(location)
#
#             wlst_path = alias_helper.get_wlst_attributes_path(location)
#             __wlst_helper.cd(wlst_path)
#
#             location.append_location(JDBC_DRIVER_PARAMS_PROPERTIES)
#             token_name = alias_helper.get_name_token(location)
#             if token_name is not None:
#                 location.add_name_token(token_name, DRIVER_PARAMS_USER_PROPERTY)
#             wlst_path = alias_helper.get_wlst_attributes_path(location)
#             __wlst_helper.cd(wlst_path)
#             ds_user = __wlst_helper.get('Value')
#
#             if ds_user in rcu_schemas:
#                 print ds_user
#                 print password_location
#                 wlst_path = alias_helper.get_wlst_attributes_path(password_location)
#                 __wlst_helper.cd(wlst_path)
#                 print wlst_path
#                 print 'rcu pwd is now'
#                 print rcu_schema_pass
#
#                 wlst_name, wlst_value = \
#                     alias_helper.get_wlst_attribute_name_and_value(password_location, PASSWORD_ENCRYPTED,
#                                                                         rcu_schema_pass, masked=True)
#                 __wlst_helper.set(wlst_name, wlst_value, masked=True)
#
#             domain_home = model_context.get_domain_home()
#             config_file = domain_home + '/config/fmwconfig/jps-config-jse.xml'
#             opss_user = rcu_prefix + '_OPSS'
#             modifyBootStrapCredential(jpsConfigFile=config_file, username=opss_user, password=rcu_schema_pass)

def __update(model, model_context, aliases):
    """
    The method that does the heavy lifting for update.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases
    :raises DeployException: if an error occurs
    """
    if __wlst_mode == WlstModes.ONLINE:
        ret_code = __update_online(model, model_context, aliases)
    else:
        ret_code = __update_offline(model, model_context, aliases)

    return ret_code

def __update_online(model, model_context, aliases):
    """
    Online update orchestration
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :raises: DeployException: if an error occurs
    """
    _method_name = '__update_online'

    admin_url = model_context.get_admin_url()
    admin_user = model_context.get_admin_user()
    admin_pwd = model_context.get_admin_password()

    __logger.info("WLSDPLY-09005", admin_url, method_name=_method_name, class_name=_class_name)

    try:
        __wlst_helper.connect(admin_user, admin_pwd, admin_url)
        deployer_utils.ensure_no_uncommitted_changes_or_edit_sessions()
        __wlst_helper.edit()
        __wlst_helper.start_edit()
    except BundleAwareException, ex:
        raise ex

    __logger.info("WLSDPLY-09007", admin_url, method_name=_method_name, class_name=_class_name)

    try:
        topology_updater = TopologyUpdater(model, model_context, aliases, wlst_mode=WlstModes.ONLINE)
        topology_updater.update()
        model_deployer.deploy_resources(model, model_context, aliases, wlst_mode=__wlst_mode)
    except DeployException, de:
        __release_edit_session_and_disconnect()
        raise de

    exit_code = 0

    try:
        # First we enable the stdout again and then redirect the stdoout to a string output stream
        # call isRestartRequired to get the output, capture the string and then silence wlst output again
        #

        __wlst_helper.enable_stdout()
        sostream = StringOutputStream()
        System.setOut(PrintStream(sostream))
        restart_required = __wlst_helper.is_restart_required()
        is_restartreq_output = sostream.get_string()
        __wlst_helper.silence()
        if model_context.is_rollback_if_restart_required() and restart_required:
            __wlst_helper.cancel_edit()
            __logger.severe('WLSDPLY_09015', is_restartreq_output)
            exit_code = CommandLineArgUtil.PROG_ROLLBACK_IF_RESTART_EXIT_CODE
        else:
            __wlst_helper.save()
            __wlst_helper.activate()
            if restart_required:
                exit_code = CommandLineArgUtil.PROG_RESTART_REQUIRED
    except BundleAwareException, ex:
        __release_edit_session_and_disconnect()
        raise ex

    model_deployer.deploy_applications(model, model_context, aliases, wlst_mode=__wlst_mode)

    try:
        __wlst_helper.disconnect()
    except BundleAwareException, ex:
        # All the changes are made and active so don't raise an error that causes the program
        # to indicate a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09009', _program_name, ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return exit_code


def __update_offline(model, model_context, aliases):
    """
    Offline update orchestration
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :raises: DeployException: if an error occurs
    """
    _method_name = '__update_offline'

    domain_home = model_context.get_domain_home()
    __logger.info("WLSDPLY-09010", domain_home, method_name=_method_name, class_name=_class_name)

    __wlst_helper.read_domain(domain_home)

    topology_updater = TopologyUpdater(model, model_context, aliases, wlst_mode=WlstModes.OFFLINE)
    topology_updater.update()

    model_deployer.deploy_model_offline(model, model_context, aliases, wlst_mode=__wlst_mode)
    if model_context.get_update_rcu_schema_pass() is True:
        rcu_helper = RCUHelper(model, model_context, aliases)
        rcu_helper.update_rcu_password()

    try:
        __wlst_helper.update_domain()
    except BundleAwareException, ex:
        __close_domain_on_error()
        raise ex

    model_deployer.deploy_model_after_update(model, model_context, aliases, wlst_mode=__wlst_mode)

    try:
        __wlst_helper.close_domain()
    except BundleAwareException, ex:
        # All the changes are made so don't raise an error that causes the program to indicate
        # a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09011', _program_name, ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return 0


def __release_edit_session_and_disconnect():
    """
    An online error recovery method.
    """
    _method_name = '__release_edit_session_and_disconnect'
    try:
        __wlst_helper.undo()
        __wlst_helper.stop_edit()
        __wlst_helper.disconnect()
    except BundleAwareException, ex:
        # This method is only used for cleanup after an error so don't mask
        # the original problem by throwing yet another exception...
        __logger.warning('WLSDPLY-09012', ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return


def __close_domain_on_error():
    """
    An offline error recovery method.
    """
    _method_name = '__close_domain_on_error'
    try:
        __wlst_helper.close_domain()
    except BundleAwareException, ex:
        # This method is only used for cleanup after an error so don't mask
        # the original problem by throwing yet another exception...
        __logger.warning('WLSDPLY-09013', ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return


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
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    if return_code == Validator.ReturnCode.STOP:
        __logger.severe('WLSDPLY-20001', _program_name, class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)


def main(args):
    """
    The python entry point for updateDomain.

    :param args:
    :return:
    """
    _method_name = 'main'

    __logger.entering(args[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    __wlst_helper.silence()

    exit_code = CommandLineArgUtil.PROG_OK_EXIT_CODE

    try:
        model_context = __process_args(args)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-20008', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()

        # create a minimal model for summary logging
        model_context = model_context_helper.create_exit_context(_program_name)
        tool_exit.end(model_context, exit_code)

    variable_map = {}
    try:
        if model_context.get_variable_file():
            variable_map = variables.load_variables(model_context.get_variable_file())
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    model_file_value = model_context.get_model_file()
    try:
        model_dictionary = cla_helper.merge_model_files(model_file_value, variable_map)
    except TranslateException, te:
        __logger.severe('WLSDPLY-09014', _program_name, model_file_value, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    try:
        variables.substitute(model_dictionary, variable_map, model_context)
    except VariableException, ex:
        __logger.severe('WLSDPLY-20004', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    cla_helper.persist_model(model_context, model_dictionary)

    aliases = Aliases(model_context, wlst_mode=__wlst_mode)
    validate_model(model_dictionary, model_context, aliases)

    if filter_helper.apply_filters(model_dictionary, "update"):
        # if any filters were applied, re-validate the model
        validate_model(model_dictionary, model_context, aliases)

    try:
        model = Model(model_dictionary)
        exit_code = __update(model, model_context, aliases)
    except DeployException, ex:
        __logger.severe('WLSDPLY-09015', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        cla_helper.clean_up_temp_files()
        tool_exit.end(model_context, CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    cla_helper.clean_up_temp_files()

    tool_exit.end(model_context, exit_code)
    return


if __name__ == '__main__' or __name__ == 'main':
    WebLogicDeployToolingVersion.logVersionInfo(_program_name)
    main(sys.argv)
