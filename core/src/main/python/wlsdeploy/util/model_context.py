"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0
"""
import javaos as os
import tempfile

from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.logging import platform_logger
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util import path_utils
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class ModelContext(object):
    """
    This class contains fields derived from the command-line parameters and external configuration files,
    excluding the model file.
    """
    _class_name = "ModelContext"

    __ORACLE_HOME_TOKEN = '@@ORACLE_HOME@@'
    __WL_HOME_TOKEN = '@@WL_HOME@@'
    __DOMAIN_HOME_TOKEN = '@@DOMAIN_HOME@@'
    __CURRENT_DIRECTORY_TOKEN = '@@PWD@@'
    __TEMP_DIRECTORY_TOKEN = '@@TMP@@'

    def __init__(self, program_name, arg_map):
        self._program_name = program_name
        self._logger = platform_logger.PlatformLogger('wlsdeploy.util')
        self._wls_helper = WebLogicHelper(self._logger)

        self._oracle_home = None
        self._wl_home = None
        self._java_home = None
        self._domain_home = None
        self._domain_name = None
        self._domain_parent_dir = None
        self._domain_type = 'WLS'
        self._domain_typedef = None
        self._admin_url = None
        self._admin_user = None
        self._admin_password = None
        self._archive_file_name = None
        self._archive_file = None
        self._model_file = None
        self._previous_model_file = None
        self._print_usage = None
        self._variable_file_name = None
        self._run_rcu = False
        self._rcu_database = None
        self._rcu_prefix = None
        self._rcu_sys_pass = None
        self._rcu_schema_pass = None
        self._encryption_passphrase = None
        self._encrypt_manual = False
        self._encrypt_one_pass = None
        self._use_encryption = False
        self._wl_version = None
        self._wlst_mode = None
        self._recursive = False
        self._attributes_only = False
        self._folders_only = False

        if CommandLineArgUtil.ORACLE_HOME_SWITCH in arg_map:
            self._oracle_home = arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH]
            self._wl_home = self._wls_helper.get_weblogic_home(self._oracle_home)

        if CommandLineArgUtil.JAVA_HOME_SWITCH in arg_map:
            self._java_home = arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH]

        if CommandLineArgUtil.DOMAIN_HOME_SWITCH in arg_map:
            self._domain_home = arg_map[CommandLineArgUtil.DOMAIN_HOME_SWITCH]
            self._domain_name = os.path.basename(self._domain_home)

        if CommandLineArgUtil.DOMAIN_PARENT_SWITCH in arg_map:
            self._domain_parent_dir = arg_map[CommandLineArgUtil.DOMAIN_PARENT_SWITCH]

        if CommandLineArgUtil.DOMAIN_TYPE_SWITCH in arg_map:
            self._domain_type = arg_map[CommandLineArgUtil.DOMAIN_TYPE_SWITCH]

        if CommandLineArgUtil.ADMIN_URL_SWITCH in arg_map:
            self._admin_url = arg_map[CommandLineArgUtil.ADMIN_URL_SWITCH]

        if CommandLineArgUtil.ADMIN_USER_SWITCH in arg_map:
            self._admin_user = arg_map[CommandLineArgUtil.ADMIN_USER_SWITCH]

        if CommandLineArgUtil.ADMIN_PASS_SWITCH in arg_map:
            self._admin_password = arg_map[CommandLineArgUtil.ADMIN_PASS_SWITCH]

        if CommandLineArgUtil.ARCHIVE_FILE_SWITCH in arg_map:
            self._archive_file_name = arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH]

        if CommandLineArgUtil.MODEL_FILE_SWITCH in arg_map:
            self._model_file = arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH]

        if CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH in arg_map:
            self._previous_model_file = arg_map[CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH]

        if CommandLineArgUtil.PRINT_USAGE_SWITCH in arg_map:
            self._print_usage = arg_map[CommandLineArgUtil.PRINT_USAGE_SWITCH]

        if CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH in arg_map:
            self._attributes_only = arg_map[CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH]

        if CommandLineArgUtil.FOLDERS_ONLY_SWITCH in arg_map:
            self._folders_only = arg_map[CommandLineArgUtil.FOLDERS_ONLY_SWITCH]

        if CommandLineArgUtil.RECURSIVE_SWITCH in arg_map:
            self._recursive = arg_map[CommandLineArgUtil.RECURSIVE_SWITCH]

        if CommandLineArgUtil.VARIABLE_FILE_SWITCH in arg_map:
            self._variable_file_name = arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]

        if CommandLineArgUtil.RUN_RCU_SWITCH in arg_map:
            self._run_rcu = arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]

        if CommandLineArgUtil.RCU_DB_SWITCH in arg_map:
            self._rcu_database = arg_map[CommandLineArgUtil.RCU_DB_SWITCH]

        if CommandLineArgUtil.RCU_PREFIX_SWITCH in arg_map:
            self._rcu_prefix = arg_map[CommandLineArgUtil.RCU_PREFIX_SWITCH]

        if CommandLineArgUtil.RCU_SYS_PASS_SWITCH in arg_map:
            self._rcu_sys_pass = arg_map[CommandLineArgUtil.RCU_SYS_PASS_SWITCH]

        if CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH in arg_map:
            self._rcu_schema_pass = arg_map[CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH]

        if CommandLineArgUtil.DOMAIN_TYPEDEF in arg_map:
            self._domain_typedef = arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF]

        if CommandLineArgUtil.PASSPHRASE_SWITCH in arg_map:
            self._encryption_passphrase = arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH]

        if CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH in arg_map:
            self._encrypt_manual = arg_map[CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH]

        if CommandLineArgUtil.ONE_PASS_SWITCH in arg_map:
            self._encrypt_one_pass = arg_map[CommandLineArgUtil.ONE_PASS_SWITCH]

        if CommandLineArgUtil.USE_ENCRYPTION_SWITCH in arg_map:
            self._use_encryption = arg_map[CommandLineArgUtil.USE_ENCRYPTION_SWITCH]

        if CommandLineArgUtil.ARCHIVE_FILE in arg_map:
            self._archive_file = arg_map[CommandLineArgUtil.ARCHIVE_FILE]

        if CommandLineArgUtil.TARGET_VERSION_SWITCH in arg_map:
            self._wl_version = arg_map[CommandLineArgUtil.TARGET_VERSION_SWITCH]

        if CommandLineArgUtil.TARGET_MODE_SWITCH in arg_map:
            wlst_mode_string = arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH]
            if wlst_mode_string.lower() == 'online':
                self._wlst_mode = WlstModes.ONLINE
            else:
                self._wlst_mode = WlstModes.OFFLINE

        if self._wl_version is None:
            self._wl_version = self._wls_helper.get_actual_weblogic_version()

        if self._wlst_mode is None:
            self._wlst_mode = WlstModes.OFFLINE

        return

    def get_program_name(self):
        """
        Get the program name of the program that is executing.
        :return: the program name
        """
        return self._program_name

    def get_oracle_home(self):
        """
        Get the Oracle Home.
        :return: the Oracle Home
        """
        return self._oracle_home

    def get_wl_home(self):
        """
        Get the WebLogic Home.
        :return: the WebLogic Home
        """
        return self._wl_home

    def get_java_home(self):
        """
        Get the Java Home.
        :return: the Java Home
        """
        return self._java_home

    def get_domain_home(self):
        """
        Get the Domain Home.
        :return: the Domain Home
        """
        return self._domain_home

    def get_domain_name(self):
        """
        Get the Domain name.
        :return: the Domain name
        """
        return self._domain_name

    def set_domain_home(self, domain_home):
        """
        This method is a hack to allow create to add the domain home after reading the domain name from the model.
        This method is a no-op if the domain home was previously initialized via command-line argument processing.
        :param domain_home: the domain home directory
        """
        if self._domain_home is None and domain_home is not None and len(domain_home) > 0:
            self._domain_home = domain_home
            self._domain_name = os.path.basename(self._domain_home)
        return

    def get_domain_parent_dir(self):
        """
        Get the domain parent directory
        :return: the domain parent directory
        """
        return self._domain_parent_dir

    def get_domain_type(self):
        """
        Get the domain type.
        :return: the domain type
        """
        return self._domain_type

    def get_domain_typedef(self):
        """
        Get the domain typedef.
        :return: the domain typedef
        """
        return self._domain_typedef

    def get_admin_url(self):
        """
        Get the admin URL.
        :return: the admin URL
        """
        return self._admin_url

    def get_admin_user(self):
        """
        Get the admin username.
        :return: the admin username
        """
        return self._admin_user

    def get_admin_password(self):
        """
        Get the admin password.
        :return: the admin password
        """
        return self._admin_password

    def get_archive_file_name(self):
        """
        Get the archive file name.
        :return: the archive file name
        """
        return self._archive_file_name

    def get_archive_file(self):
        """
        Get the archive file.
        :return: the archive file
        """
        return self._archive_file

    def get_model_file(self):
        """
        Get the model file.
        :return: the model file
        """
        return self._model_file

    def get_previous_model_file(self):
        """
        Get the previous model file.
        :return: the previous model file
        """
        return self._previous_model_file

    def get_print_usage(self):
        """
        Get the print usage value.
        :return: the print usage value
        """
        return self._print_usage

    def get_folders_only_control_option(self):
        """
        Get the -folders_only command-line switch associated
        with print usage value.
        :return: the -folders_only command-line switch
        """
        return self._folders_only

    def get_attributes_only_control_option(self):
        """
        Get the -attributes_only command-line switch associated
        with print usage value.
        :return: the -attributes_only command-line switch
        """
        return self._attributes_only

    def get_recursive_control_option(self):
        """
        Get the -recursive command-line switch associated
        with print usage value.
        :return: the -recursive command-line switch
        """
        return self._recursive

    def get_variable_file(self):
        """
        Get the variable file.
        :return: the variable file
        """
        return self._variable_file_name

    def is_run_rcu(self):
        """
        Get whether or not to run RCU.
        :return: whether or not to run RCU
        """
        return self._run_rcu

    def get_rcu_database(self):
        """
        Get the RCU database connect string.
        :return: the RCU database connect string
        """
        return self._rcu_database

    def get_rcu_prefix(self):
        """
        Get the RCU prefix.
        :return: the RCU prefix
        """
        return self._rcu_prefix

    def get_rcu_sys_pass(self):
        """
        Get the RCU database SYS user password.
        :return: the RCU database SYS user password
        """
        return self._rcu_sys_pass

    def get_rcu_schema_pass(self):
        """
        Get the RCU schema users' password.
        :return: the RCU schema users' password
        """
        return self._rcu_schema_pass

    def get_encryption_passphrase(self):
        """
        Get the encryption passphrase.
        :return: the encryption passphrase
        """
        return self._encryption_passphrase

    def is_encryption_manual(self):
        """
        Get whether or not the user selected to do manual encryption.
        :return: whether or not the user selected to do manual encryption
        """
        return self._encrypt_manual

    def get_encrypt_one_pass(self):
        """
        Get the password to encrypt manually.
        :return: the password to encrypt manually
        """
        return self._encrypt_one_pass

    def is_using_encryption(self):
        """
        Get whether or not the model is using encryption.
        :return: whether or not the model is using encryption
        """
        return self._use_encryption

    def get_target_wls_version(self):
        """
        Get the target WebLogic version.
        :return: the target WebLogic version
        """
        return self._wl_version

    def get_target_wlst_mode(self):
        """
        Get the target WLST mode.
        :return: the target WLST mode
        """
        return self._wlst_mode

    def is_wlst_online(self):
        """
        Determine if the tool was started using WLST online mode
        :return: True if the tool is in online mode
        """
        return self._wlst_mode == WlstModes.ONLINE

    def is_wlst_offline(self):
        """
        Determine if the tool was started using WLST offline mode
        :return: True if the tool is in offline mode
        """
        return self._wlst_mode == WlstModes.OFFLINE

    def replace_tokens_in_path(self, attribute_name, resource_dict):
        """
        Replace any tokens in a path with the current values.
        :param attribute_name: the attrribute name
        :param resource_dict: the dictionary to use to lookup and replace the attribute value
        """
        separator = ':'
        path_elements = resource_dict[attribute_name].split(':')
        semicolon_path_elements = resource_dict[attribute_name].split(';')
        if len(semicolon_path_elements) > len(path_elements):
            separator = ';'
            path_elements = semicolon_path_elements

        for index, value in enumerate(path_elements):
            path_elements[index] = self.replace_token_string(value)

        result = ''
        for path_element in path_elements:
            if len(result) != 0:
                result += separator
            result += path_element

        resource_dict[attribute_name] = result
        return

    def has_token_prefix(self, path):
        """
        Determines if the specified path begins with one of the known, portable token prefix paths.
        :param path: the path to check for token prefix
        :return: true if the path begins with a known prefix, false otherwise
        """
        return path.startswith(self.__ORACLE_HOME_TOKEN) or \
               path.startswith(self.__WL_HOME_TOKEN) or \
               path.startswith(self.__DOMAIN_HOME_TOKEN) or \
               path.startswith(self.__CURRENT_DIRECTORY_TOKEN) or \
               path.startswith(self.__TEMP_DIRECTORY_TOKEN)

    def replace_tokens(self, resource_type, resource_name, attribute_name, resource_dict):
        """
        Replace the tokens in attribute value with the current value.
        :param resource_type: the resource type (used for logging purposes)
        :param resource_name: the resource name (used for logging purposes)
        :param attribute_name: the attribute name for which to replace tokens
        :param resource_dict: the dictionary to use to lookup and replace the attribute value
        """
        attribute_value = resource_dict[attribute_name]
        if attribute_value.startswith(self.__ORACLE_HOME_TOKEN):
            message = "Replacing {0} in {1} {2} {3} with {4}"
            self._logger.fine(message, self.__ORACLE_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_oracle_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.__ORACLE_HOME_TOKEN,
                                                                    self.get_oracle_home())
        elif attribute_value.startswith(self.__WL_HOME_TOKEN):
            message = "Replacing {0} in {1} {2} {3} with {4}"
            self._logger.fine(message, self.__WL_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_wl_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.__WL_HOME_TOKEN, self.get_wl_home())
        elif attribute_value.startswith(self.__DOMAIN_HOME_TOKEN):
            message = "Replacing {0} in {1} {2} {3} with {4}"
            self._logger.fine(message, self.__DOMAIN_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_domain_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.__DOMAIN_HOME_TOKEN,
                                                                    self.get_domain_home())
        elif attribute_value.startswith(self.__CURRENT_DIRECTORY_TOKEN):
            cwd = path_utils.fixup_path(os.getcwd())
            message = "Replacing {0} in {1} {2} {3} with {4}"
            self._logger.fine(message, self.__CURRENT_DIRECTORY_TOKEN, resource_type, resource_name,
                              attribute_name, cwd, class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.__CURRENT_DIRECTORY_TOKEN, cwd)
        elif attribute_value.startswith(self.__TEMP_DIRECTORY_TOKEN):
            temp_dir = path_utils.fixup_path(tempfile.gettempdir())
            message = "Replacing {0} in {1} {2} {3} with {4}"
            self._logger.fine(message, self.__TEMP_DIRECTORY_TOKEN, resource_type, resource_name, attribute_name,
                              temp_dir, class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.__TEMP_DIRECTORY_TOKEN, temp_dir)

        return

    def replace_token_string(self, string_value):
        """
        Replace the tokens in string value with the current value of the token.
        :param string_value: the value on which to perform token replacement
        :return: the detokenized value, or the original value if there were no tokens
        """
        if string_value is None:
            result = None
        elif string_value.startswith(self.__ORACLE_HOME_TOKEN):
            result = _replace(string_value, self.__ORACLE_HOME_TOKEN, self.get_oracle_home())
        elif string_value.startswith(self.__WL_HOME_TOKEN):
            result = _replace(string_value, self.__WL_HOME_TOKEN, self.get_wl_home())
        elif string_value.startswith(self.__DOMAIN_HOME_TOKEN):
            result = _replace(string_value, self.__DOMAIN_HOME_TOKEN, self.get_domain_home())
        elif string_value.startswith(self.__CURRENT_DIRECTORY_TOKEN):
            result = _replace(string_value, self.__CURRENT_DIRECTORY_TOKEN, path_utils.fixup_path(os.getcwd()))
        elif string_value.startswith(self.__TEMP_DIRECTORY_TOKEN):
            result = _replace(string_value, self.__TEMP_DIRECTORY_TOKEN, path_utils.fixup_path(tempfile.gettempdir()))
        else:
            result = string_value

        return result

    def tokenize_path(self, path):
        """
        Replace known directories that will be different in the target with tokens denoting the type
        of directory

        :param path: to check for directories to be tokenized
        :return: tokenized path or original path
        """
        my_path = path_utils.fixup_path(path)
        tmp_dir = path_utils.fixup_path(tempfile.gettempdir())
        cwd = path_utils.fixup_path(os.path.dirname(os.path.abspath(__file__)))

        # decide later what is required to be in context home for appropriate exception prevention
        result = my_path
        if my_path:
            if self.get_wl_home() and my_path.startswith(self.get_wl_home()):
                result = my_path.replace(self.get_wl_home(), self.__WL_HOME_TOKEN)
            elif self.get_domain_home() and  my_path.startswith(self.get_domain_home()):
                result = my_path.replace(self.get_domain_home(), self.__DOMAIN_HOME_TOKEN)
            elif self.get_oracle_home() and my_path.startswith(self.get_oracle_home()):
                result = my_path.replace(self.get_oracle_home(), self.__ORACLE_HOME_TOKEN)
            elif my_path.startswith(cwd):
                result = my_path.replace(cwd, self.__CURRENT_DIRECTORY_TOKEN)
            elif my_path.startswith(tmp_dir):
                result = my_path.replace(tmp_dir, self.__TEMP_DIRECTORY_TOKEN)

        return result

    def tokenize_classpath(self, classpath):
        """
        Replace known types of directories with a tokens that represent the directory.

        :param classpath: containing a string of directories separated by environment specific classpath separator
        :return: tokenized classpath string
        """
        cp_elements, separator = path_utils.split_classpath(classpath)
        for index, value in enumerate(cp_elements):
            cp_elements[index] = self.tokenize_path(value)

        return separator.join(cp_elements)

    # private methods


def _replace(string_value, token, replace_token_string):
    """
    Replace the token in the string value with the replace token string. This replace method
    replaces the python replace because if the string only contains the token, python throws an exception
    :param token: in the string to replace
    :param string_value: string value to fix up
    :param replace_token_string: value with which the token is replaced
    :return: updated string value
    """
    if string_value == token:
        result = replace_token_string
    else:
        result = string_value.replace(token, replace_token_string)
    return result
