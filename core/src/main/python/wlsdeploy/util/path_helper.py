"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import ntpath
import os
import posixpath

from java.io import File

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import env_helper
from wlsdeploy.util import string_utils

__path_helper = None


def initialize_path_helper(exception_type, unit_test_force=False, unit_test_is_windows=False):
    """
    Initialize the path helper singleton with the local file system type.
    :param exception_type: the exception type for the executing tool
    :param unit_test_force: force reinitialization for unit testing
    :param unit_test_is_windows: unit test is for windows
    :return:
    """
    global __path_helper
    if __path_helper is None or unit_test_force:
        __path_helper = PathHelper(exception_type, unit_test_is_windows)


def get_path_helper():
    global __path_helper
    return __path_helper


def set_remote_file_system_from_oracle_home(remote_oracle_home):
    """
    Set the remote file system based on the remote Oracle Home path.
    :param remote_oracle_home: the remote Oracle Home path
    :param unit_test_force: force reinitialization for unit testing
    """
    global __path_helper

    if __path_helper is not None and not string_utils.is_empty(remote_oracle_home):
        __path_helper.set_remote_path_module('\\' in remote_oracle_home)


class PathHelper(object):
    _logger = PlatformLogger('wlsdeploy.util')
    _class_name = 'PathHelper'

    WINDOWS = 'Windows'
    POSIX = 'Posix'

    WLSDEPLOY_HOME_VARIABLE = 'WLSDEPLOY_HOME'
    OLD_CUSTOM_CONFIG_VARIABLE = 'WDT_CUSTOM_CONFIG'
    CUSTOM_CONFIG_VARIABLE = 'WLSDEPLOY_CUSTOM_CONFIG'

    def __init__(self, exception_type, is_windows=False):
        """
        Constructor
        :param exception_type: the exception type for the executing tool
        :param is_windows: For unit-tests only to override platform for testing
        """
        _method_name = '__init__'
        self._logger.entering(exception_type, class_name=self._class_name, method_name=_method_name)

        self._exception_type = exception_type
        self._remote_path_module = None
        self._remote_path_type = None

        if is_windows or File.separator == '\\':
            self._local_path_module = ntpath
            self._local_path_type = self.WINDOWS
        else:
            self._local_path_module = posixpath
            self._local_path_type = self.POSIX
        self._logger.info('WLSDPLY-02100', self._local_path_type,
                          class_name=self._class_name, method_name=_method_name)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def set_remote_path_module(self, is_windows):
        """
        Initialize the remote path module once the OS of the remote system is known.
        :param is_windows: Whether the remote OS is running Windows or not
        """
        _method_name = 'set_remote_path_module'
        self._logger.entering(is_windows, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is None:
            if is_windows:
                self._remote_path_module = ntpath
                self._remote_path_type = self.WINDOWS
            else:
                self._remote_path_module = posixpath
                self._remote_path_type = self.POSIX
            self._logger.info('WLSDPLY-02101', self._remote_path_type,
                              class_name=self._class_name, method_name=_method_name)
        else:
            if self._remote_path_type == self.WINDOWS is not is_windows:
                if is_windows:
                    new_type = self.WINDOWS
                else:
                    new_type = self.POSIX
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02102',
                                                       self._remote_path_type, new_type)
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            else:
                self._logger.fine('WLSDPLY-02103', self._remote_path_type,
                                  class_name=self._class_name, method_name=_method_name)
        self._logger.exiting(class_name=self._class_name, method_name=_method_name)


    def join(self, *paths):
        _method_name = 'join'
        self._logger.entering(paths, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.remote_join(*paths)
        else:
            result = self.local_join(*paths)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def local_join(self, *paths):
        _method_name = 'local_join'
        self._logger.entering(paths, class_name=self._class_name, method_name=_method_name)

        result = self._local_path_module.join(*paths)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result


    def remote_join(self, *paths):
        _method_name = 'remote_join'
        self._logger.entering(paths, class_name=self._class_name, method_name=_method_name)

        result = self._remote_path_module.join(*paths)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def split(self, path):
        _method_name = 'split'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            path_name, file_or_dir_name = self.remote_split(path)
        else:
            path_name, file_or_dir_name = self.local_split(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=[path_name, file_or_dir_name])
        return path_name, file_or_dir_name

    def local_split(self, path):
        _method_name = 'local_split'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        path_name = None
        file_or_dir_name = None
        if not string_utils.is_empty(path):
            path_name, file_or_dir_name = self._local_path_module.split(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=[path_name, file_or_dir_name])
        return path_name, file_or_dir_name

    def remote_split(self, path):
        _method_name = 'remote_split'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        path_name = None
        file_or_dir_name = None
        if not string_utils.is_empty(path):
            path_name, file_or_dir_name = self._remote_path_module.split(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=[path_name, file_or_dir_name])
        return path_name, file_or_dir_name

    def basename(self, path):
        _method_name = 'basename'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.remote_basename(path)
        else:
            result = self.local_basename(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def local_basename(self, path):
        _method_name = 'local_basename'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = None
        if not string_utils.is_empty(path):
            result = self._local_path_module.basename(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def remote_basename(self, path):
        _method_name = 'remote_basename'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        result = None
        if not string_utils.is_empty(path):
            result = self._remote_path_module.basename(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def fixup_path(self, path, relative_to=None):
        _method_name = 'fixup_path'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.fixup_remote_path(path, relative_to)
        else:
            result = self.fixup_local_path(path, relative_to)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def fixup_local_path(self, path, relative_to=None):
        _method_name = 'fixup_local_path'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        result = self._fixup_path_internal(self._local_path_module, path, relative_to)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def fixup_remote_path(self, path, relative_to=None):
        _method_name = 'fixup_remote_path'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        result = self._fixup_path_internal(self._remote_path_module, path, relative_to)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_canonical_path(self, path, relative_to=None):
        _method_name = 'get_canonical_path'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.get_remote_canonical_path(path, relative_to)
        else:
            result = self.get_local_canonical_path(path, relative_to)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_local_canonical_path(self, path, relative_to=None):
        _method_name = 'get_local_canonical_path'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        result = path
        if not string_utils.is_empty(path):
            if not self._local_path_module.isabs(path) and not string_utils.is_empty(relative_to):
                result = self._local_path_module.join(relative_to, path)
            result = self._local_path_module.realpath(result)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_remote_canonical_path(self, path, relative_to=None):
        _method_name = 'get_remote_canonical_path'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        result = path
        if not string_utils.is_empty(path):
            if not self._remote_path_module.isabs(path) and not string_utils.is_empty(relative_to):
                result = self._remote_path_module.join(relative_to, path)
            result = self._remote_path_module.realpath(result)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_parent_directory(self, path):
        _method_name = 'get_parent_directory'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.get_remote_parent_directory(path)
        else:
            result = self.get_local_parent_directory(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_local_parent_directory(self, path):
        _method_name = 'get_local_parent_directory'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = path
        if not string_utils.is_empty(path):
            if not self._local_path_module.isabs(path):
                result = self._local_path_module.abspath(path)
            result = self._local_path_module.dirname(result)
            if string_utils.is_empty(result):
                result = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_remote_parent_directory(self, path):
        _method_name = 'get_remote_parent_directory'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        result = path
        if not string_utils.is_empty(path):
            if not self._remote_path_module.isabs(path):
                ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02107', path)
                self._logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex
            result = self._remote_path_module.dirname(path)
            if string_utils.is_empty(result):
                result = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_absolute_path(self, path):
        _method_name = 'is_absolute_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.is_absolute_remote_path(path)
        else:
            result = self.is_absolute_local_path(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_absolute_local_path(self, path):
        _method_name = 'is_absolute_local_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = self._is_absolute_path_internal(self._local_path_module, path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_absolute_remote_path(self, path):
        _method_name = 'is_absolute_remote_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        result = self._is_absolute_path_internal(self._remote_path_module, path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_relative_path(self, path):
        _method_name = 'is_relative_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.is_relative_remote_path(path)
        else:
            result = self.is_relative_local_path(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_relative_local_path(self, path):
        _method_name = 'is_relative_local_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = not self._is_absolute_path_internal(self._local_path_module, path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_relative_remote_path(self, path):
        _method_name = 'is_relative_remote_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)
        result = not self._is_absolute_path_internal(self._remote_path_module, path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_filename_from_path(self, path):
        _method_name = 'get_filename_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.get_remote_filename_from_path(path)
        else:
            result = self.get_local_filename_from_path(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_local_filename_from_path(self, path):
        _method_name = 'get_local_filename_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        file_name = None

        # posixpath.isfile() seems to not work in Jython 2.2.1 even though os.path.isfile() does...
        if not string_utils.is_empty(path) and \
                (not self._local_path_module.exists(path) or os.path.isfile(path)):
            __, file_name = self._local_path_module.split(path)
            self._logger.fine('file_name returned %s' % file_name, class_name=self._class_name, method_name=_method_name)
            if string_utils.is_empty(file_name):
                file_name = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=file_name)
        return file_name

    def get_remote_filename_from_path(self, path):
        _method_name = 'get_remote_filename_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)

        file_name = None
        # Cannot use the isfile() method check since it requires direct access to the file system.
        if not string_utils.is_empty(path):
            __, file_name = self._remote_path_module.split(path)
            if string_utils.is_empty(file_name):
                file_name = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=file_name)
        return file_name

    #
    # No current need for a generic or remote version of get_pathname_from_path()
    #

    def get_local_pathname_from_path(self, path):
        _method_name = 'get_local_pathname_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        file_path = None
        # posixpath.isfile() seems to not work in Jython 2.2.1 even though os.path.isfile() does...
        if not string_utils.is_empty(path) and \
                (not self._local_path_module.exists(path) or os.path.isfile(path)):
            file_path, __ = self._local_path_module.split(path)
            if string_utils.is_empty(file_path):
                file_path = None

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=file_path)
        return file_path

    def get_filename_no_ext_from_path(self, path):
        _method_name = 'get_filename_no_ext_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            file_name = self.get_remote_filename_no_ext_from_path(path)
        else:
            file_name = self.get_local_filename_no_ext_from_path(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=file_name)
        return file_name

    def get_local_filename_no_ext_from_path(self, path):
        _method_name = 'get_local_filename_no_ext_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        file_name = None
        file_name_ext = self.get_local_filename_from_path(path)
        if not string_utils.is_empty(file_name_ext):
            file_name, __ = self._local_path_module.splitext(file_name_ext)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=file_name)
        return file_name

    def get_remote_filename_no_ext_from_path(self, path):
        _method_name = 'get_remote_filename_no_ext_from_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)

        file_name = None
        file_name_ext = self.get_remote_filename_from_path(path)
        if not string_utils.is_empty(file_name_ext):
            file_name, __ = self._remote_path_module.splitext(file_name_ext)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=file_name)
        return file_name

    def is_jar_file(self, path):
        _method_name = 'is_jar_file'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        if self._remote_path_module is not None:
            result = self.is_remote_jar_file(path)
        else:
            result = self.is_local_jar_file(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_local_jar_file(self, path):
        _method_name = 'is_local_jar_file'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = False
        if not string_utils.is_empty(path):
            file_name_ext = self.get_local_filename_from_path(path)
            if not string_utils.is_empty(file_name_ext):
                __, ext = self._local_path_module.splitext(file_name_ext)
                if not string_utils.is_empty(ext):
                    result = ext.lower() == '.jar'

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def is_remote_jar_file(self, path):
        _method_name = 'is_remote_jar_file'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)

        result = False
        if not string_utils.is_empty(path):
            file_name_ext = self.get_remote_filename_from_path(path)
            if not string_utils.is_empty(file_name_ext):
                __, ext = self._remote_path_module.splitext(file_name_ext)
                if not string_utils.is_empty(ext):
                    result = ext.lower() == '.jar'

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def get_local_wls_deploy_path(self):
        return env_helper.getenv(self.WLSDEPLOY_HOME_VARIABLE, None)

    # TODO - This method uses os.path directly due to unit test failures.
    #
    def find_local_config_path(self, path):
        _method_name = 'find_local_config_path'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        custom_config_dir = env_helper.getenv(self.CUSTOM_CONFIG_VARIABLE)
        if string_utils.is_empty(custom_config_dir):
            custom_config_dir = env_helper.getenv(self.OLD_CUSTOM_CONFIG_VARIABLE)
            if not string_utils.is_empty(custom_config_dir):
                self._logger.deprecation('WLSDPLY-02104', self.OLD_CUSTOM_CONFIG_VARIABLE,
                                         self.CUSTOM_CONFIG_VARIABLE,
                                         class_name=self._class_name, method_name=_method_name)
        result = None
        if not string_utils.is_empty(custom_config_dir):
            custom_file_path = os.path.join(custom_config_dir, path)
            if os.path.isfile(custom_file_path):
                self._logger.info('WLSDPLY-02105', custom_file_path,
                                  class_name=self._class_name, method_name=_method_name)
                result = custom_file_path

        if result is None:
            wls_deploy_path = env_helper.getenv(self.WLSDEPLOY_HOME_VARIABLE, '')
            result = os.path.join(wls_deploy_path, 'lib', path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def download_file_from_remote_server(self, model_context, remote_source_path, local_download_root_directory, file_type):
        _method_name = 'download_file_from_remote_server'
        self._logger.entering(remote_source_path, local_download_root_directory, file_type,
                              class_name=self._class_name, method_name=_method_name)

        self._verify_remote_path_module(_method_name)

        return_path = None
        if not string_utils.is_empty(remote_source_path):
            download_file_or_dir_name = self._remote_path_module.basename(remote_source_path)
            download_target_path = self._local_path_module.join(local_download_root_directory, file_type)
            if not self._local_path_module.exists(download_target_path):
                os.makedirs(download_target_path)

            return_path = \
                self._local_path_module.join(local_download_root_directory, file_type, download_file_or_dir_name)
            model_context.get_ssh_context().download(remote_source_path, download_target_path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=return_path)
        return return_path

    ###################################################################################
    #                              Internal methods                                   #
    ###################################################################################

    def _verify_remote_path_module(self, calling_method_name):
        if self._remote_path_module is None:
            ex = exception_helper.create_exception(self._exception_type, 'WLSDPLY-02106', calling_method_name)
            self._logger.throwing(ex, class_name=self._class_name, method_name=calling_method_name)
            raise ex

    def _fixup_path_internal(self, path_module, path, relative_to):
        _method_name = '_fixup_path_internal'
        self._logger.entering(path, relative_to, class_name=self._class_name, method_name=_method_name)

        result = path
        if not string_utils.is_empty(path):
            if path_module.isabs(path):
                result = path_module.realpath(path)
            elif relative_to is not None:
                result = path_module.join(relative_to, path)
            result = result.replace('\\', '/')

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _is_absolute_path_internal(self, path_module, path):
        _method_name = '_is_absolute_path_internal'
        self._logger.entering(path, class_name=self._class_name, method_name=_method_name)

        result = not string_utils.is_empty(path) and path_module.isabs(path)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result
