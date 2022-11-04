"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import random

import java.lang.Boolean as Boolean
import java.util.logging.Level as Level

import oracle.weblogic.deploy.json.JsonException as JJsonException
from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil

from aliastest.verify import constants
from aliastest.verify.verify_context import VerifyModelContext

__logger = PlatformLogger('test.aliases')
__logger.set_level(Level.FINER)
CLASS_NAME = 'generate/utils'

OFFLINE_ALIAS_FOLDER_IGNORE_MAP = {
    '/': ['ODLConfiguration', 'OHS', 'RCUDbInfo', 'Security', 'UnixMachine', 'WLSRoles',
          'WLSUserPasswordCredentialMappings'],
    '/ResourceGroupTemplate': ['OHS', 'SystemComponent']
}

ONLINE_ALIAS_FOLDER_IGNORE_MAP = {
    '/ResourceGroupTemplate': ['SystemComponents']
}

OFFLINE_TEST_ANOMALIES_MAP = {
    '/Application': {
        'ModuleType': 'war',
        'SourcePath': 'wlsdeploy/applications/get-listen-address-app.war'
    },
    '/Library': {
        'ModuleType': 'war',
        'SourcePath': 'wlsdeploy/sharedLibraries/jstl-1.2.war'
    }
}

def get_verify_args_map(args):
    """
    The provided arguments are the command line key, value pairs.
    :param args: Command line arguments
    :return: Dictionary of the command line arguments
    """
    verify_args = dict()
    idx = 1
    while idx < len(args):
        key = args[idx]
        idx += 1
        if constants.OUTPUT_DIR_SWITCH == key:
            verify_args[constants.OUTPUT_DIR_SWITCH] = args[idx]
            idx += 1
        elif constants.GENERATED_DIR_SWITCH == key:
            verify_args[constants.GENERATED_DIR_SWITCH] = args[idx]
            idx += 1
        elif constants.WLS_VERSION_SWITCH == key:
            verify_args[constants.WLS_VERSION_SWITCH] = args[idx]
            idx += 1

    return verify_args


def get_model_context(program_name, wlst_mode, verify_args):
    verify_args[CommandLineArgUtil.TARGET_MODE_SWITCH] = wlst_mode
    return VerifyModelContext(program_name, wlst_mode, verify_args)


def get_generated_file_name(model_context, mode):
    return '%s/generated%s-%s.json' % (model_context.get_generated_dir(), mode, model_context.get_target_wls_version())


