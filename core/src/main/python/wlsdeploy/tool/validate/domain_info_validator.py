"""
Copyright (c) 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from oracle.weblogic.deploy.create import RCURunner

from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import DATABASE_TYPE
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import METHOD
from wlsdeploy.aliases.model_constants import MODEL_LIST_DELIMITER
from wlsdeploy.aliases.model_constants import ORACLE_DATABASE_CONNECTION_TYPE
from wlsdeploy.aliases.model_constants import PROTOCOL
from wlsdeploy.aliases.model_constants import RCU_DATABASE_TYPE
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import RCU_TEMP_TBLSPACE
from wlsdeploy.aliases.model_constants import REMOTE_RESOURCE
from wlsdeploy.aliases.model_constants import SERVER_GROUP_TARGETING_LIMITS
from wlsdeploy.aliases.model_constants import STORE_TYPE_SSO
from wlsdeploy.aliases.model_constants import WLS_POLICIES
from wlsdeploy.aliases.model_constants import WLS_ROLES
from wlsdeploy.aliases.model_constants import WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS
from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.tool.create import wlspolicies_helper
from wlsdeploy.tool.create import wlsroles_helper
from wlsdeploy.tool.validate.model_validator import ModelValidator
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import unicode_helper as str_helper
from wlsdeploy.util import variables

_class_name = 'DomainInfoValidator'
_logger = PlatformLogger('wlsdeploy.validate')

WALLET_PATH_ATTRIBUTES = [
    DRIVER_PARAMS_KEYSTORE_PROPERTY,
    DRIVER_PARAMS_TRUSTSTORE_PROPERTY
]

ALL_DB_TYPES = [
    RCURunner.ORACLE_DB_TYPE,
    RCURunner.EBR_DB_TYPE,
    RCURunner.SQLSERVER_DB_TYPE,
    RCURunner.DB2_DB_TYPE,
    RCURunner.MYSQL_DB_TYPE
]

ORACLE_DB_CONNECTION_TYPES = [
    RCURunner.ORACLE_ATP_DB_TYPE,
    RCURunner.ORACLE_SSL_DB_TYPE
]

STORE_TYPES = [
    STORE_TYPE_SSO,
    'PKCS12',
    'JKS'
]

RESOURCE_METHODS = [
    'GET',
    'POST'
]

RESOURCE_PROTOCOLS = [
    'http',
    'https',
    't3',
    't3s'
]

DEPRECATED_DB_TYPES = [
    RCURunner.ORACLE_DB_TYPE,
    RCURunner.ORACLE_ATP_DB_TYPE,
    RCURunner.ORACLE_SSL_DB_TYPE
]


class DomainInfoValidator(ModelValidator):
    """
    Class for validating the domainInfo section of a model file
    """

    def __init__(self, variables_map, archive_helper, validation_mode, model_context, aliases,
                 wlst_mode):
        """
        Create a validator instance.
        :param variables_map: map of variables used in the model
        :param archive_helper: used to validate archive paths
        :param model_context: used to get command-line options
        :param aliases: used to validate folders, attributes. also determines exception type
        :param wlst_mode: online or offline mode
        """
        ModelValidator.__init__(self, variables_map, archive_helper, validation_mode, model_context, aliases,
                                wlst_mode)

    def validate(self, model_dict):
        """
        Validate the domainInfo section of the model.
        :param model_dict: the top-level model dictionary
        """
        self.validate_model_section(DOMAIN_INFO, model_dict,
                                    self._aliases.get_model_section_top_level_folder_names(DOMAIN_INFO))

    ####################
    # OVERRIDE METHODS
    ####################

    # Override
    def _validate_folder(self, model_node, location):
        """
        Override this method to perform additional validation of the WLSRoles and WLSPolicies folders.
        This method examines the folder directly below those keys, including the names level.
        """
        ModelValidator._validate_folder(self, model_node, location)

        folder_name = location.get_current_model_folder()
        if folder_name == WLS_ROLES:
            self.__validate_wlsroles_section(model_node)
        elif folder_name == WLS_POLICIES:
            self.__validate_wlspolicies_section(model_node)
        elif folder_name == WLS_USER_PASSWORD_CREDENTIAL_MAPPINGS:
            self.__validate_wls_credential_mappings_section(model_node)
        elif folder_name == RCU_DB_INFO:
            self.__validate_rcu_db_info_section(model_node)

    # Override
    def _validate_attribute(self, attribute_name, attribute_value, valid_attr_infos, path_tokens_attr_keys,
                            model_folder_path, validation_location):
        """
        Extend this method to perform additional validation of the targeting limits attributes.
        """
        ModelValidator._validate_attribute(self, attribute_name, attribute_value, valid_attr_infos,
                                           path_tokens_attr_keys, model_folder_path, validation_location)

        if attribute_name in [SERVER_GROUP_TARGETING_LIMITS, DYNAMIC_CLUSTER_SERVER_GROUP_TARGETING_LIMITS]:
            self.__validate_server_group_targeting_limits(attribute_name, attribute_value, model_folder_path)

    # Override
    def _validate_single_path_in_archive(self, path, attribute_name, model_folder_path):
        """
        Extend this method to allow wallet paths to be in a wallet zip in the archive.
        """
        # avoid INFO WLSDPLY-05031 - *Store paths may be relative to oracle.net.tns_admin,
        # or in a zipped wallet in the archive.
        # these cases are checked using the merged model in create_content_validator.
        if attribute_name in WALLET_PATH_ATTRIBUTES:
            return

        ModelValidator._validate_single_path_in_archive(self, path, attribute_name, model_folder_path)

    ####################
    # PRIVATE METHODS
    ####################

    def __validate_wlspolicies_section(self, policies_dict):
        __method_name = '__validate_wlspolicies_section'
        self._logger.entering(class_name=_class_name, method_name=__method_name)

        # Validate WebLogic policy content using WLSPolicies helper
        wlspolicies_validator = \
            wlspolicies_helper.get_wls_policies_validator(policies_dict, self._model_context, self._logger)
        wlspolicies_validator.validate_policies()

        self._logger.exiting(class_name=_class_name, method_name=__method_name)

    def __validate_wlsroles_section(self, roles_dict):
        __method_name = '__validate_wlsroles_section'
        self._logger.entering(class_name=_class_name, method_name=__method_name)

        # Validate WebLogic role content using WLSRoles helper
        wlsroles_validator = wlsroles_helper.get_wls_roles_validator(self._model_context, roles_dict, self._logger,
                                                                     archive_helper=self._archive_helper)
        wlsroles_validator.validate_roles()

        self._logger.exiting(class_name=_class_name, method_name=__method_name)

    def __validate_wls_credential_mappings_section(self, mappings_dict):
        # This method validates fields that can be checked in an unmerged model, such as value ranges.
        # Checks for merged model (such as required/missing fields) are done in create_content_validator.py .
        _method_name = '__validate_wls_credential_mappings_section'

        # no field checks for cross-domain mappings

        remote_resources_dict = dictionary_utils.get_dictionary_element(mappings_dict, REMOTE_RESOURCE)
        for mapping_name, mapping_dict in remote_resources_dict.iteritems():
            method = dictionary_utils.get_element(mapping_dict, METHOD)
            if method and method not in RESOURCE_METHODS:
                self._logger.severe('WLSDPLY-05313', method, REMOTE_RESOURCE, mapping_name, METHOD,
                                    ', '.join(RESOURCE_METHODS), class_name=_class_name, method_name=_method_name)

            protocol = dictionary_utils.get_element(mapping_dict, PROTOCOL)
            if protocol and protocol not in RESOURCE_PROTOCOLS:
                self._logger.severe('WLSDPLY-05313', protocol, REMOTE_RESOURCE, mapping_name, PROTOCOL,
                                    ', '.join(RESOURCE_PROTOCOLS), class_name=_class_name, method_name=_method_name)

    def __validate_rcu_db_info_section(self, info_dict):
        _method_name = '__validate_rcu_db_info_section'

        # This method validates fields that can be checked in an unmerged model,
        # such as deprecations and value ranges.
        # Checks that must be done on a merged model are done in create_content_validator.py .

        self._check_deprecated_field(DATABASE_TYPE, info_dict, RCU_DB_INFO, ORACLE_DATABASE_CONNECTION_TYPE)
        self._check_deprecated_field(ATP_DEFAULT_TABLESPACE, info_dict, RCU_DB_INFO, RCU_DEFAULT_TABLESPACE)
        self._check_deprecated_field(ATP_TEMPORARY_TABLESPACE, info_dict, RCU_DB_INFO, RCU_TEMP_TBLSPACE)

        # deprecated DATABASE_TYPE, must be ORACLE, ATP, or SSL if specified
        old_database_type = dictionary_utils.get_element(info_dict, DATABASE_TYPE)
        if old_database_type and old_database_type not in DEPRECATED_DB_TYPES:
            self._logger.severe(
                'WLSDPLY-05302', old_database_type, RCU_DB_INFO, DATABASE_TYPE,
                ', '.join(DEPRECATED_DB_TYPES), class_name=_class_name, method_name=_method_name)

        # RCU_DATABASE_TYPE must be one of allowed types if specified
        database_type = dictionary_utils.get_element(info_dict, RCU_DATABASE_TYPE)
        if database_type and database_type not in ALL_DB_TYPES:
            self._logger.severe(
                'WLSDPLY-05302', database_type, RCU_DB_INFO, RCU_DATABASE_TYPE,
                ', '.join(ALL_DB_TYPES), class_name=_class_name, method_name=_method_name)

        # ORACLE_DATABASE_CONNECTION_TYPE must be one of allowed types if specified
        connection_type = dictionary_utils.get_element(info_dict, ORACLE_DATABASE_CONNECTION_TYPE)
        if connection_type and connection_type not in ORACLE_DB_CONNECTION_TYPES:
            self._logger.severe(
                'WLSDPLY-05302', connection_type, RCU_DB_INFO, ORACLE_DATABASE_CONNECTION_TYPE,
                ', '.join(ORACLE_DB_CONNECTION_TYPES), class_name=_class_name, method_name=_method_name)

        # *StoreType must be one of allowed types if specified
        for type_field in [DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY, DRIVER_PARAMS_KEYSTORETYPE_PROPERTY]:
            type_value = dictionary_utils.get_element(info_dict, type_field)
            if type_value and type_value.upper() not in STORE_TYPES:
                self._logger.severe(
                    'WLSDPLY-05302', type_value, RCU_DB_INFO, type_field,
                    ', '.join(STORE_TYPES), class_name=_class_name, method_name=_method_name)

    def __validate_server_group_targeting_limits(self, attribute_key, attribute_value, model_folder_path):
        """
        Verify that entries in the ServerGroupTargetingLimits and DynamicClusterServerGroupTargetingLimits are
        the correct types, and do not use tokens.
        :param attribute_key: the name of the attribute
        :param attribute_value: the value of the attribute
        :param model_folder_path: the model folder path, for logging
        """
        __method_name = '__validate_server_group_targeting_limits'
        self._logger.entering(attribute_key, attribute_value, model_folder_path, class_name=_class_name,
                              method_name=__method_name)

        if attribute_value is not None:
            if not isinstance(attribute_value, dict):
                self._logger.severe('WLSDPLY-05032', attribute_key, model_folder_path,
                                    str_helper.to_string(type(attribute_value)),
                                    class_name=_class_name, method_name=__method_name)
            else:
                model_folder_path += '/' + attribute_key
                for key, value in attribute_value.iteritems():
                    if not isinstance(key, basestring):
                        # Force the key to a string for any value validation issues reported below
                        key = str_helper.to_string(key)
                        self._logger.severe('WLSDPLY-05033', str_helper.to_string, model_folder_path,
                                            str_helper.to_string(type(key)),
                                            class_name=_class_name, method_name=__method_name)
                    else:
                        if variables.has_variables(key):
                            self._report_unsupported_variable_usage(key, model_folder_path)

                    if isinstance(value, basestring) and MODEL_LIST_DELIMITER in value:
                        value = value.split(MODEL_LIST_DELIMITER)

                    if type(value) is list:
                        for element in value:
                            self._validate_single_server_group_target_limits_value(key, element,
                                                                                   model_folder_path)
                    elif isinstance(value, basestring):
                        self._validate_single_server_group_target_limits_value(key, value, model_folder_path)
                    else:
                        self._logger.severe('WLSDPLY-05034', key, model_folder_path,
                                            str_helper.to_string(type(value)),
                                            class_name=_class_name, method_name=__method_name)

        self._logger.exiting(class_name=_class_name, method_name=__method_name)

    def _validate_single_server_group_target_limits_value(self, key, value, model_folder_path):
        _method_name = '_validate_single_server_group_target_limits_value'

        if type(value) in [unicode, str]:
            if variables.has_variables(str_helper.to_string(value)):
                self._report_unsupported_variable_usage(str_helper.to_string(value), model_folder_path)
        else:
            self._logger.severe('WLSDPLY-05035', key, str_helper.to_string(value), model_folder_path,
                                str_helper.to_string(type(value)),
                                class_name=_class_name, method_name=_method_name)

    def _check_deprecated_field(self, field_name, info_dict, folder_name, new_field_name):
        _method_name = '_check_deprecated_field'
        if dictionary_utils.get_element(info_dict, field_name):
            self._logger.deprecation('WLSDPLY-05303', folder_name, field_name, new_field_name,
                                     class_name=_class_name, method_name=_method_name)
