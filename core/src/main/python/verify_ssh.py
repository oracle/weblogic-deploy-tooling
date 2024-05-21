"""
Copyright (c) 2023, 2024, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

The main module for the WebLogic Deploy tool to verify the user's SSH configuration is compatible with WDT.
"""
import os
import sys

from oracle.weblogic.deploy.util import SSHException

sys.path.insert(0, os.path.dirname(os.path.realpath(sys.argv[0])))

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.util import model_context_helper
from wlsdeploy.tool.util import wlst_helper
from wlsdeploy.tool.util.wlst_helper import WlstHelper
from wlsdeploy.util import path_helper
from wlsdeploy.util import tool_main
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.cla_utils import TOOL_TYPE_DEFAULT
from wlsdeploy.util.exit_code import ExitCode

wlst_helper.wlst_functions = globals()

_program_name = 'verifySSH'

_class_name = 'verify_ssh'
__logger = PlatformLogger('wlsdeploy.tool.util')

__required_arguments = [
    CommandLineArgUtil.ORACLE_HOME_SWITCH,
    CommandLineArgUtil.SSH_HOST_SWITCH
]

__optional_arguments = [
    CommandLineArgUtil.LOCAL_TEST_FILE_SWITCH,
    CommandLineArgUtil.REMOTE_TEST_FILE_SWITCH,
    CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH,
    CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH,
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
]


def __process_args(args, is_encryption_supported):
    """
    Process the command-line arguments and prompt the user for any missing information
    :param args: the command-line arguments list
    :param is_encryption_supported: whether WDT encryption is supported by the JVM
    :raises CLAException: if an error occurs while validating and processing the command-line arguments
    """
    cla_util = CommandLineArgUtil(_program_name, __required_arguments, __optional_arguments)
    combined_argument_map = cla_util.process_args(args, TOOL_TYPE_DEFAULT)
    __ensure_upload_download_args(combined_argument_map)
    return model_context_helper.create_context(_program_name, combined_argument_map)


def __ensure_upload_download_args(argument_map):
    _method_name = '__ensure_upload_download_args'

    if CommandLineArgUtil.REMOTE_TEST_FILE_SWITCH in argument_map:
        if CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH not in argument_map:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32900',
                                                       argument_map[CommandLineArgUtil.REMOTE_TEST_FILE_SWITCH])
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH in argument_map:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32901',
                                                   argument_map[CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH])
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    if CommandLineArgUtil.LOCAL_TEST_FILE_SWITCH in argument_map:
        if CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH not in argument_map:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32902',
                                                       argument_map[CommandLineArgUtil.LOCAL_TEST_FILE_SWITCH])
            __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
            raise ex
    elif CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH in argument_map:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32902',
                                                   argument_map[CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH])
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex


def __do_test_download(model_context):
    _method_name = '__do_test_download'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    remote_path = model_context.get_remote_test_file()
    if remote_path is None:
        return

    local_path = model_context.get_local_output_dir()
    model_context.get_ssh_context().download(remote_path, local_path)


def __do_test_upload(model_context):
    _method_name = '__do_test_upload'
    __logger.entering(class_name=_class_name, method_name=_method_name)

    local_path = model_context.get_local_test_file()
    if local_path is None:
        return

    remote_path = model_context.get_remote_output_dir()
    model_context.get_ssh_context().upload(local_path, remote_path)


def __initialize_remote_path_helper(model_context):
    _method_name = '__initialize_remote_path_helper'
    _path_helper = path_helper.get_path_helper()
    ssh_context = model_context.get_ssh_context()
    if path_helper is None:
        ex = exception_helper.create_ssh_exception('WLSDPLY-32905')
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex
    elif ssh_context is None:
        ex = exception_helper.create_ssh_exception('WLSDPLY-32906')
        __logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    _path_helper.set_remote_path_module(ssh_context.is_remote_system_running_windows())

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
        __initialize_remote_path_helper(model_context)
        __do_test_download(model_context)
        __do_test_upload(model_context)
    except SSHException,ex:
        __logger.severe('WLSDPLY-32904', _program_name, ex.getLocalizedMessage(),
                        error=ex, class_name=_class_name, method_name=_method_name)
        _exit_code = ExitCode.ERROR

    __logger.exiting(class_name=_class_name, method_name=_method_name, result=_exit_code)
    return _exit_code


if __name__ == '__main__' or __name__ == 'main':
    tool_main.run_tool(main, __process_args, sys.argv, _program_name, _class_name, __logger)
