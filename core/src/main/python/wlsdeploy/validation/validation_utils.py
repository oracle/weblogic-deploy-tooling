"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""

from java.io import IOException
from java.io import FileInputStream
from java.lang import IllegalArgumentException
from java.util import Properties

import zipfile

from wlsdeploy.aliases import model_constants
from wlsdeploy.exception import exception_helper

import oracle.weblogic.deploy.util.WLSDeployArchive as WLSDeployArchive
import oracle.weblogic.deploy.exception.ExceptionHelper as ExceptionHelper


divider_string = '-----------------------------------------------'

_class_name = "validation_helper"


def load_model_variables_file_properties(variable_properties_file, logger):
    """

    :param variable_properties_file:
    :param logger:
    :return:
    """
    _method_name = 'load_model_variables_file_properties'

    variable_properties = Properties()

    try:
        prop_inputstream = FileInputStream(variable_properties_file)
        variable_properties.load(prop_inputstream)
        prop_inputstream.close()
    except (IOException, IllegalArgumentException), e:
        ex = exception_helper.create_validate_exception('WLSDPLY-03123', variable_properties_file,
                                                        e.getLocalizedMessage(), error=e)
        logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    return variable_properties


def load_model_archive_file_entries(archive_file_name, logger):
    """

    :param archive_file_name:
    :param logger:
    :return:
    """
    _method_name = 'load_model_archive_file_entries'

    try:
        archive_entries = zipfile.ZipFile(archive_file_name)
    except (IOError, zipfile.BadZipfile), e:
        ex = exception_helper.create_validate_exception('WLSDPLY-03161',
                                                        archive_file_name,
                                                        e.getLocalizedMessage(),
                                                        error=e)
        logger.throwing(ex, class_name=_class_name, method_name=_method_name)
        raise ex

    return archive_entries


def format_message(key, *args):
    return ExceptionHelper.getMessage(key, list(args))


def get_property_data_type(value):
    data_types_map = {
        "<type 'str'>": 'string',
        "<type 'int'>": 'integer',
        "<type 'long'>": 'long',
        "<type 'float'>": 'float',
        "<type 'dict'>": 'properties',
        "<type 'list'>": 'list'
    }
    data_type = str(type(value))
    if data_type in data_types_map:
        return data_types_map[data_type]
    else:
        return data_type


def get_properties(value):
    rtnval = None
    if isinstance(value, dict):
        rtnval = value
    elif '=' in value:
        properties = value.split('=')
        if properties:
            rtnval = { properties[0]: properties[1] }

    if rtnval is None:
        rtnval = { 'Value': value }

    return rtnval


def is_compatible_data_type(expected_data_type, actual_data_type):
    retval = False
    if expected_data_type == 'string':
        retval = (actual_data_type in ["<type 'str'>", "<type 'long'>"])
    elif expected_data_type == 'integer':
        retval = (actual_data_type in ["<type 'int'>", "<type 'long'>", "<type 'str'>"])
    elif expected_data_type == 'long':
        retval = (actual_data_type in ["<type 'int'>", "<type 'long'>", "<type 'str'>"])
    elif expected_data_type == 'boolean':
        retval = (actual_data_type in ["<type 'int'>", "<type 'str'>"])
    elif expected_data_type == 'float':
        retval = (actual_data_type in ["<type 'float'>", "<type 'str'>"])
    elif expected_data_type == 'properties' or expected_data_type == 'dict':
        retval = (actual_data_type in ["<type 'PyOrderedDict'>", "<type 'dict'>", "<type 'str'>"])
    elif 'list' in expected_data_type:
        retval = (actual_data_type in ["<type 'list'>", "<type 'str'>"])
    elif expected_data_type == 'password':
        retval = (actual_data_type in ["<type 'str'>"])
    elif expected_data_type == 'credential':
        retval = (actual_data_type in ["<type 'str'>"])
    elif 'delimited_' in expected_data_type:
        retval = (actual_data_type in ["<type 'str'>", "<type 'list'>"])
    elif expected_data_type == 'jarray':
        retval = (actual_data_type in ["<type 'str'>"])

    return retval


def get_param_value(modelDict, param, top_level_key=None):
    try:
        plist = param.split('.')
        # DO NOT CHANGE THIS - using eval and it must be a literal of modelDict
        cmd = 'modelDict'
        if top_level_key is not None:
            cmd += '[\'' + top_level_key + '\']'
        for p in plist:
            cmd += '[\'' + p + '\']'
        return eval(cmd)
    except KeyError:
        return None


def get_domain_info_data_types():
    """

    :return:
    """
    return {
        'AdminUserName': 'string',
        'AdminPassword': 'string',
        'ServerStartMode': 'string'
    }


def get_deployable_item_paths():
    """

    :return:
    """
    return [
        model_constants.SOURCE_PATH,
        model_constants.PLAN_PATH
    ]


def get_valid_archive_entries_keys():
    """

    :return:
    """
    return [WLSDeployArchive.WLSDPLY_ARCHIVE_BINARY_DIR,
            WLSDeployArchive.ARCHIVE_MODEL_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_APPS_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_SHLIBS_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_DOMLIB_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_CPLIB_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_FILE_STORE_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_COHERENCE_TARGET_DIR,
            WLSDeployArchive.ARCHIVE_SCRIPTS_DIR]


def get_valid_app_sourcepath_entries():
    """

    :return:
    """
    return [WLSDeployArchive.ARCHIVE_APPS_TARGET_DIR]


def get_valid_lib_sourcepath_entries():
    """

    :return:
    """
    return [WLSDeployArchive.ARCHIVE_SHLIBS_TARGET_DIR]


def print_indent(msg, level=1):
    """

    :param msg:
    :param level:
    :return:
    """
    result = ''
    for i in range(0, level):
        result += '  '
    print '%s%s' % (result, msg)
    return


def print_blank_lines(number=1):
    """

    :param self:
    :param number:
    :return:
    """
    for i in range(0, number):
        print

    return
