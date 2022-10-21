"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import random

import java.lang.Boolean as Boolean
import java.lang.Exception as JException
import java.util.logging.Level as Level

from oracle.weblogic.deploy.util import PyOrderedDict

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util.model_context import ModelContext

OUTPUT_DIR_SWITCH = '-output_dir'

__logger = PlatformLogger('test.aliases')
__logger.set_level(Level.FINER)
CLASS_NAME = 'generate/utils'


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
        if CommandLineArgUtil.ORACLE_HOME_SWITCH == key:
            generate_args[CommandLineArgUtil.ORACLE_HOME_SWITCH] = args[idx]
        elif CommandLineArgUtil.DOMAIN_HOME_SWITCH == key:
            generate_args[CommandLineArgUtil.DOMAIN_HOME_SWITCH] = args[idx]
        elif CommandLineArgUtil.ADMIN_USER_SWITCH == key:
            generate_args[CommandLineArgUtil.ADMIN_USER_SWITCH] = args[idx]
        elif CommandLineArgUtil.ADMIN_PASS_SWITCH == key:
            generate_args[CommandLineArgUtil.ADMIN_PASS_SWITCH] = args[idx]
        elif CommandLineArgUtil.ADMIN_URL_SWITCH == key:
            generate_args[CommandLineArgUtil.ADMIN_URL_SWITCH] = args[idx]

    return generate_args


def get_model_context(program_name, wlst_mode, generate_args):
    generate_args[CommandLineArgUtil.TARGET_MODE_SWITCH] = wlst_mode
    return GenerateModelContext(program_name, generate_args)


def get_output_file_name(model_context, mode_type):
    """
    Get the full path to the file we want to write.
    :param model_context: model context object
    :param mode_type: 'offline', 'online', or 'SC'
    :return: full path to the output file
    """
    file_name = 'generated%s%s' % (mode_type, model_context.get_target_wls_version().replace('.', ''))
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


def mbean_name(mbean_type):
    """
    Generate two different names for creating an MBean. The first name is a randomly generated name. The second
    name is for those MBeans that cannot take a random generated name.
    :param mbean_type: for which to generate the mbean
    :return: two names
    """

    return mbean_type + '-' + str(random.randint(100, 65535)),  mbean_type


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
