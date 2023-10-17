"""
Copyright (c) 2017, 2023, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that handles SSH communication with remote machines.
"""
import os

import java.io.IOException as IOException
import java.lang.Exception as JException
import java.lang.String as JString
import java.lang.System as JSystem
import java.lang.StringBuilder as StringBuilder
import java.util.concurrent.TimeUnit as TimeUnit

from net.schmizz.sshj import SSHClient
import net.schmizz.sshj.common.SSHException as SSHJException
from net.schmizz.sshj.transport import TransportException
from net.schmizz.sshj.userauth import UserAuthException

from oracle.weblogic.deploy.util import FileUtils
from oracle.weblogic.deploy.util import SSHException
from oracle.weblogic.deploy.util import StringUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.exception.expection_types import ExceptionType
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import getcreds
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.exit_code import ExitCode

__class_name = 'ssh_helper'
__logger = PlatformLogger('wlsdeploy.util')

def initialize_ssh(model_context, argument_map, exception_type=ExceptionType.SSH):
    _method_name = 'initialize_ssh'
    __logger.entering(class_name=__class_name, method_name=_method_name)

    if model_context.get_ssh_host() is None:
        __logger.finest('WLSDPLY-32007', class_name=__class_name, method_name=_method_name)
        __logger.exiting(class_name=__class_name, method_name=_method_name)
        return

    __validate_ssh_arguments(argument_map)
    __ensure_ssh_credentials(model_context)

    try:
        ssh_context = SSHContext(model_context, exception_type)
    except (SSHException, SSHJException, JException),err:
        ex = exception_helper.create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32008',
                                                   err.getLocalizedMessage(), error=err)
        __logger.throwing(ex, method_name=_method_name, class_name=__class_name)
        raise ex

    model_context.set_ssh_context(ssh_context)
    __logger.exiting(class_name=__class_name, method_name=_method_name)


def __validate_ssh_arguments(argument_map):
    _method_name = '__validate_ssh_arguments'
    __logger.entering(class_name=__class_name, method_name=_method_name)

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
            ex = exception_helper.create_exception(exception_type, ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32004',
                                                   err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._authenticate()

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def is_connected(self):
        return self._ssh_client is not None and self._ssh_client.isConnected()

    def is_authenticated(self):
        return self.is_connected() and self._ssh_client.isAuthenticated()

    def download(self, source_path, target_path):
        _method_name = 'download'
        self._logger.entering(source_path, target_path, class_name=self._class_name, method_name=_method_name)

        if StringUtils.isEmpty(source_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32012')
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif not FileUtils.isRemotePathAbsolute(source_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32013', source_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if StringUtils.isEmpty(target_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32014', source_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        abs_target_path = FileUtils.getCanonicalPath(target_path)

        try:
            remote_host = self._ssh_client.getRemoteHostname()
            self._logger.info('WLSDPLY-32016', source_path, remote_host, abs_target_path,
                              class_name=self._class_name, method_name=_method_name)
            self._ssh_client.newSCPFileTransfer().download(source_path, abs_target_path)
            self._logger.info('WLSDPLY-32017', source_path, remote_host, abs_target_path,
                              class_name=self._class_name, method_name=_method_name)
        except IOException,ioe:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32015', source_path, abs_target_path,
                                                   ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def upload(self, source_path, target_path):
        _method_name = 'upload'
        self._logger.entering(target_path, source_path, class_name=self._class_name, method_name=_method_name)

        if StringUtils.isEmpty(target_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32018')
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        elif not FileUtils.isRemotePathAbsolute(target_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32019', target_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        if StringUtils.isEmpty(source_path):
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32020', target_path)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        abs_source_path = FileUtils.getCanonicalPath(source_path)

        try:
            remote_host = self._ssh_client.getRemoteHostname()
            self._logger.info('WLSDPLY-32022', abs_source_path, remote_host, target_path,
                              class_name=self._class_name, method_name=_method_name)
            self._ssh_client.newSCPFileTransfer().upload(abs_source_path, target_path)
            self._logger.info('WLSDPLY-32023', abs_source_path, remote_host, target_path,
                              class_name=self._class_name, method_name=_method_name)
        except IOException,ioe:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32021', abs_source_path, target_path,
                                                   ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def remote_command(self, command):
        _method_name = 'remote_command'
        self._logger.entering(command, class_name=self._class_name, method_name=_method_name)

        if StringUtils.isEmpty(command):
            return
        try:
            session = self._ssh_client.startSession()
            self._logger.info('WLSDPLY-32024', command,
                              class_name=self._class_name, method_name=_method_name)
            cmd = session.exec(command)
            ins = cmd.getInputStream()
            result = StringBuilder()
            while True:
                c = ins.read()
                if c == -1:
                    break
                else:
                    result.append(chr(c))

            self._logger.info('WLSDPLY-32025', str(cmd.getExitStatus()),
                              class_name=self._class_name, method_name=_method_name)
            session.close()
            return result.toString()
        except IOException,ioe:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-32021', abs_source_path, target_path,
                                                   ioe.getLocalizedMessage(), error=ioe)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

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

    def _use_username_password_auth(self):
        return self._model_context.get_ssh_pass() is not None

    def _username_password_auth(self):
        _method_name = '_username_password_auth'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        user = self._model_context.get_ssh_user()
        passwd = self._model_context.get_ssh_pass()
        try:
            self._ssh_client.authPassword(user, passwd)
        except (UserAuthException, TransportException),err:
            ex = exception_helper.create_exception(self._exception_type, ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32004',
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

        try:
            if passphrase is not None:
                key_provider = self._ssh_client.loadKeys(key_path, passphrase)
            else:
                key_provider = self._ssh_client.loadKeys(key_path)
        except (SSHJException, IOException),err:
            ex = exception_helper.create_exception(self._exception_type, ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32006',
                                                   key_path, err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

        self._logger.exiting(result=key_provider, class_name=self._class_name, method_name=_method_name)
        return key_provider

    def _do_public_key_auth(self, user, key_arg=None):
        _method_name = '_do_public_key_auth'
        self._logger.entering(user, key_arg, class_name=self._class_name, method_name=_method_name)

        try:
            if key_arg is not None:
                self._ssh_client.authPublickey(user, [ key_arg ])
            else:
                self._ssh_client.authPublickey(user)
        except (UserAuthException, TransportException),err:
            ex = exception_helper.create_exception(self._exception_type, ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-32005',
                                                   user, err.getLocalizedMessage(), error=err)
            self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
