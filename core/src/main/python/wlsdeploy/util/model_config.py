"""
Copyright (c) 2020, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

from java.io import IOException
from java.lang import Long
from java.lang import NumberFormatException
from java.lang import System

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import path_utils
from wlsdeploy.util import string_utils

TOOL_PROPERTIES_FILE_NAME = 'tool.properties'

_logger = PlatformLogger('wlsdeploy.config')
_class_name = 'ModelConfig'
_config_object = None

# Tool Properties for configuration and default values if properties not loaded

# WLST TIMEOUT PROPERTIES
CONNECT_TIMEOUT_PROP = 'connect.timeout'
CONNECT_TIMEOUT_DEFAULT = '120000'
ACTIVATE_TIMEOUT_PROP = 'activate.timeout'
ACTIVATE_TIMEOUT_DEFAULT = '180000'
DEPLOY_TIMEOUT_PROP = 'deploy.timeout'
DEPLOY_TIMEOUT_DEFAULT = '180000'
REDEPLOY_TIMEOUT_PROP = 'redeploy.timeout'
REDEPLOY_TIMEOUT_DEFAULT = '180000'
UNDEPLOY_TIMEOUT_PROP = 'undeploy.timeout'
UNDEPLOY_TIMEOUT_DEFAULT = '180000'
START_APP_TIMEOUT_PROP = 'start.application.timeout'
START_APP_TIMEOUT_DEFAULT = '180000'
STOP_APP_TIMEOUT_PROP = 'stop.application.timeout'
STOP_APP_TIMEOUT_DEFAULT = '180000'
SET_SERVER_GRPS_TIMEOUT_PROP = 'set.server.groups.timeout'
SET_SERVER_GRPS_TIMEOUT_DEFAULT = '30000'
WLST_EDIT_LOCK_ACQUIRE_TIMEOUT_PROP = 'wlst.edit.lock.acquire.timeout'
WLST_EDIT_LOCK_ACQUIRE_TIMEOUT_DEFAULT = '0'
WLST_EDIT_LOCK_RELEASE_TIMEOUT_PROP = 'wlst.edit.lock.release.timeout'
WLST_EDIT_LOCK_RELEASE_TIMEOUT_DEFAULT = '-1'
WLST_EDIT_LOCK_EXCLUSIVE_PROP = 'wlst.edit.lock.exclusive'
WLST_EDIT_LOCK_EXCLUSIVE_DEFAULT = 'false'
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


def _load_properties_file():
    """
    Load the properties from the WLSDEPLOY properties file into dictionary
    :return: tool config properties in dict format
    """
    _method_name = 'load_properties_file'
    _logger.entering(class_name=_class_name, method_name=_method_name)
    wlsdeploy_path = path_utils.find_config_path(TOOL_PROPERTIES_FILE_NAME)
    result = None
    try:
        result = string_utils.load_properties(wlsdeploy_path)
    except IOException, ioe:
        _logger.warning('WLSDPLY-01570', wlsdeploy_path, ioe.getMessage(),
                        class_name=_class_name, method_name=_method_name)

        # Return an empty dict so that failing to load the tool.properties file does
        # not prevent the code above from working using the default values.  The WLST
        # unit tests are depending on this behavior until they are refactored to all
        # copy the tool.properties file into the target/unit_tests/config directory
        # and setting the WDT_CUSTOM_CONFIG environment variable to point to it.
        #
        result = dict()
    _logger.exiting(class_name=_class_name, method_name=_method_name)
    return result
