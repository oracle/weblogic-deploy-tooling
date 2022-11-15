"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import random

import java.lang.Boolean as Boolean
import java.lang.Exception as JException

import oracle.weblogic.deploy.json.JsonException as JJsonException

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.json.json_translator import PythonToJson
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext

ATTRIBUTES = 'attributes'
CMO_READ_TYPE = 'cmo_read_type'
CMO_TYPE = 'cmo_wlst_type'
DEPRECATED = 'deprecated'
FAIL = '*FAIL*'
INSTANCE_TYPE = 'instance'
MULTIPLE = 'multiple'
READ_ONLY = 'readonly'
READ_WRITE = 'readwrite'
RECHECK = 'recheck'
RESTART = 'restart_required'
SINCE_VERSION = 'since_version'
SINGLE = 'single'
SINGLE_NO_NAME = 'single_no_name'
TYPE = 'wlst_type'
UNKNOWN = 'unknown'

ADJUDICATOR_STRING = 'Adjudicator'
AUDITOR_STRING = 'Auditors'
AUTHENTICATION_PROVIDER_STRING = 'AuthenticationProviders'
AUTHORIZER_STRING = 'Authorizers'
CERTPATH_PROVIDER_STRING = 'CertPathProviders'
CREDENTIAL_MAPPER_STRING = 'CredentialMappers'
PASSWORD_VALIDATOR_STRING = 'PasswordValidators'
ROLE_MAPPER_STRING = 'RoleMappers'

PROVIDERS = [
    ADJUDICATOR_STRING,
    AUDITOR_STRING,
    AUTHENTICATION_PROVIDER_STRING,
    AUTHORIZER_STRING,
    CERTPATH_PROVIDER_STRING,
    CREDENTIAL_MAPPER_STRING,
    PASSWORD_VALIDATOR_STRING,
    ROLE_MAPPER_STRING
]

OUTPUT_DIR_SWITCH = '-output_dir'

# In offline mode, we cannot create a JDBC Store if the domain doesn't
# have a JDBCSystemResource (or other JDBCStore) so we need to make sure
# to reorder the dictionary so that JDBCStores comes after
# JDBCSystemResources.
#
TOP_LEVEL_INFO_MAP_DEPENDENCIES = {
    'JDBCStores': 'JDBCSystemResources'
}


__logger = PlatformLogger('test.aliases.generate.utils')
CLASS_NAME = 'generate/utils'


def reorder_info_map(mbean_path, info_map):
    if mbean_path == '/':
        return _reorder_top_level_info_map(info_map)
    return info_map


def get_generate_args_map(args):
    """
    The provided arguments are the command line key, value pairs.
    :param args: Command line arguments
    :return: Dictionary of the command line arguments
    """
    generate_args = dict()
    idx = 1
    while idx < len(args):
        key = args[idx]
        idx += 1
        if OUTPUT_DIR_SWITCH == key:
            generate_args[OUTPUT_DIR_SWITCH] = args[idx]
            idx += 1
        elif CommandLineArgUtil.ORACLE_HOME_SWITCH == key:
            generate_args[CommandLineArgUtil.ORACLE_HOME_SWITCH] = args[idx]
            idx += 1
        elif CommandLineArgUtil.DOMAIN_HOME_SWITCH == key:
            generate_args[CommandLineArgUtil.DOMAIN_HOME_SWITCH] = args[idx]
            idx += 1
        elif CommandLineArgUtil.ADMIN_USER_SWITCH == key:
            generate_args[CommandLineArgUtil.ADMIN_USER_SWITCH] = args[idx]
            idx += 1
        elif CommandLineArgUtil.ADMIN_PASS_SWITCH == key:
            generate_args[CommandLineArgUtil.ADMIN_PASS_SWITCH] = args[idx]
            idx += 1
        elif CommandLineArgUtil.ADMIN_URL_SWITCH == key:
            generate_args[CommandLineArgUtil.ADMIN_URL_SWITCH] = args[idx]
            idx += 1

    java_home = os.environ['JAVA_HOME']
    generate_args[CommandLineArgUtil.JAVA_HOME_SWITCH] = java_home

    return generate_args


def get_model_context(program_name, wlst_mode, generate_args):
    generate_args[CommandLineArgUtil.TARGET_MODE_SWITCH] = wlst_mode
    return GenerateModelContext(program_name, generate_args)


