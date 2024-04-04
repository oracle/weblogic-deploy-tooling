"""
Copyright (c) 2017, 2024, Oracle and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
import os

from oracle.weblogic.deploy.create.RCURunner import DB2_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import EBR_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import MYSQL_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import ORACLE_DB_TYPE
from oracle.weblogic.deploy.create.RCURunner import SQLSERVER_DB_TYPE
from oracle.weblogic.deploy.util import WLSDeployArchive

from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import TNS_ENTRY
# Deprecated in WDT 4.0.0
from wlsdeploy.aliases.model_constants import DATABASE_TYPE

from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import ORACLE_DATABASE_CONNECTION_TYPE
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_ADMIN_USER
from wlsdeploy.aliases.model_constants import RCU_COMP_INFO
from wlsdeploy.aliases.model_constants import RCU_DATABASE_TYPE
from wlsdeploy.aliases.model_constants import RCU_DB_CONN_STRING
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import RCU_EDITION
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_STG_INFO
from wlsdeploy.aliases.model_constants import RCU_TEMP_TBLSPACE
from wlsdeploy.aliases.model_constants import RCU_UNICODE_SUPPORT
from wlsdeploy.aliases.model_constants import RCU_VARIABLES
from wlsdeploy.aliases.model_constants import USE_ATP
from wlsdeploy.aliases.model_constants import USE_SSL

from wlsdeploy.logging.platform_logger import PlatformLogger
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util import string_utils

_class_name = 'rcudbinfo_helper'


class RcuDbInfo(object):
    """
    Accesses the fields of the domainInfo/RCUDbInfo section of the model.
    Decrypts fields if the model was encrypted.
    Corrects archive paths for path attributes.
    Returns default values for some unspecified fields.
    """

    def __init__(self, model_context, aliases, rcu_properties_map):
        self.model_context = model_context
        self.aliases = aliases
        self.rcu_properties_map = rcu_properties_map
        self._logger = PlatformLogger('wlsdeploy.util')

    def _get_dictionary_element_value(self, key):
        if self.rcu_properties_map is None:
            return None
        else:
            return dictionary_utils.get_element(self.rcu_properties_map, key)

    def _get_dictionary_path_value(self, key):
        """
        Values may be archive paths, and need adjustment.
        For example, wlsdeploy/dbWallet/* becomes config/wlsdeploy/dbWallet/* .
        Allow for a path that starts with @@DOMAIN_HOME@@ .
        :param key: the key for the RCUDbInfo model folder
        :return: the original value, or an adjusted path if needed
        """
        value = self._get_dictionary_element_value(key)
        if value:
            prefix = ''
            if value.startswith(self.model_context.DOMAIN_HOME_TOKEN):
                # point past the token and first slash
                prefix = self.model_context.DOMAIN_HOME_TOKEN + WLSDeployArchive.ZIP_SEP
                value = value[len(prefix):]
            value = prefix + WLSDeployArchive.getExtractPath(value)
        return value

    def get_rcu_database_type(self):
        rcu_database_type = self._get_dictionary_element_value(RCU_DATABASE_TYPE)
        if rcu_database_type is None:
            rcu_database_type = ORACLE_DB_TYPE
        return rcu_database_type

    def get_oracle_database_connection_type(self):
        _method_name = 'get_oracle_database_connection_type'
        oracle_db_conn_type = self._get_dictionary_element_value(ORACLE_DATABASE_CONNECTION_TYPE)
        if oracle_db_conn_type is None:
            oracle_db_conn_type = self._get_dictionary_element_value(DATABASE_TYPE)
        return oracle_db_conn_type

    def get_rcu_unicode_support(self):
        return self._get_dictionary_element_value(RCU_UNICODE_SUPPORT)

    def get_rcu_edition(self):
        return self._get_dictionary_element_value(RCU_EDITION)

    def get_rcu_default_tablespace(self):
        tablespace = self._get_dictionary_element_value(RCU_DEFAULT_TABLESPACE)
        if self.is_oracle_database_type() and tablespace is None:
            if self.is_use_atp():
                tablespace = 'DATA'
            else:  # for both SSL and ORACLE
                tablespace = 'USERS'
        return tablespace

    def get_rcu_temp_tablespace(self):
        tablespace = self._get_dictionary_element_value(RCU_TEMP_TBLSPACE)
        if self.is_oracle_database_type() and tablespace is None:
            tablespace = 'TEMP'
        return tablespace

    def get_tns_admin(self):
        return self._get_dictionary_path_value(DRIVER_PARAMS_NET_TNS_ADMIN)

    def get_tns_entry(self):
        return self._get_dictionary_element_value(TNS_ENTRY)

    def get_rcu_prefix(self):
        return self._get_dictionary_element_value(RCU_PREFIX)

    def get_rcu_schema_password(self):
        password = self._get_dictionary_element_value(RCU_SCHEMA_PASSWORD)
        rcu_schema_pass = self.aliases.decrypt_password(password)
        return rcu_schema_pass

    def get_keystore(self):
        return self._get_dictionary_path_value(DRIVER_PARAMS_KEYSTORE_PROPERTY)

    def get_qualified_keystore_path(self):
        """
        Prepend the TNS admin path to keystore if keystore is a relative path and not in archive.
        :return: the derived keystore path
        """
        return self.__get_qualified_store_path(self.get_keystore())

    def get_keystore_type(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_KEYSTORETYPE_PROPERTY)

    def get_keystore_password(self):
        password = self._get_dictionary_element_value(DRIVER_PARAMS_KEYSTOREPWD_PROPERTY)
        return self.aliases.decrypt_password(password)

    def get_truststore(self):
        return self._get_dictionary_path_value(DRIVER_PARAMS_TRUSTSTORE_PROPERTY)

    def get_qualified_truststore_path(self):
        """
        Prepend the TNS admin path to truststore if truststore is a relative path and not in archive.
        :return: the derived truststore path
        """
        return self.__get_qualified_store_path(self.get_truststore())

    def get_truststore_type(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY)

    def get_truststore_password(self):
        password = self._get_dictionary_element_value(DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY)
        return self.aliases.decrypt_password(password)

    def get_rcu_db_conn_string(self):
        return self._get_dictionary_element_value(RCU_DB_CONN_STRING)

    def get_atp_default_tablespace(self):
        _method_name = 'get_atp_default_tablespace'
        result = self.get_rcu_default_tablespace()
        if result is None:
            result = self._get_dictionary_element_value(ATP_DEFAULT_TABLESPACE)
        return result

    def get_atp_temporary_tablespace(self):
        _method_name = 'get_atp_temp_tablespace'

        result = self.get_rcu_temp_tablespace()
        if result is None:
            result = self._get_dictionary_element_value(ATP_TEMPORARY_TABLESPACE)
            if result is None:
                result = 'TEMP'
        return result

    def get_rcu_admin_user(self):
        _method_name = 'get_rcu_admin_user'

        rcu_database_type = self.get_rcu_database_type()
        result = self._get_dictionary_element_value(RCU_ADMIN_USER)
        if result is None:
            if self.is_oracle_database_type():
                if self.is_use_atp():
                    result = 'admin'
                else:
                    result = 'SYS'
            elif rcu_database_type == SQLSERVER_DB_TYPE:
                result = 'sa'
            elif rcu_database_type == DB2_DB_TYPE:
                result = 'db2admin'
            elif rcu_database_type == MYSQL_DB_TYPE:
                result = '\'root\'@\'localhost\''
        return result

    def get_comp_info_location(self):
        result = self._get_dictionary_element_value(RCU_COMP_INFO)
        if result is not None:
            return self.model_context.replace_token_string(result)
        return None

    def get_storage_location(self):
        result = self._get_dictionary_element_value(RCU_STG_INFO)
        if result is not None:
            return self.model_context.replace_token_string(result)
        return None

    def get_rcu_variables(self):
        return self._get_dictionary_element_value(RCU_VARIABLES)

    def get_rcu_admin_password(self):
        password = self._get_dictionary_element_value(RCU_ADMIN_PASSWORD)
        rcu_admin_password = self.aliases.decrypt_password(password)
        return rcu_admin_password

    # has_tns_admin is used to find the extract location if it is already extracted by the user
    # it's an optional field, so insufficient to determine whether it has atp
    def has_tns_admin(self):
        result = self._get_dictionary_element_value(DRIVER_PARAMS_NET_TNS_ADMIN)
        return result is not None

    def is_oracle_database_type(self):
        rcu_database_type = self.get_rcu_database_type()
        return rcu_database_type == ORACLE_DB_TYPE or rcu_database_type == EBR_DB_TYPE

    def is_regular_db(self):
        return not (self.is_use_atp() or self.is_use_ssl())

    def is_regular_oracle_db(self):
        return not (self.is_use_atp() or self.is_use_ssl()) and self.is_oracle_database_type()

    def is_use_atp(self):
        """
        Determine if the RCU DB info uses the ATP database.
        The model should allow all the values allowed by boolean alias model elements.
        The default when not specified is False.
        :return: True if the model value is present and indicates true, False otherwise
        """
        _method_name = 'is_use_atp'

        result = False
        if self.is_oracle_database_type():
            use_atp = self.get_oracle_database_connection_type()
            if use_atp is None:
                use_atp = self._get_dictionary_element_value(USE_ATP)
                if use_atp is not None:
                    model_value = self.rcu_properties_map[USE_ATP]
                    value = alias_utils.convert_to_type('boolean', model_value)
                    result = value == 'true'
            else:
                result = use_atp == 'ATP'

        return result

    def is_use_ssl(self):
        """
        Determine if the RCU DB info uses SSL.
        :return: True if the model value is present and set to true
        """
        _method_name = 'is_use_ssl'

        result = False
        if self.is_oracle_database_type():
            use_ssl = self.get_oracle_database_connection_type()
            if use_ssl is None:
                use_ssl = self._get_dictionary_element_value(USE_SSL)
                if use_ssl is not None:
                    model_value = self.rcu_properties_map[USE_SSL]
                    value = alias_utils.convert_to_type('boolean', model_value)
                    result = value == 'true'
            else:
                result = use_ssl == 'SSL'

        return result

    def __get_qualified_store_path(self, store_value):
        return get_qualified_store_path(self.get_tns_admin(), store_value)


# "static" method for validation, etc.
def get_qualified_store_path(tns_admin, store_value):
    if not string_utils.is_empty(store_value) and not string_utils.is_empty(tns_admin) and \
            not os.path.isabs(store_value) and not WLSDeployArchive.isPathIntoArchive(store_value):
        store_value = tns_admin + WLSDeployArchive.ZIP_SEP + store_value
    return store_value


def create(model_dictionary, model_context, aliases):
    """
    Create an RcuDbInfo object from the model dictionary.
    If domainInfo / RCUDbInfo section, create using those values,
    otherwise create from an empty dictionary to use empty or default values.
    :param model_dictionary: the model dictionary to be checked
    :param model_context: used to resolve paths, check CLI arguments
    :param aliases: used for decryption
    :return: a new RcuDbInfo object
    """
    domain_info = dictionary_utils.get_dictionary_element(model_dictionary, DOMAIN_INFO)
    rcu_properties_map = {}
    if RCU_DB_INFO in domain_info:
        rcu_properties_map = domain_info[RCU_DB_INFO]
    return RcuDbInfo(model_context, aliases, rcu_properties_map)
