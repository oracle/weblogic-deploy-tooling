"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.

Module that handles command-line argument parsing and common validation.
"""
import os
import java.io.File as JFile
import java.io.BufferedReader as BufferedReader
import java.io.InputStreamReader as InputStreamReader
import java.io.IOException as IOException
import java.lang.IllegalArgumentException as JIllegalArgumentException
import java.lang.System as System
import java.net.URI as JURI
import java.net.URISyntaxException as JURISyntaxException

import oracle.weblogic.deploy.aliases.VersionUtils as JVersionUtils
import oracle.weblogic.deploy.util.FileUtils as JFileUtils

from wlsdeploy.exception.exception_helper import create_cla_exception
from wlsdeploy.json.json_translator import JsonToPython
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import path_utils
import wlsdeploy.util.unicode_helper as str_helper
from wlsdeploy.util.exit_code import ExitCode
from wlsdeploy.util.target_configuration import TargetConfiguration
from wlsdeploy.util.validate_configuration import VALIDATION_METHODS

# tool type may indicate variations in argument processing
TOOL_TYPE_CREATE = "create"
TOOL_TYPE_DEFAULT = "default"
TOOL_TYPE_EXTRACT = "extract"
TOOL_TYPE_DISCOVER = 'discover'

_logger = PlatformLogger('wlsdeploy.util')

class CommandLineArgUtil(object):
    """
    Class that handles command-line argument parsing and common validation.
    """
    _class_name = 'CommandLineArgUtil'

    HELP_SWITCH                = '-help'
    ORACLE_HOME_SWITCH         = '-oracle_home'
    JAVA_HOME_SWITCH           = '-java_home'
    DOMAIN_HOME_SWITCH         = '-domain_home'
    DOMAIN_PARENT_SWITCH       = '-domain_parent'
    DOMAIN_TYPE_SWITCH         = '-domain_type'
    # never used by the tools but used by shell scripts
    WLST_PATH_SWITCH           = '-wlst_path'
    ADMIN_URL_SWITCH           = '-admin_url'
    ADMIN_USER_SWITCH          = '-admin_user'
    # phony arg used as a key to store the password
    ADMIN_PASS_SWITCH          = '-admin_pass'
    ADMIN_PASS_FILE_SWITCH     = '-admin_pass_file'
    ADMIN_PASS_ENV_SWITCH      = '-admin_pass_env'
    ARCHIVE_FILE_SWITCH        = '-archive_file'
    SKIP_ARCHIVE_FILE_SWITCH    = '-skip_archive'
    MODEL_FILE_SWITCH          = '-model_file'
    DISCARD_CURRENT_EDIT_SWITCH   = '-discard_current_edit'
    OPSS_WALLET_SWITCH         = '-opss_wallet'
    OPSS_WALLET_PASSPHRASE     = '-opss_wallet_passphrase'
    OPSS_WALLET_FILE_PASSPHRASE = '-opss_wallet_passphrase_file'
    OPSS_WALLET_ENV_PASSPHRASE  = '-opss_wallet_passphrase_env'
    PREVIOUS_MODEL_FILE_SWITCH = '-prev_model_file'
    VARIABLE_FILE_SWITCH       = '-variable_file'
    RCU_DB_SWITCH              = '-rcu_db'
    RCU_DB_USER_SWITCH         = '-rcu_db_user'
    RCU_PREFIX_SWITCH          = '-rcu_prefix'
    # phony arg used as a key to store the password
    RCU_SYS_PASS_SWITCH        = '-rcu_sys_pass'
    # phony arg used as a key to store the password
    RCU_SCHEMA_PASS_SWITCH     = '-rcu_schema_pass'
    # phony arg used as a key to store the encryption passphrase
    PASSPHRASE_SWITCH          = '-passphrase'
    PASSPHRASE_ENV_SWITCH      = '-passphrase_env'
    PASSPHRASE_FILE_SWITCH     = '-passphrase_file'
    ENCRYPT_MANUAL_SWITCH      = '-manual'
    # phony arg used as a key to store the password
    ONE_PASS_SWITCH            = '-password'
    CANCEL_CHANGES_IF_RESTART_REQ_SWITCH = '-cancel_changes_if_restart_required'
    USE_ENCRYPTION_SWITCH      = '-use_encryption'
    RUN_RCU_SWITCH             = '-run_rcu'
    TARGET_VERSION_SWITCH      = '-target_version'
    TARGET_MODE_SWITCH         = '-target_mode'
    # phony arg used as a key to store the trailing (non-switched) arguments
    TRAILING_ARGS_SWITCH       = '-trailing_arguments'
    ATTRIBUTES_ONLY_SWITCH     = '-attributes_only'
    FOLDERS_ONLY_SWITCH        = '-folders_only'
    RECURSIVE_SWITCH           = '-recursive'
    INTERACTIVE_MODE_SWITCH    = '-interactive'
    UPDATE_RCU_SCHEMA_PASS_SWITCH = '-updateRCUSchemaPassword'
    VALIDATION_METHOD          = '-method'
    REMOTE_SWITCH              = '-remote'
    # overrides for the variable injector
    VARIABLE_INJECTOR_FILE_SWITCH   = '-variable_injector_file'
    VARIABLE_KEYWORDS_FILE_SWITCH   = '-variable_keywords_file'
    VARIABLE_PROPERTIES_FILE_SWITCH = '-variable_properties_file'
    # extractDomainResource output file
    DOMAIN_RESOURCE_FILE_SWITCH   = '-domain_resource_file'
    OUTPUT_DIR_SWITCH = "-output_dir"
    WAIT_FOR_EDIT_LOCK_SWITCH = "-wait_for_edit_lock"
    TARGET_SWITCH = '-target'


    # arguments that are true if specified, false if not
    BOOLEAN_SWITCHES = [
        ATTRIBUTES_ONLY_SWITCH,
        ENCRYPT_MANUAL_SWITCH,
        FOLDERS_ONLY_SWITCH,
        INTERACTIVE_MODE_SWITCH,
        SKIP_ARCHIVE_FILE_SWITCH,
        RECURSIVE_SWITCH,
        CANCEL_CHANGES_IF_RESTART_REQ_SWITCH,
        RUN_RCU_SWITCH,
        UPDATE_RCU_SCHEMA_PASS_SWITCH,
        DISCARD_CURRENT_EDIT_SWITCH,
        USE_ENCRYPTION_SWITCH,
        REMOTE_SWITCH,
        WAIT_FOR_EDIT_LOCK_SWITCH
    ]

    # a slot to stash the parsed domain typedef dictionary
    DOMAIN_TYPEDEF             = 'domain_typedef'
    # a slot to stash the archive file object
    ARCHIVE_FILE               = 'archive_file'

    ARCHIVE_FILES_SEPARATOR = ','
    MODEL_FILES_SEPARATOR = ','

    def __init__(self, program_name, required_args, optional_args):
        self._program_name = program_name

        self._required_args = list(required_args)
        self._optional_args = list(optional_args)
        self._allow_multiple_models = False

        #
        # Add args that all tools should accept.
        #
        self._optional_args.append(self.HELP_SWITCH)
        self._optional_args.append(self.WLST_PATH_SWITCH)

        self._required_result = {}
        self._optional_result = {}

    def set_allow_multiple_models(self, allow_multiple_models):
        """
        This method determines if this instance allows multiple models to be specified for the MODEL_FILE_SWITCH
        argument. By default, multiple models are not allowed.
        :param allow_multiple_models: the flag indicating if multiple models are allowed
        """
        self._allow_multiple_models = allow_multiple_models

    def process_args(self, args, tool_type=TOOL_TYPE_DEFAULT, trailing_arg_count=0):
        """
        This method parses the command-line arguments and returns dictionaries of the required and optional args.

        :param args: sys.argv
        :param tool_type: optional, type of tool for special argument processing
        :param trailing_arg_count: optional, the number of trailing (no switch) arguments
        :return: the required and optional argument dictionaries
        :raises CLAException: if argument processing encounters a usage or validation exception
        """

        method_name = 'process_args'

        _logger.entering(args, class_name=self._class_name, method_name=method_name)
        #
        # reset the result fields in case the object was reused
        #
        self._required_result = {}
        self._optional_result = {}

        args_len = len(args)
        if args_len == 1:
            ex = create_cla_exception(ExitCode.HELP, 'Dummy Key')
            raise ex

        args = self._check_trailing_arguments(args, trailing_arg_count)
        args_len = len(args)

        idx = 1
        while idx < args_len:
            key = args[idx]
            _logger.fine('WLSDPLY-01600', key, class_name=self._class_name, method_name=method_name)
            if self.is_help_key(key):
                ex = create_cla_exception(ExitCode.HELP, 'Dummy Key')
                raise ex
            elif self.is_oracle_home_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_oracle_home_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_java_home_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_java_home_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_domain_home_key(key):
                value, idx = self._get_arg_value(args, idx)
                if tool_type == TOOL_TYPE_CREATE:
                    full_path = self._validate_domain_home_arg_for_create(value)
                elif tool_type == TOOL_TYPE_EXTRACT:
                    full_path = self._validate_domain_home_arg_for_extract(value)
                elif tool_type == TOOL_TYPE_DISCOVER:
                    full_path = value
                else:
                    full_path = validate_domain_home_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_domain_parent_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_domain_parent_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_domain_type_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_domain_type_arg(value)
                self._add_arg(key, value)
            elif self.is_wlst_path_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_wlst_path_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_admin_url_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_admin_url_arg(value)
                self._add_arg(key, value)
            elif self.is_admin_user_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_admin_user_arg(value)
                self._add_arg(key, value)
            elif self.is_admin_pass_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_admin_pass_arg(value)
                self._add_arg(key, value)
            elif self.is_admin_pass_env_key(key):
                env_var, idx = self._get_arg_value(args, idx)
                value = self._get_env_var_value(env_var)
                self._add_arg(self.get_admin_pass_key(), value)
            elif self.is_admin_pass_file_key(key):
                file_var, idx = self._get_arg_value(args, idx)
                value = self._get_from_file_value(file_var)
                self._add_arg(self.get_admin_pass_key(), value)
            elif self.is_archive_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_archive_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_opss_passphrase_env(key):
                env_var, idx = self._get_arg_value(args, idx)
                value = self._get_env_var_value(env_var)
                self._add_arg(self.get_opss_passphrase_key(), value)
            elif self.is_opss_passphrase_file(key):
                file_var, idx = self._get_arg_value(args, idx)
                value = self._get_from_file_value(file_var)
                self._add_arg(self.get_opss_passphrase_key(), value)
            elif self.is_opss_passphrase_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_opss_passphrase_arg(value)
                self._add_arg(key, value)
            elif self.is_opss_wallet_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_opss_wallet_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_model_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_model_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_previous_model_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_previous_model_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_validate_method_key(key):
                value, idx = self._get_arg_value(args, idx)
                context = self._validate_validate_method_arg(value)
                self._add_arg(key, context)
            elif self.is_variable_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._add_arg(key, value, True)
            elif self.is_rcu_database_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_rcu_database_arg(value)
                self._add_arg(key, value)
            elif self.is_rcu_dbuser_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_rcu_dbuser_arg(value)
                self._add_arg(key, value)
            elif self.is_rcu_prefix_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_rcu_prefix_arg(value)
                self._add_arg(key, value)
            elif self.is_rcu_sys_pass_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_rcu_sys_pass_arg(value)
                self._add_arg(key, value)
            elif self.is_rcu_schema_pass_key(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_rcu_schema_pass_arg(value)
                self._add_arg(key, value)
            elif self.is_passphrase_switch(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_passphrase_arg(value)
                self._add_arg(key, value)
            elif self.is_passphrase_env_switch(key):
                env_var, idx = self._get_arg_value(args, idx)
                value = self._get_env_var_value(env_var)
                self._add_arg(self.get_passphrase_switch(), value)
            elif self.is_passphrase_file_switch(key):
                file_var, idx = self._get_arg_value(args, idx)
                value = self._get_from_file_value(file_var)
                self._add_arg(self.get_passphrase_switch(), value)
            elif self.is_one_pass_switch(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_one_pass_arg(value)
                self._add_arg(key, value)
            elif self.is_target_version_switch(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_target_version_arg(value)
                self._add_arg(key, value)
            elif self.is_target_mode_switch(key):
                value, idx = self._get_arg_value(args, idx)
                self._validate_target_mode_arg(value)
                self._add_arg(key, value)
            elif self.is_variable_injector_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_variable_injector_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_variable_keywords_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_variable_keywords_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_variable_properties_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_variable_properties_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_domain_resource_file_key(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_domain_resource_file_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_boolean_switch(key):
                self._add_arg(key, True)
            elif self.is_compare_model_output_dir_switch(key):
                value, idx = self._get_arg_value(args, idx)
                full_path = self._validate_compare_model_output_dir_arg(value)
                self._add_arg(key, full_path, True)
            elif self.is_target_switch(key):
                value, idx = self._get_arg_value(args, idx)
                value = self._validate_target_arg(value)
                self._add_arg(key, value, True)
            else:
                ex = create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-01601', self._program_name, key)
                _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex
            idx += 1

        self._verify_required_args_present(self._program_name, self._required_args, self._required_result)

        combined_arg_map = self._optional_result.copy()
        combined_arg_map.update(self._required_result)

        _logger.exiting(class_name=self._class_name, method_name=method_name, result=combined_arg_map)
        return combined_arg_map

    def _get_arg_value(self, args, index):
        """
        Return the value after the specified index in the argument array.
        Throw an exception if the next index is past the end of the arguments.
        :param args: the arguments to be examined
        :param index: the index argument before the value
        :return: the value of the argument, and the next index value
        """
        method_name = '_get_arg_value'
        key = args[index]

        # check that key is valid here, to avoid validation if it is not
        if (key not in self._required_args) and (key not in self._optional_args):
            ex = create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-01632', key, self._program_name)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        index = index + 1
        if index >= len(args):
            ex = self._get_out_of_args_exception(key)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return args[index], index

    def _check_trailing_arguments(self, args, trailing_arg_count):
        """
        Remove any trailing (no switch) arguments from the argument list and add them to the required result.
          example:
            command.sh -oracle_home /oracle file1 file2
            file1 and file2 are trailing arguments

        :param args: the arguments to be examined
        :param trailing_arg_count: the number of trailing arguments that are expected
        :return: the argument list, with the trailing arguments removed
        :raises CLAException: if there are not enough arguments present
        """
        method_name = '_check_trailing_arguments'
        args_len = len(args)

        # verify there are enough arguments for any trailing (no switch) args
        if args_len < trailing_arg_count + 1:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01639', trailing_arg_count)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        # set required_result['TRAILING_ARGS'] to list of trailing args (such as ['file1', 'file2'])
        trailing_args = []
        for index in range(args_len - trailing_arg_count, args_len):
            arg = args[index]
            trailing_args.append(arg)
        self._required_result[self.TRAILING_ARGS_SWITCH] = trailing_args

        # remove trailing args from the list and return revised list
        return args[0:(args_len - trailing_arg_count)]

    def _verify_required_args_present(self, program_name, required_arguments, required_arg_map):
        """
        Verify that the required args are present.
        :param program_name: the program name, for logging
        :param required_arguments: the required arguments to be checked
        :param required_arg_map: the required arguments map
        :raises CLAException: if one or more of the required arguments are missing
        """
        _method_name = '_verify_required_args_present'

        for req_arg in required_arguments:
            if req_arg not in required_arg_map:
                ex = create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-20005', program_name, req_arg)
                _logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
                raise ex

    def get_help_key(self):
        return self.HELP_SWITCH

    def is_help_key(self, key):
        return self.HELP_SWITCH == key

    def get_oracle_home_key(self):
        return str_helper.to_string(self.ORACLE_HOME_SWITCH)

    def is_oracle_home_key(self, key):
        return self.ORACLE_HOME_SWITCH == key

    def _validate_oracle_home_arg(self, value):
        from wlsdeploy.util.weblogic_helper import WebLogicHelper
        method_name = '_validate_oracle_home_arg'

        try:
            oh = JFileUtils.validateExistingDirectory(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01602', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        oh_name = oh.getAbsolutePath()
        wl_helper = WebLogicHelper(_logger)
        wl_home_name = wl_helper.get_weblogic_home(oh_name)
        try:
            JFileUtils.validateExistingDirectory(wl_home_name)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01603', wl_home_name, oh_name,
                                      iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        wl_version = wl_helper.get_actual_weblogic_version()
        if not wl_helper.is_supported_weblogic_version():
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01604', oh_name, wl_version,
                                      wl_helper.MINIMUM_WEBLOGIC_VERSION)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return oh_name

    def get_java_home_key(self):
        return str_helper.to_string(self.JAVA_HOME_SWITCH)

    def is_java_home_key(self, key):
        return self.JAVA_HOME_SWITCH == key

    #
    # The Java Home argument is only used in create domain as the JVM version that the domain
    # should use, which may be a pre-Java 7 version.  As such, only verify that the directory
    # is valid.
    #
    def _validate_java_home_arg(self, value):
        method_name = '_validate_java_home_arg'

        try:
            jh = JFileUtils.validateExistingDirectory(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01605', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return jh.getAbsolutePath()

    def get_domain_home_key(self):
        return self.DOMAIN_HOME_SWITCH

    def is_domain_home_key(self, key):
        return self.DOMAIN_HOME_SWITCH == key

    def is_skip_archive_key(self, key):
        return self.SKIP_ARCHIVE_FILE_SWITCH == key

    #
    # The domain home arg used by create must be the child of a valid, writable directory.
    #
    def _validate_domain_home_arg_for_create(self, value):
        method_name = '_validate_domain_home_arg_for_create'

        try:
            parent_dir = os.path.dirname(value)
            JFileUtils.validateWritableDirectory(parent_dir)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01606', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        home_dir = JFile(value)
        return home_dir.getAbsolutePath()

    #
    # The domain home arg used by extract domain resource does not have to exist on local system.
    # Just check for non-empty value, and return exact text.
    #
    def _validate_domain_home_arg_for_extract(self, value):
        method_name = '_validate_domain_home_arg_for_extract'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01620')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return value

    def get_domain_parent_key(self):
        return self.DOMAIN_PARENT_SWITCH

    def is_domain_parent_key(self, key):
        return self.DOMAIN_PARENT_SWITCH == key

    #
    # The domain parent arg is only used by create domain.  It must be an existing, writable directory.
    #
    def _validate_domain_parent_arg(self, value):
        method_name = '_validate_domain_parent_arg'

        try:
            dp = JFileUtils.validateWritableDirectory(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01608', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return dp.getAbsolutePath()

    def get_domain_type_key(self):
        return self.DOMAIN_TYPE_SWITCH

    def is_domain_type_key(self, key):
        return self.DOMAIN_TYPE_SWITCH == key

    #
    # The domain type arg is only used by the shell scripts for all tools and create_domain.
    # Since create domain is extensible to new domain types, just validate that it is not empty.
    #
    def _validate_domain_type_arg(self, value):
        method_name = '_validate_domain_type_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01609')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_wlst_path_key(self):
        return self.WLST_PATH_SWITCH

    def is_wlst_path_key(self, key):
        return self.WLST_PATH_SWITCH == key

    def _validate_wlst_path_arg(self, value):
        method_name = '_validate_wlst_path_arg'

        try:
            wlst_path = JFileUtils.validateExistingDirectory(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01610', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return wlst_path.getAbsolutePath()

    def get_admin_url_key(self):
        return self.ADMIN_URL_SWITCH

    def is_admin_url_key(self, key):
        return self.ADMIN_URL_SWITCH == key

    def _validate_admin_url_arg(self, value):
        method_name = '_validate_admin_url_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01611')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        #
        # Because we cannot use java.net.URL due to it not understanding t3 and other RMI protocols,
        # do the best we can to validate the structure...
        #
        url_separator_index = value.find('://')
        if not url_separator_index > 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01612', value)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        try:
            JURI(value)
        except JURISyntaxException, use:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01613', value, use.getLocalizedMessage(), error=use)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_admin_user_key(self):
        return self.ADMIN_USER_SWITCH

    def is_admin_user_key(self, key):
        return self.ADMIN_USER_SWITCH == key

    def _validate_admin_user_arg(self, value):
        method_name = '_validate_admin_user_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01614')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_admin_pass_key(self):
        return self.ADMIN_PASS_SWITCH

    def is_admin_pass_key(self, key):
        return self.ADMIN_PASS_SWITCH == key

    def is_admin_pass_env_key(self, key):
        return self.ADMIN_PASS_ENV_SWITCH == key

    def is_admin_pass_file_key(self, key):
        return self.ADMIN_PASS_FILE_SWITCH == key

    def _validate_admin_pass_arg(self, value):
        method_name = '_validate_admin_pass_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01615')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_archive_file_key(self):
        return self.ARCHIVE_FILE_SWITCH

    def is_archive_file_key(self, key):
        return self.ARCHIVE_FILE_SWITCH == key

    def _validate_archive_file_arg(self, value):
        method_name = '_validate_archive_file_arg'

        result_archive_files = []  # type: list
        if self._allow_multiple_models:
            archive_files = get_archive_files(value)
        else:
            archive_files = [value]

        for archive_file in archive_files:
            try:
                archive_file = JFileUtils.validateFileName(archive_file)
                archive_file = archive_file.getAbsolutePath()
                result_archive_files.append(archive_file)
            except JIllegalArgumentException, iae:
                ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01616',
                                          archive_file, iae.getLocalizedMessage(), error=iae)
                _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex

        return CommandLineArgUtil.ARCHIVE_FILES_SEPARATOR.join(result_archive_files)

    def get_opss_passphrase_key(self):
        return self.OPSS_WALLET_PASSPHRASE

    def is_opss_passphrase_key(self, key):

        return self.OPSS_WALLET_PASSPHRASE == key

    def is_opss_passphrase_env(self, key):

        return self.OPSS_WALLET_ENV_PASSPHRASE == key

    def is_opss_passphrase_file(self, key):

        return self.OPSS_WALLET_FILE_PASSPHRASE == key

    def _validate_opss_passphrase_arg(self, value):
        method_name = '_validate_opss_passphrase_arg'
        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01615')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_opss_wallet_key(self):
        return self.OPSS_WALLET_SWITCH

    def get_opss_wallet_env(self):
        return self.OPSS_WALLET_ENV_SWITCH

    def get_opss_wallet_file(self):
        return self.OPSS_WALLET__SWITCH

    def is_opss_wallet_key(self, key):
        return self.OPSS_WALLET_SWITCH == key

    def _validate_opss_wallet_arg(self, value):
        method_name = '_validate_opss_wallet_arg'
        try:
            opss_wallet = JFileUtils.validateDirectoryName(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01646', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return opss_wallet.getAbsolutePath()

    def get_model_file_key(self):
        return self.MODEL_FILE_SWITCH

    def is_model_file_key(self, key):
        return self.MODEL_FILE_SWITCH == key

    def _validate_model_file_arg(self, value):
        method_name = '_validate_model_file_arg'

        result_model_files = []  # type: list
        if self._allow_multiple_models:
            model_files = get_model_files(value)
        else:
            model_files = [value]

        for model_file in model_files:
            try:
                model_file = JFileUtils.validateFileName(model_file)
                model_file = model_file.getAbsolutePath()
                result_model_files.append(model_file)
            except JIllegalArgumentException, iae:
                ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01617',
                                          model_file, iae.getLocalizedMessage(), error=iae)
                _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex

        return ",".join(result_model_files)

    def get_previous_model_file_key(self):
        return self.PREVIOUS_MODEL_FILE_SWITCH

    def is_previous_model_file_key(self, key):
        return self.PREVIOUS_MODEL_FILE_SWITCH == key

    def _validate_previous_model_file_arg(self, value):
        method_name = '_validate_previous_model_file_arg'

        try:
            model = JFileUtils.validateFileName(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01618', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return model.getAbsolutePath()

    def is_validate_method_key(self, key):
        return self.VALIDATION_METHOD == key

    def _validate_validate_method_arg(self, value):
        method_name = '_validate_validate_method_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-20029')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        elif value not in VALIDATION_METHODS:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-20030', value, VALIDATION_METHODS)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return value

    def get_variable_file_key(self):
        return self.VARIABLE_FILE_SWITCH

    def is_variable_file_key(self, key):
        return self.VARIABLE_FILE_SWITCH == key

    def get_rcu_database_key(self):
        return self.RCU_DB_SWITCH

    def is_rcu_database_key(self, key):
        return self.RCU_DB_SWITCH == key

    def _validate_rcu_database_arg(self, value):
        method_name = '_validate_rcu_database_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01621')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_rcu_dbuser_key(self):
        return self.RCU_DB_USER_SWITCH

    def is_rcu_dbuser_key(self, key):
        return self.RCU_DB_USER_SWITCH == key

    def _validate_rcu_dbuser_arg(self, value):
        method_name = '_validate_rcu_dbuser_arg'
        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01622')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_rcu_prefix_key(self):
        return self.RCU_PREFIX_SWITCH

    def is_rcu_prefix_key(self, key):
        return self.RCU_PREFIX_SWITCH == key

    def _validate_rcu_prefix_arg(self, value):
        method_name = '_validate_rcu_prefix_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01622')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_rcu_sys_pass_key(self):
        return self.RCU_SYS_PASS_SWITCH

    def is_rcu_sys_pass_key(self, key):
        return self.RCU_SYS_PASS_SWITCH == key

    def _validate_rcu_sys_pass_arg(self, value):
        method_name = '_validate_rcu_sys_pass_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01623')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_rcu_schema_pass_key(self):
        return self.RCU_SCHEMA_PASS_SWITCH

    def is_rcu_schema_pass_key(self, key):
        return self.RCU_SCHEMA_PASS_SWITCH == key

    def _validate_rcu_schema_pass_arg(self, value):
        method_name = '_validate_rcu_schema_pass_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01624')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def _get_env_var_value(self, env_var):
        _method_name = '_get_env_var_value'
        value = System.getenv(env_var)
        if not value:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01649', env_var)
            _logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex
        return value

    def _get_from_file_value(self, file_var):
        _method_name = '_get_from_file_value'
        ifile = None
        try:
            stream = JFileUtils.getFileAsStream(file_var)
            ifile = BufferedReader(InputStreamReader(stream))
            value = ifile.readLine()
            ifile.close()
            return value
        except IOException:
            if ifile:
                ifile.close()
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01651', file_var)
            _logger.throwing(ex, class_name=self._class_name, method_name=_method_name)
            raise ex

    def get_passphrase_switch(self):
        return self.PASSPHRASE_SWITCH

    def is_passphrase_switch(self, key):
        return self.PASSPHRASE_SWITCH == key

    def is_passphrase_env_switch(self, key):
        return self.PASSPHRASE_ENV_SWITCH == key

    def is_passphrase_file_switch(self, key):
        return self.PASSPHRASE_FILE_SWITCH == key

    def _validate_passphrase_arg(self, value):
        method_name = '_validate_passphrase_switch'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01625')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_one_pass_switch(self):
        return self.ONE_PASS_SWITCH

    def is_one_pass_switch(self, key):
        return self.ONE_PASS_SWITCH == key

    def _validate_one_pass_arg(self, value):
        method_name = '_validate_one_pass_switch'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01626')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_target_version_switch(self):
        return self.TARGET_VERSION_SWITCH

    def is_target_version_switch(self, key):
        return self.TARGET_VERSION_SWITCH == key

    def _validate_target_version_arg(self, value):
        from wlsdeploy.util.weblogic_helper import WebLogicHelper
        method_name = '_validate_target_version_arg'

        # Try our best to determine if this is a legitimate WLS version number.
        # At the end of the day, the user can still enter a non-existent version number
        # like 845.283.412 and this code will not invalidate it because we cannot
        # predict future version numbers...
        #
        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01627')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        elif not JVersionUtils.isVersion(value):
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01628', value)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        else:
            wl_helper = WebLogicHelper(_logger, value)
            if not wl_helper.is_supported_weblogic_version():
                ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01629', value)
                _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex

    def get_target_mode_switch(self):
        return self.TARGET_MODE_SWITCH

    def is_target_mode_switch(self, key):
        return self.TARGET_MODE_SWITCH == key

    def _validate_target_mode_arg(self, value):
        method_name = '_validate_target_mode_arg'

        if value is None or len(value) == 0:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01630')
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        elif value.lower() != 'online' and value.lower() != 'offline':
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01631', value)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def get_variable_injector_file_key(self):
        return self.VARIABLE_INJECTOR_FILE_SWITCH

    def is_variable_injector_file_key(self, key):
        return self.VARIABLE_INJECTOR_FILE_SWITCH == key

    def _validate_variable_injector_file_arg(self, value):
        method_name = '_validate_variable_injector_file_arg'

        try:
            injector = JFileUtils.validateExistingFile(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01635', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return injector.getAbsolutePath()

    def get_variable_keywords_file_key(self):
        return self.VARIABLE_KEYWORDS_FILE_SWITCH

    def is_variable_keywords_file_key(self, key):
        return self.VARIABLE_KEYWORDS_FILE_SWITCH == key

    def _validate_variable_keywords_file_arg(self, value):
        method_name = '_validate_variable_keywords_file_arg'

        try:
            keywords = JFileUtils.validateExistingFile(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01636', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return keywords.getAbsolutePath()

    # use this argument switch for the injector as the variables file does not have to exist
    def get_variable_properties_file_key(self):
        return self.VARIABLE_PROPERTIES_FILE_SWITCH

    def is_variable_properties_file_key(self, key):
        return self.VARIABLE_PROPERTIES_FILE_SWITCH == key

    def _validate_variable_properties_file_arg(self, value):
        method_name = '_validate_variable_properties_file_arg'

        try:
            variables = JFileUtils.validateFileName(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01620', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return variables.getAbsolutePath()

    def is_domain_resource_file_key(self, key):
        return self.DOMAIN_RESOURCE_FILE_SWITCH == key

    def _validate_domain_resource_file_arg(self, value):
        method_name = '_validate_domain_resource_file_arg'

        try:
            variables = JFileUtils.validateFileName(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01637', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return variables.getAbsolutePath()

    def is_boolean_switch(self, key):
        return key in self.BOOLEAN_SWITCHES

    def is_compare_model_output_dir_switch(self, key):
        return self.OUTPUT_DIR_SWITCH == key

    def _validate_compare_model_output_dir_arg(self, value):
        method_name = '_validate_compare_model_output_dir_arg'
        try:
            variables = JFileUtils.validateDirectoryName(value)
        except JIllegalArgumentException, iae:
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                      'WLSDPLY-01647', value, iae.getLocalizedMessage(), error=iae)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return variables.getAbsolutePath()

    def is_target_switch(self, key):
        return key == self.TARGET_SWITCH

    def _validate_target_arg(self, value):
        method_name = 'validate_kubernetes_script_file_switch'

        # Check if the target configuration file exists
        target_configuration_file = path_utils.find_config_path(os.path.join('targets', value, 'target.json'))
        if not os.path.exists(target_configuration_file):
            ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01643', value, target_configuration_file)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        else:
            try:
                # verify the file is in proper format
                config_dictionary = JsonToPython(target_configuration_file).parse()
                target_configuration = TargetConfiguration(config_dictionary)

                target_configuration.validate_configuration(ExitCode.ARG_VALIDATION_ERROR, target_configuration_file)

            except SyntaxError, se:
                ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01644', target_configuration_file, se)
                _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex

        return value


    ###########################################################################
    # Helper methods                                                          #
    ###########################################################################

    def _add_arg(self, key, value, is_file_path=False):
        method_name = '_add_arg'

        fixed_value = value
        if is_file_path:
            fixed_value = value.replace('\\', '/')

        if key in self._required_args:
            self._required_result[key] = fixed_value
        elif key in self._optional_args:
            self._optional_result[key] = fixed_value
        else:
            ex = create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-01632', key, self._program_name)
            _logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

    def _get_out_of_args_exception(self, key):
        ex = create_cla_exception(ExitCode.USAGE_ERROR, 'WLSDPLY-01638', key, self._program_name)
        return ex


###########################################################################
# Static methods                                                          #
###########################################################################

def get_model_files(model_files_text):
    """
    Returns a list of model files from the comma-separated MODEL_FILE_SWITCH value.
    Returns a list of one item if there is only one model in the value.
    :param model_files_text: the value of the MODEL_FILE_SWITCH argument
    :return: a list of model files
    """
    return model_files_text.split(CommandLineArgUtil.MODEL_FILES_SEPARATOR)


def get_archive_files(archive_files_text):
    """
    Returns a list of archive files from the comma-separated ARCHIVE_FILE_SWITCH value.
    Returns a list of one item if there is only one archive in the value.
    :param archive_files_text: the value of the ARCHIVE_FILE_SWITCH argument
    :return: a list of archive files
    """
    return archive_files_text.split(CommandLineArgUtil.ARCHIVE_FILES_SEPARATOR)


def validate_domain_home_arg(value):
    method_name = '_validate_domain_home_arg'

    try:
        dh = JFileUtils.validateExistingDirectory(value)
    except JIllegalArgumentException, iae:
        ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR,
                                  'WLSDPLY-01606', value, iae.getLocalizedMessage(), error=iae)
        _logger.throwing(ex, class_name='CommandLineArgUtil', method_name=method_name)
        raise ex

    config_xml = JFile(dh, 'config/config.xml')
    try:
        config_xml = JFileUtils.validateExistingFile(config_xml.getAbsolutePath())
    except JIllegalArgumentException, iae:
        ex = create_cla_exception(ExitCode.ARG_VALIDATION_ERROR, 'WLSDPLY-01607', dh.getAbsolutePath(),
                                  config_xml.getAbsolutePath(), iae.getLocalizedMessage(), error=iae)
        _logger.throwing(ex, class_name='CommandLineArgUtil', method_name=method_name)
        raise ex

    home_dir = JFile(value)
    return home_dir.getAbsolutePath()
