"""
Copyright (c) 2017, 2018, Oracle and/or its affiliates. All rights reserved.
The Universal Permissive License (UPL), Version 1.0

Module that handles command-line argument parsing and common validation.
"""
import os
import java.io.File as JFile
import java.lang.IllegalArgumentException as JIllegalArgumentException
import java.net.URI as JURI
import java.net.URISyntaxException as JURISyntaxException

import oracle.weblogic.deploy.aliases.VersionUtils as JVersionUtils
import oracle.weblogic.deploy.util.FileUtils as JFileUtils

from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util.weblogic_helper import WebLogicHelper

from wlsdeploy.aliases.model_constants import KNOWN_TOPLEVEL_MODEL_SECTIONS
from wlsdeploy.tool.validate.usage_printer import MODEL_PATH_PATTERN


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
    ARCHIVE_FILE_SWITCH        = '-archive_file'
    MODEL_FILE_SWITCH          = '-model_file'
    PREVIOUS_MODEL_FILE_SWITCH = '-prev_model_file'
    VARIABLE_FILE_SWITCH       = '-variable_file'
    PRINT_USAGE_SWITCH         = '-print_usage'
    RCU_DB_SWITCH              = '-rcu_db'
    RCU_PREFIX_SWITCH          = '-rcu_prefix'
    # phony arg used as a key to store the password
    RCU_SYS_PASS_SWITCH        = '-rcu_sys_pass'
    # phony arg used as a key to store the password
    RCU_SCHEMA_PASS_SWITCH     = '-rcu_schema_pass'
    # phony arg used as a key to store the encryption passphrase
    PASSPHRASE_SWITCH          = '-passphrase'
    ENCRYPT_MANUAL_SWITCH      = '-manual'
    # phony arg used as a key to store the password
    ONE_PASS_SWITCH            = '-password'
    USE_ENCRYPTION_SWITCH      = '-use_encryption'
    RUN_RCU_SWITCH             = '-run_rcu'
    TARGET_VERSION_SWITCH      = '-target_version'
    TARGET_MODE_SWITCH         = '-target_mode'
    ATTRIBUTES_ONLY_SWITCH     = '-attributes_only'
    FOLDERS_ONLY_SWITCH        = '-folders_only'
    RECURSIVE_SWITCH           = '-recursive'
    # overrides for the variable injector
    VARIABLE_INJECTOR_FILE_SWITCH   = '-variable_injector_file'
    VARIABLE_KEYWORDS_FILE_SWITCH   = '-variable_keywords_file'
    VARIABLE_PROPERTIES_FILE_SWITCH = '-variable_properties_file'

    # a slot to stash the parsed domain typedef dictionary
    DOMAIN_TYPEDEF             = 'domain_typedef'
    # a slot to stash the archive file object
    ARCHIVE_FILE               = 'archive_file'

    HELP_EXIT_CODE                 = 100
    USAGE_ERROR_EXIT_CODE          = 99
    ARG_VALIDATION_ERROR_EXIT_CODE = 98
    PROG_ERROR_EXIT_CODE           = 2
    PROG_WARNING_EXIT_CODE         = 1
    PROG_OK_EXIT_CODE              = 0

    def __init__(self, program_name, required_args, optional_args):
        self._program_name = program_name
        self._logger = PlatformLogger('wlsdeploy.util')

        self._required_args = list(required_args)
        self._optional_args = list(optional_args)

        #
        # Add args that all tools should accept.
        #
        self._optional_args.append(self.HELP_SWITCH)
        self._optional_args.append(self.WLST_PATH_SWITCH)

        self._required_result = {}
        self._optional_result = {}
        return

    def process_args(self, args, for_domain_create=False):
        """
        This method parses the command-line arguments and returns dictionaries of the required and optional args.

        :param args: sys.argv
        :param for_domain_create: true if validating for domain creation
        :return: the required and optional argument dictionaries
        :raises CLAException: if argument processing encounters a usage or validation exception
        """

        method_name = 'process_args'

        self._logger.entering(args, class_name=self._class_name, method_name=method_name)
        #
        # reset the result fields in case the object was reused
        #
        self._required_result = {}
        self._optional_result = {}

        args_len = len(args)
        if args_len == 1:
            ex = exception_helper.create_cla_exception('Dummy Key')
            ex.setExitCode(self.HELP_EXIT_CODE)
            raise ex

        idx = 1
        while idx < args_len:
            key = args[idx]
            self._logger.fine('WLSDPLY-01600', key, class_name=self._class_name, method_name=method_name)
            if self.is_help_key(key):
                ex = exception_helper.create_cla_exception('Dummy Key')
                ex.setExitCode(self.HELP_EXIT_CODE)
                raise ex
            elif self.is_oracle_home_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_oracle_home_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_java_home_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_java_home_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_domain_home_key(key):
                idx += 1
                if idx < args_len:
                    if for_domain_create:
                        full_path = self._validate_domain_home_arg_for_create(args[idx])
                    else:
                        full_path = self._validate_domain_home_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_domain_parent_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_domain_parent_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_domain_type_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_domain_type_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_wlst_path_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_wlst_path_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_admin_url_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_admin_url_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_admin_user_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_admin_user_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_admin_pass_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_admin_pass_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_archive_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_archive_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_model_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_model_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_previous_model_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_previous_model_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_print_usage_key(key):
                idx += 1
                if idx < args_len:
                    context = self._validate_print_usage_arg(args[idx])
                    self._add_arg(key, context)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_variable_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_variable_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_rcu_database_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_rcu_database_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_rcu_prefix_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_rcu_prefix_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_rcu_sys_pass_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_rcu_sys_pass_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_rcu_schema_pass_key(key):
                idx += 1
                if idx < args_len:
                    self._validate_rcu_schema_pass_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_passphrase_switch(key):
                idx += 1
                if idx < args_len:
                    self._validate_passphrase_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_encrypt_manual_switch(key):
                self._add_arg(key, True)
            elif self.is_one_pass_switch(key):
                idx += 1
                if idx < args_len:
                    self._validate_one_pass_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_use_encryption_switch(key):
                self._add_arg(key, True)
            elif self.is_run_rcu_switch(key):
                self._add_arg(key, True)
            elif self.is_target_version_switch(key):
                idx += 1
                if idx < args_len:
                    self._validate_target_version_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_target_mode_switch(key):
                idx += 1
                if idx < args_len:
                    self._validate_target_mode_arg(args[idx])
                    self._add_arg(key, args[idx])
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_attributes_only_switch(key):
                self._add_arg(key, True)
            elif self.is_folders_only_switch(key):
                self._add_arg(key, True)
            elif self.is_recursive_switch(key):
                self._add_arg(key, True)
            elif self.is_variable_injector_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_variable_injector_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_variable_keywords_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_variable_keywords_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            elif self.is_variable_properties_file_key(key):
                idx += 1
                if idx < args_len:
                    full_path = self._validate_variable_properties_file_arg(args[idx])
                    self._add_arg(key, full_path, True)
                else:
                    ex = self._get_out_of_args_exception(key)
                    self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                    raise ex
            else:
                ex = exception_helper.create_cla_exception('WLSDPLY-01601', self._program_name, key)
                ex.setExitCode(self.USAGE_ERROR_EXIT_CODE)
                self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex
            idx += 1

        print_result = {'required': self._required_result, 'optional': self._optional_result}
        self._logger.exiting(class_name=self._class_name, method_name=method_name, result=print_result)
        return self._required_result, self._optional_result

    def get_help_key(self):
        return self.HELP_SWITCH

    def is_help_key(self, key):
        return self.HELP_SWITCH == key

    def get_oracle_home_key(self):
        return str(self.ORACLE_HOME_SWITCH)

    def is_oracle_home_key(self, key):
        return self.ORACLE_HOME_SWITCH == key

    def _validate_oracle_home_arg(self, value):
        method_name = '_validate_oracle_home_arg'

        try:
            oh = JFileUtils.validateExistingDirectory(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01602', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        oh_name = oh.getAbsolutePath()
        wl_helper = WebLogicHelper(self._logger)
        wl_home_name = wl_helper.get_weblogic_home(oh_name)
        try:
            JFileUtils.validateExistingDirectory(wl_home_name)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01603', wl_home_name,
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        wl_version = wl_helper.get_actual_weblogic_version()
        if not wl_helper.is_supported_weblogic_version():
            ex = exception_helper.create_cla_exception('WLSDPLY-01604', oh_name, wl_version,
                                                       wl_helper.MINIMUM_WEBLOGIC_VERSION)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return oh_name

    def get_java_home_key(self):
        return str(self.JAVA_HOME_SWITCH)

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
            ex = exception_helper.create_cla_exception('WLSDPLY-01605', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return jh.getAbsolutePath()

    def get_domain_home_key(self):
        return self.DOMAIN_HOME_SWITCH

    def is_domain_home_key(self, key):
        return self.DOMAIN_HOME_SWITCH == key

    #
    # The domain home arg used by discover and deploy must be a valid domain home.
    #
    def _validate_domain_home_arg(self, value):
        method_name = '_validate_domain_home_arg'

        try:
            dh = JFileUtils.validateExistingDirectory(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01606', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        config_xml = JFile(dh, 'config/config.xml')
        try:
            config_xml = JFileUtils.validateExistingFile(config_xml.getAbsolutePath())
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01607', dh.getAbsolutePath(),
                                                       config_xml.getAbsolutePath(),
                                                       iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return dh.getAbsolutePath()

    #
    # The domain home arg used by create must be the child of a valid, writable directory.
    #
    def _validate_domain_home_arg_for_create(self, value):
        method_name = '_validate_domain_home_arg_for_create'

        try:
            parent_dir = os.path.dirname(value)
            JFileUtils.validateWritableDirectory(parent_dir)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01606', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        home_dir = JFile(value)
        return home_dir.getAbsolutePath()

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
            ex = exception_helper.create_cla_exception('WLSDPLY-01608', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
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
            ex = exception_helper.create_cla_exception('WLSDPLY-01609')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_wlst_path_key(self):
        return self.WLST_PATH_SWITCH

    def is_wlst_path_key(self, key):
        return self.WLST_PATH_SWITCH == key

    def _validate_wlst_path_arg(self, value):
        method_name = '_validate_wlst_path_arg'

        try:
            wlst_path = JFileUtils.validateExistingDirectory(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01610', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return wlst_path.getAbsolutePath()

    def get_admin_url_key(self):
        return self.ADMIN_URL_SWITCH

    def is_admin_url_key(self, key):
        return self.ADMIN_URL_SWITCH == key

    def _validate_admin_url_arg(self, value):
        method_name = '_validate_admin_url_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01611')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        #
        # Because we cannot use java.net.URL due to it not understanding t3 and other RMI protocols,
        # do the best we can to validate the structure...
        #
        url_separator_index = value.find('://')
        if not url_separator_index > 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01612', value)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        try:
            JURI(value)
        except JURISyntaxException, use:
            ex = exception_helper.create_cla_exception('WLSDPLY-01613', value, use.getLocalizedMessage(), error=use)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex

        return

    def get_admin_user_key(self):
        return self.ADMIN_USER_SWITCH

    def is_admin_user_key(self, key):
        return self.ADMIN_USER_SWITCH == key

    def _validate_admin_user_arg(self, value):
        method_name = '_validate_admin_user_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01614')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_admin_pass_key(self):
        return self.ADMIN_PASS_SWITCH

    def is_admin_pass_key(self, key):
        return self.ADMIN_PASS_SWITCH == key

    def _validate_admin_pass_arg(self, value):
        method_name = '_validate_admin_pass_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01615')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_archive_file_key(self):
        return self.ARCHIVE_FILE_SWITCH

    def is_archive_file_key(self, key):
        return self.ARCHIVE_FILE_SWITCH == key

    def _validate_archive_file_arg(self, value):
        method_name = '_validate_archive_file_arg'

        try:
            archive = JFileUtils.validateFileName(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01616', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return archive.getAbsolutePath()

    def get_model_file_key(self):
        return self.MODEL_FILE_SWITCH

    def is_model_file_key(self, key):
        return self.MODEL_FILE_SWITCH == key

    def _validate_model_file_arg(self, value):
        method_name = '_validate_model_file_arg'

        try:
            model = JFileUtils.validateFileName(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01617', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return model.getAbsolutePath()

    def get_previous_model_file_key(self):
        return self.PREVIOUS_MODEL_FILE_SWITCH

    def is_previous_model_file_key(self, key):
        return self.PREVIOUS_MODEL_FILE_SWITCH == key

    def _validate_previous_model_file_arg(self, value):
        method_name = '_validate_previous_model_file_arg'

        try:
            model = JFileUtils.validateFileName(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01618', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return model.getAbsolutePath()

    def get_print_usage_key(self):
        return self.PRINT_USAGE_SWITCH

    def is_print_usage_key(self, key):
        return self.PRINT_USAGE_SWITCH == key

    def _validate_print_usage_arg(self, value):
        method_name = '_validate_print_usage_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01619')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        matcher = MODEL_PATH_PATTERN.match(value)
        if not matcher:
            ex = exception_helper.create_cla_exception('WLSDPLY-01633', self.PRINT_USAGE_SWITCH, value)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        section_name = matcher.group(1)
        if section_name not in KNOWN_TOPLEVEL_MODEL_SECTIONS:
            ex = exception_helper.create_cla_exception('WLSDPLY-01634', self.PRINT_USAGE_SWITCH, value,
                                                       section_name, KNOWN_TOPLEVEL_MODEL_SECTIONS)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return value

    def get_variable_file_key(self):
        return self.VARIABLE_FILE_SWITCH

    def is_variable_file_key(self, key):
        return self.VARIABLE_FILE_SWITCH == key

    def _validate_variable_file_arg(self, value):
        method_name = '_validate_variable_file_arg'

        try:
            variable_file = JFileUtils.validateExistingFile(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01620', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return variable_file.getAbsolutePath()

    def get_rcu_database_key(self):
        return self.RCU_DB_SWITCH

    def is_rcu_database_key(self, key):
        return self.RCU_DB_SWITCH == key

    def _validate_rcu_database_arg(self, value):
        method_name = '_validate_rcu_database_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01621')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_rcu_prefix_key(self):
        return self.RCU_PREFIX_SWITCH

    def is_rcu_prefix_key(self, key):
        return self.RCU_PREFIX_SWITCH == key

    def _validate_rcu_prefix_arg(self, value):
        method_name = '_validate_rcu_prefix_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01622')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_rcu_sys_pass_key(self):
        return self.RCU_SYS_PASS_SWITCH

    def is_rcu_sys_pass_key(self, key):
        return self.RCU_SYS_PASS_SWITCH == key

    def _validate_rcu_sys_pass_arg(self, value):
        method_name = '_validate_rcu_sys_pass_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01623')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_rcu_schema_pass_key(self):
        return self.RCU_SCHEMA_PASS_SWITCH

    def is_rcu_schema_pass_key(self, key):
        return self.RCU_SCHEMA_PASS_SWITCH == key

    def _validate_rcu_schema_pass_arg(self, value):
        method_name = '_validate_rcu_schema_pass_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01624')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_passphrase_switch(self):
        return self.PASSPHRASE_SWITCH

    def is_passphrase_switch(self, key):
        return self.PASSPHRASE_SWITCH == key

    def _validate_passphrase_arg(self, value):
        method_name = '_validate_passphrase_switch'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01625')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_encrypt_manual_switch(self):
        return self.ENCRYPT_MANUAL_SWITCH

    def is_encrypt_manual_switch(self, key):
        return self.ENCRYPT_MANUAL_SWITCH == key

    def get_one_pass_switch(self):
        return self.ONE_PASS_SWITCH

    def is_one_pass_switch(self, key):
        return self.ONE_PASS_SWITCH == key

    def _validate_one_pass_arg(self, value):
        method_name = '_validate_one_pass_switch'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01626')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_use_encryption_switch(self):
        return self.USE_ENCRYPTION_SWITCH

    def is_use_encryption_switch(self, key):
        return self.USE_ENCRYPTION_SWITCH == key

    def get_run_rcu_switch(self):
        return self.RUN_RCU_SWITCH

    def is_run_rcu_switch(self, key):
        return self.RUN_RCU_SWITCH == key

    def get_target_version_switch(self):
        return self.TARGET_VERSION_SWITCH

    def is_target_version_switch(self, key):
        return self.TARGET_VERSION_SWITCH == key

    def _validate_target_version_arg(self, value):
        method_name = '_validate_target_version_arg'

        # Try our best to determine if this is a legitimate WLS version number.
        # At the end of the day, the user can still enter a non-existent version number
        # like 845.283.412 and this code will not invalidate it because we cannot
        # predict future version numbers...
        #
        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01627')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        elif not JVersionUtils.isVersion(value):
            ex = exception_helper.create_cla_exception('WLSDPLY-01628', value)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        else:
            wl_helper = WebLogicHelper(self._logger, value)
            if not wl_helper.is_supported_weblogic_version():
                ex = exception_helper.create_cla_exception('WLSDPLY-01629', value)
                ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
                self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
                raise ex
        return

    def get_target_mode_switch(self):
        return self.TARGET_MODE_SWITCH

    def is_target_mode_switch(self, key):
        return self.TARGET_MODE_SWITCH == key

    def get_attributes_only_switch(self):
        return self.ATTRIBUTES_ONLY_SWITCH

    def is_attributes_only_switch(self, key):
        return self.ATTRIBUTES_ONLY_SWITCH == key

    def get_folders_only_switch(self):
        return self.FOLDERS_ONLY_SWITCH

    def is_folders_only_switch(self, key):
        return self.FOLDERS_ONLY_SWITCH == key

    def get_recursive_switch(self):
        return self.RECURSIVE_SWITCH

    def is_recursive_switch(self, key):
        return self.RECURSIVE_SWITCH == key

    def _validate_target_mode_arg(self, value):
        method_name = '_validate_target_mode_arg'

        if value is None or len(value) == 0:
            ex = exception_helper.create_cla_exception('WLSDPLY-01630')
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        elif value.lower() != 'online' and value.lower() != 'offline':
            ex = exception_helper.create_cla_exception('WLSDPLY-01631', value)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def get_variable_injector_file_key(self):
        return self.VARIABLE_INJECTOR_FILE_SWITCH

    def is_variable_injector_file_key(self, key):
        return self.VARIABLE_INJECTOR_FILE_SWITCH == key

    def _validate_variable_injector_file_arg(self, value):
        method_name = '_validate_variable_injector_file_arg'

        try:
            injector = JFileUtils.validateExistingFile(value)
        except JIllegalArgumentException, iae:
            ex = exception_helper.create_cla_exception('WLSDPLY-01635', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
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
            ex = exception_helper.create_cla_exception('WLSDPLY-01636', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
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
            ex = exception_helper.create_cla_exception('WLSDPLY-01620', value, iae.getLocalizedMessage(), error=iae)
            ex.setExitCode(self.ARG_VALIDATION_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return variables.getAbsolutePath()


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
            ex = exception_helper.create_cla_exception('WLSDPLY-01632', key, self._program_name)
            ex.setExitCode(self.USAGE_ERROR_EXIT_CODE)
            self._logger.throwing(ex, class_name=self._class_name, method_name=method_name)
            raise ex
        return

    def _get_out_of_args_exception(self, key):
        ex = exception_helper.create_cla_exception('WLSDPLY-01110', key, self._program_name)
        ex.setExitCode(self.USAGE_ERROR_EXIT_CODE)
        return ex
