"""
Copyright (c) 2020, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from java.io import IOException
from java.lang import Boolean
from java.lang import Long
from java.lang import NumberFormatException
from java.lang import System

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import path_helper
from wlsdeploy.util import string_utils

TOOL_PROPERTIES_FILE_NAME = 'tool.properties'

_logger = PlatformLogger('wlsdeploy.config')
_class_name = 'ModelConfig'
_config_object = None

# Tool Properties for configuration and default values if properties not loaded

# WLST TIMEOUT PROPERTIES
ACTIVATE_TIMEOUT_PROP = 'activate.timeout'
ACTIVATE_TIMEOUT_DEFAULT = '180000'
ARCHIVE_CUSTOM_FOLDER_SIZE_LIMIT_PROP = 'archive.custom.folder.size.limit'
ARCHIVE_CUSTOM_FOLDER_SIZE_LIMIT_DEFAULT = '1048576' # 1 MB
CONNECT_TIMEOUT_PROP = 'connect.timeout'
CONNECT_TIMEOUT_DEFAULT = '120000'
DEPLOY_TIMEOUT_PROP = 'deploy.timeout'
DEPLOY_TIMEOUT_DEFAULT = '180000'
DISABLE_RCU_DROP_SCHEMA_PROP='disable.rcu.drop.schema'
DISABLE_RCU_DROP_SCHEMA_DEFAULT='false'
ENABLE_CREATE_DOMAIN_PASSWORD_VALIDATION_PROP = 'enable.create.domain.password.validation'
ENABLE_CREATE_DOMAIN_PASSWORD_VALIDATION_DEFAULT = 'true'
REDEPLOY_TIMEOUT_PROP = 'redeploy.timeout'
REDEPLOY_TIMEOUT_DEFAULT = '180000'
SET_SERVER_GRPS_TIMEOUT_PROP = 'set.server.groups.timeout'
SET_SERVER_GRPS_TIMEOUT_DEFAULT = '30000'
SSH_DEFAULT_PRIVATE_KEY_FILE_NAME_PROP='ssh.private.key.default.file.name'
SSH_DEFAULT_PRIVATE_KEY_FILE_NAME_DEFAULT='id_rsa'
START_APP_TIMEOUT_PROP = 'start.application.timeout'
START_APP_TIMEOUT_DEFAULT = '180000'
STOP_APP_TIMEOUT_PROP = 'stop.application.timeout'
STOP_APP_TIMEOUT_DEFAULT = '180000'
STORE_DISCOVER_ADMIN_CREDENTIALS_PROP='store.discover.admin_credentials'
STORE_DISCOVER_ADMIN_CREDENTIALS_DEFAULT='true'
STORE_DISCOVERED_PASSWORDS_IN_CLEAR_TEXT_PROP='store.discovered.passwords.in.clear.text'
STORE_DISCOVERED_PASSWORDS_IN_CLEAR_TEXT_DEFAULT='false'
UNDEPLOY_TIMEOUT_PROP = 'undeploy.timeout'
UNDEPLOY_TIMEOUT_DEFAULT = '180000'
USE_DEPRECATION_EXIT_CODE_PROP='use.deprecation.exit.code'
USE_DEPRECATION_EXIT_CODE_DEFAULT='false'
USE_SERVER_VERSION_FOR_ONLINE_OPERATIONS_PROP='use.server.version.for.online.operations'
USE_SERVER_VERSION_FOR_ONLINE_OPERATIONS_DEFAULT='true'
USE_SSH_COMPRESSION_PROP='use.ssh.compression'
USE_SSH_COMPRESSION_DEFAULT='true'
WLST_EDIT_LOCK_ACQUIRE_TIMEOUT_PROP = 'wlst.edit.lock.acquire.timeout'
WLST_EDIT_LOCK_ACQUIRE_TIMEOUT_DEFAULT = '0'
WLST_EDIT_LOCK_EXCLUSIVE_PROP = 'wlst.edit.lock.exclusive'
WLST_EDIT_LOCK_EXCLUSIVE_DEFAULT = 'false'
WLST_EDIT_LOCK_RELEASE_TIMEOUT_PROP = 'wlst.edit.lock.release.timeout'
WLST_EDIT_LOCK_RELEASE_TIMEOUT_DEFAULT = '-1'
YAML_FILE_MAX_CODE_POINTS_PROP = 'yaml.max.file.size'
YAML_FILE_MAX_CODE_POINTS_DEFAULT = '0'

# System Property overrides for WLST timeout properties
SYS_PROP_PREFIX = 'wdt.config.'

# This method is used to get the model configuration singleton object.
# There is an implicit assumption that the object is created by the
# model context
def get_model_config(program_name='unknown'):
    global _config_object
    if _config_object is None:
        _config_object = ModelConfiguration(program_name)
    return _config_object


class ModelConfiguration(object):
    """
    This class encapsulates the tool properties used in configuring and tuning
    """

    def __init__(self, program_name):
        """
        Load the properties from the tools.properties file and save the resulting dictionary
        :return:
        """
        self._program_name = program_name
        self.__config_dict = _load_properties_file()

    def get_connect_timeout(self):
        """
        Return the connect timeout from tool properties.
        :return: connect timeout
        """
        return self._get_from_dict(CONNECT_TIMEOUT_PROP, CONNECT_TIMEOUT_DEFAULT)

    def get_activate_timeout(self):
        """
        Return the activate timeout from tool properties.
        :return: activate timeout
        """
        return self._get_from_dict_as_long(ACTIVATE_TIMEOUT_PROP, ACTIVATE_TIMEOUT_DEFAULT)

    def get_deploy_timeout(self):
        """
        Return the deploy timeout from tool properties.
        :return: deploy timeout
        """
        return self._get_from_dict_as_long(DEPLOY_TIMEOUT_PROP, DEPLOY_TIMEOUT_DEFAULT)

    def get_redeploy_timeout(self):
        """
        Return the redeploy timeout from tool properties
        :return: redeploy timeout
        """
        return self._get_from_dict_as_long(REDEPLOY_TIMEOUT_PROP, REDEPLOY_TIMEOUT_DEFAULT)

    def get_undeploy_timeout(self):
        """
        Return undeploy timeout from tool properties.
        :return: undeploy timeout
        """
        return self._get_from_dict_as_long(UNDEPLOY_TIMEOUT_PROP, UNDEPLOY_TIMEOUT_DEFAULT)

    def get_stop_app_timeout(self):
        """
        Return stop application timeout from tool properties.
        :return: stop application timeout
        """
        return self._get_from_dict_as_long(STOP_APP_TIMEOUT_PROP, STOP_APP_TIMEOUT_DEFAULT)

    def get_start_app_timeout(self):
        """
        Return start application timeout from tool properties.
        :return: start application timeout
        """
        return self._get_from_dict_as_long(START_APP_TIMEOUT_PROP, START_APP_TIMEOUT_DEFAULT)

    def get_set_server_grps_timeout(self):
        """
        Return timeout value for setServerGroups from tool properties
        :return: set server groups timeout
        """
        return self._get_from_dict_as_long(SET_SERVER_GRPS_TIMEOUT_PROP, SET_SERVER_GRPS_TIMEOUT_DEFAULT)

    def get_wlst_edit_lock_acquire_timeout(self):
        """
        Return the waitTimeInMillis for startEdit from tool properties
        :return: wlst edit lock acquire timeout
        """
        return self._get_from_dict_as_long(WLST_EDIT_LOCK_ACQUIRE_TIMEOUT_PROP, WLST_EDIT_LOCK_ACQUIRE_TIMEOUT_DEFAULT)

    def get_wlst_edit_lock_release_timeout(self):
        """
        Return the timeOutInMillis for startEdit from tool properties
        :return: wlst edit lock release timeout
        """
        return self._get_from_dict_as_long(WLST_EDIT_LOCK_RELEASE_TIMEOUT_PROP, WLST_EDIT_LOCK_RELEASE_TIMEOUT_DEFAULT)

    def get_wlst_edit_lock_exclusive(self):
        """
        Returns the exclusive value for startEdit from tool properties
        :return: the string 'true' or 'false' (default)
        """
        return self._get_from_dict(WLST_EDIT_LOCK_EXCLUSIVE_PROP, WLST_EDIT_LOCK_EXCLUSIVE_DEFAULT)

    def get_yaml_file_max_code_points(self):
        """
        Returns the exclusive value for startEdit from tool properties
        :return: the string 'true' or 'false' (default)
        """
        return self._get_from_dict_as_long(YAML_FILE_MAX_CODE_POINTS_PROP, YAML_FILE_MAX_CODE_POINTS_DEFAULT)

    def get_use_deprecation_exit_code(self):
        """
        Returns the value to determine whether deprecation messages should trigger the use of a non-zero exit code
        :return: the string 'true' or 'false' (default)
        """
        return self._get_from_dict(USE_DEPRECATION_EXIT_CODE_PROP, USE_DEPRECATION_EXIT_CODE_DEFAULT)

    def get_disable_rcu_drop_schema(self):
        """
        Returns the value to determine whether to disable RCU from dropping schemas if they exist.
        :return: the string 'true' or 'false' (default)
        """
        return self._get_from_dict(DISABLE_RCU_DROP_SCHEMA_PROP, DISABLE_RCU_DROP_SCHEMA_DEFAULT)

    def get_enable_create_domain_password_validation(self):
        """
        Returns the value to determine whether to enable
        :return:the string 'true' or 'false' (default)
        """
        return self._get_from_dict(ENABLE_CREATE_DOMAIN_PASSWORD_VALIDATION_PROP,
                                   ENABLE_CREATE_DOMAIN_PASSWORD_VALIDATION_DEFAULT)

    def get_ssh_private_key_default_file_name(self):
        """
        Return the default file name for the SSH private key when using a passphrase
        :return: the default file name for the private key when using a passphrase
        """
        return self._get_from_dict(SSH_DEFAULT_PRIVATE_KEY_FILE_NAME_PROP, SSH_DEFAULT_PRIVATE_KEY_FILE_NAME_DEFAULT)

    def use_ssh_compression(self):
        """
        Return whether to use SSH compression.
        :return: whether to use SSH compression
        """
        return self._get_from_dict_as_boolean(USE_SSH_COMPRESSION_PROP, USE_SSH_COMPRESSION_DEFAULT)

    def use_server_version_for_online_operations(self):
        """
        Return whether online operations should use the server version for loading the aliases.
        :return: true if using the server version, false otherwise
        """
        return self._get_from_dict_as_boolean(USE_SERVER_VERSION_FOR_ONLINE_OPERATIONS_PROP,
                                              USE_SERVER_VERSION_FOR_ONLINE_OPERATIONS_DEFAULT)

    def get_archive_custom_folder_size_limit(self):
        """
        Return the recommended limit for the size of the archive custom folder contents.
        :return: the recommended limit
        """
        return self._get_from_dict_as_long(ARCHIVE_CUSTOM_FOLDER_SIZE_LIMIT_PROP,
                                           ARCHIVE_CUSTOM_FOLDER_SIZE_LIMIT_DEFAULT)

    def get_store_discovered_passwords_in_clear_text(self):
        """
        Whether to store discovered passwords in clear text in the model
        :return: True, if passwords should be stored in clear text; False otherwise
        """
        return self._get_from_dict_as_boolean(STORE_DISCOVERED_PASSWORDS_IN_CLEAR_TEXT_PROP,
                                              STORE_DISCOVERED_PASSWORDS_IN_CLEAR_TEXT_DEFAULT)

    def get_store_discover_admin_credentials(self):
        """
        When performing online discovery of security provider data, should the
        model's admin credentials be populated from supplied command-line arguments?
        :return:
        """
        return self._get_from_dict_as_boolean(STORE_DISCOVER_ADMIN_CREDENTIALS_PROP,
                                              STORE_DISCOVER_ADMIN_CREDENTIALS_DEFAULT)

    def _get_from_dict(self, name, default_value=None):
        _method_name = '_get_from_dict'
        _logger.entering(name, default_value, class_name=_class_name, method_name=_method_name)

        result = default_value
        if name in self.__config_dict:
            result = self.__config_dict[name]
        result = System.getProperty(SYS_PROP_PREFIX + name, result)

        _logger.exiting(result=result, class_name=_class_name, method_name=_method_name)
        return result

    def _get_from_dict_as_long(self, name, default_value=None):
        _method_name = '_get_from_dict_as_long'
        result = self._get_from_dict(name, default_value)
        try:
            result = Long(result).longValue()
        except NumberFormatException, nfe:
            _logger.warning('WLSDPLY-01571', result, name, self._program_name, default_value, nfe.getLocalizedMessage(),
                            class_name=_class_name, method_name=_method_name)
            result = Long(default_value).longValue()
        return result

    def _get_from_dict_as_boolean(self, name, default_value=None):
        _method_name = '_get_from_dict_as_boolean'
        result = self._get_from_dict(name, default_value)
        return Boolean.parseBoolean(result)


def _load_properties_file():
    """
    Load the properties from the WLSDEPLOY properties file into dictionary
    :return: tool config properties in dict format
    """
    _method_name = 'load_properties_file'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    _path_helper = path_helper.get_path_helper()
    tool_properties_path = _path_helper.find_local_config_path(TOOL_PROPERTIES_FILE_NAME)

    result = None
    try:
        result = string_utils.load_properties(tool_properties_path)
    except IOException, ioe:
        _logger.warning('WLSDPLY-01570', tool_properties_path, ioe.getMessage(),
                        class_name=_class_name, method_name=_method_name)

        # Return an empty dict so that failing to load the tool.properties file does
        # not prevent the code above from working using the default values.  The WLST
        # unit tests depend on this behavior until they are refactored to all
        # copy the tool.properties file into the target/unit_tests/config directory
        # and setting the WLSDEPLOY_CUSTOM_CONFIG environment variable to point to it.
        #
        result = dict()
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return result
