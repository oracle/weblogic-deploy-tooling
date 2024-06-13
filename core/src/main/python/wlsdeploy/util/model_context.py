"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""

import copy
import os
import re
import tempfile

import java.lang.System as System
import java.net.URI as URI

from oracle.weblogic.deploy.util import XPathUtil

from wlsdeploy.aliases.model_constants import ALL
from wlsdeploy.aliases.model_constants import DEFAULT_AUTHENTICATOR
from wlsdeploy.aliases.model_constants import DEFAULT_CREDENTIAL_MAPPER
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import XACML_AUTHORIZER
from wlsdeploy.aliases.model_constants import XACML_ROLE_MAPPER
from wlsdeploy.aliases.wlst_modes import WlstModes
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging import platform_logger
from wlsdeploy.util import target_configuration
from wlsdeploy.util import validate_configuration
from wlsdeploy.util.cla_utils import CommandLineArgUtil
from wlsdeploy.util import path_helper
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

    SECRET_REGEX = re.compile('@@SECRET:[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+@@')
    ENV_REGEX = re.compile('@@ENV:[a-zA-Z0-9_-]+@@')
    ORACLE_HOME_TOKEN = '@@ORACLE_HOME@@'
    WL_HOME_TOKEN = '@@WL_HOME@@'
    DOMAIN_HOME_TOKEN = '@@DOMAIN_HOME@@'
    JAVA_HOME_TOKEN = '@@JAVA_HOME@@'
    CURRENT_DIRECTORY_TOKEN = '@@PWD@@'
    TEMP_DIRECTORY_TOKEN = '@@TMP@@'

    def __init__(self, program_name, arg_map=None):
        """
        Create a new model context instance.
        Tools should use model_context_helper.create_context(), to ensure that the typedef is initialized correctly.
        Unit tests should use this constructor directly, since typedef files are not deployed.
        :param program_name: the program name, used for logging
        :param arg_map: all the arguments passed to the tool
        """
        self._program_name = program_name
        self._logger = platform_logger.PlatformLogger('wlsdeploy.util')
        #
        # We are using late initialization of the wls_helper to accommodate
        # basing it on the remote version, if applicable.
        #
        self._initialization_complete = False
        self._wls_helper = None
        self.string_utils = None
        self._model_config = model_config.get_model_config(self._program_name)
        self._ssh_context = None

        self._oracle_home = None
        self._wl_home = ""
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
        self._variable_file_name = None
        self._run_rcu = False
        self._is_encryption_supported = True
        self._encryption_passphrase = None
        self._encryption_passphrase_prompt = False
        self._encrypt_manual = False
        self._encrypt_one_pass = None
        self._wl_version = None
        self._remote_wl_version = None
        self._wlst_mode = None
        self._recursive = False
        self._attributes_only = False
        self._folders_only = False
        self._opss_wallet_passphrase = None
        self._opss_wallet = None
        self._update_rcu_schema_pass = False
        self._validation_method = None
        self._validate_configuration = None  # lazy load
        self._cancel_changes_if_restart_required = None
        self._output_dir = None
        self._target = None
        self._target_configuration = None  # lazy load
        self._variable_injector_file = None
        self._discard_current_edit = False
        self._wait_for_edit_lock = False
        self._remote = False
        self._skip_archive = False
        self._ssh_host = None
        self._ssh_port = None
        self._ssh_user = System.getProperty('user.name')
        self._ssh_pass = None
        self._ssh_pass_prompt = False
        self._ssh_private_key = None
        self._ssh_private_key_passphrase = None
        self._ssh_private_key_passphrase_prompt = False
        self._remote_oracle_home = None
        self._remote_wl_home = None
        self._remote_test_file = None
        self._local_test_file = None
        self._remote_output_dir = None
        self._local_output_dir = None
        self._discover_passwords = False
        self._discover_security_provider_data = None
        self._discover_opss_wallet = False
        self._path_helper = path_helper.get_path_helper()

        self._trailing_args = []

        if self._wl_version is None:
            from wlsdeploy.util import weblogic_helper
            self._wl_version = weblogic_helper.get_local_weblogic_version()


        if self._wlst_mode is None:
            self._wlst_mode = WlstModes.OFFLINE

        # This if test is for the tool_main's creation of the exit_context, which is
        # used for argument parsing in case an error is raised.  The issue is that
        # __copy_from_args tries to determine the PSU version but since the Oracle Home
        # is not available, the PSU detection logic and erroneously logs that there is
        # no PSU when there is (and that gets logged about 70 lines down in the log file).
        #
        if arg_map is not None:
            self.__copy_from_args(arg_map)
            if self._admin_url is None:
                self.complete_initialization()
        else:
            self._initialization_complete = True


    def __copy_from_args(self, arg_map):
        _method_name = '__copy_from_args'

        # No need to try to get the PSU if the -oracle_home is empty...
        #
        # This is yet another special case where something during the loading of
        # the typedef file creates a sparse model_context object with the -oracle_home
        # set to an empty string.
        #
        if CommandLineArgUtil.ORACLE_HOME_SWITCH in arg_map and len(arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH]) > 0:
            self._oracle_home = arg_map[CommandLineArgUtil.ORACLE_HOME_SWITCH]
            psu = XPathUtil(self._oracle_home).getPSU()
            if psu is not None:
                self._wl_version += '.' + psu

            self._logger.info('WLSDPLY-01050', self._wl_version, class_name=self._class_name,
                              method_name=_method_name)
            from wlsdeploy.util import weblogic_helper
            self._wl_home = weblogic_helper.get_weblogic_home(self._oracle_home, self._wl_version)

        if CommandLineArgUtil.JAVA_HOME_SWITCH in arg_map:
            self._java_home = arg_map[CommandLineArgUtil.JAVA_HOME_SWITCH]

        if CommandLineArgUtil.DOMAIN_HOME_SWITCH in arg_map:
            self._domain_home = arg_map[CommandLineArgUtil.DOMAIN_HOME_SWITCH]
            self._domain_name = self._path_helper.local_basename(self._domain_home)

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

        if CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH in arg_map:
            self._attributes_only = arg_map[CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH]

        if CommandLineArgUtil.FOLDERS_ONLY_SWITCH in arg_map:
            self._folders_only = arg_map[CommandLineArgUtil.FOLDERS_ONLY_SWITCH]

        if CommandLineArgUtil.RECURSIVE_SWITCH in arg_map:
            self._recursive = arg_map[CommandLineArgUtil.RECURSIVE_SWITCH]

        if CommandLineArgUtil.VARIABLE_FILE_SWITCH in arg_map:
            self._variable_file_name = arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH]

        if CommandLineArgUtil.REMOTE_SWITCH in arg_map:
            self._remote = arg_map[CommandLineArgUtil.REMOTE_SWITCH]

        if CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH in arg_map:
            self._skip_archive = arg_map[CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH]

        if CommandLineArgUtil.SSH_HOST_SWITCH in arg_map:
            self._ssh_host = arg_map[CommandLineArgUtil.SSH_HOST_SWITCH]

        if CommandLineArgUtil.SSH_PORT_SWITCH in arg_map:
            self._ssh_port = arg_map[CommandLineArgUtil.SSH_PORT_SWITCH]

        if CommandLineArgUtil.SSH_USER_SWITCH in arg_map:
            self._ssh_user = arg_map[CommandLineArgUtil.SSH_USER_SWITCH]

        if CommandLineArgUtil.SSH_PASS_SWITCH in arg_map:
            self._ssh_pass = arg_map[CommandLineArgUtil.SSH_PASS_SWITCH]

        if CommandLineArgUtil.SSH_PASS_PROMPT_SWITCH in arg_map:
            self._ssh_pass_prompt = arg_map[CommandLineArgUtil.SSH_PASS_PROMPT_SWITCH]

        if CommandLineArgUtil.SSH_PRIVATE_KEY_SWITCH in arg_map:
            self._ssh_private_key = arg_map[CommandLineArgUtil.SSH_PRIVATE_KEY_SWITCH]

        if CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_SWITCH in arg_map:
            self._ssh_private_key_passphrase = arg_map[CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_SWITCH]

        if CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH in arg_map:
            self._ssh_private_key_passphrase_prompt = \
                arg_map[CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH]

        if CommandLineArgUtil.REMOTE_TEST_FILE_SWITCH in arg_map:
            self._remote_test_file = arg_map[CommandLineArgUtil.REMOTE_TEST_FILE_SWITCH]

        if CommandLineArgUtil.LOCAL_TEST_FILE_SWITCH in arg_map:
            self._local_test_file = arg_map[CommandLineArgUtil.LOCAL_TEST_FILE_SWITCH]

        if CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH in arg_map:
            self._remote_output_dir = arg_map[CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH]

        if CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH in arg_map:
            self._local_output_dir = arg_map[CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH]

        if CommandLineArgUtil.RUN_RCU_SWITCH in arg_map:
            self._run_rcu = arg_map[CommandLineArgUtil.RUN_RCU_SWITCH]

        if CommandLineArgUtil.DOMAIN_TYPEDEF in arg_map:
            self._domain_typedef = arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF]

        if CommandLineArgUtil.PASSPHRASE_SWITCH in arg_map:
            self._encryption_passphrase = arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH]

        if CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH in arg_map:
            self._encryption_passphrase_prompt = arg_map[CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH]

        if CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH in arg_map:
            self._encrypt_manual = arg_map[CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH]

        if CommandLineArgUtil.ONE_PASS_SWITCH in arg_map:
            self._encrypt_one_pass = arg_map[CommandLineArgUtil.ONE_PASS_SWITCH]

        if CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH in arg_map:
            self._cancel_changes_if_restart_required = arg_map[CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH]

        if CommandLineArgUtil.ARCHIVE_FILE in arg_map:
            self._archive_file = arg_map[CommandLineArgUtil.ARCHIVE_FILE]

        if CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH in arg_map:
            self._opss_wallet_passphrase = arg_map[CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH]

        if CommandLineArgUtil.OPSS_WALLET_SWITCH in arg_map:
            self._opss_wallet = arg_map[CommandLineArgUtil.OPSS_WALLET_SWITCH]

        if CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH in arg_map:
            self._update_rcu_schema_pass = True

        if CommandLineArgUtil.VALIDATION_METHOD in arg_map:
            self._validation_method = arg_map[CommandLineArgUtil.VALIDATION_METHOD]

        if CommandLineArgUtil.TARGET_VERSION_SWITCH in arg_map:
            self._wl_version = arg_map[CommandLineArgUtil.TARGET_VERSION_SWITCH]

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

        if CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH in arg_map:
            self._discover_passwords = arg_map[CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH]

        if CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH in arg_map:
            self._discover_security_provider_data = \
                arg_map[CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH].split(',')

        if CommandLineArgUtil.DISCOVER_OPSS_WALLET_SWITCH in arg_map:
            self._discover_opss_wallet = arg_map[CommandLineArgUtil.DISCOVER_OPSS_WALLET_SWITCH]

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
        if self._attributes_only is not None:
            arg_map[CommandLineArgUtil.ATTRIBUTES_ONLY_SWITCH] = self._attributes_only
        if self._folders_only is not None:
            arg_map[CommandLineArgUtil.FOLDERS_ONLY_SWITCH] = self._folders_only
        if self._recursive is not None:
            arg_map[CommandLineArgUtil.RECURSIVE_SWITCH] = self._recursive
        if self._remote is not None:
            arg_map[CommandLineArgUtil.REMOTE_SWITCH] = self._remote
        if self._skip_archive is not None:
            arg_map[CommandLineArgUtil.SKIP_ARCHIVE_FILE_SWITCH] = self._skip_archive
        if self._ssh_host is not None:
            arg_map[CommandLineArgUtil.SSH_HOST_SWITCH] = self._ssh_host
        if self._ssh_port is not None:
            arg_map[CommandLineArgUtil.SSH_PORT_SWITCH] = self._ssh_port
        if self._ssh_user is not None:
            arg_map[CommandLineArgUtil.SSH_USER_SWITCH] = self._ssh_user
        if self._ssh_pass is not None:
            arg_map[CommandLineArgUtil.SSH_PASS_SWITCH] = self._ssh_pass
        if self._ssh_pass_prompt is not None:
            arg_map[CommandLineArgUtil.SSH_PASS_PROMPT_SWITCH] = self._ssh_pass_prompt
        if self._ssh_private_key is not None:
            arg_map[CommandLineArgUtil.SSH_PRIVATE_KEY_SWITCH] = self._ssh_private_key
        if self._ssh_private_key_passphrase is not None:
            arg_map[CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_SWITCH] = self._ssh_private_key_passphrase
        if self._ssh_private_key_passphrase_prompt is not None:
            arg_map[CommandLineArgUtil.SSH_PRIVATE_KEY_PASSPHRASE_PROMPT_SWITCH] = \
                self._ssh_private_key_passphrase_prompt
        if self._remote_oracle_home is not None:
            arg_map[CommandLineArgUtil.REMOTE_ORACLE_HOME_SWITCH] = self._remote_oracle_home
        if self._remote_test_file is not None:
            arg_map[CommandLineArgUtil.REMOTE_TEST_FILE_SWITCH] = self._remote_test_file
        if self._local_test_file is not None:
            arg_map[CommandLineArgUtil.LOCAL_TEST_FILE_SWITCH] = self._local_test_file
        if self._remote_output_dir is not None:
            arg_map[CommandLineArgUtil.REMOTE_OUTPUT_DIR_SWITCH] = self._remote_output_dir
        if self._local_output_dir is not None:
            arg_map[CommandLineArgUtil.LOCAL_OUTPUT_DIR_SWITCH] = self._local_output_dir
        if self._variable_file_name is not None:
            arg_map[CommandLineArgUtil.VARIABLE_FILE_SWITCH] = self._variable_file_name
        if self._run_rcu:
            arg_map[CommandLineArgUtil.RUN_RCU_SWITCH] = self._run_rcu
        if self._discard_current_edit is not None:
            arg_map[CommandLineArgUtil.DISCARD_CURRENT_EDIT_SWITCH] = self._discard_current_edit
        if self._wait_for_edit_lock is not None:
            arg_map[CommandLineArgUtil.WAIT_FOR_EDIT_LOCK_SWITCH] = self._wait_for_edit_lock
        if self._domain_typedef is not None:
            arg_map[CommandLineArgUtil.DOMAIN_TYPEDEF] = self._domain_typedef
        if self._encryption_passphrase is not None:
            arg_map[CommandLineArgUtil.PASSPHRASE_SWITCH] = self._encryption_passphrase
        if self._encryption_passphrase_prompt is not None:
            arg_map[CommandLineArgUtil.PASSPHRASE_PROMPT_SWITCH] = self._encryption_passphrase_prompt
        if self._encrypt_manual is not None:
            arg_map[CommandLineArgUtil.ENCRYPT_MANUAL_SWITCH] = self._encrypt_manual
        if self._encrypt_one_pass is not None:
            arg_map[CommandLineArgUtil.ONE_PASS_SWITCH] = self._encrypt_one_pass
        if self._cancel_changes_if_restart_required is not None:
            arg_map[CommandLineArgUtil.CANCEL_CHANGES_IF_RESTART_REQ_SWITCH] = self._cancel_changes_if_restart_required
        if self._archive_file is not None:
            arg_map[CommandLineArgUtil.ARCHIVE_FILE] = self._archive_file
        if self._opss_wallet_passphrase is not None:
            arg_map[CommandLineArgUtil.OPSS_WALLET_PASSPHRASE_SWITCH] = self._opss_wallet_passphrase
        if self._opss_wallet is not None:
            arg_map[CommandLineArgUtil.OPSS_WALLET_SWITCH] = self._opss_wallet
        if self._update_rcu_schema_pass is not None:
            arg_map[CommandLineArgUtil.UPDATE_RCU_SCHEMA_PASS_SWITCH] = self._update_rcu_schema_pass
        if self._validation_method is not None:
            arg_map[CommandLineArgUtil.VALIDATION_METHOD] = self._validation_method
        if self._wl_version is not None:
            arg_map[CommandLineArgUtil.TARGET_VERSION_SWITCH] = self._wl_version
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
        if self._discover_passwords:
            arg_map[CommandLineArgUtil.DISCOVER_PASSWORDS_SWITCH] = self._discover_passwords
        if self._discover_security_provider_data is not None:
            # Make a copy of the list...
            arg_map[CommandLineArgUtil.DISCOVER_SECURITY_PROVIDER_DATA_SWITCH] = \
                list(self._discover_security_provider_data)
        if self._discover_opss_wallet:
            arg_map[CommandLineArgUtil.DISCOVER_OPSS_WALLET_SWITCH] = self._discover_opss_wallet

        new_context = ModelContext(self._program_name, arg_map)
        if not new_context.is_initialization_complete():
            new_context.complete_initialization(self._remote_wl_version)

        return new_context

    def is_initialization_complete(self):
        return self._initialization_complete

    def complete_initialization(self, remote_wl_version = None, remote_oracle_home = None):
        """
        Set the remote version when running in online mode.
        :param remote_wl_version: the version of the online server
        :param remote_oracle_home: the directory location of the Oracle Home on the online server
        """
        if not self._initialization_complete:
            self._remote_wl_version = remote_wl_version
            self._remote_oracle_home = remote_oracle_home
            path_helper.set_remote_file_system_from_oracle_home(remote_oracle_home)

            self._wls_helper = WebLogicHelper(self._logger, remote_wl_version)
            if self._remote_oracle_home is not None:
                # If we couldn't determine the remote version, just use the local version and hope for the best.
                from wlsdeploy.util import weblogic_helper
                self._remote_wl_home = \
                    weblogic_helper.get_weblogic_home(self._remote_oracle_home, self.get_effective_wls_version())
            if self._domain_typedef is not None:
                self._domain_typedef.finish_initialization(self)
            self._initialization_complete = True

    def get_weblogic_helper(self):
        """
        Return the encapsulated WebLogicHelper instance
        :return: the encapsulated WebLogicHelper instance
        """
        return self._wls_helper

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

    def is_discover_domain_tool(self):
        return self._program_name == 'discoverDomain'

    def is_create_domain_tool(self):
        return self._program_name == 'createDomain'

    def is_validate_domain_tool(self):
        return self._program_name == 'validateModel'

    def get_oracle_home(self):
        """
        Get the Oracle Home.
        :return: the Oracle Home
        """
        return self._oracle_home

    def get_effective_oracle_home(self):
        """
        Get the effective Oracle Home.
        :return: the Oracle Home
        """
        if self.is_ssh():
            return self._remote_oracle_home
        else:
            return self._oracle_home

    def get_wl_home(self):
        """
        Get the WebLogic Home.
        :return: the WebLogic Home
        """
        return self._wl_home

    def get_remote_wl_home(self):
        """
        Get the Remote WebLogic Home.  Note that this assumes that the local
        and remote Oracle Homes have a similar version of WebLogic Server installed.
        :return: the remote WebLogic Home
        """
        return self._remote_wl_home

    def get_effective_wl_home(self):
        """
        Get the effective WebLogic Home.
        :return: the WebLogic Home
        """
        if self.is_ssh():
            return self._remote_wl_home
        else:
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

    def set_domain_name(self, domain_name):
        """
        Set the domain name when online
        :param domain_name: the domain name
        """
        self._domain_name = domain_name

    def set_domain_home(self, domain_home):
        """
        This method is a hack to allow create to add the domain home after reading the domain name from the model.
        This method is a no-op if the domain home was previously initialized via command-line argument processing.
        :param domain_home: the domain home directory
        """
        if self._domain_home is None and domain_home is not None and len(domain_home) > 0:
            self._domain_home = domain_home
            self._domain_name = self._path_helper.local_basename(self._domain_home)

    def set_domain_home_name_if_online(self, domain_home, domain_name):
        if self._wlst_mode == WlstModes.ONLINE:
            self.set_domain_home(domain_home)
            self.set_domain_name(domain_name)

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

    def set_opss_wallet_passphrase(self, opss_wallet_passphrase):
        self._opss_wallet_passphrase = opss_wallet_passphrase

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

    def get_variable_file(self):
        """
        Get the variable file.
        :return: the variable file
        """
        return self._variable_file_name

    def is_run_rcu(self):
        """
        Get whether to run RCU.
        :return: whether to run RCU
        """
        return self._run_rcu

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
            # if no target declared, construct TargetConfiguration with None
            configuration_dict = None

            if self._target:
                target_configuration_file = self.get_target_configuration_file()
                if os.path.exists(target_configuration_file):
                    configuration_dict = JsonToPython(target_configuration_file).parse()

            self._target_configuration = TargetConfiguration(configuration_dict)

        return self._target_configuration

    def get_target_configuration_file(self):
        if self._target:
            return target_configuration.get_target_configuration_path(self._target)
        return None

    def get_target(self):
        return self._target

    def is_targeted_config(self):
        """
        Determine if target configuration is used.
        :return: True if target configuration is used
        """
        return self._target is not None

    def is_encryption_manual(self):
        """
        Get whether the user selected to do manual encryption.
        :return: whether the user selected to do manual encryption
        """
        return self._encrypt_manual

    def get_encrypt_one_pass(self):
        """
        Get the password to encrypt manually.
        :return: the password to encrypt manually
        """
        return self._encrypt_one_pass

    def is_encryption_supported(self):
        return self._is_encryption_supported

    def set_encryption_supported(self, is_encryption_supported):
        self._is_encryption_supported = is_encryption_supported

    def is_using_encryption(self):
        """
        Get whether the model is using encryption.
        :return: whether the model is using encryption
        """
        return self._encryption_passphrase is not None

    def get_local_wls_version(self):
        """
        Get the local WebLogic version.
        :return: the local WebLogic version
        """
        return self._wl_version

    def get_remote_wls_version(self):
        """
        Get the remote WebLogic version.
        :return: the remote WebLogic version or None
        """
        return self._remote_wl_version

    def get_effective_wls_version(self):
        """
        Get the WebLogic version for the domain.
        :return: the WebLogic version for the domain
        """
        if self._remote_wl_version is not None:
            return self._remote_wl_version
        else:
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

    def get_trailing_arguments(self):
        """
        Return an array of trailing arguments.
        :return: the trailing arguments
        """
        return self._trailing_args

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

    def is_skip_archive(self):
        """
        Determine if the tool has the -skip_archive switch
        :return: True if the skip archive switch is set
        """
        return self._skip_archive

    def is_ssh(self):
        """
        Determine if the tool is running in SSH mode
        :return:True if running in SSH mode
        """
        return self._ssh_context is not None

    def is_ssh_user_pass_auth(self):
        """
        Determine if the SSH authentication mechanism is using username/password authentication.
        :return: True, if using username/password authentication
        """
        return self._ssh_pass is not None or self._ssh_pass_prompt

    def is_ssh_public_key_auth(self):
        """
        Determine if the SSH authentication mechanism is using public key-based authentication
        :return: True, if not using username/password authentication
        """
        return not self.is_ssh_user_pass_auth()

    def is_ssh_default_private_key(self):
        """
        Determine if the user has specified a private key.
        :return: true if the private key file was not specified, false otherwise
        """
        return self._ssh_private_key is None

    def is_ssh_private_key_encrypted(self):
        """
        Determine if the user's private key has a passphrase.
        :return: True, if the user's private key has a passphrase
        """
        return self._ssh_private_key_passphrase is not None

    def get_ssh_host(self):
        """
        Get the specified SSH host name or IP address.
        :return: SSH host name or IP address or None
        """
        return self._ssh_host

    def get_ssh_port(self):
        """
        Get the specified SSH port number, if any.
        :return: the SSH port number or None
        """
        return self._ssh_port

    def get_ssh_user(self):
        """
        Get the specified SSH username, if any.
        :return: the SSH username or None
        """
        return self._ssh_user

    def get_ssh_pass(self):
        """
        Get the specified SSH password, if any.
        :return: the SSH user's password or None
        """
        return self._ssh_pass

    def set_ssh_pass(self, ssh_pass):
        """
        Set the SSH user's password.
        :param ssh_pass: the SSH user's password
        """
        self._ssh_pass = ssh_pass

    def is_ssh_pass_prompt(self):
        """
        Whether prompting is needed for the SSH user's password.
        :return: true if prompting is needed, false otherwise
        """
        return self._ssh_pass_prompt

    def get_ssh_private_key(self):
        """
        Get the specified SSH private key file, if any.
        :return: the SSH private key file or None
        """
        return self._ssh_private_key

    def get_ssh_private_key_passphrase(self):
        """
        Get the specified SSH private key passphrase, if any.
        :return: the SSH private key passphrase or None
        """
        return self._ssh_private_key_passphrase

    def set_ssh_private_key_passphrase(self, passphrase):
        """
        Set the SSH private key passphrase.
        :param passphrase: the SSH private key passphrase
        """
        self._ssh_private_key_passphrase = passphrase

    def is_ssh_private_key_passphrase_prompt(self):
        """
        Whether prompting is needed for the SSH private key passphrase.
        :return: true if prompting is needed, false otherwise
        """
        return self._ssh_private_key_passphrase_prompt

    def get_remote_test_file(self):
        """
        Get the location of the test file or directory to download from the remote machine.
        :return: the absolute path to the test file or directory
        """
        return self._remote_test_file

    def get_local_test_file(self):
        """
        Get the location of the test file or directory to upload to the remote machine.
        :return: the path to the test file or directory
        """
        return self._local_test_file

    def get_remote_output_dir(self):
        """
        Get the location of the directory to which to upload on the remote machine.
        :return: the absolute path on the remote machine
        """
        return self._remote_output_dir

    def get_local_output_dir(self):
        """
        Get the location of the directory to which to download on the local machine.
        :return: the path to the local directory
        """
        return self._local_output_dir

    def get_remote_oracle_home(self):
        """
        Get the location of the Oracle Home on the remote machine.
        :return: the location of the remote Oracle Home or None
        """
        return self._remote_oracle_home

    def get_ssh_context(self):
        """
        Get the SSH context object.
        :return: the SSH context object
        """
        return self._ssh_context

    def set_ssh_context(self, ssh_context):
        """
        Set the SSH context object
        :param ssh_context: the new SSH context object
        """
        self._ssh_context = ssh_context

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

        # TODO - the last three tokens will not work properly for an SSH context
        message = 'WLSDPLY-01057'
        if attribute_value.startswith(self.ORACLE_HOME_TOKEN):
            self._logger.fine(message, self.ORACLE_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_effective_oracle_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.ORACLE_HOME_TOKEN,
                                                                    self.get_effective_oracle_home())
        elif attribute_value.startswith(self.WL_HOME_TOKEN):
            self._logger.fine(message, self.WL_HOME_TOKEN, resource_type, resource_name, attribute_name,
                              self.get_effective_wl_home(), class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.WL_HOME_TOKEN, self.get_effective_wl_home())
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
            cwd = self._path_helper.fixup_local_path(os.getcwd())
            self._logger.fine(message, self.CURRENT_DIRECTORY_TOKEN, resource_type, resource_name,
                              attribute_name, cwd, class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.CURRENT_DIRECTORY_TOKEN, cwd)
        elif attribute_value.startswith(self.TEMP_DIRECTORY_TOKEN):
            temp_dir = self._path_helper.fixup_local_path(tempfile.gettempdir())
            self._logger.fine(message, self.TEMP_DIRECTORY_TOKEN, resource_type, resource_name, attribute_name,
                              temp_dir, class_name=self._class_name, method_name='_replace_tokens')
            resource_dict[attribute_name] = attribute_value.replace(self.TEMP_DIRECTORY_TOKEN, temp_dir)

    def replace_token_string(self, string_value):
        """
        Replace the tokens in string value with the current value of the token.
        :param string_value: the value on which to perform token replacement
        :return: the detokenized value, or the original value if there were no tokens
        """
        # TODO - the last three tokens will not work properly for an SSH context
        if string_value is None:
            result = None
        elif string_value.startswith(self.ORACLE_HOME_TOKEN):
            result = _replace(string_value, self.ORACLE_HOME_TOKEN, self.get_effective_oracle_home())
        elif string_value.startswith(self.WL_HOME_TOKEN):
            result = _replace(string_value, self.WL_HOME_TOKEN, self.get_effective_wl_home())
        elif string_value.startswith(self.DOMAIN_HOME_TOKEN):
            result = _replace(string_value, self.DOMAIN_HOME_TOKEN, self.get_domain_home())
        elif string_value.startswith(self.JAVA_HOME_TOKEN):
            result = _replace(string_value, self.JAVA_HOME_TOKEN, self.get_java_home())
        elif string_value.startswith(self.CURRENT_DIRECTORY_TOKEN):
            result = _replace(string_value, self.CURRENT_DIRECTORY_TOKEN,
                              self._path_helper.fixup_local_path(os.getcwd()))
        elif string_value.startswith(self.TEMP_DIRECTORY_TOKEN):
            result = _replace(string_value, self.TEMP_DIRECTORY_TOKEN,
                              self._path_helper.fixup_local_path(tempfile.gettempdir()))
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
        my_path = self._path_helper.fixup_path(path)
        wl_home = self._path_helper.fixup_path(self.get_effective_wl_home())
        domain_home = self._path_helper.fixup_path(self.get_domain_home())
        oracle_home = self._path_helper.fixup_path(self.get_effective_oracle_home())
        # TODO - these last three tokens will not work properly for a remote/SSH context
        java_home = self._path_helper.fixup_local_path(self.get_java_home())
        tmp_dir = self._path_helper.fixup_local_path(tempfile.gettempdir())
        cwd = self._path_helper.fixup_local_path(os.getcwd())

        # decide later what is required to be in context home for appropriate exception prevention
        result = my_path
        if not string_utils.is_empty(my_path):
            if wl_home and my_path.startswith(wl_home):
                result = my_path.replace(wl_home, self.WL_HOME_TOKEN)
            elif domain_home and my_path.startswith(domain_home):
                result = my_path.replace(domain_home, self.DOMAIN_HOME_TOKEN)
            elif oracle_home and my_path.startswith(oracle_home):
                result = my_path.replace(oracle_home, self.ORACLE_HOME_TOKEN)
            elif java_home and my_path.startswith(java_home):
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
                value = self._path_helper.fixup_path(value)
            cp_elements[index] = self.tokenize_path(value)

        return MODEL_LIST_DELIMITER.join(cp_elements)

    def password_is_tokenized(self, password):
        """
        Does the password contain a secret or environment variable token?
        :param password: the password to test
        :return: True if a secret or environment variable token is found; False otherwise
        """
        result = False
        if password is not None:
            result = self.SECRET_REGEX.search(password) is not None or self.ENV_REGEX.search(password) is not None
        return result

    def is_discover_passwords(self):
        """
        Whether to discover domain-encrypted passwords or not.
        :return: True, if domain-encrypted passwords should be discovered; False otherwise
        """
        return self._discover_passwords

    def is_encrypt_discovered_passwords(self):
        """
        Whether to encrypt discovered passwords
        :return:
        """
        return not self._model_config.get_store_discovered_passwords_in_clear_text()

    def is_discover_security_provider_data(self):
        return self._discover_security_provider_data is not None and len(self._discover_security_provider_data) > 0

    def is_discover_default_authenticator_data(self):
        return self._is_discover_security_provider_data_type(DEFAULT_AUTHENTICATOR)

    def is_discover_default_credential_mapper_data(self):
        return self._is_discover_security_provider_data_type(DEFAULT_CREDENTIAL_MAPPER)

    def is_discover_xacml_authorizer_data(self):
        return self._is_discover_security_provider_data_type(XACML_AUTHORIZER)

    def is_discover_xacml_role_mapper_data(self):
        return self._is_discover_security_provider_data_type(XACML_ROLE_MAPPER)

    def _is_discover_security_provider_data_type(self, scope):
        result = False
        if self.is_discover_security_provider_data():
            if ALL in self._discover_security_provider_data or scope in self._discover_security_provider_data:
                result = True
        return result

    def is_discover_security_provider_passwords(self):
        # These security providers have model passwords
        return self.is_discover_default_authenticator_data() or self.is_discover_default_credential_mapper_data()

    def get_discover_security_provider_data_types_label(self):
        # Result should only be used for display or logging
        data_types = self._discover_security_provider_data or []
        return ','.join(data_types)

    def is_discover_opss_wallet(self):
        return self._discover_opss_wallet

    def copy(self, arg_map):
        model_context_copy = copy.copy(self)
        model_context_copy.__copy_from_args(arg_map)
        if not model_context_copy.is_initialization_complete():
            model_context_copy.complete_initialization(self.get_remote_wls_version())
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
