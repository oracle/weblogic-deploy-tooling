"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import exceptions
import sys
import traceback

from java.lang import Exception as JException
from java.util.logging import Level as JLevel

from oracle.weblogic.deploy.logging import DeprecationLevel
from oracle.weblogic.deploy.logging import WLSDeployLoggingConfig
from oracle.weblogic.deploy.logging import WLSDeployLogEndHandler
from oracle.weblogic.deploy.util import CLAException
from oracle.weblogic.deploy.util import WebLogicDeployToolingVersion
from oracle.weblogic.deploy.util import WLSDeployExit
from oracle.weblogic.deploy.util import WLSDeployContext
import oracle.weblogic.deploy.util.WLSDeployContext.WLSTMode as JWLSTMode

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.util import cla_helper
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode


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

    WebLogicDeployToolingVersion.logVersionInfo(program_name)
    WLSDeployLoggingConfig.logLoggingDirectory(program_name)

    logger.entering(args[0], class_name=class_name, method_name=_method_name)
    for index, arg in enumerate(args):
        logger.finer('sys.argv[{0}] = {1}', str_helper.to_string(index), str_helper.to_string(arg),
                     class_name=class_name, method_name=_method_name)

    model_context_obj = model_context_helper.create_exit_context(program_name)
    try:
        model_context_obj = process_args(args)
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
    if model_context:
        program = model_context.get_program_name()
        version = model_context.get_target_wls_version()
        use_deprecation_exit_code = model_context.get_model_config().get_use_deprecation_exit_code()
        if model_context.get_target_wlst_mode() == WlstModes.ONLINE:
            tool_mode = JWLSTMode.ONLINE

    exit_code = __get_summary_handler_exit_code(exit_code, use_deprecation_exit_code)

    WLSDeployExit.exit(WLSDeployContext(program, version, tool_mode), exit_code)


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
