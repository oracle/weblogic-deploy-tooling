"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the updateDomain tool.
"""
import exceptions
import os
import sys

from java.lang import Exception as JException
from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.exception import BundleAwareException
from oracle.weblogic.deploy.validate import ValidateException

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy.model_deployer import ModelDeployer
from wlsdeploy.tool.deploy.topology_updater import TopologyUpdater
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util import results_file
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.tool.util.rcu_helper import RCUHelper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model import Model
from wlsdeploy.tool.validate.validator import Validator


wlst_helper.wlst_functions = globals()

_program_name = 'updateDomain'
_class_name = 'update'
__logger = PlatformLogger('wlsdeploy.update')
__wlst_helper = WlstHelper(ExceptionType.DEPLOY)
__wlst_mode = WlstModes.OFFLINE

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_URL_SWITCH,
    CommandLineArgUtil.ADMIN_USER_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_ENV_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH,
    CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH,
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH,
    CommandLineArgUtil.DISCARD_CURRENT_EDIT_SWITCH,
    CommandLineArgUtil.WAIT_FOR_EDIT_LOCK_SWITCH,
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
    CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH,
    # deprecated in 4.2.0
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH
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
    cla_util.set_allow_multiple_models(True)
    argument_map = cla_util.process_args(args)

    cla_helper.validate_optional_archive(_program_name, argument_map)
    cla_helper.validate_required_model(_program_name, argument_map)
    cla_helper.validate_variable_file_exists(_program_name, argument_map)
    __wlst_mode = cla_helper.process_online_args(argument_map)
    cla_helper.validate_if_domain_home_required(_program_name, argument_map, __wlst_mode)
    cla_helper.validate_ssh_is_supported(_program_name, argument_map)
    cla_helper.process_encryption_args(argument_map, is_encryption_supported)

    return model_context_helper.create_context(_program_name, argument_map)


def __update(model, model_context, aliases):
    """
    The method that does the heavy lifting for update.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases
    :raises DeployException: if an error occurs
    """
    model_deployer = ModelDeployer(model, model_context, aliases, wlst_mode=__wlst_mode)

    if __wlst_mode == WlstModes.ONLINE:
        ret_code = __update_online(model_deployer, model, model_context, aliases)
    else:
        model_deployer.extract_early_archive_files()
        ret_code = __update_offline(model_deployer, model, model_context, aliases)

    results_file.check_and_write(model_context, ExceptionType.DEPLOY)

    return ret_code


def __update_online(model_deployer, model, model_context, aliases):
    """
    Online update orchestration
    :param model_deployer: ModelDeployer object
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :raises: DeployException: if an error occurs
    """
    _method_name = '__update_online'

    admin_url = model_context.get_admin_url()
    admin_user = model_context.get_admin_user()
    admin_pwd = model_context.get_admin_password()
    timeout = model_context.get_model_config().get_connect_timeout()
    skip_edit_session_check = model_context.is_discard_current_edit() or model_context.is_wait_for_edit_lock()
    edit_lock_acquire_timeout = model_context.get_model_config().get_wlst_edit_lock_acquire_timeout()
    edit_lock_release_timeout = model_context.get_model_config().get_wlst_edit_lock_release_timeout()
    edit_lock_exclusive = model_context.get_model_config().get_wlst_edit_lock_exclusive()

    __logger.info("WLSDPLY-09005", admin_url, timeout, method_name=_method_name, class_name=_class_name)

    try:

        if model_context.is_remote():
            model_validator = Validator(model_context, aliases, wlst_mode=WlstModes.ONLINE)
            model_validator.validate_in_tool_mode(model.get_model(), None,
                                                  model_context.get_archive_file_name())

        __wlst_helper.connect(admin_user, admin_pwd, admin_url, timeout)

        # All online operations do not have domain home set, so get it from online wlst after connect
        model_context.set_domain_home_name_if_online(__wlst_helper.get_domain_home_online(),
                                                     __wlst_helper.get_domain_name_online())

        model_deployer.extract_early_archive_files()
        deployer_utils.ensure_no_uncommitted_changes_or_edit_sessions(skip_edit_session_check)
        __wlst_helper.edit()
        __logger.fine("WLSDPLY-09019", edit_lock_acquire_timeout, edit_lock_release_timeout, edit_lock_exclusive)
        __wlst_helper.start_edit(acquire_timeout=edit_lock_acquire_timeout, release_timeout=edit_lock_release_timeout,
                                 exclusive=edit_lock_exclusive)
        if model_context.is_discard_current_edit():
            deployer_utils.discard_current_edit()
    except ValidateException, ve:
        raise ve
    except BundleAwareException, ex:
        raise ex

    __logger.info("WLSDPLY-09007", admin_url, method_name=_method_name, class_name=_class_name)

    topology_updater = TopologyUpdater(model, model_context, aliases, wlst_mode=WlstModes.ONLINE)
    try:
        jdbc_names = topology_updater.update_machines_clusters_and_servers(delete_now=False)
        topology_updater.warn_set_server_groups()

        # Server or Cluster may be added, this is to make sure they are targeted properly
        topology_updater.set_server_groups()

        topology_updater.clear_placeholder_targeting(jdbc_names)
        topology_updater.update_nm_properties()  # alias will skip for online, but log the omission
        topology_updater.update()
        model_deployer.deploy_resources()
        model_deployer.distribute_database_wallets_online()
        model_deployer.deploy_app_attributes_online()

    except (DeployException, exceptions.Exception, JException), ex:
        # release the edit session, and raise the exception for tool_main to handle
        deployer_utils.release_edit_session_and_disconnect()
        raise ex

    exit_code = deployer_utils.online_check_save_activate(model_context)
    # if user requested cancel changes if restart required stops

    if exit_code != ExitCode.CANCEL_CHANGES_IF_RESTART:
        is_restart_required = exit_code == ExitCode.RESTART_REQUIRED
        model_deployer.deploy_applications(is_restart_required=is_restart_required)

    try:
        __wlst_helper.disconnect()
    except BundleAwareException, ex:
        # All the changes are made and active so don't raise an error that causes the program
        # to indicate a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09009', _program_name, ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return exit_code


def __update_offline(model_deployer, model, model_context, aliases):
    """
    Offline update orchestration
    :param model_deployer: ModelDeployer object
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
    # deleting servers that are added by templates before set server groups causes mayhem
    jdbc_names = topology_updater.update_machines_clusters_and_servers(delete_now=False)

    # update rcu schema password must happen before updating a jrf domain
    if model_context.get_update_rcu_schema_pass() is True:
        rcu_helper = RCUHelper(model, None, model_context, aliases, exception_type=ExceptionType.DEPLOY)
        rcu_helper.update_rcu_password()

    # this needs to be before first updateDomain for NativeVersionEnabled=true to update correctly
    topology_updater.update_nm_properties()

    __update_offline_domain()

    topology_updater.set_server_groups()
    topology_updater.clear_placeholder_targeting(jdbc_names)
    topology_updater.update()

    # Add resources after server groups are established to prevent auto-renaming
    model_deployer.deploy_model_offline()

    __update_offline_domain()

    model_deployer.deploy_model_after_update()

    try:
        __wlst_helper.close_domain()
    except BundleAwareException, ex:
        # All the changes are made so don't raise an error that causes the program to indicate
        # a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09011', _program_name, ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return 0


def __update_offline_domain():
    try:
        __wlst_helper.update_domain()
    except BundleAwareException, ex:
        __close_domain_on_error()
        raise ex


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


def main(model_context):
    """
    The python entry point for updateDomain.

    :param model_context: the model context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    _exit_code = ExitCode.OK
    __wlst_helper.silence()

    try:
        aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.DEPLOY)
        model_dictionary = cla_helper.load_model(_program_name, model_context, aliases, "update", __wlst_mode,
                                                 validate_crd_sections=False)
        model = Model(model_dictionary)

        _exit_code = __update(model, model_context, aliases)
    except DeployException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-09015', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
