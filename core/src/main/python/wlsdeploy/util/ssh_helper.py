"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that handles SSH communication with remote machines.
"""
import os

from java.io import BufferedReader
from java.io import InputStreamReader
import java.io.IOException as IOException
import java.lang.Exception as JException
import java.lang.String as JString
import java.lang.System as JSystem

from oracle.weblogic.deploy.exception import BundleAwareException
from oracle.weblogic.deploy.util import SSHException
from oracle.weblogic.deploy.util import StringUtils

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.exception_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import getcreds
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util import path_helper
from wlsdeploy.util import string_utils
from wlsdeploy.util.ssh_command_line_helper import SSHUnixCommandLineHelper
from wlsdeploy.util.ssh_command_line_helper import SSHWindowsCommandLineHelper

__class_name = 'ssh_helper'
__logger = PlatformLogger('wlsdeploy.util')

def initialize_ssh(model_context, argument_map, exception_type=ExceptionType.SSH):
    _method_name = 'initialize_ssh'
    __logger.entering(exception_type, class_name=__class_name, method_name=_method_name)

    if model_context.get_ssh_host() is None:
        __logger.finest('WLSDPLY-32007', class_name=__class_name, method_name=_method_name)
        __logger.exiting(class_name=__class_name, method_name=_method_name)
        return
    elif not string_utils.is_java_version_or_above('1.8.0'):
        __logger.fine('WLSDPLY-32041', class_name=__class_name, method_name=_method_name)
        __logger.exiting(class_name=__class_name, method_name=_method_name)
        return

    __validate_ssh_arguments(argument_map, model_context)
    __ensure_ssh_credentials(model_context)

    import net.schmizz.sshj.common.SSHException as SSHJException
    try:
        ssh_context = SSHContext(model_context, exception_type)
    except (SSHException, SSHJException, JException),err:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32008',
                                                   err.getLocalizedMessage(), error=err)
        __logger.throwing(ex, method_name=_method_name, class_name=__class_name)
        raise ex

    model_context.set_ssh_context(ssh_context)
    __logger.exiting(class_name=__class_name, method_name=_method_name)


def __validate_ssh_arguments(argument_map, model_context):
    _method_name = '__validate_ssh_arguments'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    if model_context.get_program_name() != 'verifySSH':
        if CommandLineArgUtil.REMOTE_SWITCH in argument_map:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32039',
                CommandLineArgUtil.SSH_HOST_SWITCH, CommandLineArgUtil.REMOTE_SWITCH)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex
        elif not model_context.get_target_wlst_mode() == WlstModes.ONLINE:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32040')
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex

    has_password_args, password_arg_name = __has_ssh_user_password_args(argument_map)
    has_passphrase_args, passphrase_arg_name = __has_ssh_private_key_passphrase_args(argument_map)

    if has_password_args:
        if has_passphrase_args:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32011',
                                                       password_arg_name, passphrase_arg_name)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex
        elif CommandLineArgUtil.SSH_PRIVATE_KEY_SWITCH in argument_map:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32011',
                                                       password_arg_name, CommandLineArgUtil.SSH_PRIVATE_KEY_SWITCH)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex

    __logger.exiting(class_name=__class_name, method_name=_method_name)


def __ensure_ssh_credentials(model_context):
    _method_name = '__ensure_ssh_credentials'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    if model_context.is_ssh_pass_prompt():
        try:
            password = getcreds.getpass('WLSDPLY-32000')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32001',
                                                       ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex

        model_context.set_ssh_pass(str(JString(password)))

    if model_context.is_ssh_private_key_passphrase_prompt():
        try:
            password = getcreds.getpass('WLSDPLY-32002')
        except IOException, ioe:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32003',
                                                       ioe.getLocalizedMessage(), error=ioe)
            __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
            raise ex
        model_context.set_ssh_private_key_passphrase(str(JString(password)))

    __logger.exiting(class_name=__class_name, method_name=_method_name)


def __has_ssh_user_password_args(argument_map):
    _method_name = '__has_ssh_user_password_args'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    arg_list = []
    if CommandLineArgUtil.SSH_PASS_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PASS_SWITCH)
    if CommandLineArgUtil.SSH_PASS_ENV_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PASS_ENV_SWITCH)
    if CommandLineArgUtil.SSH_PASS_FILE_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PASS_FILE_SWITCH)
    if CommandLineArgUtil.SSH_PASS_PROMPT_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PASS_PROMPT_SWITCH)

    if len(arg_list) == 0:
        result = (False, None)
    elif len(arg_list) == 1:
        result = (True, arg_list[0])
    else:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32009', str(arg_list))
        __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=result)
    return result


def __has_ssh_private_key_passphrase_args(argument_map):
    _method_name = '__has_ssh_private_key_passphrase_args'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    arg_list = []
    if CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_SWITCH)
    if CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_ENV_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_ENV_SWITCH)
    if CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_FILE_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_FILE_SWITCH)
    if CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH in argument_map:
        arg_list.append(CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH)

    if len(arg_list) == 0:
        result = (False, None)
    elif len(arg_list) == 1:
        result = (True, arg_list[0])
    else:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32010', str(arg_list))
        __logger.throwing(ex, class_name=__class_name, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=__class_name, method_name=_method_name, result=result)
    return result


class SSHContext(object):
    _class_name = 'SSHContext'
    _logger = PlatformLogger('wlsdeploy.util')

    def __init__(self, model_context, exception_type):
        _method_name = '__init__'
        self._logger.entering(exception_type, class_name=self._class_name, method_name=_method_name)

        self._model_context = model_context
        self._exception_type = exception_type
        self._ssh_client = None
        try:
            self._ssh_client = self._connect()
        except IOException,err:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32038',
                                                       self._model_context.get_ssh_host(), err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._authenticate()
        self.is_windows = self._is_windows()
        if self.is_windows:
            self._os_helper = SSHWindowsCommandLineHelper()
        else:
            self._os_helper = SSHUnixCommandLineHelper()

        self.path_helper = path_helper.get_path_helper()

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def is_connected(self):
        return self._ssh_client is not None and self._ssh_client.isConnected()

    def is_authenticated(self):
        return self.is_connected() and self._ssh_client.isAuthenticated()

    def is_remote_system_running_windows(self):
        return self.is_windows

    def download(self, source_path, target_path):
        _method_name = 'download'
        self._logger.entering(source_path, target_path, class_name=self._class_name, method_name=_method_name)

        if StringUtils.isEmpty(source_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32012')
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif not self.path_helper.is_absolute_remote_path(source_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32013', source_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if StringUtils.isEmpty(target_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32014', source_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        abs_source_path = self.path_helper.get_remote_canonical_path(source_path)
        abs_target_path = self.path_helper.get_local_canonical_path(target_path).replace('\\', '/')

        try:
            remote_host = self._ssh_client.getRemoteHostname()
            self._logger.info('WLSDPLY-32016', abs_source_path, remote_host, abs_target_path,
                              class_name=self._class_name, method_name=_method_name)
            self._ssh_client.newSCPFileTransfer().download(abs_source_path, abs_target_path)
            self._logger.info('WLSDPLY-32017', abs_source_path, remote_host, abs_target_path,
                              class_name=self._class_name, method_name=_method_name)
        except IOException,ioe:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32015', abs_source_path,
                                                   abs_target_path, ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def upload(self, source_path, target_path):
        _method_name = 'upload'
        self._logger.entering(target_path, source_path, class_name=self._class_name, method_name=_method_name)

        if StringUtils.isEmpty(target_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32018')
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif not self.path_helper.is_absolute_remote_path(target_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32019', target_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if StringUtils.isEmpty(source_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32020', target_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        abs_source_path = self.path_helper.get_local_canonical_path(source_path).replace('\\', '/')
        abs_target_path = self.path_helper.get_remote_canonical_path(target_path)

        try:
            remote_host = self._ssh_client.getRemoteHostname()
            self._logger.info('WLSDPLY-32022', abs_source_path, remote_host, abs_target_path,
                              class_name=self._class_name, method_name=_method_name)
            self._ssh_client.newSCPFileTransfer().upload(abs_source_path, target_path)
            self._logger.info('WLSDPLY-32023', abs_source_path, remote_host, abs_target_path,
                              class_name=self._class_name, method_name=_method_name)
        except IOException,ioe:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32021', abs_source_path,
                                                   abs_target_path, ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def create_directories_if_not_exist(self, directory_path):
        _method_name = 'create_directories_if_not_exist'
        self._logger.entering(directory_path, class_name=self._class_name, method_name=_method_name)

        result = False
        if directory_path is not None and len(directory_path) > 0:
            command = self._os_helper.get_mkdirs_command(directory_path)
            exit_code, output_lines = self._run_exec_command(command)
            if exit_code == 0:
                result = True
            else:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32035', directory_path,
                    command, self._ssh_client.getRemoteHostname(), self._join_lines(output_lines))
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        else:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32036',
                                                   self._ssh_client.getRemoteHostname())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def remove_file_or_directory(self, path):
        _method_name = 'remove_file_or_directory'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = False
        if path is not None and len(path) > 0:
            # This is messy because Windows requires a path type-specific command
            if self.is_windows:
                if self.does_directory_exist(path):
                    command = self._os_helper.get_remove_dir_command(path)
                else:
                    command = self._os_helper.get_remove_file_command(path)
            else:
                command = self._os_helper.get_remove_command(path)

            exit_code, output_lines = self._run_exec_command(command)
            if exit_code == 0:
                result = True
            else:
                self._logger.severe('WLSDPLY-32033', path, command, self._ssh_client.getRemoteHostname(),
                                    self._join_lines(output_lines), class_name=self._class_name, method_name=_method_name)
        else:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32034',
                                                   self._ssh_client.getRemoteHostname())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def does_directory_exist(self, directory_path):
        _method_name = 'does_directory_exist'
        self._logger.entering(directory_path, class_name=self._class_name, method_name=_method_name)

        result = False
        if directory_path is not None and len(directory_path) > 0:
            command = self._os_helper.get_does_directory_exist_command(directory_path)
            exit_code, _ = self._run_exec_command(command)
            if exit_code == 0:
                result = True

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_directory_contents(self, directory_path, files_only=True, filtering_regex_pattern=None):
        _method_name = 'get_directory_contents'
        self._logger.entering(directory_path, files_only, filtering_regex_pattern,
                              class_name=self._class_name, method_name=_method_name)

        result = list()
        if directory_path is not None and len(directory_path) > 0:
            command = self._os_helper.get_directory_contents_command(directory_path)
            exit_code, output_lines = self._run_exec_command(command)
            if exit_code == 0:
                result = self._os_helper.get_directory_contents(output_lines, files_only, filtering_regex_pattern)
            else:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32024', directory_path,
                    command, self._ssh_client.getRemoteHostname(), self._join_lines(output_lines))
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        else:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32025',
                                                   self._ssh_client.getRemoteHostname())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def create_temp_directory_for_security_data_export(self):
        _method_name = 'create_temp_directory_for_security_data_export'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        user_name = JSystem.getProperty('user.name')
        ssh_user = self._model_context.get_ssh_user()
        if ssh_user is not None and ssh_user != '':
            user_name = ssh_user

        if self._is_windows():
            env_var = 'TEMP'
        else:
            env_var = 'TMPDIR'
        command = self._os_helper.get_environment_variable_command(env_var)
        exit_code, output_lines = self._run_exec_command(command)
        if exit_code == 0:
            result = self._os_helper.get_environment_variable_value(output_lines, env_var)
        else:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32042', env_var,
                command, self._ssh_client.getRemoteHostname(), self._join_lines(output_lines))
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if self._is_windows():
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32043', user_name, env_var,
                                                   self._ssh_client.getRemoteHostname())
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        else:
            if result is None or result == '':
                result = '/tmp'

        if self._is_windows():
            remote_tmp_dir = '%s\\%s\\' % (result, 'wdt_export_temp')
        else:
            remote_tmp_dir = '%s/%s_%s/' % (result, 'wdt_export_temp', user_name)

        if self.does_directory_exist(remote_tmp_dir):
            self.remove_file_or_directory(remote_tmp_dir)
        self.create_directories_if_not_exist(remote_tmp_dir)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=remote_tmp_dir)
        return remote_tmp_dir

    def connect(self):
        _method_name = 'connect'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        if not self.is_connected():
            self._ssh_client = self._connect()

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def disconnect(self):
        _method_name = 'disconnect'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        if self.is_connected():
            try:
                try:
                    self._ssh_client.disconnect()
                except IOException,err:
                    ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32008',
                                                           err.getLocalizedMessage(), error=err)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
            finally:
                self._ssh_client = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _connect(self):
        _method_name = '_connect'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        from net.schmizz.sshj import SSHClient

        ssh_client = SSHClient()
        if self._model_context.get_model_config().use_ssh_compression():
            ssh_client.useCompression()
        ssh_client.loadKnownHosts()

        host = self._model_context.get_ssh_host()
        port = self._model_context.get_ssh_port()
        if port is None:
            ssh_client.connect(host)
        else:
            ssh_client.connect(host, port)

        self._logger.exiting(result=ssh_client, class_name=self._class_name, method_name=_method_name)
        return ssh_client

    def _authenticate(self):
        _method_name = '_authenticate'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        if self._use_username_password_auth():
            self._username_password_auth()
        else:
            self._public_key_auth()

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _is_windows(self):
        _method_name = '_is_windows'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        result = False
        session = None
        host = self._model_context.get_ssh_host()
        try:
            #
            # uname command does not normally exist on Windows unless the shell
            # has Unix utilities installed, in which case it normally returns
            # the string Windows_NT.
            #
            exit_code, result_lines = self._run_exec_command('uname')
            if exit_code == 0:
                # May or may not be Windows.
                for result_line in result_lines:
                    if result_line.startswith('Windows'):
                        result = True
                        break
            else:
                # More than likely, it is Windows but let's make sure.
                exit_code, result_lines = self._run_exec_command('wmic os get caption')
                if exit_code == 0:
                    for result_line in result_lines:
                        if result_line.startswith('Microsoft Windows'):
                            result = True
                            break
                else:
                    ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32026',
                                                           host, self._join_lines(result_lines))
                    self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex
        except (IOException, BundleAwareException), error:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32027', host,
                                                   error.getLocalizedMessage(), error=error)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if result:
            key = 'WLSDPLY-32029'
        else:
            key = 'WLSDPLY-32030'

        self._logger.info(key, host, class_name=self._class_name, method_name=_method_name)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _use_username_password_auth(self):
        return self._model_context.get_ssh_pass() is not None

    def _username_password_auth(self):
        _method_name = '_username_password_auth'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        from net.schmizz.sshj.transport import TransportException
        from net.schmizz.sshj.userauth import UserAuthException
        user = self._model_context.get_ssh_user()
        passwd = self._model_context.get_ssh_pass()
        try:
            self._ssh_client.authPassword(user, passwd)
        except (UserAuthException, TransportException),err:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32004',
                                                   user, err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _public_key_auth(self):
        _method_name = '_public_key_auth'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        user = self._model_context.get_ssh_user()
        if self._model_context.is_ssh_default_private_key():
            if not self._model_context.is_ssh_private_key_encrypted():
                self._do_public_key_auth(user)
            else:
                key_path = self._get_default_private_key_path()
                passphrase = self._model_context.get_ssh_private_key_passphrase()
                key_provider = self._get_private_key_provider(key_path, passphrase)
                self._do_public_key_auth(user, key_provider)
        else:
            key_path = self._model_context.get_ssh_private_key()
            if not self._model_context.is_ssh_private_key_encrypted():
                self._do_public_key_auth(user, key_path)
            else:
                passphrase = self._model_context.get_ssh_private_key_passphrase()
                key_provider = self._get_private_key_provider(key_path, passphrase)
                self._do_public_key_auth(user, key_provider)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _get_default_private_key_path(self):
        _method_name = '_get_default_private_key_path'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        pk_file_name = self._model_context.get_model_config().get_ssh_private_key_default_file_name()
        pk_path = os.path.join(JSystem.getProperty('user.home'), '.ssh', pk_file_name)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=pk_path)
        return pk_path

    def _get_private_key_provider(self, key_path, passphrase):
        _method_name = '_get_private_key_provider'
        self._logger.entering(key_path, class_name=self._class_name, method_name=_method_name)

        import net.schmizz.sshj.common.SSHException as SSHJException
        try:
            if passphrase is not None:
                key_provider = self._ssh_client.loadKeys(key_path, passphrase)
            else:
                key_provider = self._ssh_client.loadKeys(key_path)
        except (SSHJException, IOException),err:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32006',
                                                   key_path, err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(result=key_provider, class_name=self._class_name, method_name=_method_name)
        return key_provider

    def _do_public_key_auth(self, user, key_arg=None):
        _method_name = '_do_public_key_auth'
        self._logger.entering(user, key_arg, class_name=self._class_name, method_name=_method_name)

        from net.schmizz.sshj.transport import TransportException
        from net.schmizz.sshj.userauth import UserAuthException
        try:
            if key_arg is not None:
                self._ssh_client.authPublickey(user, [ key_arg ])
            else:
                self._ssh_client.authPublickey(user)
        except (UserAuthException, TransportException),err:
            ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32005',
                                                   user, err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def _run_exec_command(self, command):
        _method_name = '_run_exec_command'
        self._logger.entering(command, class_name=self._class_name, method_name=_method_name)

        session = None
        host = self._model_context.get_ssh_host()
        try:
            try:
                session = self._ssh_client.startSession()
                cmd = session.exec(command)
                if cmd is None:
                    ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32031',
                                                           command, host)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                    raise ex

                output_lines = self._get_text_from_input_stream(cmd.getInputStream())
                error_lines = self._get_text_from_input_stream(cmd.getErrorStream())

                # Must close the session (and its underlying channel) prior to reading the exit status
                self._close_ssh_session(session)
                session = None
                exit_code = cmd.getExitStatus()
                error_signal = cmd.getExitSignal()
                error_message = cmd.getExitErrorMessage()
                if error_signal is not None and error_message is not None:
                    exit_code = -1
                    output_lines = [ error_message ]
                elif exit_code != 0 and len(error_lines) > 0:
                    output_lines = error_lines

            except IOException, ioe:
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32032',
                                                       command, host, ioe.getLocalizedMessage(), error=ioe)
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
        finally:
            self._close_ssh_session(session)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name,
                             result=(exit_code, output_lines))
        return exit_code, output_lines

    def _get_text_from_input_stream(self, input_stream):
        _method_name = '_get_text_from_input_stream'
        self._logger.entering(input_stream, class_name=self._class_name, method_name=_method_name)

        reader = None
        result = list()
        try:
            reader = BufferedReader(InputStreamReader(input_stream))
            while True:
                line = reader.readLine()
                if line is not None:
                    result.append(line)
                else:
                    break
        finally:
            if reader is not None:
                reader.close()

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result


    def _fix_directory_path(self, path):
        _method_name = '_fix_directory_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = path
        if self.is_windows:
            result = result.replace('/', '\\')
            if not result.endswith('\\'):
                result = '%s\\' % result
        elif not result.endswith('/'):
            result = '%s/' % result

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _close_ssh_session(self, session):
        _method_name = '_close_ssh_session'
        self._logger.entering(session, class_name=self._class_name, method_name=_method_name)

        if session is not None:
            try:
                session.close()
            except IOException, ioe:
                self._logger.finer('WLSDPLY-32028', ioe.getLocalizedMessage(), error=ioe)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _join_lines(self, lines):
        stripped_lines = list()
        if isinstance(lines, list):
            for line in lines:
                stripped_line = line.strip()
                if len(stripped_line) > 0:
                    stripped_lines.append(stripped_line)
        return '; '.join(stripped_lines)
