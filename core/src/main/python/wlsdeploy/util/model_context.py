"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import copy
import os
import re
import tempfile

import java.net.URI as URI

from oracle.weblogic.deploy.util import XPathUtil
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging import platform_logger
from wlsdeploy.util import validate_configuration
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util import path_utils
from wlsdeploy.util import string_utils
from wlsdeploy.util import model_config
from wlsdeploy.util.target_configuration import TargetConfiguration
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.validate_configuration import ValidateConfiguration
from wlsdeploy.util.weblogic_helper import WebLogicHelper


class ModelContext(object):
    """
    This class contains fields derived from the command-line parameters and external configuration files,
    excluding the model file.
    """
    _class_name = "ModelContext"

    ORACLE_HOME_TOKEN = '@@ORACLE_HOME@@'
    WL_HOME_TOKEN = '@@WL_HOME@@'
    DOMAIN_HOME_TOKEN = '@@DOMAIN_HOME@@'
    JAVA_HOME_TOKEN = '@@JAVA_HOME@@'
    CURRENT_DIRECTORY_TOKEN = '@@PWD@@'
    TEMP_DIRECTORY_TOKEN = '@@TMP@@'

    DB_USER_DEFAULT = 'SYS'

    def __init__(self, program_name, arg_map):
        """
        Create a new model context instance.
        Tools should use model_context_helper.create_context(), to ensure that the typedef is initialized correctly.
        Unit tests should use this constructor directly, since typedef files are not deployed.
        :param program_name: the program name, used for logging
        :param arg_map: all the arguments passed to the tool
        """
        self._program_name = program_name
        self._logger = platform_logger.PlatformLogger('wlsdeploy.util')
        self._wls_helper = WebLogicHelper(self._logger)
        self._model_config = model_config.get_model_config(self._program_name)

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
        self._interactive_mode = False
        self._attributes_only = False
        self._folders_only = False
        self._opss_wallet_passphrase = None
        self._opss_wallet = None
        self._update_rcu_schema_pass = False
        self._validation_method = None
        self._validate_configuration = None  # lazy load
        self._cancel_changes_if_restart_required = None
        self._domain_resource_file = None
        self._output_dir = None
        self._target = None
        self._target_configuration = None  # lazy load
        self._variable_injector_file = None
        self._variable_keywords_file = None
        self._variable_properties_file = None
        self._rcu_db_user = self.DB_USER_DEFAULT
        self._discard_current_edit = False
        self._wait_for_edit_lock = False
        self._remote = False
        self._skip_archive = False

        self._trailing_args = []

        if self._wl_version is None:
            self._wl_version = self._wls_helper.get_actual_weblogic_version()


        if self._wlst_mode is None:
            self._wlst_mode = WlstModes.OFFLINE

        self.__copy_from_args(arg_map)

    def __copy_from_args(self, arg_map):
        _method_name = '__copy_from_args'
        if CommandLineArgUtil.ORACLE_HOME_SWITCH in arg_map:
            self._oracle_home = arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH]
            psu = XPathUtil(self._oracle_home).getPSU()
            if psu is not None:
                self._wl_version += '.' + psu

            self._logger.info('WLSDPLY-01050', self._wl_version, class_name=self._class_name,
                              method_name=_method_name)
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

        if CommandLineArgUtil.DISCARD_CURRENT_EDIT_SWITCH in arg_map:
            self._discard_current_edit = arg_map[CommandLineArgUtil.DISCARD_CURRENT_EDIT_SWITCH]

        if CommandLineArgUtil.WAIT_FOR_EDIT_LOCK_SWITCH in arg_map:
            self._wait_for_edit_lock = arg_map[CommandLineArgUtil.WAIT_FOR_EDIT_LOCK_SWITCH]

        if CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH in arg_map:
            self._previous_model_file = arg_map[CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH]

        if CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH in arg_map:
            self._attributes_only = arg_map[CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH]

        if CommandLineArgUtil.FOLDERS_ONLY_SWITCH in arg_map:
            self._folders_only = arg_map[CommandLineArgUtil.FOLDERS_ONLY_SWITCH]

        if CommandLineArgUtil.RECURSIVE_SWITCH in arg_map:
            self._recursive = arg_map[CommandLineArgUtil.RECURSIVE_SWITCH]

        if CommandLineArgUtil.INTERACTIVE_MODE_SWITCH in arg_map:
            self._interactive_mode = arg_map[CommandLineArgUtil.INTERACTIVE_MODE_SWITCH]

        if CommandLineArgUtil.VARIABLE_FILE_SWITCH in arg_map:
            self._variable_file_name = arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]

        if CommandLineArgUtil.REMOTE_SWITCH in arg_map:
            self._remote = arg_map[CommandLineArgUtil.REMOTE_SWITCH]

        if CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH in arg_map:
            self._skip_archive = arg_map[CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH]

        if CommandLineArgUtil.RUN_RCU_SWITCH in arg_map:
            self._run_rcu = arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]

        if CommandLineArgUtil.RCU_DB_SWITCH in arg_map:
            self._rcu_database = arg_map[CommandLineArgUtil.RCU_DB_SWITCH]

        if CommandLineArgUtil.RCU_PREFIX_SWITCH in arg_map:
            self._rcu_prefix = arg_map[CommandLineArgUtil.RCU_PREFIX_SWITCH]

        if CommandLineArgUtil.RCU_SYS_PASS_SWITCH in arg_map:
            self._rcu_sys_pass = arg_map[CommandLineArgUtil.RCU_SYS_PASS_SWITCH]

        if CommandLineArgUtil.RCU_DB_USER_SWITCH in arg_map:
            self._rcu_db_user = arg_map[CommandLineArgUtil.RCU_DB_USER_SWITCH]

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

        if CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH in arg_map:
            self._cancel_changes_if_restart_required = arg_map[CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH]

        if CommandLineArgUtil.USE_ENCRYPTION_SWITCH in arg_map:
            self._use_encryption = arg_map[CommandLineArgUtil.USE_ENCRYPTION_SWITCH]

        if CommandLineArgUtil.ARCHIVE_FILE in arg_map:
            self._archive_file = arg_map[CommandLineArgUtil.ARCHIVE_FILE]

        if CommandLineArgUtil.OPSS_WALLET_PASSPHRASE in arg_map:
            self._opss_wallet_passphrase = arg_map[CommandLineArgUtil.OPSS_WALLET_PASSPHRASE]

        if CommandLineArgUtil.OPSS_WALLET_SWITCH in arg_map:
            self._opss_wallet = arg_map[CommandLineArgUtil.OPSS_WALLET_SWITCH]

        if CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH in arg_map:
            self._update_rcu_schema_pass = True

        if CommandLineArgUtil.VALIDATION_METHOD in arg_map:
            self._validation_method = arg_map[CommandLineArgUtil.VALIDATION_METHOD]

        if CommandLineArgUtil.TARGET_VERSION_SWITCH in arg_map:
            self._wl_version = arg_map[CommandLineArgUtil.TARGET_VERSION_SWITCH]

        if CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH in arg_map:
            self._domain_resource_file = arg_map[CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH]

        if CommandLineArgUtil.TRAILING_ARGS_SWITCH in arg_map:
            self._trailing_args = arg_map[CommandLineArgUtil.TRAILING_ARGS_SWITCH]

        if CommandLineArgUtil.TARGET_SWITCH in arg_map:
            self._target = arg_map[CommandLineArgUtil.TARGET_SWITCH]

        if CommandLineArgUtil.TARGET_MODE_SWITCH in arg_map:
            wlst_mode_string = arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH]
            if type(wlst_mode_string) == int:
                self._wlst_mode = wlst_mode_string
            else:
                if wlst_mode_string.lower() == 'online':
                    self._wlst_mode = WlstModes.ONLINE
                else:
                    self._wlst_mode = WlstModes.OFFLINE

        if CommandLineArgUtil.OUTPUT_DIR_SWITCH in arg_map:
            self._output_dir = arg_map[CommandLineArgUtil.OUTPUT_DIR_SWITCH]

        if CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH in arg_map:
            self._variable_injector_file = arg_map[CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH]

        if CommandLineArgUtil.VARIABLE_KEYWORDS_FILE_SWITCH in arg_map:
            self._variable_keywords_file = arg_map[CommandLineArgUtil.VARIABLE_KEYWORDS_FILE_SWITCH]

        if CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH in arg_map:
            self._variable_properties_file = arg_map[CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH]

    def __copy__(self):
        arg_map = dict()
        if self._oracle_home is not None:
            arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH] = self._oracle_home
        if self._java_home is not None:
            arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH] = self._java_home
        if self._domain_home is not None:
            arg_map[CommandLineArgUtil.DOMAIN_HOME_SWITCH] = self._domain_home
        if self._domain_parent_dir is not None:
            arg_map[CommandLineArgUtil.DOMAIN_PARENT_SWITCH] = self._domain_parent_dir
        if self._domain_type is not None:
            arg_map[CommandLineArgUtil.DOMAIN_TYPE_SWITCH] = self._domain_type
        if self._admin_url is not None:
            arg_map[CommandLineArgUtil.ADMIN_URL_SWITCH] = self._admin_url
        if self._admin_user is not None:
            arg_map[CommandLineArgUtil.ADMIN_USER_SWITCH] = self._admin_user
        if self._admin_password is not None:
            arg_map[CommandLineArgUtil.ADMIN_PASS_SWITCH] = self._admin_password
        if self._archive_file_name is not None:
            arg_map[CommandLineArgUtil.ARCHIVE_FILE_SWITCH] = self._archive_file_name
        if self._model_file is not None:
            arg_map[CommandLineArgUtil.MODEL_FILE_SWITCH] = self._model_file
        if self._previous_model_file is not None:
            arg_map[CommandLineArgUtil.PREVIOUS_MODEL_FILE_SWITCH] = self._previous_model_file
        if self._attributes_only is not None:
            arg_map[CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH] = self._attributes_only
        if self._folders_only is not None:
            arg_map[CommandLineArgUtil.FOLDERS_ONLY_SWITCH] = self._folders_only
        if self._recursive is not None:
            arg_map[CommandLineArgUtil.RECURSIVE_SWITCH] = self._recursive
        if self._interactive_mode is not None:
            arg_map[CommandLineArgUtil.INTERACTIVE_MODE_SWITCH] = self._interactive_mode
        if self._remote is not None:
            arg_map[CommandLineArgUtil.REMOTE_SWITCH] = self._remote
        if self._skip_archive is not None:
            arg_map[CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH] = self._skip_archive
        if self._variable_file_name is not None:
            arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH] = self._variable_file_name
        if self._run_rcu is not None:
            arg_map[CommandLineArgUtil.RUN_RCU_SWITCH] = self._run_rcu
        if self._discard_current_edit is not None:
            arg_map[CommandLineArgUtil.DISCARD_CURRENT_EDIT_SWITCH] = self._discard_current_edit
        if self._wait_for_edit_lock is not None:
            arg_map[CommandLineArgUtil.WAIT_FOR_EDIT_LOCK_SWITCH] = self._wait_for_edit_lock
        if self._rcu_database is not None:
            arg_map[CommandLineArgUtil.RCU_DB_SWITCH] = self._rcu_database
        if self._rcu_prefix is not None:
            arg_map[CommandLineArgUtil.RCU_PREFIX_SWITCH] = self._rcu_prefix
        if self._rcu_sys_pass is not None:
            arg_map[CommandLineArgUtil.RCU_SYS_PASS_SWITCH] = self._rcu_sys_pass
        if self._rcu_db_user is not None:
            arg_map[CommandLineArgUtil.RCU_DB_USER_SWITCH] = self._rcu_db_user
        if self._rcu_schema_pass is not None:
            arg_map[CommandLineArgUtil.RCU_SCHEMA_PASS_SWITCH] = self._rcu_schema_pass
        if self._domain_typedef is not None:
            arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF] = self._domain_typedef
        if self._encryption_passphrase is not None:
            arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = self._encryption_passphrase
        if self._encrypt_manual is not None:
            arg_map[CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH] = self._encrypt_manual
        if self._encrypt_one_pass is not None:
            arg_map[CommandLineArgUtil.ONE_PASS_SWITCH] = self._encrypt_one_pass
        if self._cancel_changes_if_restart_required is not None:
            arg_map[CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH] = self._cancel_changes_if_restart_required
        if self._use_encryption is not None:
            arg_map[CommandLineArgUtil.USE_ENCRYPTION_SWITCH] = self._use_encryption
        if self._archive_file is not None:
            arg_map[CommandLineArgUtil.ARCHIVE_FILE] = self._archive_file
        if self._opss_wallet_passphrase is not None:
            arg_map[CommandLineArgUtil.OPSS_WALLET_PASSPHRASE] = self._opss_wallet_passphrase
        if self._opss_wallet is not None:
            arg_map[CommandLineArgUtil.OPSS_WALLET_SWITCH] = self._opss_wallet
        if self._update_rcu_schema_pass is not None:
            arg_map[CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH] = self._update_rcu_schema_pass
        if self._validation_method is not None:
            arg_map[CommandLineArgUtil.VALIDATION_METHOD] = self._validation_method
        if self._wl_version is not None:
            arg_map[CommandLineArgUtil.TARGET_VERSION_SWITCH] = self._wl_version
        if self._domain_resource_file is not None:
            arg_map[CommandLineArgUtil.DOMAIN_RESOURCE_FILE_SWITCH] = self._domain_resource_file
        if self._trailing_args is not None:
            arg_map[CommandLineArgUtil.TRAILING_ARGS_SWITCH] = self._trailing_args
        if self._target is not None:
            arg_map[CommandLineArgUtil.TARGET_SWITCH] = self._target
        if self._wlst_mode is not None:
            arg_map[CommandLineArgUtil.TARGET_MODE_SWITCH] = self._wlst_mode
        if self._output_dir is not None:
            arg_map[CommandLineArgUtil.OUTPUT_DIR_SWITCH] = self._output_dir
        if self._variable_injector_file is not None:
            arg_map[CommandLineArgUtil.VARIABLE_INJECTOR_FILE_SWITCH] = self._variable_injector_file
        if self._variable_keywords_file is not None:
            arg_map[CommandLineArgUtil.VARIABLE_KEYWORDS_FILE_SWITCH] = self._variable_keywords_file
        if self._variable_properties_file is not None:
            arg_map[CommandLineArgUtil.VARIABLE_PROPERTIES_FILE_SWITCH] = self._variable_properties_file

        return ModelContext(self._program_name, arg_map)

    def get_model_config(self):
        """
        Return the encapsulated tool properties configuration instance.
        :return: model configuration instance
        """
        return self._model_config

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

    def get_domain_resource_file(self):
        """
        Get the domain resource file.
        :return: the domain resource file
        """
        return self._domain_resource_file

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

    def is_cancel_changes_if_restart_required(self):
        """
        Get the cancel changes if restart required
        :return: true or false
        """
        return self._cancel_changes_if_restart_required

    def is_discard_current_edit(self):
        """
        Get the discard current edit value.
        :return: true or false
        """
        return self._discard_current_edit

    def is_wait_for_edit_lock(self):
        """
        Get the wait for edit lock value.
        :return: true or false
        """
        return self._wait_for_edit_lock

    def get_opss_wallet(self):
        """
        Get the opss wallet.
        :return: the opss wallet
        """
        return self._opss_wallet

    def get_opss_wallet_passphrase(self):
        """
        Get the wallet passphrase.
        :return: the wallet passphrase
        """
        return self._opss_wallet_passphrase

    def get_update_rcu_schema_pass(self):
        """
        Get the update rcu schema password flag
        """
        return self._update_rcu_schema_pass

    def get_validation_method(self):
        """
        Get the validation method.
        :return: the validation method
        """
        if self._validation_method is None:
            self._validation_method = 'strict'
        return self._validation_method

    def set_validation_method(self, method):
        """
        Set the validation method.
        :param method: validation method
        """
        self._validation_method = method

    def get_validate_configuration(self):
        """
        Get the validation method object, creating if necessary
        :return: the validation method object
        """
        if not self._validate_configuration:
            method_key = self.get_validation_method()
            if self._target:
                method_key = self.get_target_configuration().get_validation_method()
            if not method_key:
                method_key = validate_configuration.STRICT_METHOD
            self._validate_configuration = ValidateConfiguration(method_key)
        return self._validate_configuration

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

    def get_folders_only_control_option(self):
        """
        Get the -folders_only command-line switch for model help tool.
        :return: the -folders_only command-line switch
        """
        return self._folders_only

    def get_attributes_only_control_option(self):
        """
        Get the -attributes_only command-line switch for model help tool.
        :return: the -attributes_only command-line switch
        """
        return self._attributes_only

    def get_recursive_control_option(self):
        """
        Get the -recursive command-line switch for model help tool.
        :return: the -recursive command-line switch
        """
        return self._recursive

    def get_interactive_mode_option(self):
        """
        Get the -interactive command-line switch for model help tool.
        :return: the -interactive command-line switch
        """
        return self._interactive_mode

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

    def get_rcu_db_user(self):
        """
        Get the RCU DB user.
        :return: the RCU dbUser
        """
        return self._rcu_db_user

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

    def get_output_dir(self):
        """
        Return the output directory.
        :return: output directory
        """
        return self._output_dir

    def get_target_configuration(self):
        """
        Return the target configuration object, based on the target name.
        Lazy-load this the first time it is requested.
        Return a default target configuration if none was specified.
        :return: target configuration object
        """
        if self._target_configuration is None:
            configuration_dict = {}

            if self._target:
                target_configuration_file = self.get_target_configuration_file()
                if os.path.exists(target_configuration_file):
                    configuration_dict = JsonToPython(target_configuration_file).parse()

            self._target_configuration = TargetConfiguration(configuration_dict)

        return self._target_configuration

    def get_target_configuration_file(self):
        if self._target:
            target_path = os.path.join('targets', self._target, 'target.json')
            return path_utils.find_config_path(target_path)
        return None

    def get_target(self):
        return self._target

    def is_targetted_config(self):
        """
        Return the output directory for generated k8s target.
        :return: output directory
        """
        return self._target is not None

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

    def get_variable_injector_file(self):
        """
        Get the variable injector file override.
        :return: the variable injector file
        """
        return self._variable_injector_file

    def get_variable_keywords_file(self):
        """
        Get the variable keywords file override.
        :return: the variable keywords file
        """
        return self._variable_keywords_file

    def get_variable_properties_file(self):
        """
        Get the variable properties file override.
        :return: the variable properties file
        """
        return self._variable_properties_file

    def get_trailing_argument(self, index):
        """
        Get the trailing argument at index.
        :param index: the index of the trailing argument
        :return: the trailing argument
        """
        return self._trailing_args[index]

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

    def is_remote(self):
        """
        Determine if the tool has the remote switch to true
        :return: True if -remote was set
        """
        return self._remote

    def skip_archive(self):
        """
        Determine if the tool has the -skip_archive switch
        :return: True if the skip archive switch is set
        """
        return self._skip_archive

    def replace_tokens_in_path(self, attribute_name, resource_dict):
        """
        Replace any tokens in a path with the current values.
        :param attribute_name: the attribute name
        :param resource_dict: the dictionary to use to lookup and replace the attribute value
        """
        separator = ':'
        attribute_value = resource_dict[attribute_name]
        path_elements = attribute_value.split(':')
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

    def has_token_prefix(self, path):
        """
        Determines if the specified path begins with one of the known, portable token prefix paths.
        :param path: the path to check for token prefix
        :return: true if the path begins with a known prefix, false otherwise
        """
        return path.startswith(self.ORACLE_HOME_TOKEN) or \
            path.startswith(self.WL_HOME_TOKEN) or \
            path.startswith(self.DOMAIN_HOME_TOKEN) or \
            path.startswith(self.JAVA_HOME_TOKEN) or \
            path.startswith(self.CURRENT_DIRECTORY_TOKEN) or \
            path.startswith(self.TEMP_DIRECTORY_TOKEN)

    def replace_tokens(self, resource_type, resource_name, attribute_name, resource_dict):
        """
        Replace the tokens in attribute value with the current value.
        :param resource_type: the resource type (used for logging purposes)
        :param resource_name: the resource name (used for logging purposes)
        :param attribute_name: the attribute name for which to replace tokens
        :param resource_dict: the dictionary to use to lookup and replace the attribute value
        """
        attribute_value = resource_dict[attribute_name]
        if attribute_value is None:
            return
        uri = URI(attribute_value)
        uri_scheme = uri.getScheme()
        if uri_scheme is not None and str_helper.to_string(uri_scheme).startswith('file'):
            attribute_value = uri.getPath()

        message = "Replacing {0} in {1} {2} {3} with {4}"
        if attribute_value.startswith(self.ORACLE_HOME_TOKEN):
            self._logger.fine(message, self.ORACLE_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_oracle_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.ORACLE_HOME_TOKEN,
                                                                    self.get_oracle_home())
        elif attribute_value.startswith(self.WL_HOME_TOKEN):
            self._logger.fine(message, self.WL_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_wl_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.WL_HOME_TOKEN, self.get_wl_home())
        elif attribute_value.startswith(self.DOMAIN_HOME_TOKEN):
            self._logger.fine(message, self.DOMAIN_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_domain_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.DOMAIN_HOME_TOKEN,
                                                                    self.get_domain_home())
        elif attribute_value.startswith(self.JAVA_HOME_TOKEN):
            self._logger.fine(message, self.JAVA_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_domain_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.JAVA_HOME_TOKEN,
                                                                    self.get_java_home())
        elif attribute_value.startswith(self.CURRENT_DIRECTORY_TOKEN):
            cwd = path_utils.fixup_path(os.getcwd())
            self._logger.fine(message, self.CURRENT_DIRECTORY_TOKEN, resource_type, resource_name,
                              attribute_name, cwd, class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.CURRENT_DIRECTORY_TOKEN, cwd)
        elif attribute_value.startswith(self.TEMP_DIRECTORY_TOKEN):
            temp_dir = path_utils.fixup_path(tempfile.gettempdir())
            self._logger.fine(message, self.TEMP_DIRECTORY_TOKEN, resource_type, resource_name, attribute_name,
                              temp_dir, class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.TEMP_DIRECTORY_TOKEN, temp_dir)

    def replace_token_string(self, string_value):
        """
        Replace the tokens in string value with the current value of the token.
        :param string_value: the value on which to perform token replacement
        :return: the detokenized value, or the original value if there were no tokens
        """
        if string_value is None:
            result = None
        elif string_value.startswith(self.ORACLE_HOME_TOKEN):
            result = _replace(string_value, self.ORACLE_HOME_TOKEN, self.get_oracle_home())
        elif string_value.startswith(self.WL_HOME_TOKEN):
            result = _replace(string_value, self.WL_HOME_TOKEN, self.get_wl_home())
        elif string_value.startswith(self.DOMAIN_HOME_TOKEN):
            result = _replace(string_value, self.DOMAIN_HOME_TOKEN, self.get_domain_home())
        elif string_value.startswith(self.JAVA_HOME_TOKEN):
            result = _replace(string_value, self.JAVA_HOME_TOKEN, self.get_java_home())
        elif string_value.startswith(self.CURRENT_DIRECTORY_TOKEN):
            result = _replace(string_value, self.CURRENT_DIRECTORY_TOKEN, path_utils.fixup_path(os.getcwd()))
        elif string_value.startswith(self.TEMP_DIRECTORY_TOKEN):
            result = _replace(string_value, self.TEMP_DIRECTORY_TOKEN, path_utils.fixup_path(tempfile.gettempdir()))
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
        wl_home = path_utils.fixup_path(self.get_wl_home())
        domain_home = path_utils.fixup_path(self.get_domain_home())
        oracle_home = path_utils.fixup_path(self.get_oracle_home())
        java_home = path_utils.fixup_path(self.get_java_home())
        tmp_dir = path_utils.fixup_path(tempfile.gettempdir())
        cwd = path_utils.fixup_path(os.path.dirname(os.path.abspath(__file__)))

        # decide later what is required to be in context home for appropriate exception prevention
        result = my_path
        if not string_utils.is_empty(my_path):
            if wl_home is not None and my_path.startswith(wl_home):
                result = my_path.replace(wl_home, self.WL_HOME_TOKEN)
            elif domain_home is not None and my_path.startswith(domain_home):
                result = my_path.replace(domain_home, self.DOMAIN_HOME_TOKEN)
            elif oracle_home is not None and my_path.startswith(oracle_home):
                result = my_path.replace(oracle_home, self.ORACLE_HOME_TOKEN)
            elif java_home is not None and my_path.startswith(java_home):
                result = my_path.replace(java_home, self.JAVA_HOME_TOKEN)
            elif my_path.startswith(cwd):
                result = my_path.replace(cwd, self.CURRENT_DIRECTORY_TOKEN)
            elif my_path.startswith(tmp_dir):
                result = my_path.replace(tmp_dir, self.TEMP_DIRECTORY_TOKEN)

        return result

    def tokenize_classpath(self, classpath):
        """
        Replace known types of directories with a tokens that represent the directory.

        :param classpath: containing a string of directories separated by commas
        :return: tokenized classpath string
        """
        cp_elements = classpath.split(MODEL_LIST_DELIMITER)
        for index, value in enumerate(cp_elements):
            path_is_windows = '\\' in value or re.match('^[a-zA-Z][:]', value)
            if path_is_windows:
                value = path_utils.fixup_path(value)
            cp_elements[index] = self.tokenize_path(value)

        return MODEL_LIST_DELIMITER.join(cp_elements)

    def copy(self, arg_map):
        model_context_copy = copy.copy(self)
        model_context_copy.__copy_from_args(arg_map)
        return model_context_copy

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

