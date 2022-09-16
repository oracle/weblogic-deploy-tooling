"""
Copyright (c) 2017, 2022, Oracle Corporation and/or its affiliates.
Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
"""
from wlsdeploy.aliases import alias_utils
from wlsdeploy.aliases.model_constants import ATP_ADMIN_USER
from wlsdeploy.aliases.model_constants import ATP_DEFAULT_TABLESPACE
from wlsdeploy.aliases.model_constants import ATP_TEMPORARY_TABLESPACE
from wlsdeploy.aliases.model_constants import TNS_ENTRY
from wlsdeploy.aliases.model_constants import DOMAIN_INFO
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_KEYSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_NET_TNS_ADMIN
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORE_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY
from wlsdeploy.aliases.model_constants import DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY
from wlsdeploy.aliases.model_constants import RCU_ADMIN_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_DB_CONN
from wlsdeploy.aliases.model_constants import RCU_DB_INFO
from wlsdeploy.aliases.model_constants import RCU_DB_USER
from wlsdeploy.aliases.model_constants import RCU_PREFIX
from wlsdeploy.aliases.model_constants import RCU_SCHEMA_PASSWORD
from wlsdeploy.aliases.model_constants import RCU_STG_INFO
from wlsdeploy.aliases.model_constants import RCU_COMP_INFO
from wlsdeploy.aliases.model_constants import RCU_VARIABLES
from wlsdeploy.aliases.model_constants import USE_ATP
from wlsdeploy.aliases.model_constants import USE_SSL
from wlsdeploy.aliases.model_constants import DATABASE_TYPE
from wlsdeploy.aliases.model_constants import RCU_DEFAULT_TBLSPACE
from wlsdeploy.aliases.model_constants import RCU_TEMP_TBLSPACE
from wlsdeploy.util import dictionary_utils
from wlsdeploy.util.model_context import ModelContext
from wlsdeploy.logging.platform_logger import PlatformLogger


_class_name = 'rcudbinfo_helper'

