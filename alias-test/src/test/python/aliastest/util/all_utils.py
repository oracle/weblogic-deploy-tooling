"""
Copyright (c) 2020, 2021, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os
import random
import types

import java.lang.ClassNotFoundException as ClassNotFoundException
import java.lang.Exception as JException
import java.lang.IllegalArgumentException as IllegalArgumentException
import java.io.FileNotFoundException as FileNotFoundException
import java.io.File as File
import java.io.FileInputStream as FileInputStream
import java.io.FileOutputStream as JFileOutputStream
import java.io.IOException as IOException
import java.io.PrintWriter as JPrintWriter
import java.lang.Boolean as Boolean
import java.lang.Class as Class

import java.lang.SecurityException as SecurityException

import java.lang.StringBuilder as StringBuilder
import java.lang.System as JSystem
import java.util.logging.FileHandler as FileHandler
import java.util.logging.Level as Level
import java.util.IllegalFormatException as IllegalFormatException


from oracle.weblogic.deploy.json import JsonException
from oracle.weblogic.deploy.json import JsonStreamTranslator
from oracle.weblogic.deploy.util import PyOrderedDict

import wlsdeploy.aliases.alias_constants as alias_constants
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.cla_utils import CommandLineArgUtil

from aliastest.util.verify_context import VerifyContext

LOGGER_PROPERTIES_LOCATION = 'resources'
LOGGER_PROPERTIES = 'logging.properties'

_indent_unit = '    '
LINE_SEPARATOR = JSystem.getProperty('line.separator')
IGNORE_METHODS_LIST = ['Attribute', 'Attributes', 'CachingDisabled', 'Class', 'Comments',
                       'DefaultedMBean', 'Descriptor', 'Editable', 'InvocationHandler', 'MBeanInfo',
                       'NotificationInfo', 'ObjectName', 'ParentBean', 'PersistenceEnabled',
                       'ProxyClass', 'Registered']
IGNORE_TOP_MBEANS_MAP = {
}
FAIL = '*FAIL*'
LSA_DEFAULT = 'lsa_default'
GET_DEFAULT = 'get_default'
CMO_DEFAULT = 'cmo_default'

CREATE = 'create'

ATTRIBUTES = 'attributes'
READ_TYPE = 'read_type'
CMO_READ_TYPE = 'cmo_read_type'
READ_ONLY = 'readonly'
READ_WRITE = 'readwrite'
TRUE = 'true'
FALSE = 'false'
RECHECK = 'recheck'
ADDITIONAL_RECHECK = "additional"
TYPE = 'wlst_type'
LSA_TYPE = 'lsa_wlst_type'
GET_TYPE = 'get_wlst_type'
CMO_TYPE = 'cmo_wlst_type'
RESTART = 'restart_required'
UNSET = 'unSet'
REFERENCE = 'reference'
DEPRECATED = 'deprecated'
SINCE_VERSION = 'since_version'
RESTART_NO_CHECK = 'none'
DO_NOT_IMPLEMENT = 'true'
ONLINE_REFERENCE_ONLY = 'reference_only'
INSTANCE_TYPE = 'instance'
UNKNOWN = 'unknown'
SINGLE = 'single'
SINGLE_NO_NAME = 'single_no_name'
MULTIPLE = 'multiple'
TEST_FILE_LOCATION_SWITCH = '-testfiles_path'


__test_files_location = None

__logger = PlatformLogger('test.aliases', resource_bundle_name='aliastest_rb')
__logger.set_level(Level.FINER)
CLASS_NAME = 'all_utils'


def create_json_file(dictionary, file_name):
    """
    Create a json file from the provided dictionary and store at the location specified by the file name.
    :param dictionary: information to persist in json format
    :param file_name: path and name of the file to persist
    """
    _method_name = 'create_json_file'
    __logger.entering(file_name, class_name=CLASS_NAME, method_name=_method_name)
    try:
        fos = JFileOutputStream(file_name, False)
    except (FileNotFoundException, SecurityException), fe:
        __logger.warning('WLSDPLYST-01315', file_name, fe.getLocalizedMessage(), class_name=CLASS_NAME,
                         method_name=_method_name)
        return
    writer = JPrintWriter(fos, True)
    try:
        _write_dictionary_to_json_file(dictionary, writer)
    finally:
        writer.close()
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)


def get_dictionary_from_json_file(json_file_name):
    """
    Load the dictionary with the generated folder and attribute information from the provided location.
    :param json_file_name: path and name of the generated file
    :return: loaded dictionary or None if unable to parse and load the file
    """
    _method_name = 'get_dictionary_from_json_file'
    __logger.entering(json_file_name, class_name=CLASS_NAME, method_name=_method_name)
    json_input_stream = FileInputStream(File(json_file_name))
    json_translator = JsonStreamTranslator(json_file_name, json_input_stream)
    dictionary = None
    try:
        dictionary = json_translator.parse()
    except JsonException, je:
        __logger.severe('WLSDPLYST-01317', json_file_name, je.getLocalizedMessage(), class_name=CLASS_NAME,
                        method_name=_method_name)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return dictionary


def filename(prefix, mode, wls_version):
    """
    Generate a test file path and file to be stored at the test files location specified for this test instance.
    :param prefix: type of file
    :param mode: online or offline
    :param wls_version: version of WebLogic server
    :return: Test file name with mode and version concatenated with the test files location path
    """
    new_filename = None
    if prefix and mode:
        new_filename = prefix + mode.lower() + wls_version
        if __test_files_location:
            new_filename = os.path.join(get_test_files_location(), new_filename)
    return new_filename


def get_missing_names(mbean_type, check_map, check_map_type, against_map, against_map_type):
    _method_name = 'get_missing_names'

    __logger.fine('WLSDPLYST-01338', mbean_type,
                  check_map_type, len(check_map), against_map_type, len(against_map),
                  class_name=CLASS_NAME, method_name=_method_name)

    missing_names = list()
    for attribute_name in check_map:
        if attribute_name not in against_map:
            missing_names.append(attribute_name)
    return missing_names


def get_class_name(interface_name):
    _method_name = 'get_class_name'
    __logger.entering(interface_name, class_name=CLASS_NAME, method_name=_method_name)
    class_name = None
    try:
        class_name = Class.forName(interface_name).getSimpleName()
    except ClassNotFoundException:
        __logger.finer('Class not found for interface name {0}', interface_name)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=class_name)
    return class_name


def get_index_from_list_of_names(search_list_for, name):
    _method_name = 'get_index_from_list_of_names'
    try:
        return [named_item.getName() for named_item in search_list_for].index(name)
    except ValueError:
        __logger.finest('WLSDPLYST-01336', name, class_name=CLASS_NAME, method_name=_method_name)
    return -1


def get_mbean_methods(mbean_instance):
    if mbean_instance is not None:
        return mbean_instance.getClass().getMethods()
    return list()


def is_valid_getter(mbean_instance, mbean_type, get_method_name, attribute):
    _method_name = 'is_valid_getter'
    __logger.entering(get_method_name, mbean_type, class_name=CLASS_NAME, method_name=_method_name)
    valid, __ = get_from_bean_proxy(mbean_instance, mbean_type, get_method_name, attribute)
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name, result=Boolean(valid))
    return valid


def get_from_bean_proxy(mbean_instance, mbean_type, method_name, attribute):
    _method_name = 'get_from_bean_proxy'
    __logger.entering(mbean_type, method_name, attribute, class_name=CLASS_NAME, method_name=_method_name)
    success = False
    value = None
    try:
        get_method = getattr(mbean_instance, method_name)
        if get_method is not None:
            value = get_method()
            __logger.finer('WLSDPLYST-01329', mbean_type, method_name, attribute,
                           class_name=CLASS_NAME, method_name=_method_name)
            success = True
        else:
            __logger.finer('Get method {0} is not found on mbean {1} attribute {2}', method_name, mbean_type, attribute,
                           class_name=CLASS_NAME, method_name=_method_name)
    except (Exception, JException), e:
        __logger.finest('WLSDPLYST-01330', mbean_type, method_name, attribute, str(e),
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


def close_file(open_file):
    """
    Close the open file.
    :param open_file: file handle of the open file
    """
    open_file.close()


def open_file_for_write(file_name):
    """
    Open a file for write (no append) with the location / file name provided.
    :param file_name: to open for write
    :return: file handle of opened file
    """
    _method_name = 'open_file_for_write'
    __logger.entering(file_name, class_name=CLASS_NAME, method_name=_method_name)
    my_file = open(file_name, 'w')
    __logger.exiting(class_name=CLASS_NAME, method_name=_method_name)
    return my_file


def mbean_name(mbean_type):
    """
    Generate two different names for creating an MBean. The first name is a randomly generated name. The second
    name is for those MBeans that cannot take a random generated name.
    :param mbean_type: for which to generate the mbean
    :return: two names
    """

    return mbean_type + '-' + str(random.randint(100, 65535)),  mbean_type


def kwargs_map(args):
    """
    The provided arguments are the command line key, value pairs.
    :param args: Command line arguments
    :return: Dictionary of the command line arguments
    """
    kwargs = dict()
    idx = 1
    while idx < len(args):
        key = args[idx]
        idx += 1
        if TEST_FILE_LOCATION_SWITCH == key:
            kwargs[TEST_FILE_LOCATION_SWITCH] = args[idx]
        if CommandLineArgUtil.ORACLE_HOME_SWITCH == key:
            kwargs[CommandLineArgUtil.ORACLE_HOME_SWITCH] = args[idx]
        elif CommandLineArgUtil.DOMAIN_HOME_SWITCH == key:
            kwargs[CommandLineArgUtil.DOMAIN_HOME_SWITCH] = args[idx]
        elif CommandLineArgUtil.ADMIN_USER_SWITCH == key:
            kwargs[CommandLineArgUtil.ADMIN_USER_SWITCH] = args[idx]
        elif CommandLineArgUtil.ADMIN_PASS_SWITCH == key:
            kwargs[CommandLineArgUtil.ADMIN_PASS_SWITCH] = args[idx]
        elif CommandLineArgUtil.ADMIN_URL_SWITCH == key:
            kwargs[CommandLineArgUtil.ADMIN_URL_SWITCH] = args[idx]
        elif '-wls_version' == key:
            kwargs['-wls_version'] = args[idx]

    return kwargs


def populate_model_context(program_name, wlst_mode, kwargs):
    """
    Create a model context with the values for this instance of the system test.
    Aliases requires a populated model context, so this will be used to encapsulate
    the runtime values for the system test use.
    :param program_name: name of the program for logging purposes
    :param wlst_mode: online or offline
    :param kwargs: map of the command line arguments
    :return: verify context encapsulating runtime information
    """
    kwargs[CommandLineArgUtil.TARGET_MODE_SWITCH] = WlstModes.from_value(wlst_mode)
    return VerifyContext(program_name, kwargs)


def str_mode(model_context):
    """
    Return the string representation of the current wlst mode in process - online or offline
    :param model_context: containing the mode currently being used in the test processing
    :return: string representation of the current mode
    """
    return WlstModes.from_value(model_context.get_target_wlst_mode())


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


def populate_test_files_location(kwargs):
    """
    Find the test files path from the argument list, for the test file location command. This is
    populated in the global location of the utils file, for use during this instance of the integration test.
    Any generated json files will be stored and read from this location, and verification reports will be strored
    at this location.
    :param kwargs: command line argument map
    """
    _method_name = 'populate_test_files_location'
    global __test_files_location
    if TEST_FILE_LOCATION_SWITCH in kwargs:
        __test_files_location = kwargs[TEST_FILE_LOCATION_SWITCH]
    else:
        __logger.severe('Test File location is missing in {0}', kwargs)
        exit()
    if __test_files_location:
        assert __test_files_location and os.path.exists(__test_files_location) and os.path.isdir(__test_files_location)
    __logger.info('Test files location {0}', __test_files_location,
                  class_name=CLASS_NAME, method_name=_method_name)


def setup_logger_overrides(logger):
    """
    Set up overrides for the callers Logger
    """
    handlers = logger.getHandlers()
    for handler in handlers:
        if isinstance(handler, FileHandler):
            os.path.join(get_test_files_location(), LOGGER_PROPERTIES_LOCATION, LOGGER_PROPERTIES)
            handler.setPattern(get_test_files_location())


def get_test_files_location():
    """
    Return the test files location passed on the command line argument.
    :return: test files directory location
    """
    return __test_files_location


def test_directory_exists(location):
    """
    Test if the location exists and is a directory.
    :param location: directory name to test
    :return: True if exists and is directory
    """
    return os.path.exists(location) and os.path.isdir(location)


def test_file_exists(fname):
    """
    Test if the file exists and is a file
    :param fname:
    :return: True if is an existing file
    """
    return os.path.exists(fname) and os.path.isfile(fname)


def dict_obj():
    """
    Return a dictionary instance which will retain the order in which items are added.
    :return:
    """
    return PyOrderedDict()


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


def sort_dict(dictionary):
    """
    Return a dictionary that is sorted with the keys in order.
    :param dictionary: Original dictionary
    :return: Dictionary now in order of the sorted keys.
    """
    new_dictionary = dict_obj()
    if dictionary:
        keys = dictionary.keys()
        keys.sort()
        for key in keys:
            new_dictionary[key] = dictionary[key]
    return new_dictionary


def set_domain_home_arg(arg_map, domain_home):
    """
    Override or add the domain home in the arguments map.

    :param arg_map: containing the command line arguments
    :param domain_home: to replace in the argument map
    """
    if CommandLineArgUtil.DOMAIN_HOME_SWITCH in arg_map:
        __logger.info("domain home arg {0}", arg_map[CommandLineArgUtil.DOMAIN_HOME_SWITCH],
                      class_name=CLASS_NAME, method_name='set_domain_home_arg')
    set_arg(arg_map, CommandLineArgUtil.DOMAIN_HOME_SWITCH, domain_home)


def set_arg(arg_map, key, value):
    """
    Add or override the map entry in the arg_map. If the value contains None, the entry is removed from the
    arg map.

    :param arg_map: map containing the map
    :param key: of entry in the map
    :param value: of entry in the map.
    """
    if key is not None:
        if (key not in arg_map or arg_map[key] is None) and value is not None:
            arg_map[key] = value


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


def is_boolean_type(attr_type, attr_default):
    """
    Determine if the type of the WLST attribute is an acceptable type for Boolean.
    :param attr_type: Type of the attribute
    :param attr_default: Attribute default, if present, that tests the conversion of the acceptable type
    :return: True if the attribute type can represent a python boolean
    """
    if attr_type == alias_constants.STRING or attr_type == alias_constants.INTEGER:
        return is_bool_instance(attr_default)
    else:
        return False


def is_bool_instance(attr_value):
    """
    Determine if the attribute value can be converted to a (Java) Boolean object.
    :param attr_value: Value of the attribute to test for boolean
    :return: True if the value can be represented as a python boolean
    """
    try:
        Boolean(attr_value)
        return True
    except (IllegalArgumentException, TypeError):
        return False


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


def _format_json_value(value):
    """
    Format the value as a JSON snippet.
    :param value: the value
    :return: the JSON snippet
    """
    builder = StringBuilder()
    if isinstance(value, basestring):
        value = value.replace('\\', '\\\\')
        builder.append('"').append(_quote_embedded_quotes(value)).append('"')
    elif isinstance(value, (types.ListType, types.TupleType)):
        if not value:
            builder.append('[]')
        else:
            builder.append('[')
            nexttime = False
            for entry in value:
                if nexttime:
                    builder.append(',')
                else:
                    nexttime = True
                builder.append(_format_json_value(entry))
            builder.append(']')
    else:
        builder.append(value)
    return builder.toString()


def _quote_embedded_quotes(text):
    """
    Quote all embedded double quotes in a string with a backslash.
    :param text: the text to quote
    :return: the quotes result
    """
    result = text
    if isinstance(text, basestring) and '"' in text:
        result = text.replace('"', '\\"')
    return result


def _write_dictionary_to_json_file(dictionary, writer, indent=''):
    """
    Write the python dictionary in json syntax using the provided writer stream.
    :param dictionary: python dictionary to convert to json syntax
    :param writer: where to write the dictionary into json syntax
    :param indent: current string indention of the json syntax. If not provided, indent is an empty string
    """
    _method_name = '_write_dictionary_to_json_file'
    _start_dict = '{'
    _end_dict = '}'

    if dictionary is None:
        return
    try:
        end_line = ''
        # writer.print causes print to be flagged with error in ide
        writer.write(_start_dict)
        end_indent = indent

        indent += _indent_unit
        for key, value in dictionary.iteritems():
            writer.println(end_line)
            end_line = ','
            writer.write(indent + '"' + _quote_embedded_quotes(key) + '" : ')
            if isinstance(value, dict):
                _write_dictionary_to_json_file(value, writer, indent)
            else:
                writer.write(_format_json_value(value))
        writer.println()
        writer.write(end_indent + _end_dict)
    except (IOException, IllegalFormatException), io:
        __logger.warning('WLSDPLYST-01316', io.getLocalizedMessage(), class_name=CLASS_NAME, method_name=_method_name)
    return


def ignore_mbean(mbean_type):
    """
    Determine if the MBean is one that WDT does not currently consider for domains in the particular version.
    :param mbean_type: Type name of the MBean
    :return: True if the test should not generate information for the MBean
    """
    _method_name = 'ignore_mbean'

    __logger.entering(mbean_type, _method_name, class_name=CLASS_NAME, method_name=_method_name)
    ignore = False
    mbean_tuples = list()
    if not _is_empty(mbean_type):
        for version in IGNORE_TOP_MBEANS_MAP.keys():
            if is_weblogic_version_or_above(version):
                mbean_tuples.append(IGNORE_TOP_MBEANS_MAP[version])
        for ignore_mbeans in mbean_tuples:
            if len([mbean for mbean in ignore_mbeans if mbean_type.startswith(mbean)]) > 0:
                ignore = True
                break

    __logger.exiting(result=str_bool(ignore), class_name=CLASS_NAME, method_name=_method_name)
    return ignore


def _is_empty(value):
    return value is None or not isinstance(value, types.StringTypes) or len(value) == 0


def get_interface_name(mbean_interface):
    try:
        getname = getattr(mbean_interface, 'getTypeName')
        result = getname()
    except (Exception, JException):
        result = str(mbean_interface)
    return result


def generated_filename():
    return 'generated'