def load_sc_provider_dict(model_context):
    _method_name = 'load_sc_provider_dict'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    sc_file_name = get_output_file_name(model_context, 'SC')
    try:
        json_reader = JsonToPython(sc_file_name)
        dictionary = json_reader.parse()
    except JJsonException, ex:
        __logger.severe('Failed to read security configuration from {0}: {1}', sc_file_name, ex.getMessage(),
                        error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


def load_online_dict(model_context):
    _method_name = 'load_online_dict'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    online_file_name = get_output_file_name(model_context, 'Online')
    try:
        json_reader = JsonToPython(online_file_name)
        dictionary = json_reader.parse()
    except JJsonException, ex:
        __logger.severe('Failed to read online file from {0}: {1}', online_file_name, ex.getMessage(),
                        error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=len(dictionary))
    return dictionary


def persist_file(model_context, dictionary, mode):
    """
    Persist the generated online dictionary to the test files location and generated file name.
    :param model_context: containing the test files' location
    :param dictionary: generated dictionary
    :mode: the mode being run (SC, online, or offline)
    :return: File name for persisted dictionary
    """
    _method_name = 'persist_file'
    __logger.entering(class_name=CLASS_NAME, method_name=_method_name)

    output_file = get_output_file_name(model_context, mode)
    __logger.info('Persist generated {0} dictionary to {1}', mode, output_file,
                  class_name=CLASS_NAME, method_name=_method_name)
    try:
        json_writer = PythonToJson(dictionary)
        json_writer.write_to_json_file(output_file)
    except JJsonException, ex:
        __logger.severe('Failed to write {0}} data to {1}: {2}', mode, output_file, ex.getMessage(),
                        error=ex, class_name=CLASS_NAME, method_name=_method_name)
        raise ex

    __logger.exiting(result=output_file, class_name=CLASS_NAME, method_name=_method_name)
    return output_file


def get_output_file_name(model_context, mode_type):
    """
    Get the full path to the file we want to write.
    :param model_context: model context object
    :param mode_type: 'Offline', 'Online', or 'SC'
    :return: full path to the output file
    """
    file_name = 'generated%s-%s.json' % (mode_type, model_context.get_target_wls_version())
    return os.path.join(model_context.get_output_dir(), file_name)


def get_from_bean_proxy(mbean_instance, mbean_type, method_name, attribute):
    _method_name = 'get_from_bean_proxy'
    __logger.entering(mbean_type, method_name, attribute, class_name=CLASS_NAME, method_name=_method_name)
    success = False
    value = None
    try:
        get_method = getattr(mbean_instance, method_name)
        if get_method is not None:
            value = get_method()
            __logger.finer('MBean {0} attribute method {1} can be invoked', mbean_type, method_name, attribute,
                           class_name=CLASS_NAME, method_name=_method_name)
            success = True
        else:
            __logger.finer('Get method {0} is not found on mbean {1} attribute {2}', method_name, mbean_type, attribute,
                           class_name=CLASS_NAME, method_name=_method_name)
    except (Exception, JException), e:
        __logger.finest('MBean {0} attribute {1} getter {2} cannot be invoked on the mbean_instance : {3}',
                        mbean_type, method_name, attribute, str(e), error=e,
                        class_name=CLASS_NAME, method_name=_method_name)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=value)
    return success, value


def is_subfolder(descriptor):
    """
    Is this attribute a child MBean to the current
    :param descriptor:
    :return:
    """
    return descriptor.getValue('relationship') == 'containment'


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
    return ('Credential' in attribute_name or 'Pass' in attribute_name or 'Encrypted' in attribute_name) and \
           not attribute_name.endswith('Encrypted')


def str_bool(bool_value):
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


def get_lower_case_dict(value_list):
    """
    Create a dictionary whose key is the provided key value in lower case and whose value is the original key value.
    :param value_list: List of key strings.
    :return: Dictionary with lower case key and original value
    """
    lower_case_map = PyOrderedDict()
    for value in value_list:
        lower_case_map[value.lower()] = value
    return lower_case_map


def mbean_name(mbean_type):
    """
    Generate two different names for creating an MBean. The first name is a randomly generated name. The second
    name is for those MBeans that cannot take a random generated name.
    :param mbean_type: for which to generate the mbean
    :return: two names
    """

    return mbean_type + '-' + str(random.randint(100, 65535)),  mbean_type


def is_valid_getter(mbean_instance, mbean_type, get_method_name, attribute):
    _method_name = 'is_valid_getter'
    __logger.entering(get_method_name, mbean_type, class_name=CLASS_NAME, method_name=_method_name)

    valid, __ = get_from_bean_proxy(mbean_instance, mbean_type, get_method_name, attribute)

    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=Boolean(valid))
    return valid


def list_from_enumerations(enumerations):
    """
    Turn the list of Enumerations to a list of python strings.
    :param enumerations: List of Enumeration types
    :return: List of strings
    """
    result_list = list()
    while enumerations.hasMoreElements():
        result_list.append(enumerations.nextElement())
    return result_list


def get_interface_name(mbean_interface):
    try:
        getname = getattr(mbean_interface, 'getTypeName')
        result = getname()
    except (Exception, JException):
        result = str(mbean_interface)
    return result


def get_mbean_methods(mbean_instance):
    if mbean_instance is not None:
        return mbean_instance.getClass().getMethods()
    return list()


def _reorder_top_level_info_map(info_map):
    keys = info_map.keys()

    new_keys = list()
    delayed_keys = list()
    for key in keys:
        if key in TOP_LEVEL_INFO_MAP_DEPENDENCIES and TOP_LEVEL_INFO_MAP_DEPENDENCIES[key] not in new_keys:
            delayed_keys.append(key)
        else:
            new_keys.append(key)

    if len(delayed_keys) > 0:
        new_info_map = PyOrderedDict()
        for key in new_keys:
            new_info_map[key] = info_map[key]
        for key in delayed_keys:
            new_info_map[key] = info_map[key]
        return new_info_map
    return info_map


class GenerateModelContext(ModelContext):
    def __init__(self, program_name, arg_map):
        super(GenerateModelContext, self).__init__(program_name, arg_map)
        self._output_dir = arg_map[OUTPUT_DIR_SWITCH]

    def get_output_dir(self):
        return self._output_dir

    #
    # Override methods
    #
    def replace_token_string(self, string_value):
        return string_value

    def tokenize_path(self, path):
        return path

    def is_using_encryption(self):
        return False