def load_generated_online_dict(model_context):
    _method_name = 'load_generated_online_dict'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)

    generated_file_name = get_generated_file_name(model_context, 'Online')
    try:
        json_reader = JsonToPython(generated_file_name)
        dictionary = json_reader.parse()
    except JJsonException, ex:
        __logger.severe('Failed to read generated online configuration from {0}: {1}', generated_file_name,
                        ex.getMessage(), error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


def load_generated_offline_dict(model_context):
    _method_name = 'load_generated_offline_dict'
    __logger.entering(model_context, class_name=CLASS_NAME, method_name=_method_name)

    generated_file_name = get_generated_file_name(model_context, 'Offline')
    try:
        json_reader = JsonToPython(generated_file_name)
        dictionary = json_reader.parse()
    except JJsonException, ex:
        __logger.severe('Failed to read generated offline configuration from {0}: {1}', generated_file_name,
                        ex.getMessage(), error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


def bool_to_string(bool_value):
    """
    Return string representation of the integer boolean value.
    :param bool_value: to return in string format
    :return: string boolean representation or None if a valid boolean value was not passed
    """
    if bool_value is True:
        return Boolean('true').toString()
    elif bool_value is False:
        return Boolean('false').toString()
    return None


def is_clear_text_password(attribute_name):
    """
    Any encrypted field that follows the pattern of containing a clear text representation of the encrypted value
    is not added to the generated dictionary.
    :param attribute_name: Name of the attribute to check. Each encrypted attribute that takes an encrypted value has
        Encrypted on the end of its name.
    :return: True if the name indicates that the encrypted attribute contains a clear text representation
    """
    # clear text password attributes are not in the alias definition and are skipped on discover or set
    # clear text do not have Encrypted on the end
    return ('Credential' in attribute_name or 'Pass' in attribute_name or 'Encrypted' in attribute_name) \
        and not attribute_name.endswith('Encrypted')


def get_lower_case_dict(value_list):
    """
    Create a dictionary whose key is the provided key value in lower case and whose value is the original key value.
    :param value_list: List of key strings.
    :return: Dictionary with lower case key and original value
    """
    lower_case_map = dict()
    for value in value_list:
        lower_case_map[value.lower()] = value
    return lower_case_map


def find_name_in_mbean_with_model_name(wlst_name, lower_case_map):
    """
    Find the mbean name or attribute name as known in WLST MBeanInfo, MBI and CMO methods.
    :param wlst_name: Name from the mentioned resources
    :param lower_case_map: map of the lower case names to original wlst names for the search
    :return: True if found in the map, name from the map
    """
    _method_name = 'find_name_in_mbean_with_model_name'
    __logger.entering(wlst_name, class_name=CLASS_NAME, method_name=_method_name)
    result = wlst_name
    found = False

    if result in lower_case_map.keys():
        found = True
    else:
        lower_case = wlst_name.lower()
        result = _key_in_case_map(lower_case, lower_case_map)
        if result is None and lower_case.endswith('y'):
            result = _key_in_case_map(lower_case[:len(lower_case) - 1] + 'ies', lower_case_map)
        if result is None:
            result = _key_in_case_map(lower_case + 'es', lower_case_map)
        if result is None:
            result = _key_in_case_map(lower_case + 's', lower_case_map)
        if result is None:
            result = wlst_name
        else:
            found = True

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=result)
    return found, result


def mbean_name(mbean_type):
    """
    Generate two different names for creating an MBean. The first name is a randomly generated name. The second
    name is for those MBeans that cannot take a random generated name.
    :param mbean_type: for which to generate the mbean
    :return: two names
    """
    return mbean_type + '-' + str(random.randint(100, 65535)),  mbean_type


def get_wlst_mode_as_string(model_context):
    """
    Return the string representation of the current wlst mode in process - online or offline
    :param model_context: containing the mode currently being used in the test processing
    :return: string representation of the current mode
    """
    return WlstModes.from_value(model_context.get_target_wlst_mode())


def get_report_file_name(model_context):
    return 'report%s-%s.txt' % \
           (get_wlst_mode_as_string(model_context).lower().capitalize(), model_context.get_target_wls_version())


def sort_dict(dictionary):
    """
    Return a dictionary that is sorted with the keys in order.
    :param dictionary: Original dictionary
    :return: Dictionary now in order of the sorted keys.
    """
    new_dictionary = PyOrderedDict()
    if dictionary:
        keys = dictionary.keys()
        keys.sort()
        for key in keys:
            new_dictionary[key] = dictionary[key]
    return new_dictionary


def is_alias_folder_in_ignore_list(model_context, location, alias_name):
    if model_context.get_target_wlst_mode == WlstModes.ONLINE:
        ignore_map = ONLINE_ALIAS_FOLDER_IGNORE_MAP
    else:
        ignore_map = OFFLINE_ALIAS_FOLDER_IGNORE_MAP

    path = location.get_folder_path()
    if path in ignore_map and alias_name in ignore_map[path]:
        return True
    return False


def is_attribute_value_test_anomaly(model_context, location, attribute_name, attribute_value):
    anomaly_map = OFFLINE_TEST_ANOMALIES_MAP
    path = location.get_folder_path()
    return path in anomaly_map and attribute_name in anomaly_map[path] and \
        anomaly_map[path][attribute_name] == attribute_value


def _key_in_case_map(key, case_map):
    if key in case_map:
        return case_map[key]
    return None