class RcuDbInfo(object):
    """
    Accesses the fields of the domainInfo/RCUDbInfo section of the model.
    Decrypts fields if the model was encrypted.
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

    def get_database_type(self):
        type = self._get_dictionary_element_value(DATABASE_TYPE)
        if type is None:
            return 'ORACLE'
        else:
            return type

    def get_rcu_default_tablespace(self):
        type = self._get_dictionary_element_value(RCU_DEFAULT_TBLSPACE)
        if type is None:
            if self.is_use_atp():
                return 'DATA'
            else:  # for both SSL and ORACLE
                return 'USERS'
        else:
            return type

    def get_rcu_temp_tablespace(self):
        type = self._get_dictionary_element_value(RCU_TEMP_TBLSPACE)
        if type is None:
            return 'TEMP'
        else:
            return type

    def get_tns_admin(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_NET_TNS_ADMIN)

    def get_tns_entry(self):
        entry = self._get_dictionary_element_value(TNS_ENTRY)
        if entry is not None:
            return entry
        else:
            return None

    def get_rcu_prefix(self):
        return self._get_dictionary_element_value(RCU_PREFIX)

    def get_rcu_schema_password(self):
        password = self._get_dictionary_element_value(RCU_SCHEMA_PASSWORD)
        return self.aliases.decrypt_password(password)

    def get_keystore(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_kEYSTORE_PROPERTY)

    def get_keystore_type(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_KEYSTORETYPE_PROPERTY)

    def get_keystore_password(self):
        password = self._get_dictionary_element_value(DRIVER_PARAMS_KEYSTOREPWD_PROPERTY)
        return self.aliases.decrypt_password(password)

    def get_truststore(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_TRUSTSTORE_PROPERTY)

    def get_truststore_type(self):
        return self._get_dictionary_element_value(DRIVER_PARAMS_TRUSTSTORETYPE_PROPERTY)

    def get_truststore_password(self):
        password = self._get_dictionary_element_value(DRIVER_PARAMS_TRUSTSTOREPWD_PROPERTY)
        return self.aliases.decrypt_password(password)

    def get_admin_password(self):
        password = self._get_dictionary_element_value(RCU_ADMIN_PASSWORD)
        return self.aliases.decrypt_password(password)

    def get_rcu_regular_db_conn(self):
        return self._get_dictionary_element_value(RCU_DB_CONN)

    def get_atp_default_tablespace(self):
        _method_name = 'get_atp_default_tablespace'
        result = self._get_dictionary_element_value(ATP_DEFAULT_TABLESPACE)
        if result is not None:
            self._logger.warning('WLSDPLY-22000', ATP_DEFAULT_TABLESPACE, RCU_DEFAULT_TBLSPACE,
                              class_name=_class_name, method_name=_method_name)
            return result
        elif self.get_rcu_default_tablespace() is not None:
            return self.get_rcu_default_tablespace()
        else:
            return self.get_rcu_default_tablespace()

    def get_atp_temporary_tablespace(self):
        _method_name = 'get_atp_temp_tablespace'
        result = self._get_dictionary_element_value(ATP_TEMPORARY_TABLESPACE)
        if result is not None:
            self._logger.warning('WLSDPLY-22000', ATP_TEMPORARY_TABLESPACE, RCU_TEMP_TBLSPACE,
                              class_name=_class_name, method_name=_method_name)
            return result
        elif self.get_rcu_temp_tablespace() is not None:
            return self.get_rcu_temp_tablespace()
        else:
            return 'TEMP'

    def get_atp_admin_user(self):
        _method_name = 'get_atp_admin_user'
        result = self._get_dictionary_element_value(ATP_ADMIN_USER)
        if result is not None:
            self._logger.warning('WLSDPLY-22000', ATP_ADMIN_USER, RCU_DB_USER,
                              class_name=_class_name, method_name=_method_name)
            return result
        elif self.get_rcu_db_user() is not None:
            return self.get_rcu_db_user()
        else:
            return 'admin'

    def get_rcu_db_user(self):
        result = self._get_dictionary_element_value(RCU_DB_USER)
        if result is not None:
            return result
        else:
            return ModelContext.DB_USER_DEFAULT

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
        result = self._get_dictionary_element_value(RCU_VARIABLES)
        if result is not None:
            return result
        else:
            return None

    # has_tns_admin is used to find the extract location if it is already extracted by the user
    # its an optional field, so insufficient to determine whether it has atp
    def has_tns_admin(self):
        result = self._get_dictionary_element_value(DRIVER_PARAMS_NET_TNS_ADMIN)
        return result is not None

    def has_atpdbinfo(self):
        return self.is_use_atp()

    def has_ssldbinfo(self):
        return self.is_use_ssl()

    def is_multidatasource(self):
        if self.get_multidatasource_urls() is not None and self.get_database_type() != 'AGL':
            return True
        else:
            return False

    def is_regular_db(self):
        result = self._get_dictionary_element_value(RCU_DB_CONN)
        if result is not None:
            if self.get_database_type() == 'ORACLE' and  not (self.is_use_atp() or self.is_use_ssl()):
                return True
        return False

    def is_use_atp(self):
        """
        Determine if the RCU DB info uses the ATP database.
        The model should allow all the values allowed by boolean alias model elements.
        The default when not specified is False.
        :return: True if the model value is present and indicates true, False otherwise
        """
        _method_name = 'is_use_atp'
        result = self._get_dictionary_element_value(USE_ATP)
        if result is not None:
            self._logger.warning('WLSDPLY-22000', USE_ATP, DATABASE_TYPE,
                              class_name=_class_name, method_name=_method_name)
            model_value = self.rcu_properties_map[USE_ATP]
            value = alias_utils.convert_to_type('boolean', model_value)
            return value == 'true'

        return self.get_database_type() == 'ATP'

    def is_use_ssl(self):
        """
        Determine if the RCU DB info uses SSL.user
        :return: True if the model value is present and set to true
        """
        _method_name = 'is_use_ssl'
        result = self._get_dictionary_element_value(USE_SSL)
        if result is not None:
            self._logger.warning('WLSDPLY-22000', USE_ATP, DATABASE_TYPE,
                              class_name=_class_name, method_name=_method_name)
            model_value = self.rcu_properties_map[USE_SSL]
            value = alias_utils.convert_to_type('boolean', model_value)
            return value == 'true'
        return self.get_database_type() == 'SSL'
        
    def get_preferred_db(self):
        """
        Return the regular db connect string from command line or model.
        :return: the db connect string
        """
        cli_value = self.model_context.get_rcu_database()
        if cli_value is not None:
            return cli_value
        return self.get_rcu_regular_db_conn()

    def get_preferred_db_user(self):
        """
        Return the db user from command line or model.
        :return: the db user
        """
        cli_value = self.model_context.get_rcu_db_user()
        if cli_value != ModelContext.DB_USER_DEFAULT:
            return cli_value
        return self.get_rcu_db_user()

    def get_preferred_prefix(self):
        """
        Return the prefix from command line or model.
        :return: the prefix
        """
        cli_value = self.model_context.get_rcu_prefix()
        if cli_value is not None:
            return cli_value
        return self.get_rcu_prefix()

    def get_preferred_schema_pass(self):
        """
        Return the schema password from command line or model.
        :return: the schema password
        """
        cli_value = self.model_context.get_rcu_schema_pass()
        if cli_value is not None:
            return cli_value
        return self.get_rcu_schema_password()

    def get_preferred_sys_pass(self):
        """
        Return the system password from command line or model.
        :return: the system password
        """
        cli_value = self.model_context.get_rcu_sys_pass()
        if cli_value is not None:
            return cli_value
        return self.get_admin_password()


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
