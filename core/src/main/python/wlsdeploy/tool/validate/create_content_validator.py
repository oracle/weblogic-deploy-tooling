"""
Copyright (c) 2023, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from java.lang import Boolean
from java.lang import Integer
from java.util import HashMap
from oracle.weblogic.deploy.create import RCURunner
from oracle.weblogic.deploy.validate import PasswordValidator
from oracle.weblogic.deploy.validate import ValidateException

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.location_context import LocationContext
from wlsdeploy.aliases.model_constants import ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import ADMIN_USERNAME
from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import DATABASE_TYPE
from wlsdeploy.aliases.model_constants import DEFAULT_REALM
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DOMAIN_INFO_ALIAS
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import ORACLE_DATABASE_CONNECTION_TYPE
from wlsdeploy.aliases.model_constants import PASSWORD
from wlsdeploy.aliases.model_constants import PASSWORD_VALIDATOR
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_DATABASE_TYPE
from wlsdeploy.aliases.model_constants import RCU_DB_CONN_STRING
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_TEMP_TBLSPACE
from wlsdeploy.aliases.model_constants import REALM
from wlsdeploy.aliases.model_constants import SECURITY
from wlsdeploy.aliases.model_constants import SECURITY_CONFIGURATION
from wlsdeploy.aliases.model_constants import SYSTEM_PASSWORD_VALIDATOR
from wlsdeploy.aliases.model_constants import TNS_ENTRY
from wlsdeploy.aliases.model_constants import TOPOLOGY
from wlsdeploy.aliases.model_constants import USER
from wlsdeploy.exception import exception_helper
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.validate.content_validator import ContentValidator
from wlsdeploy.util import dictionary_utils

ALL_DB_TYPES = [
    RCURunner.ORACLE_DB_TYPE,
    RCURunner.EBR_DB_TYPE,
    RCURunner.SQLSERVER_DB_TYPE,
    RCURunner.DB2_DB_TYPE,
    RCURunner.MYSQL_DB_TYPE
]

ORACLE_DB_TYPES = [
    RCURunner.ORACLE_DB_TYPE,
    RCURunner.EBR_DB_TYPE
]

ORACLE_DB_CONNECTION_TYPES = [
    RCURunner.ORACLE_ATP_DB_TYPE,
    RCURunner.ORACLE_SSL_DB_TYPE
]

DEPRECATED_DB_TYPES = [
    RCURunner.ORACLE_DB_TYPE,
    RCURunner.ORACLE_ATP_DB_TYPE,
    RCURunner.ORACLE_SSL_DB_TYPE
]

class CreateDomainContentValidator(ContentValidator):
    """
    Class for validating consistency and compatibility of model folders and attributes for creating a domain.
    These checks are done after alias folder and attribute checks.
    These checks should be performed against a complete, merged model.
    """
    _class_name = 'CreateDomainContentValidator'
    _logger = PlatformLogger('wlsdeploy.validate')

    def __init__(self, model_context, archive_helper, aliases):
        ContentValidator.__init__(self, model_context, aliases)
        self._archive_helper = archive_helper

    # Override
    def validate_model_content(self, model_dict):
        """
        Override to perform additional checks for createDomain tool
        :param model_dict: the model dictionary
        """
        self.validate_domain_info_section(model_dict)
        self.validate_user_passwords(model_dict)
        ContentValidator.validate_model_content(self, model_dict)

    def validate_domain_info_section(self, model_dict):
        """
        Validate domainInfo section exists in the model.
        :param model_dict: A Python dictionary of the model to be validated
        :return: ValidationException: if problems occur during validation
        """
        _method_name = 'validate_domain_info_section'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        if DOMAIN_INFO not in model_dict:
            self._logger.severe(
                'WLSDPLY-12200', self._model_context.get_program_name(), DOMAIN_INFO,
                self._model_context.get_model_file(), class_name=self._class_name, method_name=_method_name)

        domain_info_dict = dictionary_utils.get_dictionary_element(model_dict, DOMAIN_INFO)
        rcu_info_dict = dictionary_utils.get_dictionary_element(domain_info_dict, RCU_DB_INFO)
        self.__validate_rcu_db_info_section(rcu_info_dict)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def __validate_rcu_db_info_section(self, info_dict):
        _method_name = '__validate_rcu_db_info_section'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        if not self._model_context.get_domain_typedef().requires_rcu():
            return

        rcu_prefix = dictionary_utils.get_element(info_dict, RCU_PREFIX)
        if not rcu_prefix:
            self._logger.severe('WLSDPLY-05304', RCU_DB_INFO, RCU_PREFIX,
                                class_name=self._class_name, method_name=_method_name)

        schema_password = dictionary_utils.get_element(info_dict, RCU_SCHEMA_PASSWORD)
        if not schema_password:
            self._logger.severe('WLSDPLY-05304', RCU_DB_INFO, RCU_SCHEMA_PASSWORD,
                                  class_name=self._class_name, method_name=_method_name)

        self.__validate_rcu_connection_string(info_dict)

        # deprecated fields
        self._check_deprecated_field(DATABASE_TYPE, info_dict, RCU_DB_INFO, ORACLE_DATABASE_CONNECTION_TYPE)
        self._check_deprecated_field(ATP_DEFAULT_TABLESPACE, info_dict, RCU_DB_INFO, RCU_DEFAULT_TABLESPACE)
        self._check_deprecated_field(ATP_TEMPORARY_TABLESPACE, info_dict, RCU_DB_INFO, RCU_TEMP_TBLSPACE)

        # deprecated DATABASE_TYPE, must be ORACLE, ATP, or SSL if specified
        old_database_type = dictionary_utils.get_element(info_dict, DATABASE_TYPE)
        if old_database_type and old_database_type not in DEPRECATED_DB_TYPES:
            self._logger.severe(
                'WLSDPLY-05302', old_database_type, RCU_DB_INFO, DATABASE_TYPE,
                ', '.join(DEPRECATED_DB_TYPES), class_name=self._class_name, method_name=_method_name)

        # RCU_DATABASE_TYPE must be one of allowed types if specified
        database_type = dictionary_utils.get_element(info_dict, RCU_DATABASE_TYPE)
        if database_type and database_type not in ALL_DB_TYPES:
            self._logger.severe(
                'WLSDPLY-05302', database_type, RCU_DB_INFO, RCU_DATABASE_TYPE,
                ', '.join(ALL_DB_TYPES), class_name=self._class_name, method_name=_method_name)

        # ORACLE_DATABASE_CONNECTION_TYPE must be one of allowed types if specified
        connection_type = dictionary_utils.get_element(info_dict, ORACLE_DATABASE_CONNECTION_TYPE)
        if connection_type and connection_type not in ORACLE_DB_CONNECTION_TYPES:
            self._logger.severe(
                'WLSDPLY-05302', connection_type, RCU_DB_INFO, ORACLE_DATABASE_CONNECTION_TYPE,
                ', '.join(ORACLE_DB_CONNECTION_TYPES), class_name=self._class_name, method_name=_method_name)

        if self._model_context.is_run_rcu():
            admin_password = dictionary_utils.get_element(info_dict, RCU_ADMIN_PASSWORD)
            if not admin_password:
                self._logger.severe('WLSDPLY-05305', RCU_DB_INFO, RCU_ADMIN_PASSWORD,
                                    class_name=self._class_name, method_name=_method_name)

    def __validate_rcu_connection_string(self, rcu_info_dict):
        _method_name = '__validate_connection_string'
        connection_string = dictionary_utils.get_element(rcu_info_dict, RCU_DB_CONN_STRING)

        # connection string is required, unless using ORACLE db with tnsnames.ora
        if not connection_string:
            database_type = dictionary_utils.get_element(rcu_info_dict, RCU_DATABASE_TYPE)
            database_type = database_type or RCURunner.ORACLE_DB_TYPE
            is_oracle = database_type in ORACLE_DB_TYPES

            if is_oracle:
                # ORACLE db must have connection string, or TNS admin path and alias
                tns_path = self.__has_tns_path(rcu_info_dict)
                if not tns_path:
                    self._logger.severe(
                        'WLSDPLY-05306', database_type, RCU_DB_INFO, RCU_DB_CONN_STRING,
                        DRIVER_PARAMS_NET_TNS_ADMIN, class_name=self._class_name, method_name=_method_name)

                tns_alias = dictionary_utils.get_element(rcu_info_dict, TNS_ENTRY)
                if not tns_alias:
                    self._logger.severe(
                        'WLSDPLY-05307', database_type, RCU_DB_INFO, RCU_DB_CONN_STRING,
                        TNS_ENTRY, class_name=self._class_name, method_name=_method_name)
            else:
                self._logger.severe(
                    'WLSDPLY-05301', RCU_DB_INFO, RCU_DB_CONN_STRING, RCURunner.ORACLE_DB_TYPE,
                    class_name=self._class_name, method_name=_method_name)


    def __has_tns_path(self, rcu_info_dict):
        """
        Determine if a path to the tnsnames.ora file can be found.
        :param rcu_info_dict: the RCUDbInfo section from the model
        :return: True if a path can be determined, False otherwise
        """
        if dictionary_utils.get_element(rcu_info_dict, DRIVER_PARAMS_NET_TNS_ADMIN):
            return True

        # if there is an RCU wallet in the archive,
        return self._archive_helper and self._archive_helper.has_rcu_wallet_path()

    def validate_user_passwords(self, model_dict):
        """
        Validate user passwords in the model if password validation is enabled
        :param model_dict: the model dictionary
        """
        _method_name = 'validate_user_passwords'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        enabled = self._model_context.get_model_config().get_enable_create_domain_password_validation()
        if not alias_utils.convert_boolean(enabled):
            self._logger.info('WLSDPLY-05202', class_name=self._class_name, method_name=_method_name)
            self._logger.exiting(class_name=self._class_name, method_name=_method_name)
            return

        password_validator_model_map = self._get_system_password_validator_model_map(model_dict)
        password_validator_defaults_map = self._get_system_password_validator_defaults_map()
        password_validator = PasswordValidator(password_validator_model_map, password_validator_defaults_map)
        admin_username, admin_password = self._get_admin_credentials(model_dict)
        users_dict = self._get_users_dictionary(model_dict)

        found_errors = False
        try:
            if not self._model_context.password_is_tokenized(admin_password):
                if not password_validator.validate(admin_username, admin_password):
                    found_errors = True
            else:
                self._logger.notification('WLSDPLY-05208', admin_username,
                                          class_name=self._class_name, method_name=_method_name)
        except ValidateException, ex:
            self._logger.severe('WLSDPLY-05203', ex.getLocalizedMessage(),
                                error=ex, class_name=self._class_name, method_name=_method_name)

        if users_dict:
            for user_name, user_dict in users_dict.items():
                password = dictionary_utils.get_element(user_dict, PASSWORD)
                password = self._aliases.decrypt_password(password)
                try:
                    if not self._model_context.password_is_tokenized(password):
                        if not password_validator.validate(user_name, password):
                            found_errors = True
                    else:
                        self._logger.notification('WLSDPLY-05208', user_name,
                                                  class_name=self._class_name, method_name=_method_name)
                except ValidateException, ex:
                    _logger.severe('WLSDPLY-05204', user_name, ex.getLocalizedMessage(),
                                    error=ex, class_name=self._class_name, method_name=_method_name)

        if found_errors:
            ce = exception_helper.create_validate_exception('WLSDPLY-05205')
            self._logger.throwing(error=ce, class_name=self._class_name, method_name=_method_name)
            raise ce

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)

    def _get_system_password_validator_model_map(self, model_dict):
        _method_name = '_get_system_password_validator_model_map'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        result = dict()
        topology_folder = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        security_config_folder = dictionary_utils.get_dictionary_element(topology_folder, SECURITY_CONFIGURATION)
        realm_name = dictionary_utils.get_element(security_config_folder, DEFAULT_REALM)
        if realm_name is None:
            location = LocationContext()
            location.append_location(SECURITY_CONFIGURATION)
            realm_name = self._aliases.get_model_attribute_default_value(location, DEFAULT_REALM)

        realms_folder = dictionary_utils.get_dictionary_element(security_config_folder, REALM)
        realm_folder = dictionary_utils.get_dictionary_element(realms_folder, realm_name)
        password_validators_folder = dictionary_utils.get_dictionary_element(realm_folder, PASSWORD_VALIDATOR)
        for pv_name, pv_fields in password_validators_folder.items():
            if SYSTEM_PASSWORD_VALIDATOR in pv_fields:
                result = dictionary_utils.get_dictionary_element(pv_fields, SYSTEM_PASSWORD_VALIDATOR)
                break

        result_map = self._dict_to_map(result, 'WLSDPLY-05206')
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result_map)
        return result_map

    def _get_system_password_validator_defaults_map(self):
        _method_name = '_get_system_password_validator_defaults_map'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        location = _get_system_password_validator_location()
        attr_map = self._get_alias_attribute_names_and_types(location)

        default_dict = dict()
        for attr_name, attr_type in attr_map.items():
            default_value = self._aliases.get_model_attribute_default_value(location, attr_name)
            default_dict[attr_name] = default_value

        default_map = self._dict_to_map(default_dict, 'WLSDPLY-05207')
        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=default_map)
        return default_map

    def _get_alias_attribute_names_and_types(self, location = None):
        if location is None:
            location = _get_system_password_validator_location()
        return self._aliases.get_model_attribute_names_and_types(location)

    def _dict_to_map(self, dictionary, message_key):
        _method_name = '_dict_to_map'
        self._logger.entering(dictionary, message_key, class_name=self._class_name, method_name=_method_name)

        result_map = HashMap()
        if dictionary:
            attr_type_map = self._get_alias_attribute_names_and_types()
            for attr_name, attr_value in dictionary.items():
                attr_type = attr_type_map[attr_name]
                self._logger.finer(message_key, attr_name, attr_type, attr_value,
                                   class_name=self._class_name, method_name=_method_name)
                java_value = self._get_java_value(attr_name, attr_type, attr_value)
                if java_value is not None:
                    result_map.put(attr_name, java_value)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result_map)
        return result_map

    def _get_java_value(self, attr_name, attr_type, attr_value):
        _method_name = '_get_java_value'
        self._logger.entering(attr_name, attr_type, attr_value,
                              class_name=self._class_name, method_name=_method_name)

        result = attr_value
        if attr_type == 'integer':
            result = Integer.valueOf('%s' % attr_value)
        elif attr_type == 'boolean':
            result = alias_utils.convert_boolean(attr_value)
            if result is not None:
                result = Boolean.valueOf(result)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name, result=result)
        return result

    def _get_admin_credentials(self, model_dict):
        _method_name = '_get_admin_credentials'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        domain_info_folder = dictionary_utils.get_dictionary_element(model_dict, DOMAIN_INFO)
        admin_username = dictionary_utils.get_element(domain_info_folder, ADMIN_USERNAME)
        if admin_username is None:
            location = LocationContext()
            location.append_location(DOMAIN_INFO_ALIAS)
            admin_username = self._aliases.get_model_attribute_default_value(location, ADMIN_USERNAME)
        admin_password = dictionary_utils.get_element(domain_info_folder, ADMIN_PASSWORD)
        admin_password = self._aliases.decrypt_password(admin_password)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return admin_username, admin_password

    def _get_users_dictionary(self, model_dict):
        _method_name = '_get_users_dictionary'
        self._logger.entering(class_name=self._class_name, method_name=_method_name)

        topology_folder = dictionary_utils.get_dictionary_element(model_dict, TOPOLOGY)
        security_folder = dictionary_utils.get_dictionary_element(topology_folder, SECURITY)
        users_folder = dictionary_utils.get_dictionary_element(security_folder, USER)

        self._logger.exiting(class_name=self._class_name, method_name=_method_name)
        return users_folder

    def _check_deprecated_field(self, field_name, info_dict, folder_name, new_field_name):
        _method_name = '_check_deprecated_field'
        if dictionary_utils.get_element(info_dict, field_name):
            self._logger.deprecation(
                'WLSDPLY-05303', folder_name, field_name, new_field_name,
                class_name=self._class_name, method_name=_method_name)


def _get_system_password_validator_location():
    location = LocationContext()
    location.append_location(SECURITY_CONFIGURATION, REALM, PASSWORD_VALIDATOR, SYSTEM_PASSWORD_VALIDATOR)
    return location
