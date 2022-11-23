"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The entry point for the deployApps tool.
"""
import exceptions
import os
import sys

from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.exception import BundleAwareException

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy import model_deployer
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.model import Model
from wlsdeploy.util.weblogic_helper import WebLogicHelper

wlst_helper.wlst_functions = globals()


_program_name = 'deployApps'
_class_name = 'deploy'
__logger = PlatformLogger('wlsdeploy.deploy')
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
    CommandLineArgUtil.ADMIN_PASS_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_ENV_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_FILE_SWITCH,
    CommandLineArgUtil.PASSPHRASE_ENV_SWITCH,
    CommandLineArgUtil.OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.DISCARD_CURRENT_EDIT_SWITCH,
    CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH
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
    argument_map = cla_util.process_args(args)

    cla_helper.validate_optional_archive(_program_name, argument_map)
    cla_helper.validate_model_present(_program_name, argument_map)
    cla_helper.validate_variable_file_exists(_program_name, argument_map)

    __wlst_mode = cla_helper.process_online_args(argument_map)
    cla_helper.process_encryption_args(argument_map)

    return model_context_helper.create_context(_program_name, argument_map)


def __deploy(model, model_context, aliases):
    """
    The method that does the heavy lifting for deploy.
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases
    :raises DeployException: if an error occurs
    """
    if __wlst_mode == WlstModes.ONLINE:
        ret_code = __deploy_online(model, model_context, aliases)
    else:
        ret_code = __deploy_offline(model, model_context, aliases)
    return ret_code


def __deploy_online(model, model_context, aliases):
    """
    Online deployment orchestration
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :raises: DeployException: if an error occurs
    """
    _method_name = '__deploy_online'

    admin_url = model_context.get_admin_url()
    admin_user = model_context.get_admin_user()
    admin_pwd = model_context.get_admin_password()
    timeout = model_context.get_model_config().get_connect_timeout()
    skip_edit_session_check = model_context.is_discard_current_edit() or model_context.is_wait_for_edit_lock()
    edit_lock_acquire_timeout = model_context.get_model_config().get_wlst_edit_lock_acquire_timeout()
    edit_lock_release_timeout = model_context.get_model_config().get_wlst_edit_lock_release_timeout()
    edit_lock_exclusive = model_context.get_model_config().get_wlst_edit_lock_exclusive()

    __logger.info("WLSDPLY-09005", admin_url, timeout, method_name=_method_name, class_name=_class_name)

    __wlst_helper.connect(admin_user, admin_pwd, admin_url, timeout)
    deployer_utils.ensure_no_uncommitted_changes_or_edit_sessions(skip_edit_session_check)
    __wlst_helper.edit()
    __logger.fine("WLSDPLY-09019", edit_lock_acquire_timeout, edit_lock_release_timeout, edit_lock_exclusive)
    __wlst_helper.start_edit(acquire_timeout=edit_lock_acquire_timeout, release_timeout=edit_lock_release_timeout,
                             exclusive=edit_lock_exclusive)
    if model_context.is_discard_current_edit():
        deployer_utils.discard_current_edit()

    __logger.info("WLSDPLY-09007", admin_url, method_name=_method_name, class_name=_class_name)

    try:
        model_deployer.deploy_resources(model, model_context, aliases, wlst_mode=__wlst_mode)
        deployer_utils.delete_online_deployment_targets(model, aliases, __wlst_mode)
        model_deployer.deploy_app_attributes_online(model, model_context, aliases)
    except DeployException, de:
        deployer_utils.release_edit_session_and_disconnect()
        raise de

    exit_code = deployer_utils.online_check_save_activate(model_context)

    if exit_code != ExitCode.CANCEL_CHANGES_IF_RESTART:
        model_deployer.deploy_applications(model, model_context, aliases, wlst_mode=__wlst_mode)

    try:
        __wlst_helper.disconnect()
    except BundleAwareException, ex:
        # All the changes are made and active so don't raise an error that causes the program
        # to indicate a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09009', _program_name, ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return exit_code


def __deploy_offline(model, model_context, aliases):
    """
    Offline deployment orchestration
    :param model: the model
    :param model_context: the model context
    :param aliases: the aliases object
    :raises: DeployException: if an error occurs
    """
    _method_name = '__deploy_offline'

    domain_home = model_context.get_domain_home()
    __logger.info("WLSDPLY-09010", domain_home, method_name=_method_name, class_name=_class_name)

    __wlst_helper.read_domain(domain_home)

    model_deployer.deploy_model_offline(model, model_context, aliases, wlst_mode=__wlst_mode)

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
    The python entry point for deployApps.

    :param model_context: the model context object
    :return: exit code
    """
    _method_name = 'main'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    __wlst_helper.silence()
    _exit_code = ExitCode.OK

    try:
        aliases = Aliases(model_context, wlst_mode=__wlst_mode, exception_type=ExceptionType.DEPLOY)

        model_dictionary = cla_helper.load_model(_program_name, model_context, aliases, "deploy", __wlst_mode,
                                                 validate_crd_sections=False)
        model = Model(model_dictionary)
        _exit_code = __deploy(model, model_context, aliases)
    except DeployException, ex:
        _exit_code = ExitCode.ERROR
        __logger.severe('WLSDPLY-09015', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
