"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.  All rights reserved.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

import java.io.File as JFile

import oracle.weblogic.deploy.util.StringUtils as JStringUtils
from wlsdeploy.logging.platform_logger import PlatformLogger

WLSDEPLOY_HOME_VARIABLE = 'WLSDEPLOY_HOME'
CUSTOM_CONFIG_VARIABLE = 'WDT_CUSTOM_CONFIG'

__logger = PlatformLogger('wlsdeploy.util')
_class_name = 'path_utils'


def fixup_path(path):
    """
    Standardize the path, replacing the back slashes with forward slash. This is more suitable for wlst
    commands. If the end of the path contains a slash, strip the slash from the resulting path.
    :param path: to be standardized with forward slashes
    :return: reformatted path
    """
    result = path
    if path is not None:
        if is_relative_path(path):
            result = path.replace('\\', '/')
        else:
            result = get_canonical_path(path)
        if result.endswith('/'):
            result = result[:-1]
    return result


def get_canonical_path(path):
    """
    Return the canonical representation of the path and standardize the path, replacing back slashes with
        forward slashes.
    :param path:
    :return:
    """
    result = path
    if path is not None:
        result = JFile(path).getCanonicalPath().replace('\\', '/')
    return result


def get_parent_directory(path):
    """
    Return the parent directory of the last folder or file in the provided path. The path will be reformatted
    into its canonical form.
    :param path: containing the parent directory
    :return: parent directory in its canonical format
    """
    result = path
    if path is not None:
        result = JFile(path).getParentFile().getCanonicalPath()
    return result


def get_last_path_node(path):
    """
    Return the last node in the path.

    :param path: in which to locate the last node
    :return: last path node
    """
    __, tail = os.path.split(path)
    return tail


def is_relative_path(file_name):
    """
    Return true if the file name is not None and the path is not an absolute path.
    :param file_name: to check for relative path
    :return: True if the path is not absolute
    """
    return file_name is not None and not os.path.isabs(file_name)


def get_filename_from_path(file_path):
    """
    Return the filename from the existing file path.
    :param file_path: path containing a file name
    :return: file name or None if a file name is not present or the file or file path does not exist
    """
    file_name = None
    if not JStringUtils.isEmpty(file_path) and (os.path.exists(file_path) is False or os.path.isfile(file_path)):
        __, file_name = os.path.split(file_path)
    return file_name


def get_pathname_from_path(file_path):
    """
    Return the path without the file name from the existing file path.
    :param file_path: file path
    :return: path without file name or None if a file name is not present or the file or file path does not exist
    """
    if not JStringUtils.isEmpty(file_path) and (os.path.exists(file_path) is False or os.path.isfile(file_path)):
        file_path, _ = os.path.split(file_path)
    return file_path


def get_filename_no_ext_from_path(file_path):
    """
    Return the filename with the extension stripped off from the provided file path.
    :param file_path: path containing the file name
    :return: file name without extension or None if the file path doesn't exist or contain a file name
    """
    file_name = None
    file_name_ext = get_filename_from_path(file_path)
    if file_name_ext is not None:
        file_name, __ = os.path.splitext(file_name_ext)
    return file_name


def get_file_ext_from_path(file_path):
    """
    Return the extension for the file in the file path.
    :param file_path: containing the file
    :return: extension or None if the file path does not exist or contain a file
    """
    ext = None
    file_name_ext = get_filename_from_path(file_path)
    if file_name_ext is not None:
        __, ext = os.path.splitext(file_name_ext)
    return ext.strip()


def is_jar_file(file_path):
    """
    Determine if the file at the provided location represents a java archive file.
    :param file_path: location and file
    :return: true if the file_path represents a file and is a jar file
    """
    return os.path.isfile(file_path) and get_file_ext_from_path(file_path) == '.jar'


def get_wls_deploy_path():
    return os.environ.get(WLSDEPLOY_HOME_VARIABLE, None)


def find_config_path(file_path):
    """
    Find the config file path for the relative file path.
    If the WDT_CUSTOM_CONFIG environment variable is set, look for $WDT_CUSTOM_CONFIG/file_path.
    If not found, return $WLSDEPLOY_HOME/lib/file_path.
    :param file_path: the relative path where the file is expected, such as 'typedefs/WLS.json'
    :return: the absolute path to the file
    """
    _method_name = 'find_config_path'

    custom_config_dir = os.environ.get(CUSTOM_CONFIG_VARIABLE, None)
    if custom_config_dir is not None:
        custom_file_path = os.path.join(custom_config_dir, file_path)
        if os.path.isfile(custom_file_path):
            __logger.info('WLSDPLY-01725', custom_file_path, class_name=_class_name, method_name=_method_name)
            return custom_file_path

    wls_deploy_path = os.environ.get(WLSDEPLOY_HOME_VARIABLE, '')
    return os.path.join(wls_deploy_path, 'lib', file_path)
