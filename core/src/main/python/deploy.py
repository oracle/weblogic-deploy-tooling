"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

The entry point for the deployApps tool.
"""

import os
import sys

import java.io.IOException as IOException
import java.lang.IllegalArgumentException as IllegalArgumentException
import java.lang.IllegalStateException as IllegalStateException
import java.lang.String as String

from oracle.weblogic.deploy.deploy import DeployException
from oracle.weblogic.deploy.util import PyWLSTException
from oracle.weblogic.deploy.util import VariableException

import oracle.weblogic.deploy.util.CLAException as CLAException
import oracle.weblogic.deploy.util.FileUtils as FileUtils
import oracle.weblogic.deploy.util.TranslateException as TranslateException
import oracle.weblogic.deploy.util.WLSDeployArchive as WLSDeployArchive
import oracle.weblogic.deploy.util.WLSDeployArchiveIOException as WLSDeployArchiveIOException
from oracle.weblogic.deploy.exception import BundleAwareException

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))

# imports from local packages start here
from wlsdeploy.aliases.aliases import Aliases
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.deploy import deployer_utils
from wlsdeploy.tool.deploy import model_deployer
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import getcreds
from wlsdeploy.util import variables
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model import Model
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.util.model_translator import FileToPython
from wlsdeploy.util.weblogic_helper import WebLogicHelper


_program_name = 'deployApps'
_class_name = 'deploy'
__logger = PlatformLogger('wlsdeploy.deploy')
__wls_helper = WebLogicHelper(__logger)
__wlst_helper = WlstHelper(__logger, ExceptionType.DEPLOY)
__wlst_mode = WlstModes.OFFLINE
__tmp_model_dir = None

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.DOMAIN_HOME_SWITCH,
    CommandLineArgUtil.ARCHIVE_FILE_SWITCH
]

__optional_arguments = [
    # Used by shell script to locate WLST
    CommandLineArgUtil.DOMAIN_TYPE_SWITCH,
    CommandLineArgUtil.MODEL_FILE_SWITCH,
    CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH,
    CommandLineArgUtil.VARIABLE_FILE_SWITCH,
    CommandLineArgUtil.ADMIN_URL_SWITCH,
    CommandLineArgUtil.ADMIN_USER_SWITCH,
    CommandLineArgUtil.ADMIN_PASS_SWITCH,
    CommandLineArgUtil.USE_ENCRYPTION_SWITCH,
    CommandLineArgUtil.PASSPHRASE_SWITCH
]


def __process_args(args):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    global __wlst_mode

    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    required_arg_map, optional_arg_map = cla_util.process_args(args)

    __verify_required_args_present(required_arg_map)
    archive_file_name = __validate_archive_file_arg(required_arg_map)
    __process_model_args(optional_arg_map, archive_file_name)
    __wlst_mode = __process_online_args(optional_arg_map)
    __process_encryption_args(optional_arg_map)

    combined_arg_map = optional_arg_map.copy()
    combined_arg_map.update(required_arg_map)

    return ModelContext(_program_name, combined_arg_map)


def __verify_required_args_present(required_arg_map):
    """
    Verify that the required args are present.
    :param required_arg_map: the required arguments map
    :raises CLAException: if one or more of the required arguments are missing
    """
    _method_name = '__verify_required_args_present'

    for req_arg in __required_arguments:
        if req_arg not in required_arg_map:
            ex = exception_helper.create_cla_exception('WLSDPLY-09040', _program_name, req_arg)
            ex.setExitCode(CommandLineArgUtil.USAGE_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    return


def __validate_archive_file_arg(required_arg_map):
    """
    Verify that the archive file exists.
    :param required_arg_map: the required arguments map
    :return: the archive file name
    :raises CLAException: if the archive file is not valid
    """
    _method_name = '__validate_archive_file_arg'

    archive_file_name = required_arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]
    try:
        FileUtils.validateExistingFile(archive_file_name)
    except IllegalArgumentException, iae:
        ex = exception_helper.create_cla_exception('WLSDPLY-09041', _program_name, archive_file_name,
                                                   iae.getLocalizedMessage(), error=iae)
        ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    return archive_file_name


def __process_model_args(optional_arg_map, archive_file_name):
    """
    Determine if the model file was passed separately or requires extraction from the archive.
    :param optional_arg_map:   the optional arguments map
    :param archive_file_name:  the archive file name
    :raises CLAException: If an error occurs validating the arguments or extracting the model from the archive
    """
    _method_name = '__process_model_args'
    global __tmp_model_dir

    if CommandLineArgUtil.MODEL_FILE_SWITCH in optional_arg_map:
        model_file_name = optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]

        try:
            FileUtils.validateExistingFile(model_file_name)
        except IllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-09042', _program_name, model_file_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    else:
        try:
            archive_file = WLSDeployArchive(archive_file_name)
            __tmp_model_dir = FileUtils.createTempDirectory(_program_name)
            model_file_name = archive_file.extractModel(__tmp_model_dir)
        except (IllegalArgumentException, IllegalStateException, WLSDeployArchiveIOException), archex:
            ex = exception_helper.create_cla_exception('WLSDPLY-09043', _program_name, archive_file_name,
                                                       archex.getLocalizedMessage(), error=archex)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = model_file_name
    return


def __process_online_args(optional_arg_map):
    """
    Determine if we are deploy in online mode and if so, validate/prompt for the necessary parameters.
    :param optional_arg_map: the optional arguments map
    :return: the WLST mode
    :raises CLAException: if an error occurs reading input from the user
    """
    _method_name = '__process_online_args'

    mode = WlstModes.OFFLINE
    if CommandLineArgUtil.ADMIN_URL_SWITCH in optional_arg_map:
        if CommandLineArgUtil.ADMIN_USER_SWITCH not in optional_arg_map:
            try:
                username = getcreds.getuser('WLSDPLY-09044')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception('WLSDPLY-09046', ioe.getLocalizedMessage(), error=ioe)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_USER_SWITCH] = username

        if CommandLineArgUtil.ADMIN_PASS_SWITCH not in optional_arg_map:
            try:
                password = getcreds.getpass('WLSDPLY-09045')
            except IOException, ioe:
                ex = exception_helper.create_cla_exception('WLSDPLY-09047', ioe.getLocalizedMessage(), error=ioe)
                ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
                __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
                raise ex
            optional_arg_map[CommandLineArgUtil.ADMIN_PASS_SWITCH] = String(password)

        mode = WlstModes.ONLINE
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
            passphrase = getcreds.getpass('WLSDPLY-12066')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception('WLSDPLY-12067', ioe.getLocalizedMessage(),
                                                       error=ioe)
            ex.setExitCode(CommandLineArgUtil.ARG_VALIDATION_ERROR_EXIT_CODE)
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
        optional_arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = String(passphrase)
    return


def __deploy(model, model_context):
    """
    The method that does the heavy lifting for deploy.
    :param model: the model
    :param model_context: the model context
    :raises DeployException: if an error occurs
    """
    aliases = Aliases(model_context, __wlst_mode)
    if __wlst_mode == WlstModes.ONLINE:
        __deploy_online(model, model_context, aliases)
    else:
        __deploy_offline(model, model_context, aliases)
    return


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

    __logger.info("WLSDPLY-09035", admin_url, method_name=_method_name, class_name=_class_name)

    try:
        __wlst_helper.connect(admin_user, admin_pwd, admin_url)
        deployer_utils.ensure_no_uncommitted_changes_or_edit_sessions()
        __wlst_helper.edit()
        __wlst_helper.start_edit()
    except PyWLSTException, pwe:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09078', _program_name, admin_url,
                                                      pwe.getLocalizedMessage(), error=pwe)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    __logger.info("WLSDPLY-09036", admin_url, method_name=_method_name, class_name=_class_name)

    try:
        model_deployer.deploy_resources(model, model_context, aliases, wlst_mode=__wlst_mode)
    except DeployException, de:
        __release_edit_session_and_disconnect()
        raise de

    try:
        __wlst_helper.save()
        __wlst_helper.activate()
    except PyWLSTException, pwe:
        ex = exception_helper.create_deploy_exception('WLSDPLY-09080', pwe.getLocalizedMessage(), error=pwe)
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        __release_edit_session_and_disconnect()
        raise ex

    model_deployer.deploy_applications(model, model_context, aliases, wlst_mode=__wlst_mode)

    try:
        __wlst_helper.disconnect()
    except PyWLSTException, pwe:
        # All the changes are made and active so don't raise an error that causes the program
        # to indicate a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09081', _program_name, pwe.getLocalizedMessage(), error=pwe,
                         class_name=_class_name, method_name=_method_name)
    return


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
    __logger.info("WLSDPLY-09037", domain_home, method_name=_method_name, class_name=_class_name)

    __wlst_helper.read_domain(domain_home)

    model_deployer.deploy_model_offline(model, model_context, aliases, wlst_mode=__wlst_mode)

    try:
        __wlst_helper.update_domain()
    except BundleAwareException, ex:
        __close_domain_on_error()
        raise ex

    try:
        __wlst_helper.close_domain()
    except BundleAwareException, ex:
        # All the changes are made so don't raise an error that causes the program to indicate
        # a failure...just log the error since the process is going to exit anyway.
        __logger.warning('WLSDPLY-09085', _program_name, ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return


def __release_edit_session_and_disconnect():
    """
    An online error recovery method.
    """
    _method_name = '__release_edit_session_and_disconnect'
    try:
        __wlst_helper.stop_edit()
        __wlst_helper.disconnect()
    except BundleAwareException, ex:
        # This method is only used for cleanup after an error so don't mask
        # the original problem by throwing yet another exception...
        __logger.warning('WLSDPLY-09079', ex.getLocalizedMessage(), error=ex,
                         class_name=_class_name, method_name=_method_name)
    return


def __close_domain_on_error():
    """
    An offline error recovery method.
    """
    _method_name = '__close_domain_on_error'
    try:
        __wlst_helper.close_domain()
    except PyWLSTException, pwe:
        # This method is only used for cleanup after an error so don't mask
        # the original problem by throwing yet another exception...
        __logger.warning('WLSDPLY-09084', pwe.getLocalizedMessage(), error=pwe,
                         class_name=_class_name, method_name=_method_name)
    return


def __clean_up_temp_files():
    """
    If a temporary directory was created to extract the model from the archive, delete the directory and its contents.
    """
    global __tmp_model_dir

    if __tmp_model_dir is not None:
        FileUtils.deleteDirectory(__tmp_model_dir)
        __tmp_model_dir = None


def main():
    """
    The python entry point for deployApps.
    """
    _method_name = 'main'

    __logger.entering(sys.argv[0], class_name=_class_name, method_name=_method_name)
    for index, arg in enumerate(sys.argv):
        __logger.finer('sys.argv[{0}] = {1}', str(index), str(arg), class_name=_class_name, method_name=_method_name)

    __wlst_helper.silence()

    try:
        model_context = __process_args(sys.argv)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != CommandLineArgUtil.HELP_EXIT_CODE:
            __logger.severe('WLSDPLY-09039', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(exit_code)

    model_file = model_context.get_model_file()
    try:
        model_dictionary = FileToPython(model_file, True).parse()
    except TranslateException, te:
        __logger.severe('WLSDPLY-09072', _program_name, model_file, te.getLocalizedMessage(), error=te,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    if model_context.get_variable_file():
        try:
            variable_map = variables.load_variables(model_context.get_variable_file())
            variables.substitute(model_dictionary, variable_map)
        except VariableException, ex:
            __logger.severe('WLSDPLY-09059', _program_name, ex.getLocalizedMessage(), error=ex,
                            class_name=_class_name, method_name=_method_name)
            __clean_up_temp_files()
            sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    try:
        model = Model(model_dictionary)
        __deploy(model, model_context)
    except DeployException, ex:
        __logger.severe('WLSDPLY-09060', _program_name, ex.getLocalizedMessage(), error=ex,
                        class_name=_class_name, method_name=_method_name)
        __clean_up_temp_files()
        sys.exit(CommandLineArgUtil.PROG_ERROR_EXIT_CODE)

    __clean_up_temp_files()
    return

if __name__ == "main":
    main()
