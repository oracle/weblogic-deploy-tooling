"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import exceptions
import sys
import traceback

from java.lang import Exception as JException
from java.lang import System as JSystem
from java.util.logging import Level as JLevel

from oracle.weblogic.deploy.aliases import VersionUtils
from oracle.weblogic.deploy.encrypt import EncryptionUtils
from oracle.weblogic.deploy.logging import DeprecationLevel
from oracle.weblogic.deploy.logging import WLSDeployLoggingConfig
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import ExitCode
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.util import WLSDeployExit
from oracle.weblogic.deploy.util import WLSDeployContext
import oracle.weblogic.deploy.util.WLSDeployContext.WLSTMode as JWLSTMode

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import cla_helper
from wlsdeploy.util import path_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode

_class_name = 'tool_main'
_java_version = JSystem.getProperty('java.version')
_os_name = JSystem.getProperty('os.name')
_os_arch = JSystem.getProperty('os.arch')
_os_version = JSystem.getProperty('os.version')

_wdt_log_config_class_name = 'oracle.weblogic.deploy.logging.WLSDeployLoggingConfig'

def run_tool(main, process_args, args, program_name, class_name, logger):
    """
    The standardized entry point into each tool.

    :param main: main function of the tool
    :param process_args: parse_args function that returns the model_context object
    :param args: sys.argv value
    :param program_name: the name of the tool that was invoked
    :param class_name: the name of the tool class for the log file entry
    :param logger: the logger configured for the tool
    """
    _method_name = 'main'

    __assertWebLogicDeployToolingLoggingIsConfigured(program_name)

    WebLogicDeployToolingVersion.logVersionInfo(program_name)
    WLSDeployLoggingConfig.logLoggingDirectory(program_name)
    logger.info('WLSDPLY-20043', args[0], _java_version, __format_os_version(),
                class_name=class_name, method_name=_method_name)

    logger.entering(args[0], class_name=class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        logger.finer('sys.argv[{0}] = {1}', str_helper.to_string(index), str_helper.to_string(arg),
                     class_name=class_name, method_name=_method_name)

    is_encryption_supported = EncryptionUtils.isEncryptionSupported()
    if is_encryption_supported:
        logger.info('WLSDPLY-20044', args[0], class_name=class_name, method_name=_method_name)
    else:
        logger.info('WLSDPLY-20045', args[0], class_name=class_name, method_name=_method_name)

    __initialize_path_helper(program_name)
    model_context_obj = model_context_helper.create_exit_context(program_name)
    try:
        model_context_obj = process_args(args, is_encryption_supported=is_encryption_supported)
        __update_model_context(model_context_obj, logger, is_encryption_supported)
        exit_code = main(model_context_obj)
    except CLAException, ex:
        exit_code = ex.getExitCode()
        if exit_code != ExitCode.HELP and exit_code != ExitCode.OK:
            logger.severe('WLSDPLY-20008', program_name, ex.getLocalizedMessage(),
                          error=ex, class_name=class_name, method_name=_method_name)
        # Fall through
    except exceptions.SystemExit, ex:
        cla_helper.clean_up_temp_files()
        raise ex
    except (exceptions.Exception, JException), ex:
        exit_code = ExitCode.ERROR
        __handle_unexpected_exception(ex, model_context_obj, class_name, _method_name, logger)

    cla_helper.clean_up_temp_files()
    __exit_tool(model_context_obj, exit_code)

def __assertWebLogicDeployToolingLoggingIsConfigured(program_name):
    log_config_class_name = JSystem.getProperty('java.util.logging.config.class')

    err_message = None
    if log_config_class_name is None:
        err_message = 'The WebLogic Deploy Tooling logging configuration class was not defined...%s will exit' \
                      % program_name
    elif str_helper.to_string(log_config_class_name) != _wdt_log_config_class_name:
        err_message = 'The WebLogic Deploy Tooling logging configuration class was overridden with %s...%s will exit' \
                      % (log_config_class_name, program_name)

    if err_message is not None:
        JSystem.err.println(err_message)
        JSystem.exit(ExitCode.ERROR)


def __format_os_version():
    return '%s %s (%s)' % (_os_name, _os_version, _os_arch)


def __initialize_path_helper(program_name):
    path_helper.initialize_path_helper(exception_helper.get_exception_type_from_program_name(program_name))


def __update_model_context(model_context, logger, encryption_supported):
    if not model_context.is_initialization_complete():
        remote_version, remote_oracle_home = __get_remote_server_version_and_oracle_home(model_context, logger)
        model_context.complete_initialization(remote_version, remote_oracle_home)
    elif model_context.get_program_name() == 'createDomain':
        # createDomain needs access to the rcuSchemas list from the typedef during process_args.
        # Since createDomain is always a local operation, re-initialization after process_args completes.
        model_context.get_domain_typedef().finish_initialization(model_context)
    model_context.set_encryption_supported(encryption_supported)

def __get_remote_server_version_and_oracle_home(model_context, logger):
    _method_name = '__check_remote_server_version'
    logger.entering(class_name=_class_name, method_name=_method_name)

    admin_url = model_context.get_admin_url()
    result = None
    remote_oracle_home = None
    if admin_url is not None:
        admin_user = model_context.get_admin_user()
        admin_pass = model_context.get_admin_password()
        timeout = model_context.get_model_config().get_connect_timeout()

        from wlsdeploy.tool.util.wlst_helper import WlstHelper
        wlst_helper = WlstHelper(ExceptionType.CLA)
        wlst_helper.silence()
        version_string, patch_list_array, remote_oracle_home = \
            wlst_helper.get_online_server_version_data(admin_user, admin_pass, admin_url, timeout)
        result = VersionUtils.getWebLogicVersion(version_string)
        logger.fine('WLSDPLY-20023', result, version_string, class_name=_class_name, method_name=_method_name)
        if result is not None:
            if patch_list_array is not None:
                psu = VersionUtils.getPSUVersion(patch_list_array)
                logger.fine('WLSDPLY-20039', psu, ",".join(patch_list_array),
                            class_name=_class_name, method_name=_method_name)
                if psu is not None:
                    result = "%s.%s" % (result, psu)

    if result is not None:
        logger.info('WLSDPLY-20040', result, class_name=_class_name, method_name=_method_name)
    logger.exiting(class_name=_class_name, method_name=_method_name, result=result)
    return result, remote_oracle_home

def __exit_tool(model_context, exit_code):
    """
    Private method for use only within this module.

    :param model_context: tool python context
    :param exit_code: for completion of tool
    """
    program = None
    version = None
    use_deprecation_exit_code = None
    tool_mode = JWLSTMode.OFFLINE
    is_remote = False
    remote_wl_version = None
    if model_context:
        program = model_context.get_program_name()
        version = model_context.get_local_wls_version()
        use_deprecation_exit_code = model_context.get_model_config().get_use_deprecation_exit_code()
        if model_context.get_target_wlst_mode() == WlstModes.ONLINE:
            tool_mode = JWLSTMode.ONLINE
            is_remote = True
            remote_wl_version = model_context.get_remote_wls_version()

    exit_code = __get_summary_handler_exit_code(exit_code, use_deprecation_exit_code)

    WLSDeployExit.exit(WLSDeployContext(program, version, tool_mode, is_remote, remote_wl_version), exit_code)


def __handle_unexpected_exception(ex, model_context, class_name, method_name, logger):
    """
    Private method for use only within this module.

    Helper method to log and unexpected exception with exiting message and call sys.exit()
    Note that the user sees the 'Unexpected' message along with the exception, but no stack trace.
    The stack trace goes to the log
    :param ex:  the exception thrown
    :param model_context: the context object
    :param class_name: the class where it occurred
    :param logger: the logger to use
    """
    program_name = model_context.get_program_name()
    logger.severe('WLSDPLY-20035', program_name, sys.exc_info()[0], error=ex,
                  class_name=class_name, method_name=method_name)

    if hasattr(ex, 'stackTrace'):
        # this works best for java exceptions, and gets the full stacktrace all the way back to weblogic.WLST
        logger.fine('WLSDPLY-20036', program_name, ex.stackTrace, class_name=class_name, method_name=method_name,
                    error=ex)
    else:
        # this is for Python exceptions
        # Note: since this is Python 2, it seems we can only get the traceback object via sys.exc_info,
        # and of course only while in the except block handling code
        logger.fine('WLSDPLY-20036', program_name, traceback.format_exception(type(ex), ex, sys.exc_info()[2]),
                    class_name=class_name, method_name=method_name, error=ex)


def __get_summary_handler_exit_code(program_exit_code, use_deprecation_exit_code):
    """
    Private method for use only within this module.

    Helper method to get the proper tool exit code based on the exit code from the tool and the number
    of errors and warnings from the summary log handler.
    :param program_exit_code: the exit code from the tool
    :param use_deprecation_exit_code: whether to use the non-zero exit code for deprecations
    :return: the exit code to use
    """
    if program_exit_code != ExitCode.OK:
        return program_exit_code

    exit_code = ExitCode.OK
    summary_handler = WLSDeployLogEndHandler.getSummaryHandler()
    if summary_handler is not None:
        if summary_handler.getMessageCount(JLevel.SEVERE) > 0:
            exit_code = ExitCode.ERROR
        elif summary_handler.getMessageCount(JLevel.WARNING) > 0:
            exit_code = ExitCode.WARNING
        elif use_deprecation_exit_code == 'true' and \
            summary_handler.getMessageCount(DeprecationLevel.DEPRECATION) > 0:
            exit_code = ExitCode.DEPRECATION

    return exit_code
